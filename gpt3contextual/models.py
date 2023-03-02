import json
from sqlalchemy import (
    Column, String, Integer
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def create_tables(engine):
    Base.metadata.create_all(bind=engine)


class Context(Base):
    __tablename__ = "contexts"

    id = Column("id", Integer, autoincrement=True, primary_key=True)
    updated_at = Column("updated_at", Integer, default=0)
    key = Column("key", String(255), nullable=False)
    username = Column("username", String(255), nullable=False)
    agentname = Column("agentname", String(255), nullable=False)
    chat_description = Column("chat_description", String(2000), nullable=False)
    history_count = Column("history_count", Integer, nullable=False)
    histories = Column("histories", String, nullable=True)

    def get_histories(self, join_with: str = "\n") -> str:
        history_list = json.loads(self.histories)
        return join_with.join(history_list[self.history_count * -1:])

    def get_histories_as_list(self) -> list[str]:
        history_list = json.loads(self.histories)
        return history_list[self.history_count * -1:]

    def add_history(self, text: str):
        history_list = json.loads(self.histories)
        history_list.append(text)
        self.histories = json.dumps(history_list)

    def clear_history(self):
        self.histories = "[]"


class CompletionLog(Base):
    __tablename__ = "completionlogs"

    id = Column("id", Integer, autoincrement=True, primary_key=True)
    created_at = Column("created_at", Integer, nullable=False)
    prompt = Column("prompt", String(2000), nullable=False)
    text = Column("text", String(2000), nullable=False)
    parameters = Column("parameters", String, nullable=False)
    completion = Column("completion", String, nullable=False)
