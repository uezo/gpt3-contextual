from .context import Context, ContextManager
from openai import Completion
from openai.openai_object import OpenAIObject


class CompletionException(Exception):
    def __init__(self, completion_response, *args: object) -> None:
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

    async def chat(self, context_key: str, text: str) -> tuple[str, OpenAIObject]:
        context = self.context_manager.get(context_key)

        prompt = self.make_prompt(context, text)

        completion = await Completion.acreate(
            api_key=self.api_key,
            engine=self.engine,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            prompt=prompt,
            stop=[f"{context.username}:", f"{context.agentname}:"],
            **self.completion_params
        )

        response_text = \
            completion["choices"][0]["text"].strip() \
            if "choices" in completion else None

        self.update_context(context, text, response_text, completion)

        return response_text, prompt, completion
