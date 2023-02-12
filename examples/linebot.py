import aiohttp
import logging
import traceback
from fastapi import FastAPI, Request, BackgroundTasks
from linebot import AsyncLineBotApi, WebhookParser
from linebot.aiohttp_async_http_client import AiohttpAsyncHttpClient
from linebot.models import MessageEvent, TextMessage
from gpt3contextual import ContextualChat


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
contextual_chat = ContextualChat(
    openai_apikey,

    # # Human with AI
    # username="Human",
    # agentname="AI",

    # Brother with Sister in Japanese
    username="兄",
    agentname="妹",
    chat_description="これは兄と親しい妹との会話です。仲良しなので丁寧語を使わずに話してください。"
)


async def handle_events(events):
    for ev in events:
        if isinstance(ev, MessageEvent):
            try:
                resp, _ = await contextual_chat.chat(
                    ev.source.user_id,
                    ev.message.text
                )
                await line_api.reply_message(
                    ev.reply_token,
                    TextMessage(text=resp))

            except Exception as ex:
                logger.error(f"Error: {ex}\n{traceback.format_exc()}")


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
