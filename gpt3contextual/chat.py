from copy import deepcopy
import json
from datetime import datetime
from openai import Completion, ChatCompletion
from openai.openai_object import OpenAIObject
from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import sessionmaker, Session
from .models import Context, CompletionLog, create_tables


class CompletionException(Exception):
    def __init__(self, *args: object, completion_response) -> None:
        super().__init__(*args)

        self.completion_response = completion_response


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
        self.chat_description = chat_description or ""
        self.history_count = history_count

    def get(self, session: Session, key: str) -> Context:
        stmt = select(Context).where(Context.key == key)
        context = session.execute(stmt).scalars().one_or_none()

        if not context:
            context = Context(
                key=key,
                username=self.username,
                agentname=self.agentname,
                chat_description=self.chat_description,
                history_count=self.history_count,
                histories="[]"
            )
            session.add(context)
            session.commit()

        elif datetime.utcnow().timestamp() - context.updated_at > self.timeout:
            context.clear_history()

        return context

    def set(self, session: Session, context: Context):
        context.updated_at = int(datetime.utcnow().timestamp())

        stmt = select(Context).where(Context.key == context.key)
        if not session.execute(stmt).scalars().one_or_none():
            session.add(context)

        session.commit()

    def reset(
        self,
        session: Session,
        key: str,
        username: str = None,
        agentname: str = None,
        chat_description: str = None,
        history_count: int = None
    ):
        context = self.get(session, key)

        if username:
            context.username = username
        if agentname:
            context.agentname = agentname
        if chat_description:
            context.chat_description = chat_description
        if history_count:
            context.history_count = history_count
        context.clear_history()

        self.set(session, context)

    def remove(self, session: Session, key: str):
        context = self.get(session, key)
        session.delete(context)
        session.commit()

    def remove_all(self, session: Session):
        session.execute(delete(Context))
        session.commit()


class ContextualChatBase:
    DEFAULT_MODEL = "text-davinci-003"

    def __init__(
        self,
        api_key: str,
        connection_str: str = "sqlite:///gpt3contextual.db",
        context_manager: ContextManager = None,
        *,
        model: str = None,
        temperature: float = 0.5,
        max_tokens: int = 2000,
        **completion_params
    ) -> None:

        self.api_key = api_key
        self.connection_str = connection_str
        self.engine = create_engine(self.connection_str)
        create_tables(self.engine)
        self.get_session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.context_manager = context_manager or ContextManager()
        self.model = model or self.DEFAULT_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.completion_params = completion_params

    def make_params(self, context: Context, *, prompt: str = None, messages: list[dict[str, str]] = None, completion_params: dict = None) -> dict:
        params = deepcopy(self.completion_params) if self.completion_params else {}

        params["api_key"] = self.api_key
        params["model"] = self.model
        params["temperature"] = self.temperature
        params["max_tokens"] = self.max_tokens
        if prompt:
            params["stop"] = [f"{context.username}:", f"{context.agentname}:"]
            params["prompt"] = prompt
        else:
            params["messages"] = messages

        # Overwrite on the fly
        if completion_params:
            for k, v in completion_params.items():
                params[k] = v

        return params

    def update_context(self, session: Session, context: Context, request_text: str, response_text: str, completion: dict):
        if response_text:
            # Add request and response to context
            context.add_history(f"{context.username}:{request_text}")
            context.add_history(f"{context.agentname}:{response_text}")
            self.context_manager.set(session, context)

        else:
            # Reset histories to start new context in next turn
            self.context_manager.reset(session, context.key)
            raise CompletionException(
                "Completion returns an error",
                completion_response=completion
            )

    async def execute_completion_async(self, session: Session, context: Context, text: str, **completion_params):
        raise NotImplementedError("execute_completion_async() in not implemented")

    def execute_completion(self, session: Session, context: Context, text: str, **completion_params):
        raise NotImplementedError("execute_completion() in not implemented")

    async def chat(self, context_key: str, text: str, **completion_params) -> tuple[str, dict, OpenAIObject]:
        session = self.get_session()

        try:
            context = self.context_manager.get(session, context_key)
            response_text, params, completion = await self.execute_completion_async(session, context, text, **completion_params)
            self.save_log(session, response_text, params, completion)
            self.update_context(session, context, text, response_text, completion)
            return response_text, params, completion

        except Exception as ex:
            raise ex

        finally:
            session.close()

    def chat_sync(self, context_key: str, text: str, **completion_params) -> tuple[str, dict, OpenAIObject]:
        session = self.get_session()

        try:
            context = self.context_manager.get(session, context_key)
            response_text, params, completion = self.execute_completion(session, context, text, **completion_params)
            self.save_log(session, response_text, params, completion)
            self.update_context(session, context, text, response_text, completion)
            return response_text, params, completion

        except Exception as ex:
            raise ex

        finally:
            session.close()

    def save_log(self, session: Session, response_text: str, params: dict, completion: dict):
        history = CompletionLog(
            created_at=int(datetime.utcnow().timestamp()),
            prompt=params["prompt"] if "prompt" in params else json.dumps(params["messages"], ensure_ascii=False),
            text=response_text,
            parameters=json.dumps(params, ensure_ascii=False),
            completion=json.dumps(completion, ensure_ascii=False)
        )
        session.add(history)
        session.commit()


