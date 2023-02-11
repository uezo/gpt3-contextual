# gpt3-contextual

Contextual chat with GPT-3 of OpenAI API.

# 🚀 Quick start

Install.

```bash
$ pip install gpt3-contextual
```

Make script as console.py.

```python
import asyncio
from gpt3contextual import ContextualChat

async def main():
    cc = ContextualChat(
        "YOUR_OPENAI_APIKEY",
        username="Human",
        agentname="AI"
    )

    while True:
        text = input("human> ")
        resp, _ = await cc.chat("user1234567890", text)
        print(f"AI> {resp}")

asyncio.run(main())
```

Run console.py and chat with GPT-3.

```
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
```


# 🧸 Usage

You can set parameters to customize conversation senario when you make the instance of `ContextualChat`.
See also https://platform.openai.com/docs/api-reference/completions to understands some params.

- `api_key`: str : API key for OpenAI API.
- `context_count`: int : Count of turns(request and response) to use as the context. Default=`6`
- `username`: str : Name of roll of user. Default=`customer`.
- `agentname`: str = Name or role of agent(bot). Default=`agent`.
- `chat_description`: str : Some conditions to be considered in the senario of conversation.
- `engine`: str : The engine(model) to use. Default=`text-davinci-003`.
- `temperature`: float : What sampling temperature to use, between 0 and 2. Default=`0.5`.
- `max_tokens`: int : The maximum number of tokens to generate in the completion. Default=`2000`.
- `context_manager`: ContextManager : Custom ContextManager.


# 🥪 How it works

As you know, `Completion` endpoint doesn't provide the features for keep and use context.
So, simply, this library send the previous conversation histories with the request text like below.

Prompt on the 1st turn:
```
human:hello
AI:
```
Chatbot returns `Hi, how can I help you?`.

Prompt on the 2nd turn:
```
human:hello
AI:Hi, how can I help you?
human:I'm hungry
AI:
```
Chatbot returns `What would you like to eat?`

:

Prompt on the 6th turn:
```
human:sandwitches
AI:What kind of sandwich would you like?
human:ham&egg        
AI:Would you like that on a white or wheat bread?
human:wheet
AI:Would you like anything else with your ham and egg sandwich on wheat bread?
human:Everything is fine, thank you.
AI:
```
Chatbot returns `Great! Your order has been placed. Enjoy your meal!`


If you change the `username` and `agentname` the senario of conversation changes.
And, setting `chat_description` also make effects on the situations.

Here is an example to simulate the conversation by brother and sister in Japanese.

```python
cc = ContextualChat(
    openai_apikey,
    username="兄",
    agentname="妹",
    chat_description="これは兄と親しい妹との会話です。仲良しなので丁寧語を使わずに話してください。"
)
```

Prompt to be sent to OpenAI API is like bellow. `chat_description` is always set to the first line, no matter how many turns of conversation proceed.

```
これは兄と親しい妹との会話です。仲良しなので丁寧語を使わずに話してください。
兄:おはよー
妹:おはよー！今日の予定は？
兄:いつも通り、特にないよ
妹:じゃあ、今日は一緒に遊ぼうよ！
兄:何かしたいことある？
妹:うん、今日は映画を見よう！
兄:いいね。 どんなのがいい？
妹:思いついた！サスペンス映画がいいかな！
````
