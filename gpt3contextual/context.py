from copy import deepcopy
from datetime import datetime


class Context:
    def __init__(self, key: str, histories: list[str] = None) -> None:
        self.key = key
        self.histories = histories or []
        self.updated_at = datetime.utcnow().timestamp()

    def get_histories(self, count=1, join_with: str = "\n"):
        return join_with.join(self.histories[count * -1:])

    def add_history(self, text: str):
        self.histories.append(text)


class ContextManager:
    def __init__(self, timeout=300) -> None:
        self.timeout = timeout
        self.contexts: dict[str, Context] = {}

    def get(self, key: str) -> Context:
        if key in self.contexts:
            if datetime.utcnow().timestamp() \
                    - self.contexts[key].updated_at <= self.timeout:
                return deepcopy(self.contexts[key])

        return Context(key)

    def set(self, context):
        context.updated_at = datetime.utcnow().timestamp()
        self.contexts[context.key] = deepcopy(context)

    def remove(self, key: str):
        del self.contexts[key]
