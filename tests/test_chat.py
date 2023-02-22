import pytest
from gpt3contextual.chat import ContextualChat, CompletionException
from gpt3contextual.context import Context, ContextManager

openai_apikey = "SET_YOUR_OPENAI_API_KEY"


class TestCompletionException:
    def test_init(self):
        ex = CompletionException("error", completion_response={"foo": "bar"})
        assert str(ex) == "error"
        assert ex.completion_response == {"foo": "bar"}


class TestContextualChat:
    def test_make_prompt(self):
        cc = ContextualChat(openai_apikey, ContextManager())
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

    def test_make_params(self):
        cc = ContextualChat(openai_apikey, ContextManager())
        context = Context(
            key="1234",
            username="A",
            agentname="B",
            chat_description="A conversation between A and B",
            history_count=4,
            histories=["A:line01", "B:line02", "A:line03", "B:line04", "A:line05", "B:line06", "A:line07", "B:line08"]
        )

        prompt = cc.make_prompt(context, "hello")

        completion_params = {
            "api_key": "new_api_key",
            "engine": "new_engine",
            "temperature": 0.1,
            "max_tokens": 1234,
            "stop": ["new_stop1", "new_stop2"],
            "prompt": "new_prompt"
        }
        params = cc.make_params(context, prompt, completion_params)
        assert params["api_key"] == "new_api_key"
        assert params["engine"] == "new_engine"
        assert params["temperature"] == 0.1
        assert params["max_tokens"] == 1234
        assert params["stop"] == ["new_stop1", "new_stop2"]
        assert params["prompt"] == "new_prompt"

        completion_params = {
            "api_key": "new_api_key",
            "engine": "new_engine"
        }
        params = cc.make_params(context, prompt, completion_params)
        assert params["api_key"] == "new_api_key"
        assert params["engine"] == "new_engine"
        assert params["temperature"] == cc.temperature
        assert params["max_tokens"] == cc.max_tokens
        assert params["stop"] == [f"{context.username}:", f"{context.agentname}:"]
        assert params["prompt"] == prompt

        completion_params = None
        params = cc.make_params(context, prompt, completion_params)
        assert params["api_key"] == cc.api_key
        assert params["engine"] == cc.engine
        assert params["temperature"] == cc.temperature
        assert params["max_tokens"] == cc.max_tokens
        assert params["stop"] == [f"{context.username}:", f"{context.agentname}:"]
        assert params["prompt"] == prompt

    def test_update_context(self):
        cm = ContextManager()
        cc = ContextualChat(openai_apikey, cm)

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
        cc = ContextualChat(openai_apikey, cm)

        context = Context(
            key="1234",
            username="A",
            agentname="B",
            chat_description="Just echo the text from A",
            history_count=4,
            histories=["A:line01", "B:line01", "A:line02", "B:line02", "A:line03", "B:line03", "A:line04", "B:line04"]
        )
        cm.set(context)

        resp, params, _ = cc.chat_sync("1234", "hello")

        assert resp == "hello"
        assert params["prompt"] == "Just echo the text from A\nA:line03\nB:line03\nA:line04\nB:line04\nA:hello\nB:"

        context = cm.get("1234")
        assert context.username == "A"
        assert context.agentname == "B"
        assert context.chat_description == "Just echo the text from A"
        assert context.history_count == 4
        assert context.get_histories() == "A:line04\nB:line04\nA:hello\nB:hello"
