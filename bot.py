import sys
import subprocess
import random
import string
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# سيتم استبدال هذا السطر تلقائياً بواسطة سكريبت التثبيت
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

SCRIPT_PATH = '/usr/local/bin/create_ssh_user.sh'
ACCOUNT_EXPIRY_DAYS = 2

def generate_password():
    """تنشئ كلمة مرور عشوائية."""
    return "ssh-" + ''.join(random.choices(string.ascii_letters + string.digits, k=6))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تعرض رسالة ترحيب وزر الطلب."""
    keyboard = [[KeyboardButton("💳 طلب حساب SSH جديد")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "أهلاً بك!\n\nاضغط على الزر أدناه لإنشاء حساب SSH جديد.",
        reply_markup=reply_markup
    )

async def request_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تستدعي السكريبت لإنشاء حساب SSH."""
    user_id = update.effective_user.id
    username = f"tguser{user_id}"
    password = generate_password()
    command_to_run = ["sudo", SCRIPT_PATH, username, password, str(ACCOUNT_EXPIRY_DAYS)]

    await update.message.reply_text("⏳ جاري إنشاء حسابك، يرجى الانتظار...")

    try:
        process = subprocess.run(
            command_to_run,
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )
        result_details = process.stdout
        response_message = (
            f"✅ تم إنشاء حسابك بنجاح!\n\n"
            f"**البيانات:**\n```\n{result_details}\n```\n\n"
            f"⚠️ **ملاحظة**: سيتم حذف الحساب تلقائيًا بعد **{ACCOUNT_EXPIRY_DAYS} أيام**."
        )
        await update.message.reply_text(response_message, parse_mode='MarkdownV2')

    except Exception as e:
        print(f"An error occurred: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء إنشاء الحساب. قد يكون لديك حساب بالفعل.")

def main():
    """الدالة الرئيسية لتشغيل البوت."""
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^💳 طلب حساب SSH جديد$"), request_account))
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
