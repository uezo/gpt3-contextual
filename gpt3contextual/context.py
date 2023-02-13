from copy import deepcopy
from datetime import datetime


class Context:
    def __init__(
        self,
        key: str,
        username: str,
        agentname: str,
        chat_description: str = None,
        history_count: int = 6,
        histories: list[str] = None
    ) -> None:

        self.key = key
        self.username = username
        self.agentname = agentname
        self.chat_description = chat_description
        self.history_count = history_count
        self.histories = histories or []
        self.updated_at = datetime.utcnow().timestamp()

    def get_histories(self, join_with: str = "\n") -> str:
        return join_with.join(self.histories[self.history_count * -1:])

    def add_history(self, text: str):
        self.histories.append(text)


class ContextManager:
    def __init__(
        self,
        timeout=300,
        username: str = "Human",
        agentname: str = "AI",
        chat_description: str = None,
        history_count: int = 6
    ) -> None:

        self.timeout = timeout
        self.username = username
        self.agentname = agentname
        self.chat_description = chat_description
        self.history_count = history_count
        self.contexts: dict[str, Context] = {}

    def get(self, key: str) -> Context:
        if key in self.contexts:
            if datetime.utcnow().timestamp() \
                    - self.contexts[key].updated_at <= self.timeout:
                return deepcopy(self.contexts[key])

        return Context(
            key,
            self.username,
            self.agentname,
            self.chat_description,
            self.history_count
        )

    def set(self, context):
        context.updated_at = datetime.utcnow().timestamp()
        self.contexts[context.key] = deepcopy(context)

    def reset(
        self,
        key: str,
        username: str = None,
        agentname: str = None,
        chat_description: str = None,
        history_count: int = None
    ):
        context = self.get(key)

        if username:
            context.username = username
        if agentname:
            context.agentname = agentname
        if chat_description:
            context.chat_description = chat_description
        if history_count:
            history_count = history_count

        self.set(context)

    def remove(self, key: str):
        del self.contexts[key]
