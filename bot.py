import sys
import subprocess
import random
import string
import re
import traceback
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.error import BadRequest

# هذا التوكن يتم تحديثه بواسطة سكربت التثبيت
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN" 

SCRIPT_PATH = '/usr/local/bin/create_ssh_user.sh'
ACCOUNT_EXPIRY_DAYS = 2

def escape_markdown_v2(text: str) -> str:
    """يقوم بتهريب الأحرف الخاصة لتنسيق MarkdownV2 الخاص بتليجرام."""
    # قائمة الأحرف التي يجب تهريبها
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    # استخدام re.sub لتهريب كل حرف بوضع \ قبله
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def generate_password():
    """ينشئ كلمة مرور عشوائية."""
    return "ssh-" + ''.join(random.choices(string.ascii_letters + string.digits, k=6))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعرض رسالة ترحيب وزر الطلب."""
    keyboard = [[KeyboardButton("💳 طلب حساب SSH جديد")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "أهلاً بك!\n\nاضغط على الزر أدناه لإنشاء حساب SSH جديد.",
        reply_markup=reply_markup
    )

async def request_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يستدعي السكريبت لإنشاء حساب SSH ويرسل التفاصيل."""
    await update.message.reply_text("⏳ جاري إنشاء الحساب...")
    try:
        user_id = update.effective_user.id
        username = f"tguser{user_id}"
        password = generate_password()
        command_to_run = ["sudo", SCRIPT_PATH, username, password, str(ACCOUNT_EXPIRY_DAYS)]

        # تنفيذ الأمر على الخادم
        process = subprocess.run(
            command_to_run,
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )
        result_details = process.stdout
        
        # تهريب الأحرف الخاصة من نتيجة السكريبت
        safe_details = escape_markdown_v2(result_details)

        response_message = (
            f"✅ تم إنشاء حسابك بنجاح!\n\n"
            f"**البيانات:**\n```\n{safe_details}\n```\n\n"
            f"⚠️ **ملاحظة**: سيتم حذف الحساب تلقائيًا بعد **{ACCOUNT_EXPIRY_DAYS} أيام**."
        )
        
        # إرسال رسالة النجاح
        await update.message.reply_text(response_message, parse_mode='MarkdownV2')

    except BadRequest as e:
        # هذا الخطأ يحدث إذا فشل التنسيق في تليجرام
        print(f"--- Telegram Formatting Error: {e} ---")
        # كحل بديل، أرسل الرسالة كنص عادي بدون تنسيق
        await update.message.reply_text(f"✅ تم إنشاء حسابك بنجاح، ولكن فشل عرض التفاصيل بشكل منسق. إليك البيانات:\n\n{result_details}")
    except Exception as e:
        # أي خطأ آخر غير متوقع
        print("--- AN UNEXPECTED ERROR OCCURRED ---")
        traceback.print_exc()
        print("------------------------------------")
        await update.message.reply_text("❌ حدث خطأ أثناء إنشاء الحساب. قد يكون لديك حساب بالفعل.")

def main():
    """الدالة الرئيسية لتشغيل البوت."""
    # التأكد من أن التوكن تم تعيينه
    if "YOUR_TELEGRAM_BOT_TOKEN" in TOKEN:
        print("FATAL ERROR: Bot token is not set in the bot.py file.")
        sys.exit(1)
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^💳 طلب حساب SSH جديد$"), request_account))
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
