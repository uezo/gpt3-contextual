import asyncio
from gpt3contextual import ContextualChat


"""
[example]

human> hello
AI>  Hi, how can I help you?
human> I'm hungry
AI>  What would you like to eat?
human> sandwitches
AI>  What kind of sandwich would you like?
human> ham&egg        
AI>  Would you like that on a white or wheat bread?
human> wheet
AI>  Would you like anything else with your ham and egg sandwich on wheat bread?
human> Everything is fine, thank you.
AI>  Great! Your order has been placed. Enjoy your meal!
"""

openai_apikey = "SET_YOUR_OPENAI_API_KEY"
context_key = "user1234567890"  # set a key that identifies the user when you use this library for chatbot


async def main():
    cc = ContextualChat(
        openai_apikey,

        # Human with AI
        username="Human",
        agentname="AI",

        # # Brother with Sister in Japanese
        # username="兄",
        # agentname="妹",
        # chat_description="これは兄と親しい妹との会話です。仲良しなので丁寧語を使わずに話してください。"
    )

    while True:
        text = input(f"{cc.username}> ")
        resp, _ = await cc.chat(context_key, text)
        print(f"{cc.agentname}> {resp}")

asyncio.run(main())
