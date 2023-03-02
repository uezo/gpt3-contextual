import aiohttp
import logging
import traceback
from fastapi import FastAPI, Request, BackgroundTasks
from linebot import AsyncLineBotApi, WebhookParser
from linebot.aiohttp_async_http_client import AiohttpAsyncHttpClient
from linebot.models import MessageEvent, TextMessage
from gpt3contextual import ContextualChatGPT, ContextManager


openai_apikey = "SET_YOUR_OPENAI_API_KEY"
channel_access_token = "<YOUR CHANNEL ACCESS TOKEN>"
channel_secret = "<YOUR CHANNEL SECRET>"

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s"))
logger = logging.Logger(__name__)
logger.addHandler(stream_handler)

session = aiohttp.ClientSession()
client = AiohttpAsyncHttpClient(session)
line_api = AsyncLineBotApi(
    channel_access_token=channel_access_token,
    async_http_client=client
)
parser = WebhookParser(channel_secret=channel_secret)
context_manager = ContextManager(
    username="兄",
    agentname="妹",
    chat_description="仲良しなので丁寧語を使わずに話してください。"
)
contextual_chat = ContextualChatGPT(
    openai_apikey,
    context_manager=context_manager
)


async def handle_events(events):
    for ev in events:
        if isinstance(ev, MessageEvent):
            try:
                resp, _, _ = await contextual_chat.chat(
                    ev.source.user_id,
                    ev.message.text
                )

            except Exception as ex:
                logger.error(f"Chat error: {ex}\n{traceback.format_exc()}")
                resp = "😣"

            try:
                await line_api.reply_message(
                    ev.reply_token,
                    TextMessage(text=resp)
                )

            except Exception as ex:
                logger.error(f"LINE error: {ex}\n{traceback.format_exc()}")


app = FastAPI()


@app.on_event("shutdown")
async def app_shutdown():
    await session.close()


@app.post("/linebot")
async def handle_request(request: Request, background_tasks: BackgroundTasks):
    events = parser.parse(
        (await request.body()).decode("utf-8"),
        request.headers.get("X-Line-Signature", "")
    )
    background_tasks.add_task(handle_events, events=events)
    return "ok"
