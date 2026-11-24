// Minimal Telegram bot with Telegraf (long polling, no server needed).
const { Telegraf } = require('telegraf')
const { message } = require('telegraf/filters')

const BOT_TOKEN = process.env.BOT_TOKEN
if (!BOT_TOKEN) {
  console.error('Set the BOT_TOKEN environment variable (token from @BotFather).')
  process.exit(1)
}

const bot = new Telegraf(BOT_TOKEN)
bot.start((ctx) => ctx.reply('Welcome'))
bot.help((ctx) => ctx.reply('Send me a sticker'))
bot.on(message('sticker'), (ctx) => ctx.reply('👍'))
bot.hears('hi', (ctx) => ctx.reply('Hey there'))
bot.launch()
console.log('Bot running, Ctrl+C to stop.')

// Enable graceful stop
process.once('SIGINT', () => bot.stop('SIGINT'))
process.once('SIGTERM', () => bot.stop('SIGTERM'))
