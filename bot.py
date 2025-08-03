import sys
import subprocess
import random
import string
import re
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# سيتم استبدال هذا السطر تلقائياً بواسطة سكربت التثبيت
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

SCRIPT_PATH = '/usr/local/bin/create_ssh_user.sh'
ACCOUNT_EXPIRY_DAYS = 2

# إعداد السجلات
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def escape_markdown_v2(text: str) -> str:
    """تهريب الأحرف الخاصة لتنسيق MarkdownV2 الخاص بتليجرام."""
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

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

        result_details = process.stdout.strip()
        if not result_details:
            result_details = process.stderr.strip()

        safe_details = escape_markdown_v2(result_details)

        response_message = (
            f"✅ تم إنشاء حسابك بنجاح!\n\n"
            f"**البيانات:**\n```\n{safe_details}\n```\n\n"
            f"⚠️ **ملاحظة**: سيتم حذف الحساب تلقائيًا بعد **{ACCOUNT_EXPIRY_DAYS} أيام**."
        )

        await update.message.reply_text(response_message, parse_mode='MarkdownV2')
        logging.info(f"تم إنشاء حساب SSH للمستخدم {username}")

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        logging.error(f"[SCRIPT ERROR] {error_msg}")
        await update.message.reply_text("❌ فشل في تنفيذ السكربت. تحقق من صلاحيات sudo أو من سجل السيرفر.")

    except subprocess.TimeoutExpired:
        logging.error("⏱️ السكربت استغرق وقتًا طويلاً وتجاوز المهلة.")
        await update.message.reply_text("❌ فشل في إنشاء الحساب بسبب انتهاء المهلة الزمنية.")

    except Exception as e:
        logging.exception("🚨 حدث خطأ غير متوقع:")
        await update.message.reply_text("❌ حدث خطأ غير متوقع أثناء إنشاء الحساب. حاول لاحقًا.")

def main():
    """الدالة الرئيسية لتشغيل البوت."""
    if TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        logging.critical("❌ لم يتم تعيين التوكن. يرجى تشغيل سكربت التثبيت أولاً.")
        sys.exit(1)

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^💳 طلب حساب SSH جديد$"), request_account))

    logging.info("✅ البوت يعمل الآن في وضع الانتظار...")
    app.run_polling()

if __name__ == '__main__':
    main()
