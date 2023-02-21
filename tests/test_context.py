from gpt3contextual.context import Context, ContextManager


class TestContext:
    def test_get_histories(self):
        context = Context(
            key="1234",
            username="Alice",
            agentname="Bob",
            chat_description="A conversation between Alice and Bob",
            history_count=6,
            histories=["line01", "line02", "line03", "line04", "line05", "line06", "line07", "line08"]
        )
        assert context.get_histories() == "line03\nline04\nline05\nline06\nline07\nline08"
        context.history_count = 4
        assert context.get_histories() == "line05\nline06\nline07\nline08"
        context.history_count = 8
        assert context.get_histories() == "line01\nline02\nline03\nline04\nline05\nline06\nline07\nline08"
        context.history_count = 10
        assert context.get_histories() == "line01\nline02\nline03\nline04\nline05\nline06\nline07\nline08"
        context.history_count = 0
        assert context.get_histories() == "line01\nline02\nline03\nline04\nline05\nline06\nline07\nline08"

    def test_add_history(self):
        context = Context(
            key="1234",
            username="Alice",
            agentname="Bob",
            chat_description="A conversation between Alice and Bob",
            history_count=6,
            histories=["line01", "line02", "line03", "line04", "line05", "line06", "line07", "line08"]
        )
        context.add_history("line09")
        assert context.get_histories() == "line04\nline05\nline06\nline07\nline08\nline09"


class TestContextManager:
    def test_get(self):
        manager = ContextManager(
            timeout=300,
            username="Alice",
            agentname="Bob",
            chat_description="A conversation between Alice and Bob",
            history_count=6,
        )
        context = manager.get("1234")
        assert context.username == "Alice"
        assert context.agentname == "Bob"
        assert context.chat_description == "A conversation between Alice and Bob"
        assert context.history_count == 6

        manager.set(Context(
            key="2345",
            username="A",
            agentname="B",
            chat_description="A and B",
            history_count=10,
            histories=["line01", "line02", "line03", "line04", "line05", "line06", "line07", "line08"]
        ))
        context = manager.get("2345")
        assert context.username == "A"
        assert context.agentname == "B"
        assert context.chat_description == "A and B"
        assert context.history_count == 10

    def test_set(self):
        manager = ContextManager(
            timeout=300,
            username="Alice",
            agentname="Bob",
            chat_description="A conversation between Alice and Bob",
            history_count=6,
        )
        context = Context(
            key="1234",
            username="Alice",
            agentname="Bob",
            chat_description="A conversation between Alice and Bob",
            history_count=6,
            histories=["hi", "hello", "how are you", "goodbye"]
        )
        manager.set(context)
        assert manager.get("1234").histories == context.histories

    def test_reset(self):
        manager = ContextManager(
            timeout=300,
            username="Alice",
            agentname="Bob",
            chat_description="A conversation between Alice and Bob",
            history_count=6,
        )
        context = Context(
            key="1234",
            username="Alice",
            agentname="Bob",
            chat_description="A conversation between Alice and Bob",
            history_count=6,
            histories=["hi", "hello", "how are you", "goodbye"]
        )
        manager.set(context)
        manager.reset("1234", username="Chris", agentname="Dave", chat_description="A conversation between Chris and Dave", history_count=10)
        context = manager.get("1234")
        assert context.username == "Chris"
        assert context.agentname == "Dave"
        assert context.chat_description == "A conversation between Chris and Dave"
        assert context.history_count == 10
        assert context.histories == []

    def test_remove(self):
        manager = ContextManager(
            timeout=300,
            username="Alice",
            agentname="Bob",
            chat_description="A conversation between Alice and Bob",
            history_count=6,
        )
        context = Context(
            key="1234",
            username="Chris",
            agentname="Dave",
            chat_description="A conversation between Chris and Dave",
            history_count=10,
            histories=["hi", "hello", "how are you", "goodbye"]
        )
        manager.set(context)
        assert manager.get("1234").key == "1234"
        assert context.username == "Chris"
        assert context.agentname == "Dave"
        assert context.chat_description == "A conversation between Chris and Dave"
        assert context.history_count == 10

        manager.remove("1234")
        context = manager.get("1234")
        assert context.key == "1234"
        assert context.username == "Alice"
        assert context.agentname == "Bob"
        assert context.chat_description == "A conversation between Alice and Bob"
        assert context.history_count == 6
