import os
import yt_dlp
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TOKEN = "8753874001:AAEMtlNKeXqIBgPy2cG9YhDue3L5TcWTeJQ"

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute(
    "CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, downloads INTEGER DEFAULT 0, premium INTEGER DEFAULT 0)"
)
conn.commit()

FREE_LIMIT = 3

def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        return (user_id, 0, 0)
    return user

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a video link 📥")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user = get_user(user_id)
    if user[2] == 0 and user[1] >= FREE_LIMIT:
        await update.message.reply_text("Free limit reached. Use /premium")
        return
    url = update.message.text
    try:
        ydl_opts = {"format": "best", "outtmpl": f"{user_id}.%(ext)s", "quiet": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
        await update.message.reply_video(video=open(file_path, "rb"))
        cursor.execute("UPDATE users SET downloads = downloads + 1 WHERE user_id=?", (user_id,))
        conn.commit()
        os.remove(file_path)
    except Exception as e:
        print(e)
        await update.message.reply_text("Download failed. Try another link.")

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Upgrade here: YOUR_STRIPE_LINK")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("premium", premium))
app.add_handler(MessageHandler(filters.TEXT, handle_message))
app.run_polling()
