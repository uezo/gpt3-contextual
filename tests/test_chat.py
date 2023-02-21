import pytest
from gpt3contextual.chat import ContextualChat, CompletionException
from gpt3contextual.context import Context, ContextManager

openapi_apikey = "SET_YOUR_OPENAI_API_KEY"


class TestCompletionException:
    def test_init(self):
        ex = CompletionException("error", completion_response={"foo": "bar"})
        assert str(ex) == "error"
        assert ex.completion_response == {"foo": "bar"}


class TestContextualChat:
    def test_make_prompt(self):
        cc = ContextualChat(openapi_apikey, ContextManager())
        context = Context(
            key="1234",
            username="A",
            agentname="B",
            chat_description="A conversation between A and B",
            history_count=4,
            histories=["A:line01", "B:line02", "A:line03", "B:line04", "A:line05", "B:line06", "A:line07", "B:line08"]
        )

        prompt = cc.make_prompt(context, "hello")

        assert prompt == "A conversation between A and B\nA:line05\nB:line06\nA:line07\nB:line08\nA:hello\nB:"

    def test_update_context(self):
        cm = ContextManager()
        cc = ContextualChat(openapi_apikey, cm)

        context = Context(
            key="1234",
            username="A",
            agentname="B",
            chat_description="A conversation between A and B",
            history_count=4,
            histories=["A:line01", "B:line02", "A:line03", "B:line04", "A:line05", "B:line06", "A:line07", "B:line08"]
        )
        cm.set(context)

        cc.update_context(context, "hello", "hi", {})

        context = cm.get("1234")
        assert context.username == "A"
        assert context.agentname == "B"
        assert context.chat_description == "A conversation between A and B"
        assert context.history_count == 4
        assert context.get_histories() == "A:line07\nB:line08\nA:hello\nB:hi"

        with pytest.raises(CompletionException):
            cc.update_context(context, "hello", None, {"foo": "bar"})

        context = cm.get("1234")
        assert context.username == "A"
        assert context.agentname == "B"
        assert context.chat_description == "A conversation between A and B"
        assert context.history_count == 4
        assert context.get_histories() == ""

    def test_chat(self):
        cm = ContextManager()
        cc = ContextualChat(openapi_apikey, cm)

        context = Context(
            key="1234",
            username="A",
            agentname="B",
            chat_description="Just echo the text from A",
            history_count=4,
            histories=["A:line01", "B:line01", "A:line02", "B:line02", "A:line03", "B:line03", "A:line04", "B:line04"]
        )
        cm.set(context)

        resp, prompt, _ = cc.chat_sync("1234", "hello")

        assert resp == "hello"
        assert prompt == "Just echo the text from A\nA:line03\nB:line03\nA:line04\nB:line04\nA:hello\nB:"

        context = cm.get("1234")
        assert context.username == "A"
        assert context.agentname == "B"
        assert context.chat_description == "Just echo the text from A"
        assert context.history_count == 4
        assert context.get_histories() == "A:line04\nB:line04\nA:hello\nB:hello"
