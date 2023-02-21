from copy import deepcopy
from datetime import datetime
import json
import sqlite3


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
                    - self.contexts[key].updated_at > self.timeout:
                self.contexts[key].histories = []
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
            context.history_count = history_count
        context.histories = []

        self.set(context)

    def remove(self, key: str):
        del self.contexts[key]


class SQLiteContextManager(ContextManager):
    sqls = {
        "create": "create table context (key TEXT primary key, username TEXT, agentname TEXT, chat_description TEXT, history_count INT, histories TEXT, updated_at INT)",
        "get": "select key, username, agentname, chat_description, history_count, histories, updated_at from context where key = ?",
        "set": "replace into context (key, username, agentname, chat_description, history_count, histories, updated_at) values (?,?,?,?,?,?,?)",
        "remove": "delete from context where key = ?"
    }

    def __init__(
        self,
        timeout=300,
        username: str = "Human",
        agentname: str = "AI",
        chat_description: str = None,
        history_count: int = 6,
        connection_str: str = None
    ) -> None:

        super().__init__(
            timeout,
            username,
            agentname,
            chat_description,
            history_count
        )
        self.connection_str = connection_str

    def get_connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.connection_str, detect_types=sqlite3.PARSE_DECLTYPES)
        connection.row_factory = sqlite3.Row
        return connection

    def get(self, key: str) -> Context:
        conn = self.get_connection()

        try:
            cursor = conn.cursor()
            cursor.execute(self.sqls["get"], (key, ))
            record = cursor.fetchone()
            if record:
                context = Context(
                    key,
                    record["username"],
                    record["agentname"],
                    record["chat_description"],
                    record["history_count"],
                )
                if datetime.utcnow().timestamp() \
                        - record["updated_at"] <= self.timeout:
                    context.histories = json.loads(record["histories"])
                context.updated_at = record["updated_at"]

                return context

            else:
                return Context(
                    key,
                    self.username,
                    self.agentname,
                    self.chat_description,
                    self.history_count
                )

        except Exception as ex:
            raise ex

        finally:
            conn.close()

    def set(self, context: Context):
        conn = self.get_connection()

        try:
            cursor = conn.cursor()
            cursor.execute(self.sqls["set"], (
                context.key,
                context.username,
                context.agentname,
                context.chat_description,
                context.history_count,
                json.dumps(context.histories),
                datetime.utcnow().timestamp()
            ))
            conn.commit()

        except Exception as ex:
            raise ex

        finally:
            conn.close()

    def remove(self, key: str):
        conn = self.get_connection()

        try:
            cursor = conn.cursor()
            cursor.execute(self.sqls["remove"], (key, ))
            conn.commit()

        except Exception as ex:
            raise ex

        finally:
            conn.close()
