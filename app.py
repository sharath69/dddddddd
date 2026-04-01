import time
import random
import threading

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ========= CONFIG =========
BOT_TOKEN = "8728250390:AAGaSCS9EykApYCzeQMT0k4PcTsA8xj-hD4"
ADMIN_ID = 1770697159

LOGIN_URL = "https://jaiclub04.com/#/login"
USERNAME = "9351108392"
PASSWORD = "piyush1234"

channels = set()
history = []
last_prediction = None
last_period = None
running = False

# ===== DRIVER =====
def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver

driver = get_driver()

# ===== LOGIN =====
def login():
    driver.get(LOGIN_URL)
    time.sleep(5)

    driver.find_element(By.XPATH, "//input[@type='text']").send_keys(USERNAME)
    driver.find_element(By.XPATH, "//input[@type='password']").send_keys(PASSWORD)
    driver.find_element(By.XPATH, "//button").click()

    time.sleep(8)

# ===== GAME DATA =====
def get_game_data():
    try:
        rows = driver.find_elements(By.XPATH, "//table//tr")
        latest = rows[1]
        cols = latest.find_elements(By.TAG_NAME, "td")

        period = cols[0].text
        number = cols[1].text

        num = int(number)
        result = "BIG" if num >= 5 else "SMALL"

        return period, result
    except:
        return None, None

# ===== PREDICTION =====
def predict():
    if len(history) >= 3 and history[-1] == history[-2] == history[-3]:
        return "SMALL" if history[-1] == "BIG" else "BIG"
    return random.choice(["BIG", "SMALL"])

# ===== SEND =====
async def send_all(app, msg):
    for ch in list(channels):
        try:
            await app.bot.send_message(chat_id=ch, text=msg)
        except:
            pass

# ===== MAIN LOOP =====
def run_loop(app):
    global last_prediction, last_period, running

    login()

    while running:
        period, result = get_game_data()

        if period and period != last_period:
            history.append(result)

            if last_prediction:
                status = "WIN ✅" if last_prediction == result else "LOSS ❌"

                asyncio.run(send_all(app, f"""
🎯 Period: {period}
Result: {result}
Status: {status}
"""))

            prediction = predict()
            last_prediction = prediction
            last_period = period

            asyncio.run(send_all(app, f"""
🔮 Next Prediction: {prediction}
"""))

        time.sleep(5)

# ===== TELEGRAM =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("➕ Add Channel", callback_data="add")],
        [InlineKeyboardButton("▶️ Start Bot", callback_data="startbot")],
        [InlineKeyboardButton("⏹ Stop Bot", callback_data="stopbot")],
    ]

    await update.message.reply_text("🔥 CONTROL PANEL", reply_markup=InlineKeyboardMarkup(keyboard))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global running

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    if query.data == "add":
        await query.message.reply_text("👉 Channel me /addchannel likho")

    elif query.data == "startbot":
        if not running:
            running = True
            threading.Thread(target=run_loop, args=(context.application,)).start()
            await query.message.reply_text("🚀 Bot Started")

    elif query.data == "stopbot":
        running = False
        await query.message.reply_text("⏹ Bot Stopped")

# ===== ADD CHANNEL =====
async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    chat_id = update.effective_chat.id

    if str(chat_id).startswith("-100"):
        channels.add(chat_id)
        await update.message.reply_text("✅ Channel Added")
    else:
        await update.message.reply_text("❌ Channel nahi hai")

# ===== MAIN =====
import asyncio

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addchannel", add_channel))
    app.add_handler(CallbackQueryHandler(button))

    print("Bot Running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())