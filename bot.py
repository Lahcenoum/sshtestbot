import sys
import subprocess
import random
import string
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# =================================================================================
# 1. الإعدادات الرئيسية (Configuration)
# =================================================================================

# ⚠️ استبدل هذا برمز التوكن الخاص ببوتك
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN" 

# ⚠️ تأكد من أن هذا المسار صحيح لمكان وجود السكريبت على السيرفر الخاص بك
SCRIPT_PATH = '/usr/local/bin/create_ssh_user.sh'

# --- إعدادات الحساب ---
ACCOUNT_EXPIRY_DAYS = 2 # عدد الأيام حتى تنتهي صلاحية الحساب

# رسالة الخطأ في حال لم يتم تعيين التوكن
if TOKEN == "YOUR_TELEGRAM_BOT_TOKEN" or not TOKEN:
    print("Fatal Error: Bot token is not set correctly in bot.py.")
    sys.exit(1)

# =================================================================================
# 2. دوال مساعدة (Helper Functions)
# =================================================================================

def generate_password():
    """
    تنشئ كلمة مرور عشوائية قوية.
    """
    return "ssh-" + ''.join(random.choices(string.ascii_letters + string.digits, k=6))

# =================================================================================
# 3. وظائف البوت (Bot Functions)
# =================================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    تعرض رسالة ترحيب وزر لطلب الحساب.
    """
    keyboard = [
        [KeyboardButton("💳 طلب حساب SSH جديد")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "أهلاً بك!\n\nاضغط على الزر أدناه لإنشاء حساب SSH جديد.",
        reply_markup=reply_markup
    )

async def request_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    تستدعي السكريبت لإنشاء حساب SSH حقيقي وترسل التفاصيل للمستخدم.
    """
    user_id = update.effective_user.id
    
    # إنشاء اسم مستخدم وكلمة مرور فريدين
    username = f"tguser{user_id}"
    password = generate_password()
    
    # الأمر الذي سيتم تنفيذه في السيرفر
    # sudo ./create_ssh_user.sh <username> <password> <expiry_days>
    command_to_run = ["sudo", SCRIPT_PATH, username, password, str(ACCOUNT_EXPIRY_DAYS)]
    
    await update.message.reply_text("⏳ جاري إنشاء حسابك، يرجى الانتظار...")

    try:
        # تنفيذ الأمر باستخدام subprocess
        process = subprocess.run(
            command_to_run, 
            capture_output=True, 
            text=True, 
            timeout=30, 
            check=True
        )
        
        # الحصول على نتيجة التنفيذ (بيانات الحساب من السكريبت)
        result_details = process.stdout

        # إرسال البيانات للمستخدم
        response_message = (
            f"✅ تم إنشاء حسابك بنجاح!\n\n"
            f"**البيانات:**\n```\n{result_details}\n```\n\n"
            f"⚠️ **ملاحظة**: سيتم حذف الحساب تلقائيًا بعد **{ACCOUNT_EXPIRY_DAYS} أيام**."
        )
        # استخدم MarkdownV2 لأنه أكثر دقة في التعامل مع الأحرف الخاصة
        await update.message.reply_text(response_message, parse_mode='MarkdownV2')

    except FileNotFoundError:
        print(f"Error: Script not found at {SCRIPT_PATH}")
        await update.message.reply_text("❌ خطأ فادح: لم يتم العثور على سكريبت الإنشاء. يرجى التواصل مع مسؤول البوت.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing script: {e.stderr}")
        await update.message.reply_text("❌ حدث خطأ أثناء إنشاء الحساب. قد يكون لديك حساب بالفعل.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى لاحقًا.")

# =================================================================================
# 4. نقطة انطلاق البوت (Main Entry Point)
# =================================================================================

def main():
    """
    الدالة الرئيسية لتشغيل البوت.
    """
    print("Building bot application...")
    app = ApplicationBuilder().token(TOKEN).build()

    # إضافة المعالجات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^💳 طلب حساب SSH جديد$"), request_account))

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
