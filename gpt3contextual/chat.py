from .context import ContextManager
from openai import Completion
from openai.openai_object import OpenAIObject


class CompletionException(Exception):
    def __init__(self, completion_response, *args: object) -> None:
        super().__init__(*args)

        self.completion_response = completion_response


class ContextualChat:
    def __init__(
        self, api_key: str,
        context_count: int = 6,
        username: str = "customer",
        agentname: str = "agent",
        chat_description: str = None,
        engine: str = "text-davinci-003",
        temperature: float = 0.5,
        max_tokens: int = 2000,
        context_manager: ContextManager = None
    ) -> None:

        self.api_key = api_key
        self.context_count = context_count
        self.username = username
        self.agentname = agentname
        self.chat_description = chat_description
        self.engine = engine
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.context_manager = context_manager or ContextManager()

    async def chat(self, context_key: str, text: str) -> tuple[str, OpenAIObject]:
        context = self.context_manager.get(context_key)
        prompt = f"{self.chat_description}\n" + \
                 f"{context.get_histories(self.context_count)}\n" + \
                 f"{self.username}:{text}\n{self.agentname}:"

        completion = await Completion.acreate(
            api_key=self.api_key,
            engine=self.engine,
            temperature=self.temperature,
            max_tokens=self.max_tokens,    # prompt(actual) + completion(this value) must be < 4097 for davinci
            prompt=prompt,
            stop=[f"{self.username}:", f"{self.agentname}:"]
        )

        if "choices" in completion:
            response_text = completion["choices"][0]["text"]

            # Add request and response to context
            context.add_history(f"{self.username}:{text}")
            context.add_history(f"{self.agentname}:{response_text}")
            self.context_manager.set(context)

            return response_text, completion

        else:
            # Remove to start new context in next turn
            self.context_manager.remove(context.key)
            raise CompletionException(
                message="Completion returns an error",
                completion_response=completion
            )
