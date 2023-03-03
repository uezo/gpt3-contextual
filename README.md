# gpt3-contextual

Contextual chat with ChatGPT / GPT-3 of OpenAI API.

# ✨ ChatGPT is now available!

NOTE:
- This feature is an experimental version.
- Parameters for GPT-3 Completion API will be ignored.
- We may change the interface in the (near) future.


# 🚀 Quick start

Install.

```bash
$ pip install gpt3-contextual
```

Make script as console.py.

```python
import asyncio
from gpt3contextual import ContextualChat, ContextManager

async def main():
    cm = ContextManager()
    cc = ContextualChat("YOUR_OPENAI_APIKEY", context_manager=cm)

    while True:
        text = input("Human> ")
        resp, prompt, completion = await cc.chat("user1234567890", text)
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

If you want to use ChatGPT, use `ContextualChatGTP` instead of `ContextualChat` like below:

```python
import asyncio
from gpt3contextual import ContextualChatGTP, ContextManager

async def main():
    cm = ContextManager()
    cc = ContextualChatGTP("YOUR_OPENAI_APIKEY", context_manager=cm)

    while True:
        text = input("Human> ")
        resp, prompt, completion = await cc.chat("user1234567890", text)
        print(f"AI> {resp}")

asyncio.run(main())
```


# 🧸 Usage

You can set parameters to customize conversation senario when you make the instance of `ContextManager`.

- `timeout`: int : Stored context will be ignored when timeout(sec) passed after last updated.
- `username`: str : Name of roll of user. Default=`Human`.
- `agentname`: str = Name or role of agent(bot). Default=`AI`.
- `chat_description`: str : Some conditions to be considered in the senario of conversation.
- `history_count`: int: History count to use in prompt.

If you want to change these values for specific user(context) at runtime, call `ContextManager#reset`.

```python
context_manager.reset("user1234567890", username="兄", agentname="妹", chat_description="仲のいい兄と妹の会話です。丁寧語は使いません。")
```

And, you can customize OpenAI specs to pass the parameters to `ContextualChat`.
See also https://platform.openai.com/docs/api-reference/completions to understand more.

- `api_key`: str : API key for OpenAI API.
- `connection_str`: str : SQLAlchemy connection string for database. Default=`sqlite:///gpt3contextual.db`.
- `context_manager`: ContextManager : ContextManager you build.
- `model`: str : The AI model to use. Default=`text-davinci-003`.
- `temperature`: float : What sampling temperature to use, between 0 and 2. Default=`0.5`.
- `max_tokens`: int : The maximum number of tokens to generate in the completion. Default=`2000`.
- `**completion_params`: Other parameters for completions if you want to set.

Especially, to use other RDBMS instead of SQLite, set `connection_str` like bellow:

```python
cc = ContextualChat(
    "YOUR_OPENAI_APIKEY",
    connection_str="postgresql://user:password@host:port/dbname",
    context_manager=cm
)
```


# 💡 Tips

GPT-3 has capability of various kinds of task such as chat, research, translation, calculation, games and so on. You can switch the "mode" by setting `username`, `agentname` and `chat_description` like below.

```python
# Translation
cm = ContextManager(username="English", agentname="Japanese", chat_description="Translate from English to Japanese.")
# Calculation
cm = ContextManager(username="Question", agentname="Answer", chat_description="Calculate.")
# Customizing end of sentence (Japanese)
cm = ContextManager(username="兄", agentname="妹", chat_description="これは兄と妹との会話です。妹は語尾に「ニャ」をつけて話します。")
```


# 🔥 Host your own API server

Set your OpenAI API key and secret access key for configuration endpoints to `example/api.py`

```python
# Settings
openai_apikey = "SET_YOUR_OPENAI_API_KEY"
config_access_key = "CHANGE_THIS_VALUE_AS_YOU_LIKE"
```

Install dependencies.

```bash
$ pip install uvicorn fastapi
```

Run.

```bash
$ uvicorn run:app
```

See API document and try APIs. 👉 http://127.0.0.1:8000/docs

If you want to change IP address or port, start uvicorn like this:

```bash
$ uvicorn run:app --host 0.0.0.0 --port 80
```

And, if you want to run this API in multi-process, use database for context management.
See `gpt3contextual.context.SQLiteContextManager` and customize it for the RDBMS you want to use.

Enjoy your own contextual GPT-3 API👍


# 🥪 How it works

**This chapter is based on `text-davinci-003`**

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
cm = ContextManager(
    username="兄",
    agentname="妹",
    chat_description="これは兄と親しい妹との会話です。仲良しなので丁寧語を使わずに話してください。"
)
cc = ContextualChat("YOUR_OPENAI_APIKEY", context_manager=cm)
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
