from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import gspread
import os
import json
from keep_alive import keep_alive
import asyncio
from aiohttp import web

keep_alive()

# Авторизация Google Sheets
google_creds_json = os.environ.get("GOOGLE_CREDS")
if not google_creds_json:
    raise Exception("GOOGLE_CREDS переменная не найдена")

creds_dict = json.loads(google_creds_json)
gc = gspread.service_account_from_dict(creds_dict)
sh = gc.open('CG 1')
worksheet = sh.sheet1

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise Exception("BOT_TOKEN переменная не найдена")

# Главное меню
def get_main_keyboard():
    keyboard = [
        ["Проверить трек-код"],
        ["📦 Адрес Иву Самолёт", "🚛 Адрес Гуанчжоу Камаз"],
        ["🏢 Адрес Душанбе", "📞 Наши контакты"],
        ["💬 WhatsApp", "🏠 Главное меню"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = get_main_keyboard()
    await update.message.reply_text("Чем могу помочь?", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "Проверить трек-код":
        await update.message.reply_text("Введите свой трек-код:")
        context.user_data["wait_for_track"] = True
        return

    if context.user_data.get("wait_for_track"):
        context.user_data["wait_for_track"] = False
        user_code = text.strip()
        records = worksheet.get_all_records()

        found = False
        for record in records:
            if str(record.get("TrackingCode")).strip() == user_code:
                status = str(record.get("Status")).strip().lower()
                date = str(record.get("Date")).strip()
                if status == "arrived":
                    await update.message.reply_text(
                        f"✅ Ваш трек‑код прибыл в наш склад в {date}. Можете забрать его.",
                        reply_markup=get_main_keyboard()
                    )
                else:
                    await update.message.reply_text(
                        "❌К сожалению, ваш трек‑код ещё не поступил к нам.",
                        reply_markup=get_main_keyboard()
                    )
                found = True
                break

        if not found:
            await update.message.reply_text(
                "К сожалению, ваш трек‑код ещё не поступил к нам.",
                reply_markup=get_main_keyboard()
            )
        return

    responses = {
        "📦 Адрес Иву Самолёт": "Адрес Иву Самолёт: Zhejiang, Yiwu, улица, склад 123",
        "🚛 Адрес Гуанчжоу Камаз": "Адрес Гуанчжоу Камаз: Guangdong, Guangzhou, улица, склад 456",
        "🏢 Адрес Душанбе": "Наш склад в Душанбе: Караболо, Дехи боло 254/11",
        "📞 Наши контакты": "Телефон: +992208006726\nМенеджер Telegram: @CobraT8te",
        "💬 WhatsApp": "Напиши нам в WhatsApp: https://wa.me/992208006726",
        "🏠 Главное меню": "Hello bayka! Чем могу помочь?"
    }

    if text in responses:
        await update.message.reply_text(responses[text], reply_markup=get_main_keyboard())
    else:
        await update.message.reply_text("Я не понял, выбери команду с кнопки 🙂", reply_markup=get_main_keyboard())

# ========== AIOHTTP и Telegram Webhook ==========

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    async def webhook_handler(request):
        data = await request.json()
        update = Update.de_json(data, app.bot)
        await app.process_update(update)
        return web.Response()

    await app.initialize()
    await app.bot.set_webhook("https://my-bot-s97n.onrender.com")
    await app.start()
    print("Webhook установлен и бот запущен...")

    web_app = web.Application()
    web_app.router.add_post("/", webhook_handler)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()

    await asyncio.Event().wait()  # Бесконечное ожидание

if __name__ == "__main__":
    asyncio.run(main())
