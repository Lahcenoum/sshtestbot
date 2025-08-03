from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import subprocess
import random
import string
import os
from datetime import datetime, timedelta

BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'
SCRIPT_PATH = '/usr/local/bin/create_ssh_user.sh'
LOG_FILE = '/var/log/ssh_user_creations.log'

def generate_username(bot_username):
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{bot_username}_{suffix}"

def generate_password():
    suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=2))
    return f"sshdotbot{suffix}"

def can_create(user_id):
    now = datetime.now()
    count = 0
    if not os.path.exists(LOG_FILE):
        return True
    with open(LOG_FILE, 'r') as f:
        for line in f:
            log_user_id, log_time = line.strip().split(',')
            if log_user_id == str(user_id):
                log_time = datetime.strptime(log_time, "%Y-%m-%d %H:%M:%S")
                if now - log_time < timedelta(hours=24):
                    count += 1
    return count < 2

def log_creation(user_id):
    with open(LOG_FILE, 'a') as f:
        f.write(f"{user_id},{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحبًا! أرسل /get_ssh للحصول على حساب SSH مجاني لمدة يومين.")

async def get_ssh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not can_create(user_id):
        await update.message.reply_text("❌ لقد أنشأت حسابين خلال آخر 24 ساعة. حاول لاحقًا.")
        return

    bot_username = context.bot.username.lower().replace("bot", "")
    username = generate_username(bot_username)
    password = generate_password()

    try:
        result = subprocess.check_output([SCRIPT_PATH, username, password], stderr=subprocess.STDOUT)
        log_creation(user_id)
        await update.message.reply_text(f"✅ تم إنشاء الحساب:

{result.decode()}")
    except subprocess.CalledProcessError as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء إنشاء الحساب:

{e.output.decode()}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get_ssh", get_ssh))
    app.run_polling()
