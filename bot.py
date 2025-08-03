import sys
import subprocess
import random
import string
import traceback
import html  # Import the html library for escaping
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode # Import ParseMode for HTML

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
        "أهلاً بك!\n\nاضغط على الزر أدناه لإنشاء حساب SSH جديد.",
        reply_markup=reply_markup
    )

async def request_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Calls the script to create an SSH account and sends the details.
    await update.message.reply_text("⏳ جاري إنشاء الحساب...")
    try:
        user_id = update.effective_user.id
        username = f"tguser{user_id}"
        password = generate_password()
        command_to_run = ["sudo", SCRIPT_PATH, username, password, str(ACCOUNT_EXPIRY_DAYS)]

        process = subprocess.run(
            command_to_run,
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )
        result_details = process.stdout
        
        # Escape the details for HTML to be safe
        safe_details = html.escape(result_details.strip())

        # --- THE FIX: Using HTML formatting instead of MarkdownV2 ---
        response_message = (
            f"<b>✅ تم إنشاء حسابك بنجاح!</b>\n\n"
            f"<b>البيانات:</b>\n<pre><code>{safe_details}</code></pre>\n\n"
            f"⚠️ <b>ملاحظة</b>: سيتم حذف الحساب تلقائيًا بعد <b>{ACCOUNT_EXPIRY_DAYS} أيام</b>."
        )
        
        await update.message.reply_text(response_message, parse_mode=ParseMode.HTML)

    except Exception as e:
        # Fallback for any other errors
        print("--- AN UNEXPECTED ERROR OCCURRED ---")
        traceback.print_exc()
        await update.message.reply_text("❌ حدث خطأ أثناء إنشاء الحساب. قد يكون لديك حساب بالفعل.")

def main():
    # Main function to run the bot.
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
