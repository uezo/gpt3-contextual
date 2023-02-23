import json
from gpt3contextual.models import Context, CompletionLog


class TestContext:
    def test_get_histories(self):
        context = Context(
            key="1234",
            username="Alice",
            agentname="Bob",
            chat_description="A conversation between Alice and Bob",
            history_count=6,
            histories=json.dumps(["line01", "line02", "line03", "line04", "line05", "line06", "line07", "line08"])
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
            histories=json.dumps(["line01", "line02", "line03", "line04", "line05", "line06", "line07", "line08"])
        )
        context.add_history("line09")
        assert context.get_histories() == "line04\nline05\nline06\nline07\nline08\nline09"

    def test_clear_history(self):
        context = Context(
            key="1234",
            username="Alice",
            agentname="Bob",
            chat_description="A conversation between Alice and Bob",
            history_count=6,
            histories=json.dumps(["line01", "line02", "line03", "line04", "line05", "line06", "line07", "line08"])
        )
        context.clear_history()
        assert context.get_histories() == ""


class TestCompletionLog:
    def test_init(self):
        CompletionLog()
