import pytest
import json
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from gpt3contextual.chat import (
    ContextualChat,
    ContextualChatGPT,
    ContextManager,
    CompletionException
)
from gpt3contextual.models import Context, create_tables

connection_str = "sqlite:///test_chat.db"
openai_apikey = "SET_YOUR_OPENAI_API_KEY"


@pytest.fixture
def get_session():
    engine = create_engine(connection_str)
    create_tables(engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


class TestCompletionException:
    def test_init(self):
        ex = CompletionException("error", completion_response={"foo": "bar"})
        assert str(ex) == "error"
        assert ex.completion_response == {"foo": "bar"}


class TestContextualChat:
    def test_make_prompt(self):
        key = str(uuid4())
        cc = ContextualChat(openai_apikey, connection_str)

        context = Context(
            key=key,
            username="A",
            agentname="B",
            chat_description="A conversation between A and B",
            history_count=4,
            histories=json.dumps(["A:line01", "B:line02", "A:line03", "B:line04", "A:line05", "B:line06", "A:line07", "B:line08"])
        )

        prompt = cc.make_prompt(context, "hello")

        assert prompt == "A conversation between A and B\nA:line05\nB:line06\nA:line07\nB:line08\nA:hello\nB:"

    def test_make_params(self):
        key = str(uuid4())
        cc = ContextualChat(openai_apikey, connection_str)

        context = Context(
            key=key,
            username="A",
            agentname="B",
            chat_description="A conversation between A and B",
            history_count=4,
            histories=json.dumps(["A:line01", "B:line02", "A:line03", "B:line04", "A:line05", "B:line06", "A:line07", "B:line08"])
        )

        prompt = cc.make_prompt(context, "hello")

        completion_params = {
            "api_key": "new_api_key",
            "model": "new_model",
            "temperature": 0.1,
            "max_tokens": 1234,
            "stop": ["new_stop1", "new_stop2"]
        }
        params = cc.make_params(context, prompt=prompt, completion_params=completion_params)
        assert params["api_key"] == "new_api_key"
        assert params["model"] == "new_model"
        assert params["temperature"] == 0.1
        assert params["max_tokens"] == 1234
        assert params["stop"] == ["new_stop1", "new_stop2"]
        assert params["prompt"] == "A conversation between A and B\nA:line05\nB:line06\nA:line07\nB:line08\nA:hello\nB:"

        completion_params = {
            "api_key": "new_api_key",
            "model": "new_model"
        }
        params = cc.make_params(context, prompt=prompt, completion_params=completion_params)
        assert params["api_key"] == "new_api_key"
        assert params["model"] == "new_model"
        assert params["temperature"] == cc.temperature
        assert params["max_tokens"] == cc.max_tokens
        assert params["stop"] == [f"{context.username}:", f"{context.agentname}:"]
        assert params["prompt"] == "A conversation between A and B\nA:line05\nB:line06\nA:line07\nB:line08\nA:hello\nB:"

        params = cc.make_params(context, prompt=prompt)
        assert params["api_key"] == cc.api_key
        assert params["model"] == cc.model
        assert params["temperature"] == cc.temperature
        assert params["max_tokens"] == cc.max_tokens
        assert params["stop"] == [f"{context.username}:", f"{context.agentname}:"]
        assert params["prompt"] == "A conversation between A and B\nA:line05\nB:line06\nA:line07\nB:line08\nA:hello\nB:"

    def test_update_context(self, get_session):
        key = str(uuid4())
        cm = ContextManager()
        cc = ContextualChat(openai_apikey, connection_str, cm)

        context = Context(
            key=key,
            username="A",
            agentname="B",
            chat_description="A conversation between A and B",
            history_count=4,
            histories=json.dumps(["A:line01", "B:line02", "A:line03", "B:line04", "A:line05", "B:line06", "A:line07", "B:line08"])
        )

        with get_session() as session:
            cm.set(session, context)
            cc.update_context(session, context, "hello", "hi", {"object": "text_completion"})

            context = cm.get(session, key)
            assert context.username == "A"
            assert context.agentname == "B"
            assert context.chat_description == "A conversation between A and B"
            assert context.history_count == 4
            assert context.get_histories() == "A:line07\nB:line08\nA:hello\nB:hi"

            with pytest.raises(CompletionException):
                cc.update_context(session, context, "hello", None, {"foo": "bar"})

            context = cm.get(session, key)
            assert context.username == "A"
            assert context.agentname == "B"
            assert context.chat_description == "A conversation between A and B"
            assert context.history_count == 4
            assert context.get_histories() == ""

    def test_chat(self, get_session):
        key = str(uuid4())
        cm = ContextManager()
        cc = ContextualChat(openai_apikey, connection_str)

        context = Context(
            key=key,
            username="A",
            agentname="B",
            chat_description="Just echo the text from A",
            history_count=4,
            histories=json.dumps(["A:line01", "B:line01", "A:line02", "B:line02", "A:line03", "B:line03", "A:line04", "B:line04"])
        )

        with get_session() as session:
            cm.set(session, context)

        resp, params, _ = cc.chat_sync(key, "hello")

        assert resp == "hello"
        assert params["prompt"] == "Just echo the text from A\nA:line03\nB:line03\nA:line04\nB:line04\nA:hello\nB:"

        with get_session() as session:
            context = cm.get(session, key)
            assert context.username == "A"
            assert context.agentname == "B"
            assert context.chat_description == "Just echo the text from A"
            assert context.history_count == 4
            assert context.get_histories() == "A:line04\nB:line04\nA:hello\nB:hello"


class TestContextualChatGPT:
    def test_make_messages(self):
        key = str(uuid4())
        cc = ContextualChatGPT(openai_apikey, connection_str)

        context = Context(
            key=key,
            username="A",
            agentname="B",
            chat_description="A conversation between A and B",
            history_count=4,
            histories=json.dumps(["line01", "line02", "line03", "line04", "line05", "line06", "line07", "line08"])
        )

        messages = cc.make_messages(context, "hello")

        assert messages == [{"role": "system", "content": "[Roles]\nuser: A\nassistant: B\n\n[Conditions]\nA conversation between A and B"}, {"role": "user", "content": "line05"}, {"role": "assistant", "content": "line06"}, {"role": "user", "content": "line07"}, {"role": "assistant", "content": "line08"}, {"role": "user", "content": "hello"}]

    def test_make_params(self):
        key = str(uuid4())
        cc = ContextualChat(openai_apikey, connection_str)

        context = Context(
            key=key,
            username="A",
            agentname="B",
            chat_description="A conversation between A and B",
            history_count=4,
            histories=json.dumps(["A:line01", "B:line02", "A:line03", "B:line04", "A:line05", "B:line06", "A:line07", "B:line08"])
        )

        prompt = cc.make_prompt(context, "hello")

        completion_params = {
            "api_key": "new_api_key",
            "model": "new_model",
            "temperature": 0.1,
            "max_tokens": 1234,
            "stop": ["new_stop1", "new_stop2"]
        }
        params = cc.make_params(context, prompt=prompt, completion_params=completion_params)
        assert params["api_key"] == "new_api_key"
        assert params["model"] == "new_model"
        assert params["temperature"] == 0.1
        assert params["max_tokens"] == 1234
        assert params["stop"] == ["new_stop1", "new_stop2"]
        assert params["prompt"] == "A conversation between A and B\nA:line05\nB:line06\nA:line07\nB:line08\nA:hello\nB:"

        completion_params = {
            "api_key": "new_api_key",
            "model": "new_model"
        }
        params = cc.make_params(context, prompt=prompt, completion_params=completion_params)
        assert params["api_key"] == "new_api_key"
        assert params["model"] == "new_model"
        assert params["temperature"] == cc.temperature
        assert params["max_tokens"] == cc.max_tokens
        assert params["stop"] == [f"{context.username}:", f"{context.agentname}:"]
        assert params["prompt"] == "A conversation between A and B\nA:line05\nB:line06\nA:line07\nB:line08\nA:hello\nB:"

        params = cc.make_params(context, prompt=prompt)
        assert params["api_key"] == cc.api_key
        assert params["model"] == cc.model
        assert params["temperature"] == cc.temperature
        assert params["max_tokens"] == cc.max_tokens
        assert params["stop"] == [f"{context.username}:", f"{context.agentname}:"]
        assert params["prompt"] == "A conversation between A and B\nA:line05\nB:line06\nA:line07\nB:line08\nA:hello\nB:"

    def test_update_context(self, get_session):
        key = str(uuid4())
        cm = ContextManager()
        cc = ContextualChatGPT(openai_apikey, connection_str, cm)

        context = Context(
            key=key,
            username="A",
            agentname="B",
            chat_description="A conversation between A and B",
            history_count=4,
            histories=json.dumps(["line01", "line02", "line03", "line04", "line05", "line06", "line07", "line08"])
        )

        with get_session() as session:
            cm.set(session, context)
            cc.update_context(session, context, "hello", "hi", {"object": "chat.completion"})

            context = cm.get(session, key)
            assert context.username == "A"
            assert context.agentname == "B"
            assert context.chat_description == "A conversation between A and B"
            assert context.history_count == 4
            assert context.get_histories() == "line07\nline08\nhello\nhi"

            with pytest.raises(CompletionException):
                cc.update_context(session, context, "hello", None, {"foo": "bar"})

            context = cm.get(session, key)
            assert context.username == "A"
            assert context.agentname == "B"
            assert context.chat_description == "A conversation between A and B"
            assert context.history_count == 4
            assert context.get_histories() == ""

    def test_chat(self, get_session):
        key = str(uuid4())
        cm = ContextManager()
        cc = ContextualChatGPT(openai_apikey, connection_str)

        context = Context(
            key=key,
            username="A",
            agentname="B",
            chat_description="Just echo the text from A",
            history_count=4,
            histories=json.dumps(["line01", "line01", "line02", "line02", "line03", "line03", "line04", "line04"])
        )

        with get_session() as session:
            cm.set(session, context)

        resp, params, _ = cc.chat_sync(key, "hello")

        assert resp == "hello"
        assert params["messages"] == [{"role": "system", "content": "[Roles]\nuser: A\nassistant: B\n\n[Conditions]\nJust echo the text from A"}, {"role": "user", "content": "line03"}, {"role": "assistant", "content": "line03"}, {"role": "user", "content": "line04"}, {"role": "assistant", "content": "line04"}, {"role": "user", "content": "hello"}]
        with get_session() as session:
            context = cm.get(session, key)
            assert context.username == "A"
            assert context.agentname == "B"
            assert context.chat_description == "Just echo the text from A"
            assert context.history_count == 4
            assert context.get_histories() == "line04\nline04\nhello\nhello"
