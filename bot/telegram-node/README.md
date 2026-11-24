# telegram-node - minimal Telegram bot (Node.js + Telegraf)

Starting point for a Telegram bot. It uses **long polling**, so it runs anywhere
(even behind NAT) with no public URL or webhook. For a serverless version on AWS
Lambda + webhook see [../telegram-python.py](../telegram-python.py).

What it does out of the box:

- `/start` -> "Welcome"
- `/help` -> "Send me a sticker"
- any sticker -> 👍
- the text `hi` -> "Hey there"

## Run

1. Create a bot with [@BotFather](https://t.me/BotFather) (`/newbot`) and copy the token.
2. Start it:

```
npm install
# PowerShell
$env:BOT_TOKEN = "123456:ABC..."
# bash
export BOT_TOKEN="123456:ABC..."
npm start
```

Never put the token in the code: anyone who has it controls the bot.
If it leaks, regenerate it with `/revoke` in BotFather.
