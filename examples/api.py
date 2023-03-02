import aiohttp
import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from gpt3contextual import ContextualChatGPT, ContextManager, CompletionException


# Settings
openai_apikey = "SET_YOUR_OPENAI_API_KEY"
config_access_key = "CHANGE_THIS_VALUE_AS_YOU_LIKE"


# Schemas
class ChatRequest(BaseModel):
    text: str = Field(..., title="Request text", example="Hello", description="Request text from user to ChatGPT")
    completion_params: dict = Field(None, title="Parameters for Completion API", example={}, description="Parameters for Completion API")


class ChatResponse(BaseModel):
    text: str = Field(..., title="Response text", example="Hi", description="Response text from ChatGPT to user")
    params: dict = Field(..., title="Actual parameters sent to Completion API", example={}, description="Actual parameters sent to Completion API")
    completion: dict = Field(..., title="Completion info", example={"choices": [{"text": "hi"}]}, description="Whole completion info from OpenAI")


class ConfigContextRequest(BaseModel):
    access_key: str = Field(..., title="Access key for configuration", example="pAsSw0Rd!", description="Access key for configuration")
    timeout: int = Field(None, title="Context timeout (sec)", example=300, description="Context timeout (sec)")
    username: str = Field(None, title="Default username", example="Human", description="Default username for each context")
    agentname: str = Field(None, title="Default agentname", example="AI", description="Default agentname for each context")
    chat_description: str = Field(None, title="Description for chat", example="Chat friendly", description="Description for the first line of each conversation")
    history_count: int = Field(None, title="History count", example=6, description="Histories to be included in prompt")


class ConfigContextResponse(BaseModel):
    pass


class ConfigChatRequest(BaseModel):
    access_key: str = Field(..., title="Access key for configuration", example="pAsSw0Rd!", description="Access key for configuration")
    model: str = Field(None, title="AI model to use", example="text-davinci-003", description="AI model to use")
    temperature: float = Field(None, title="Temperature (OpenAI param)", example=0.5, description="Temperature (OpenAI param)")
    max_tokens: int = Field(None, title="Max tokens (OpenAI param)", example=2000, description="Max tokens (OpenAI param)")
    completion_params: dict = Field(None, title="Other OpenAI params", example={}, description="Other OpenAI params")


class ConfigChatResponse(BaseModel):
    pass


# Prepare logger
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s"))
logger = logging.Logger(__name__)
logger.addHandler(stream_handler)


# Shared objects
session = aiohttp.ClientSession()

context_manager = ContextManager(
    username="兄",
    agentname="妹",
    chat_description="仲良しなので丁寧語を使わずに話してください。"
)

contextual_chat = ContextualChatGPT(
    openai_apikey,
    context_manager=context_manager
)


# FastAPI
app = FastAPI()


@app.on_event("shutdown")
async def app_shutdown():
    await session.close()


# Exception handlers
@app.exception_handler(CompletionException)
async def handle_completion_exception(request: Request, ex: CompletionException):
    return JSONResponse(content={"error": str(ex), "completion_response": ex.completion_response}, status_code=500)


@app.exception_handler(Exception)
async def handle_exception(request: Request, ex: Exception):
    return JSONResponse(content={"error": "Internal Server Error"}, status_code=500)


# FastAPI Routers
@app.post("/chat/{context_key}",
          response_model=ChatResponse,
          summary="Get contextual chat response from OpenAI",
          tags=["Chat"])
async def chat(request: ChatRequest, context_key: str):
    try:
        if not request.text:
            return JSONResponse(content={"error": "text is required"}, status_code=400)

        resp, params, completion = await contextual_chat.chat(
            context_key,
            request.text,
            **(request.completion_params or {})
        )

        del params["api_key"]
        return ChatResponse(text=resp, params=params, completion=completion)

    except CompletionException as ex:
        logger.error(f"Completion error: {ex}\n{traceback.format_exc()}")
        raise ex

    except Exception as ex:
        logger.error(f"Server error: {ex}\n{traceback.format_exc()}")
        raise ex


@app.put("/context/config",
         response_model=ConfigContextResponse,
         summary="Configure context manager",
         tags=["Config"])
async def context_config(request: ConfigContextRequest):
    if request.access_key != config_access_key:
        return JSONResponse(content={"error": "unauthorized"}, status_code=401)

    if request.timeout:
        context_manager.timeout = request.timeout
    if request.username:
        context_manager.username = request.username
    if request.agentname:
        context_manager.agentname = request.agentname
    if request.chat_description:
        context_manager.chat_description = request.chat_description
    if request.history_count:
        context_manager.history_count = request.history_count

    context_manager.remove_all(contextual_chat.get_session())

    return ConfigContextResponse()


@app.put("/chat/config",
         response_model=ConfigChatResponse,
         summary="Configure chat engine",
         tags=["Config"])
async def chat_config(request: ConfigChatRequest):
    if request.access_key != config_access_key:
        return JSONResponse(content={"error": "unauthorized"}, status_code=401)

    if request.model:
        contextual_chat.model = request.model
    if request.temperature:
        contextual_chat.temperature = request.temperature
    if request.max_tokens:
        contextual_chat.max_tokens = request.max_tokens
    if request.completion_params:
        contextual_chat.completion_params = request.completion_params

    return ConfigChatResponse()


# OpenAPI info
class OpenApiInfo:
    def __init__(self, app_routes):
        self.cache = None
        self.app_routes = app_routes

    def get_openapi(self):
        if self.cache is not None:
            return self.cache

        openapi_info = get_openapi(
            title="ChatGPT Contextual API",
            version="0.7",
            description="Contextual chat with ChatGPT of OpenAI API.",
            servers=[{"description": "This Server", "url": "/"}],
            routes=self.app_routes
        )

        self.cache = openapi_info

        return self.cache


app.openapi = OpenApiInfo(app.routes).get_openapi
