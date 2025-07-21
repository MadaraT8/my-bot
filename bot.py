from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import gspread
import os
import json
from keep_alive import keep_alive
import asyncio
from aiohttp import web

keep_alive()

# ===== БЕЗОПАСНАЯ ЗАГРУЗКА GOOGLE CREDS =====
GOOGLE_CREDS = os.environ.get("GOOGLE_CREDS")
if not GOOGLE_CREDS:
    raise ValueError("GOOGLE_CREDS environment variable not found!")

try:
    creds_dict = json.loads(GOOGLE_CREDS)  # Парсим JSON из переменной
    gc = gspread.service_account_from_dict(creds_dict)
    sh = gc.open('CG 1')
    worksheet = sh.sheet1
except Exception as e:
    raise RuntimeError(f"Google Sheets auth failed: {str(e)}")

# ===== ОСНОВНОЙ КОД БОТА =====
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable not found!")

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["Проверить трек-код"],
            ["📦 Адрес Иву Самолёт", "🚛 Адрес Гуанчжоу Камаз"],
            ["🏢 Адрес Душанбе", "📞 Наши контакты"],
            ["💬 WhatsApp", "🏠 Главное меню"]
        ],
        resize_keyboard=True
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Чем могу помочь?", reply_markup=get_main_keyboard())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "Проверить трек-код":
        await update.message.reply_text("Введите трек-код:")
        context.user_data["wait_for_track"] = True
        return

    if context.user_data.get("wait_for_track"):
        context.user_data["wait_for_track"] = False
        user_code = text.strip()
        
        try:
            records = worksheet.get_all_records()
            found = any(
                str(record.get("TrackingCode", "")).strip() == user_code
                for record in records
            )
            
            if found:
                await update.message.reply_text("✅ Трек-код найден!", reply_markup=get_main_keyboard())
            else:
                await update.message.reply_text("❌ Трек-код не найден", reply_markup=get_main_keyboard())
        except Exception as e:
            await update.message.reply_text("⚠ Ошибка поиска. Попробуйте позже.")

    # ... (остальные обработчики кнопок остаются без изменений)

async def webhook_handler(request):
    data = await request.json()
    update = Update.de_json(data, app.bot)
    await app.process_update(update)
    return web.Response(text="OK")

async def main():
    global app
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    PORT = int(os.environ.get("PORT", 10000))
    WEBHOOK_URL = f"https://{os.environ.get('RENDER_SERVICE_NAME')}.onrender.com/webhook"

    await app.initialize()
    await app.bot.set_webhook(WEBHOOK_URL)

    web_app = web.Application()
    web_app.router.add_post("/webhook", webhook_handler)
    web_app.router.add_get("/", lambda _: web.Response(text="Bot is alive!"))
    
    runner = web.AppRunner(web_app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    await asyncio.Event().wait()

if _name_ == "_main_":
    asyncio.run(main())
