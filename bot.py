from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import gspread

# Подключение к Google Sheets
gc = gspread.service_account(filename='mycode.json')  # имя твоего JSON файла
sh = gc.open('CG 1')  # имя таблицы
worksheet = sh.sheet1

TOKEN = "7885647251:AAGOTDVoJy6QIbwzwKYcPT5Sxh2T6ldf4R8"

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

# Обработка сообщений
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

    # Статические ответы
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

# Запуск бота
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Бот запущен...")
app.run_polling()



