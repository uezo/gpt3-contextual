import pytest
import json
import time
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from gpt3contextual.models import Context, create_tables
from gpt3contextual.chat import ContextManager

connection_str = "sqlite:///test_context.db"


@pytest.fixture
def get_session():
    engine = create_engine(connection_str)
    create_tables(engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


class TestContextManager:
    def test_get(self, get_session):
        key1 = str(uuid4())
        key2 = str(uuid4())

        manager = ContextManager(
            timeout=3,
            username="Alice",
            agentname="Bob",
            chat_description="A conversation between Alice and Bob",
            history_count=6,
        )

        session = get_session()

        context = manager.get(session, key1)
        assert context.username == "Alice"
        assert context.agentname == "Bob"
        assert context.chat_description == "A conversation between Alice and Bob"
        assert context.history_count == 6

        manager.set(session, Context(
            key=key2,
            username="A",
            agentname="B",
            chat_description="A and B",
            history_count=10,
            histories=json.dumps(["line01", "line02", "line03", "line04", "line05", "line06", "line07", "line08"])
        ))
        context = manager.get(session, key2)
        assert context.username == "A"
        assert context.agentname == "B"
        assert context.chat_description == "A and B"
        assert context.history_count == 10
        assert context.get_histories() == "\n".join(["line01", "line02", "line03", "line04", "line05", "line06", "line07", "line08"])

        time.sleep(1)  # shorter than timeout(3)

        context = manager.get(session, key2)
        assert context.username == "A"
        assert context.agentname == "B"
        assert context.chat_description == "A and B"
        assert context.history_count == 10
        assert context.get_histories() == "\n".join(["line01", "line02", "line03", "line04", "line05", "line06", "line07", "line08"])

        time.sleep(5)  # longer than timeout(3)

        context = manager.get(session, key2)
        assert context.username == "A"
        assert context.agentname == "B"
        assert context.chat_description == "A and B"
        assert context.history_count == 10
        assert context.get_histories() == ""

        session.close()

    def test_set(self, get_session):
        key = str(uuid4())

        manager = ContextManager(
            timeout=300,
            username="Alice",
            agentname="Bob",
            chat_description="A conversation between Alice and Bob",
            history_count=6,
        )
        context = Context(
            key=key,
            username="Alice",
            agentname="Bob",
            chat_description="A conversation between Alice and Bob",
            history_count=6,
            histories=json.dumps(["hi", "hello", "how are you", "goodbye"])
        )
        session = get_session()
        manager.set(session, context)
        assert manager.get(session, key).histories == context.histories

        session.close()

    def test_reset(self, get_session):
        key = str(uuid4())

        manager = ContextManager(
            timeout=300,
            username="Alice",
            agentname="Bob",
            chat_description="A conversation between Alice and Bob",
            history_count=6,
        )
        context = Context(
            key=key,
            username="Alice",
            agentname="Bob",
            chat_description="A conversation between Alice and Bob",
            history_count=6,
            histories=json.dumps(["hi", "hello", "how are you", "goodbye"])
        )
        session = get_session()
        manager.set(session, context)
        manager.reset(session, key, username="Chris", agentname="Dave", chat_description="A conversation between Chris and Dave", history_count=10)
        context = manager.get(session, key)
        assert context.username == "Chris"
        assert context.agentname == "Dave"
        assert context.chat_description == "A conversation between Chris and Dave"
        assert context.history_count == 10
        assert context.histories == json.dumps([])

        session.close()

    def test_remove(self, get_session):
        key = str(uuid4())

        manager = ContextManager(
            timeout=300,
            username="Alice",
            agentname="Bob",
            chat_description="A conversation between Alice and Bob",
            history_count=6,
        )
        context = Context(
            key=key,
            username="Chris",
            agentname="Dave",
            chat_description="A conversation between Chris and Dave",
            history_count=10,
            histories=json.dumps(["hi", "hello", "how are you", "goodbye"])
        )
        session = get_session()
        manager.set(session, context)
        assert manager.get(session, key).key == key
        assert context.username == "Chris"
        assert context.agentname == "Dave"
        assert context.chat_description == "A conversation between Chris and Dave"
        assert context.history_count == 10

        print(key)
        manager.remove(session, key)
        context = manager.get(session, key)
        assert context.key == key
        assert context.username == "Alice"
        assert context.agentname == "Bob"
        assert context.chat_description == "A conversation between Alice and Bob"
        assert context.history_count == 6

        session.close()
