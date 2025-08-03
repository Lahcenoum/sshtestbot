import sys
import subprocess
import random
import string
import traceback
import html
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode
from telegram.error import BadRequest

# The token is replaced by the installation script
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN" 

SCRIPT_PATH = '/usr/local/bin/create_ssh_user.sh'
ACCOUNT_EXPIRY_DAYS = 2

def generate_password():
    # Creates a random password.
    return "ssh-" + ''.join(random.choices(string.ascii_letters + string.digits, k=6))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Displays a welcome message and the request button.
    keyboard = [[KeyboardButton("💳 طلب حساب SSH جديد")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "أهلاً بك! هذا إصدار تشخيصي.\n\nاضغط على الزر أدناه لبدء عملية التشخيص.",
        reply_markup=reply_markup
    )

async def request_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This is a diagnostic version of the function to find the exact point of failure.
    try:
        await update.message.reply_text("1. تم استلام الطلب...")
        
        user_id = update.effective_user.id
        username = f"tguser{user_id}"
        password = generate_password()
        command_to_run = ["sudo", SCRIPT_PATH, username, password, str(ACCOUNT_EXPIRY_DAYS)]

        await update.message.reply_text("2. جاري تشغيل سكريبت الخادم...")
        process = subprocess.run(
            command_to_run,
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )
        await update.message.reply_text("3. انتهى سكريبت الخادم بنجاح.")

        result_details = process.stdout
        print(f"--- RAW SCRIPT OUTPUT ---\n{result_details}\n---------------------")

        await update.message.reply_text("4. جاري تجهيز رسالة النجاح...")
        safe_details = html.escape(result_details.strip())
        response_message = (
            f"<b>✅ تم إنشاء حسابك بنجاح!</b>\n\n"
            f"<b>البيانات:</b>\n<pre><code>{safe_details}</code></pre>\n\n"
            f"⚠️ <b>ملاحظة</b>: سيتم حذف الحساب تلقائيًا بعد <b>{ACCOUNT_EXPIRY_DAYS} أيام</b>."
        )
        
        await update.message.reply_text("5. جاري إرسال الرسالة المنسقة النهائية...")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=response_message,
            parse_mode=ParseMode.HTML
        )
        await update.message.reply_text("6. تمت جميع الخطوات بنجاح!")

    except subprocess.CalledProcessError as e:
        # Specific error for script failure
        print("--- SCRIPT EXECUTION FAILED ---")
        traceback.print_exc()
        await update.message.reply_text(f"❌ فشل تشغيل السكريبت. خطأ الخادم:\n\n<pre>{html.escape(e.stderr)}</pre>", parse_mode=ParseMode.HTML)

    except BadRequest as e:
        # Specific error for Telegram formatting
        print("--- TELEGRAM BADREQUEST ERROR ---")
        traceback.print_exc()
        await update.message.reply_text(f"❌ خطأ في تنسيق تليجرام:\n\n<pre>{html.escape(e.message)}</pre>", parse_mode=ParseMode.HTML)

    except Exception as e:
        # Catch-all for any other error
        print("--- A COMPLETELY UNEXPECTED ERROR OCCURRED ---")
        traceback.print_exc()
        await update.message.reply_text("❌ حدث خطأ غير معروف. يرجى فحص سجلات الخادم.")

def main():
    # Main function to run the bot.
    if "YOUR_TELEGRAM_BOT_TOKEN" in TOKEN:
        print("FATAL ERROR: Bot token is not set in the bot.py file.")
        sys.exit(1)
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^💳 طلب حساب SSH جديد$"), request_account))
    print("Bot is running in DIAGNOSTIC mode...")
    app.run_polling()

if __name__ == '__main__':
    main()
