from copy import deepcopy
from .context import Context, ContextManager
from openai import Completion
from openai.openai_object import OpenAIObject


class CompletionException(Exception):
    def __init__(self, *args: object, completion_response) -> None:
        super().__init__(*args)

        self.completion_response = completion_response


class ContextualChat:
    def __init__(
        self,
        api_key: str,
        context_manager: ContextManager,
        *,
        engine: str = "text-davinci-003",
        temperature: float = 0.5,
        max_tokens: int = 2000,
        **completion_params
    ) -> None:

        self.api_key = api_key
        self.context_manager = context_manager
        self.engine = engine
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.completion_params = completion_params

    def make_prompt(self, context: Context, text: str) -> str:
        return f"{context.chat_description}\n" + \
               f"{context.get_histories()}\n" + \
               f"{context.username}:{text}\n{context.agentname}:"

    def make_params(self, context: Context, prompt: str, completion_params: dict) -> dict:
        params = deepcopy(self.completion_params) if self.completion_params else {}

        params["api_key"] = self.api_key
        params["engine"] = self.engine
        params["temperature"] = self.temperature
        params["max_tokens"] = self.max_tokens
        params["stop"] = [f"{context.username}:", f"{context.agentname}:"]
        params["prompt"] = prompt

        if completion_params:
            for k, v in completion_params.items():
                params[k] = v

        return params

    def update_context(self, context: Context, request_text: str, response_text: str, completion: dict):
        if response_text:
            # Add request and response to context
            context.add_history(f"{context.username}:{request_text}")
            context.add_history(f"{context.agentname}:{response_text}")
            self.context_manager.set(context)

        else:
            # Reset histories to start new context in next turn
            self.context_manager.reset(context.key)
            raise CompletionException(
                "Completion returns an error",
                completion_response=completion
            )

    async def chat(self, context_key: str, text: str, **completion_params) -> tuple[str, OpenAIObject]:
        context = self.context_manager.get(context_key)
        prompt = self.make_prompt(context, text)
        params = self.make_params(context, prompt, completion_params)

        if not params.get("api_key"):
            raise CompletionException("api_key is missing", completion_response=None)

        try:
            completion = await Completion.acreate(**params)
        except Exception as ex:
            raise CompletionException(str(ex), completion_response=None)

        response_text = \
            completion["choices"][0]["text"].strip() \
            if "choices" in completion else None

        self.update_context(context, text, response_text, completion)

        return response_text, params, completion

    def chat_sync(self, context_key: str, text: str, **completion_params) -> tuple[str, OpenAIObject]:
        context = self.context_manager.get(context_key)
        prompt = self.make_prompt(context, text)
        params = self.make_params(context, prompt, completion_params)

        if not params.get("api_key"):
            raise CompletionException("api_key is missing", completion_response=None)

        try:
            completion = Completion.create(**params)
        except Exception as ex:
            raise CompletionException(str(ex), completion_response=None)

        response_text = \
            completion["choices"][0]["text"].strip() \
            if "choices" in completion else None

        self.update_context(context, text, response_text, completion)

        return response_text, params, completion
