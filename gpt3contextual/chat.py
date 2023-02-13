from .context import ContextManager
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

    async def chat(
        self,
        context_key: str,
        text: str

    ) -> tuple[str, OpenAIObject]:
        context = self.context_manager.get(context_key)
        prompt = f"{context.chat_description}\n" + \
                 f"{context.get_histories()}\n" + \
                 f"{context.username}:{text}\n{context.agentname}:"

        completion = await Completion.acreate(
            api_key=self.api_key,
            engine=self.engine,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            prompt=prompt,
            stop=[f"{context.username}:", f"{context.agentname}:"],
            **self.completion_params
        )

        if "choices" in completion:
            response_text = completion["choices"][0]["text"].strip()

            # Add request and response to context
            context.add_history(f"{context.username}:{text}")
            context.add_history(f"{context.agentname}:{response_text}")
            self.context_manager.set(context)

            return response_text, completion

        else:
            # Remove to start new context in next turn
            self.context_manager.remove(context.key)
            raise CompletionException(
                message="Completion returns an error",
                completion_response=completion
            )
