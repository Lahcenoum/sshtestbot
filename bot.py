import sys
import subprocess
import random
import string
import traceback
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.error import BadRequest

# The token is replaced by the installation script
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN" 

SCRIPT_PATH = '/usr/local/bin/create_ssh_user.sh'
ACCOUNT_EXPIRY_DAYS = 2

# The escape function has been removed as it was causing the formatting error.

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
        
        # We now send the raw, unescaped text inside the code block.
        # The .strip() method removes any unwanted leading/trailing whitespace.
        response_message = (
            f"✅ تم إنشاء حسابك بنجاح!\n\n"
            f"**البيانات:**\n```\n{result_details.strip()}\n```\n\n"
            f"⚠️ **ملاحظة**: سيتم حذف الحساب تلقائيًا بعد **{ACCOUNT_EXPIRY_DAYS} أيام**."
        )
        
        await update.message.reply_text(response_message, parse_mode='MarkdownV2')

    except BadRequest as e:
        # This block is now less likely to be triggered.
        print(f"--- Telegram Formatting Error: {e} ---")
        await update.message.reply_text(f"✅ تم إنشاء حسابك بنجاح، ولكن فشل عرض التفاصيل بشكل منسق. إليك البيانات:\n\n{result_details}")
    except Exception as e:
        # Fallback for other errors
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