class ContextualChat(ContextualChatBase):
    DEFAULT_MODEL = "text-davinci-003"

    def make_prompt(self, context: Context, text: str) -> str:
        return f"{context.chat_description}\n" + \
               f"{context.get_histories()}\n" + \
               f"{context.username}:{text}\n{context.agentname}:"

    async def execute_completion_async(self, session: Session, context: Context, text: str, **completion_params) -> tuple[str, dict, OpenAIObject]:
        prompt = self.make_prompt(context, text)
        params = self.make_params(context, prompt=prompt, **(completion_params or {}))

        if not params.get("api_key"):
            raise CompletionException("api_key is missing", completion_response=None)

        try:
            completion = await Completion.acreate(**params)
        except Exception as ex:
            raise CompletionException(str(ex), completion_response=None)

        response_text = \
            completion["choices"][0]["text"].strip() \
            if "choices" in completion else None

        return response_text, params, completion

    def execute_completion(self, session: Session, context: Context, text: str, **completion_params) -> tuple[str, dict, OpenAIObject]:
        prompt = self.make_prompt(context, text)
        params = self.make_params(context, prompt=prompt, **(completion_params or {}))

        if not params.get("api_key"):
            raise CompletionException("api_key is missing", completion_response=None)

        try:
            completion = Completion.create(**params)
        except Exception as ex:
            raise CompletionException(str(ex), completion_response=None)

        response_text = \
            completion["choices"][0]["text"].strip() \
            if "choices" in completion else None

        return response_text, params, completion


class ContextualChatGPT(ContextualChatBase):
    DEFAULT_MODEL = "gpt-3.5-turbo"

    def make_messages(self, context: Context, text: str) -> list[dict[str, str]]:
        messages = []
        messages.append({"role": "system", "content": context.chat_description})
        histories = context.get_histories_as_list()
        turn_user = len(histories) % 2 == 0
        for i in range(len(histories)):
            messages.append({"role": "user" if turn_user else "assistant", "content": histories[i]})
            turn_user = not turn_user

        messages.append({"role": "user", "content": f"{context.username}:{text}"})

        return messages

    async def execute_completion_async(self, session: Session, context: Context, text: str, **completion_params) -> tuple[str, dict, OpenAIObject]:
        messages = self.make_messages(context, text)
        params = self.make_params(context, messages=messages, **(completion_params or {}))

        if not params.get("api_key"):
            raise CompletionException("api_key is missing", completion_response=None)

        try:
            completion = await ChatCompletion.acreate(**params)
        except Exception as ex:
            raise CompletionException(str(ex), completion_response=None)

        response_text = \
            completion["choices"][0]["message"]["content"].strip() \
            if "choices" in completion else None

        if response_text.startswith(f"{context.agentname}:"):
            response_text = response_text[len(context.agentname) + 1:].strip()

        return response_text, params, completion

    def execute_completion(self, session: Session, context: Context, text: str, **completion_params) -> tuple[str, dict, OpenAIObject]:
        messages = self.make_messages(context, text)
        params = self.make_params(context, messages=messages, **(completion_params or {}))

        if not params.get("api_key"):
            raise CompletionException("api_key is missing", completion_response=None)

        try:
            completion = ChatCompletion.create(**params)
        except Exception as ex:
            raise CompletionException(str(ex), completion_response=None)

        response_text = \
            completion["choices"][0]["message"]["content"].strip() \
            if "choices" in completion else None

        if response_text.startswith(f"{context.agentname}:"):
            response_text = response_text[len(context.agentname) + 1:].strip()

        return response_text, params, completion
