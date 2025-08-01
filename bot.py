import subprocess
import sys
import os
import random
import string
import sqlite3
from datetime import datetime, date, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest

# =================================================================================
# 1. الإعدادات الرئيسية (Configuration)
# =================================================================================
BOT_TOKEN = 'BOT_TOKEN'
ADMIN_USER_ID = 5344028088 # ⚠️ استبدل هذا بمعرف المستخدم الخاص بك

SCRIPT_PATH = '/usr/local/bin/create_ssh_user.sh'
DB_FILE = 'ssh_bot_users.db'

# --- قيم نظام النقاط (تم التحديث) ---
COST_PER_ACCOUNT = 4      # تكلفة إنشاء حساب
REFERRAL_BONUS = 4          # مكافأة دعوة صديق
DAILY_LOGIN_BONUS = 1       # المكافأة اليومية
INITIAL_POINTS = 2          # النقاط الأولية عند بدء البوت
JOIN_BONUS = 4              # مكافأة الانضمام للقناة والمجموعة
ACCOUNT_EXPIRY_DAYS = 2

# Channel and Group links and IDs
REQUIRED_CHANNEL_ID = -1001932589296
REQUIRED_GROUP_ID = -1002218671728
CHANNEL_LINK = "https://t.me/FASTVPSVIP"
GROUP_LINK = "https://t.me/dgtliA"

if not BOT_TOKEN:
    print("Fatal Error: BOT_TOKEN environment variable not set.")
    exit()

# Conversation handler states
REDEEM_CODE = range(1)
CREATE_CODE_NAME, CREATE_CODE_POINTS, CREATE_CODE_USES = range(3)

# =================================================================================
# 2. دعم اللغات (Localization)
# =================================================================================
TEXTS = {
    'ar': {
        "welcome": "أهلاً بك!\nاستخدم الأزرار أدناه أو غير لغتك بالأمر /language.",
        "get_ssh_button": "💳 طلب حساب جديد",
        "my_account_button": "👤 حسابي",
        "balance_button": "💰 رصيدي",
        "referral_button": "👥 الإحالة",
        "redeem_button": "🎁 استرداد كود",
        "daily_button": "☀️ مكافأة يومية",
        "request_limit_exceeded": "❌ لقد وصلت إلى الحد الأقصى ({limit} حسابات) خلال الـ 24 ساعة الماضية.",
        "processing_request": "⏳ جاري إنشاء الحساب...",
        "creation_success": "✅ تم إنشاء حسابك بنجاح!\n\n**البيانات:**\n```\n{details}\n```\n\n⚠️ **ملاحظة**: سيتم حذفه تلقائيًا بعد **{days} أيام**.",
        "no_accounts_found": "ℹ️ لم يتم العثور على أي حسابات مرتبطة بك.",
        "your_accounts": "👤 حساباتك النشطة:",
        "account_details": "🏷️ **اسم المستخدم:** `{username}`\n🗓️ **تاريخ انتهاء الصلاحية:** `{expiry}`",
        "choose_language": "اختر لغتك المفضلة:",
        "language_set": "✅ تم تعيين اللغة إلى: {lang_name}",
        "balance_info": "💰 رصيدك الحالي هو: **{points}** نقطة.",
        "referral_info": "👥 ادعُ أصدقاءك واكسب **{bonus}** نقطة لكل صديق جديد يبدأ البوت عبر رابطك!\n\n🔗 رابط الإحالة الخاص بك:\n`{link}`",
        "daily_bonus_claimed": "🎉 لقد حصلت على مكافأتك اليومية: **{bonus}** نقطة! رصيدك الآن هو **{new_balance}**.",
        "daily_bonus_already_claimed": "ℹ️ لقد حصلت بالفعل على مكافأتك اليومية. تعال غدًا!",
        "not_enough_points": "⚠️ ليس لديك نقاط كافية. التكلفة هي **{cost}** نقطة.",
        "force_join_prompt": "❗️لاستخدام البوت، يجب عليك الانضمام إلى قناتنا ومجموعتنا أولاً. هذا يساعدنا على الاستمرار!\n\nبعد الانضمام، اضغط على زر 'تحققت'.",
        "force_join_channel_button": "📢 انضم للقناة",
        "force_join_group_button": "👥 انضم للمجموعة",
        "force_join_verify_button": "✅ تحققت",
        "force_join_success": "✅ شكرًا لانضمامك! يمكنك الآن استخدام البوت.",
        "force_join_fail": "❌ لم يتم التحقق من انضمامك. يرجى التأكد من انضمامك لكليهما ثم حاول مرة أخرى.",
        "join_bonus_awarded": "🎉 مكافأة الانضمام! لقد حصلت على **{bonus}** نقطة.",
        "creation_error": "❌ حدث خطأ أثناء إنشاء الحساب. يرجى التواصل مع الأدمن.",
        "creation_timeout": "⏳ استغرقت عملية الإنشاء وقتاً طويلاً وتم إلغاؤها. يرجى المحاولة مرة أخرى أو التواصل مع الأدمن.",
        "redeem_prompt": "يرجى إرسال الكود الذي تريد استرداده.",
        "redeem_success": "🎉 تهانينا! لقد حصلت على **{points}** نقطة. رصيدك الآن هو **{new_balance}**.",
        "redeem_invalid_code": "❌ هذا الكود غير صالح أو غير موجود.",
        "redeem_limit_reached": "❌ لقد وصل هذا الكود إلى الحد الأقصى من الاستخدام.",
        "redeem_already_used": "❌ لقد قمت بالفعل باستخدام هذا الكود من قبل.",
        "admin_code_created": "✅ تم إنشاء الكود `{code}` بنجاح. يمنح **{points}** نقطة ومتاح لـ **{uses}** مستخدمين.",
        "admin_create_code_prompt_name": "أرسل اسم الكود الجديد (مثال: WELCOME2025):",
        "admin_create_code_prompt_points": "الآن أرسل عدد النقاط التي يمنحها هذا الكود:",
        "admin_create_code_prompt_uses": "أخيراً، أرسل عدد المستخدمين الذين يمكنهم استخدام هذا الكود:",
        "admin_settings_header": "⚙️ لوحة تحكم إعدادات البوت",
        "admin_feature_points": "نظام النقاط",
        "admin_feature_force_join": "الانضمام الإجباري",
        "admin_feature_redeem": "أكواد المكافآت",
        "admin_create_code_button": "➕ إنشاء كود جديد",
        "admin_create_code_instruction": "ℹ️ لإنشاء كود جديد، استخدم الأمر /create_code",
        "status_enabled": "🟢 مفعل",
        "status_disabled": "🔴 معطل"
    },
    'en': {
        "welcome": "Welcome!\nUse the buttons below or change your language with /language.",
        "get_ssh_button": "💳 Request New Account",
        "my_account_button": "👤 My Account",
        "balance_button": "💰 My Balance",
        "referral_button": "👥 Referral",
        "redeem_button": "🎁 Redeem Code",
        "daily_button": "☀️ Daily Bonus",
        "request_limit_exceeded": "❌ You have reached the maximum limit ({limit} accounts) in the last 24 hours.",
        "processing_request": "⏳ Creating your account...",
        "creation_success": "✅ Your account has been created successfully!\n\n**Credentials:**\n```\n{details}\n```\n\n⚠️ **Note**: It will be automatically deleted in **{days} days**.",
        "no_accounts_found": "ℹ️ No accounts found linked to you.",
        "your_accounts": "👤 Your active accounts:",
        "account_details": "🏷️ **Username:** `{username}`\n🗓️ **Expiration Date:** `{expiry}`",
        "choose_language": "Choose your preferred language:",
        "language_set": "✅ Language set to: {lang_name}",
        "balance_info": "💰 Your current balance is: **{points}** points.",
        "referral_info": "👥 Invite your friends and earn **{bonus}** points for each new user who starts the bot via your link!\n\n🔗 Your referral link:\n`{link}`",
        "daily_bonus_claimed": "🎉 You've claimed your daily bonus of **{bonus}** points! Your new balance is **{new_balance}**.",
        "daily_bonus_already_claimed": "ℹ️ You have already claimed your daily bonus. Come back tomorrow!",
        "not_enough_points": "⚠️ You don't have enough points. The cost is **{cost}** points.",
        "force_join_prompt": "❗️To use this bot, you must first join our channel and group. This helps us grow!\n\nAfter joining, press the 'I have joined' button.",
        "force_join_channel_button": "📢 Join Channel",
        "force_join_group_button": "👥 Join Group",
        "force_join_verify_button": "✅ I have joined",
        "force_join_success": "✅ Thank you for joining! You can now use the bot.",
        "join_bonus_awarded": "🎉 Joining Bonus! You have received **{bonus}** points.",
        "force_join_fail": "❌ Membership not verified. Please make sure you've joined both, then try again.",
        "creation_error": "❌ An error occurred while creating the account. Please contact the admin.",
        "creation_timeout": "⏳ The creation process took too long and was canceled. Please try again or contact the admin.",
        "redeem_prompt": "Please send the code you want to redeem.",
        "redeem_success": "🎉 Congratulations! You have received **{points}** points. Your new balance is **{new_balance}**.",
        "redeem_invalid_code": "❌ This code is invalid or does not exist.",
        "redeem_limit_reached": "❌ This code has reached its maximum usage limit.",
        "redeem_already_used": "❌ You have already used this code before.",
        "admin_code_created": "✅ Code `{code}` created successfully. It gives **{points}** points and is available for **{uses}** users.",
        "admin_create_code_prompt_name": "Send the new code name (e.g., WELCOME2025):",
        "admin_create_code_prompt_points": "Now send the number of points this code gives:",
        "admin_create_code_prompt_uses": "Finally, send the number of users who can use this code:",
        "admin_settings_header": "⚙️ Bot Settings Control Panel",
        "admin_feature_points": "Points System",
        "admin_feature_force_join": "Force Join",
        "admin_feature_redeem": "Redeem Codes",
        "admin_create_code_button": "➕ Create New Code",
        "admin_create_code_instruction": "ℹ️ To create a new code, use the /create_code command.",
        "status_enabled": "🟢 Enabled",
        "status_disabled": "🔴 Disabled"
    },
}

# =================================================================================
# 3. إدارة قاعدة البيانات (Database Management)
# =================================================================================
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ssh_accounts (
                id INTEGER PRIMARY KEY, telegram_user_id INTEGER, ssh_username TEXT, created_at TIMESTAMP
            )''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_user_id INTEGER PRIMARY KEY, 
                language_code TEXT DEFAULT 'en', 
                points INTEGER DEFAULT 0, 
                referral_code TEXT, 
                referred_by INTEGER, 
                last_daily_claim DATE,
                join_bonus_claimed INTEGER DEFAULT 0
            )''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS redeem_codes (
                code TEXT PRIMARY KEY, points INTEGER, max_uses INTEGER, current_uses INTEGER DEFAULT 0
            )''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS redeemed_users (
                code TEXT, telegram_user_id INTEGER, PRIMARY KEY (code, telegram_user_id)
            )''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY, value TEXT
            )''')
        default_settings = {'points_system': 'enabled', 'force_join': 'enabled', 'redeem_codes': 'enabled'}
        for key, value in default_settings.items():
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()

def get_setting(key):
    with sqlite3.connect(DB_FILE) as conn:
        result = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return result[0] if result else None

def set_setting(key, value):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("UPDATE settings SET value = ? WHERE key = ?", (value, key))
        conn.commit()

def is_feature_enabled(key):
    return get_setting(key) == 'enabled'

def get_or_create_user(user_id, referred_by=None):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_user_id = ?", (user_id,))
        user_data = cursor.fetchone()
        if not user_data:
            ref_code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            initial_pts = INITIAL_POINTS if is_feature_enabled('points_system') else 0

            if referred_by and is_feature_enabled('points_system'):
                cursor.execute("UPDATE users SET points = points + ? WHERE telegram_user_id = ?", (REFERRAL_BONUS, referred_by))

            cursor.execute(
                "INSERT INTO users (telegram_user_id, language_code, points, referral_code, referred_by) VALUES (?, 'en', ?, ?, ?)",
                (user_id, initial_pts, ref_code, referred_by)
            )
            conn.commit()
            return get_or_create_user(user_id)
        return user_data

def get_user_language(user_id):
    with sqlite3.connect(DB_FILE) as conn:
        result = conn.execute("SELECT language_code FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()
        return result[0] if result else 'en'

def set_user_language(user_id, lang_code):
    get_or_create_user(user_id)
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("UPDATE users SET language_code = ? WHERE telegram_user_id = ?", (lang_code, user_id))
        conn.commit()

def get_text(key, lang_code='en'):
    return TEXTS.get(lang_code, TEXTS['en']).get(key, TEXTS['en'].get(key, key))

def add_user_creation(telegram_user_id, ssh_username):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT INTO ssh_accounts (telegram_user_id, ssh_username, created_at) VALUES (?, ?, ?)",
                       (telegram_user_id, ssh_username, datetime.now()))
        conn.commit()

def count_recent_creations(telegram_user_id):
    with sqlite3.connect(DB_FILE) as conn:
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        result = conn.execute("SELECT COUNT(*) FROM ssh_accounts WHERE telegram_user_id = ? AND created_at > ?",
                              (telegram_user_id, twenty_four_hours_ago)).fetchone()
        return result[0]

def get_user_accounts(telegram_user_id):
    with sqlite3.connect(DB_FILE) as conn:
        results = conn.execute("SELECT ssh_username FROM ssh_accounts WHERE telegram_user_id = ?", (telegram_user_id,)).fetchall()
        return [row[0] for row in results]

# =================================================================================
# 4. دوال مساعدة (Helper Functions)
# =================================================================================
async def check_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not is_feature_enabled('force_join'):
        return True
    try:
        channel_member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL_ID, user_id=user_id)
        group_member = await context.bot.get_chat_member(chat_id=REQUIRED_GROUP_ID, user_id=user_id)
        return (channel_member.status in ['member', 'administrator', 'creator'] and
                group_member.status in ['member', 'administrator', 'creator'])
    except Exception:
        return False

def generate_username():
    return "user" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))

def generate_password():
    return "sshdotbot-" + ''.join(random.choices(string.ascii_letters + string.digits, k=4))

def is_admin(user_id):
    return user_id == ADMIN_USER_ID

# =================================================================================
# 5. أوامر البوت (Bot Commands & Handlers)
# =================================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False):
    user = update.effective_user
    message_entity = update.message if not from_callback else update.callback_query.message

    referred_by = None
    if context.args:
        try:
            with sqlite3.connect(DB_FILE) as conn:
                result = conn.execute("SELECT telegram_user_id FROM users WHERE referral_code = ?", (context.args[0],)).fetchone()
                if result and result[0] != user.id:
                    referred_by = result[0]
        except Exception: pass

    get_or_create_user(user.id, referred_by)
    lang_code = get_user_language(user.id)
    
    is_member = await check_membership(user.id, context)

    if is_feature_enabled('force_join'):
        if not is_member:
            keyboard = [
                [InlineKeyboardButton(get_text('force_join_channel_button', lang_code), url=CHANNEL_LINK)],
                [InlineKeyboardButton(get_text('force_join_group_button', lang_code), url=GROUP_LINK)],
                [InlineKeyboardButton(get_text('force_join_verify_button', lang_code), callback_data='verify_join')],
            ]
            await message_entity.reply_text(get_text('force_join_prompt', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))
            return
        else:
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                claimed = cursor.execute("SELECT join_bonus_claimed FROM users WHERE telegram_user_id = ?", (user.id,)).fetchone()
                if claimed and claimed[0] == 0:
                    cursor.execute("UPDATE users SET points = points + ?, join_bonus_claimed = 1 WHERE telegram_user_id = ?", (JOIN_BONUS, user.id))
                    conn.commit()
                    await message_entity.reply_text(get_text('join_bonus_awarded', lang_code).format(bonus=JOIN_BONUS))

    keyboard_layout = [[KeyboardButton(get_text('get_ssh_button', lang_code))]]
    row2 = [KeyboardButton(get_text('my_account_button', lang_code))]
    if is_feature_enabled('points_system'):
        row2.insert(0, KeyboardButton(get_text('balance_button', lang_code)))
        row3 = [KeyboardButton(get_text('daily_button', lang_code)), KeyboardButton(get_text('referral_button', lang_code))]
        if is_feature_enabled('redeem_codes'):
            row3.append(KeyboardButton(get_text('redeem_button', lang_code)))
        keyboard_layout.extend([row2, row3])
    else:
        keyboard_layout.append(row2)

    reply_markup = ReplyKeyboardMarkup(keyboard_layout, resize_keyboard=True)
    await message_entity.reply_text(get_text('welcome', lang_code), reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    lang_code = get_user_language(user_id)

    if is_feature_enabled('force_join') and not await check_membership(user_id, context):
        await start(update, context)
        return

    button_map = {
        'get_ssh_button': get_ssh, 'my_account_button': my_account,
        'balance_button': balance_command, 'referral_button': referral_command,
        'daily_button': daily_command, 'redeem_button': redeem_command,
    }

    for key, func in button_map.items():
        if text in [get_text(key, lang) for lang in TEXTS.keys()]:
            await func(update, context)
            return

async def get_ssh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_code = get_user_language(user_id)

    if is_feature_enabled('points_system'):
        with sqlite3.connect(DB_FILE) as conn:
            points = conn.execute("SELECT points FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
        if points < COST_PER_ACCOUNT:
            await update.message.reply_text(get_text('not_enough_points', lang_code).format(cost=COST_PER_ACCOUNT))
            return
    else:
        if count_recent_creations(user_id) >= 2:
            await update.message.reply_text(get_text('request_limit_exceeded', lang_code).format(limit=2))
            return

    await update.message.reply_text(get_text('processing_request', lang_code))
    username = generate_username()
    password = generate_password()

    command_to_run = [SCRIPT_PATH, username, password, str(ACCOUNT_EXPIRY_DAYS)]
    print(f"Attempting to run command: {' '.join(command_to_run)}")

    try:
        process = subprocess.run(
            command_to_run,
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )
        result = process.stdout
        print(f"Script executed successfully. Output:\n{result}")

        add_user_creation(user_id, username)
        if is_feature_enabled('points_system'):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE users SET points = points - ? WHERE telegram_user_id = ?", (COST_PER_ACCOUNT, user_id))
                conn.commit()

        sanitized_result = result.replace('.', '\\.').replace('-', '\\-')
        await update.message.reply_text(
            get_text('creation_success', lang_code).format(details=sanitized_result, days=ACCOUNT_EXPIRY_DAYS),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    except subprocess.TimeoutExpired:
        print(f"❌ Script timed out after 30 seconds.")
        await update.message.reply_text(get_text('creation_timeout', lang_code))
    except subprocess.CalledProcessError as e:
        error_output = e.stdout if e.stdout else e.stderr
        print(f"❌ Script failed with exit code {e.returncode}. Output:\n{error_output}")
        await update.message.reply_text(get_text('creation_error', lang_code))
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        await update.message.reply_text(get_text('creation_error', lang_code))


async def my_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_code = get_user_language(user_id)
    accounts = get_user_accounts(user_id)
    if not accounts:
        await update.message.reply_text(get_text('no_accounts_found', lang_code))
        return

    response = [get_text('your_accounts', lang_code)]
    for username in accounts:
        try:
            expiry = subprocess.check_output(['/usr/bin/chage', '-l', username], text=True).split('\n')[3].split(':')[1].strip()
            safe_username = username.replace('_', '\\_')
            safe_expiry = expiry.replace('-', '\\-')
            response.append(get_text('account_details', lang_code).format(username=safe_username, expiry=safe_expiry))
        except Exception as e:
            print(f"Could not get expiry for {username}: {e}")
            pass
    await update.message.reply_text("\n\n".join(response), parse_mode=ParseMode.MARKDOWN_V2)

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data='set_lang_en')],
        [InlineKeyboardButton("🇸🇦 العربية", callback_data='set_lang_ar')],
    ]
    lang_code = get_user_language(update.effective_user.id)
    await update.message.reply_text(get_text('choose_language', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))

async def set_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang_code = query.data.split('_')[-1]
    set_user_language(query.from_user.id, lang_code)
    lang_map = {'en': 'English', 'ar': 'العربية'}
    await query.edit_message_text(text=get_text('language_set', lang_code).format(lang_name=lang_map.get(lang_code)))
    await start(update, context, from_callback=True)

async def verify_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    lang_code = get_user_language(user_id)

    if await check_membership(user_id, context):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            claimed = cursor.execute("SELECT join_bonus_claimed FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()
            if claimed and claimed[0] == 0:
                cursor.execute("UPDATE users SET points = points + ?, join_bonus_claimed = 1 WHERE telegram_user_id = ?", (JOIN_BONUS, user_id))
                conn.commit()
                await query.answer(get_text('join_bonus_awarded', lang_code).format(bonus=JOIN_BONUS), show_alert=True)
        
        await query.answer(get_text('force_join_success', lang_code))
        await query.delete_message()
        await start(update, context, from_callback=True)
    else:
        await query.answer(get_text('force_join_fail', lang_code), show_alert=True)

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_code = get_user_language(user_id)
    with sqlite3.connect(DB_FILE) as conn:
        points = conn.execute("SELECT points FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
    await update.message.reply_text(get_text('balance_info', lang_code).format(points=points), parse_mode=ParseMode.MARKDOWN)

async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_code = get_user_language(user_id)
    with sqlite3.connect(DB_FILE) as conn:
        ref_code = conn.execute("SELECT referral_code FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={ref_code}"
    await update.message.reply_text(get_text('referral_info', lang_code).format(bonus=REFERRAL_BONUS, link=link), parse_mode=ParseMode.MARKDOWN)

async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_code = get_user_language(user_id)
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        today = date.today()
        last_claim_str = cursor.execute("SELECT last_daily_claim FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
        
        if last_claim_str and date.fromisoformat(last_claim_str) == today:
            await update.message.reply_text(get_text('daily_bonus_already_claimed', lang_code))
            return

        cursor.execute("UPDATE users SET points = points + ?, last_daily_claim = ? WHERE telegram_user_id = ?", (DAILY_LOGIN_BONUS, today.isoformat(), user_id))
        conn.commit()
        new_balance = cursor.execute("SELECT points FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
        await update.message.reply_text(get_text('daily_bonus_claimed', lang_code).format(bonus=DAILY_LOGIN_BONUS, new_balance=new_balance))

async def redeem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = get_user_language(update.effective_user.id)
    await update.message.reply_text(get_text('redeem_prompt', lang_code))
    return REDEEM_CODE

async def process_redeem_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_code = get_user_language(user_id)
    code = update.message.text

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        code_data = cursor.execute("SELECT points, max_uses, current_uses FROM redeem_codes WHERE code = ?", (code,)).fetchone()
        if not code_data:
            await update.message.reply_text(get_text('redeem_invalid_code', lang_code))
            return ConversationHandler.END

        points, max_uses, current_uses = code_data
        if current_uses >= max_uses:
            await update.message.reply_text(get_text('redeem_limit_reached', lang_code))
            return ConversationHandler.END

        already_used = cursor.execute("SELECT 1 FROM redeemed_users WHERE code = ? AND telegram_user_id = ?", (code, user_id)).fetchone()
        if already_used:
            await update.message.reply_text(get_text('redeem_already_used', lang_code))
            return ConversationHandler.END

        cursor.execute("UPDATE users SET points = points + ? WHERE telegram_user_id = ?", (points, user_id))
        cursor.execute("UPDATE redeem_codes SET current_uses = current_uses + 1 WHERE code = ?", (code,))
        cursor.execute("INSERT INTO redeemed_users (code, telegram_user_id) VALUES (?, ?)", (code, user_id))
        conn.commit()
        new_balance = cursor.execute("SELECT points FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
        await update.message.reply_text(get_text('redeem_success', lang_code).format(points=points, new_balance=new_balance))
    return ConversationHandler.END

async def create_code_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    lang_code = get_user_language(update.effective_user.id)
    await update.message.reply_text(get_text('admin_create_code_prompt_name', lang_code))
    return CREATE_CODE_NAME

async def receive_code_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['code_name'] = update.message.text
    lang_code = get_user_language(update.effective_user.id)
    await update.message.reply_text(get_text('admin_create_code_prompt_points', lang_code))
    return CREATE_CODE_POINTS

async def receive_code_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['code_points'] = int(update.message.text)
        lang_code = get_user_language(update.effective_user.id)
        await update.message.reply_text(get_text('admin_create_code_prompt_uses', lang_code))
        return CREATE_CODE_USES
    except ValueError:
        await update.message.reply_text("Invalid number. Please send only digits.")
        return CREATE_CODE_POINTS

async def receive_code_uses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uses = int(update.message.text)
        name = context.user_data['code_name']
        points = context.user_data['code_points']

        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("INSERT OR REPLACE INTO redeem_codes (code, points, max_uses) VALUES (?, ?, ?)", (name, points, uses))
            conn.commit()

        lang_code = get_user_language(update.effective_user.id)
        await update.message.reply_text(get_text('admin_code_created', lang_code).format(code=name, points=points, uses=uses))
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Invalid number. Please send only digits.")
        return CREATE_CODE_USES

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    lang_code = get_user_language(update.effective_user.id)

    features = {
        'points_system': get_text('admin_feature_points', lang_code),
        'force_join': get_text('admin_feature_force_join', lang_code),
        'redeem_codes': get_text('admin_feature_redeem', lang_code)
    }

    keyboard = []
    for key, name in features.items():
        status_icon = get_text('status_enabled', lang_code) if is_feature_enabled(key) else get_text('status_disabled', lang_code)
        button_text = f"{name}: {status_icon}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"toggle_{key}")])

    # --- تمت إضافة زر إنشاء الكود هنا ---
    keyboard.append([InlineKeyboardButton(get_text('admin_create_code_button', lang_code), callback_data="admin_instruct_create_code")])
    
    await update.message.reply_text(get_text('admin_settings_header', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))

async def toggle_setting_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_USER_ID:
        await query.answer()
        return

    key_to_toggle = query.data.replace("toggle_", "")
    new_status = 'disabled' if is_feature_enabled(key_to_toggle) else 'enabled'
    set_setting(key_to_toggle, new_status)
    await query.answer(f"{key_to_toggle} is now {new_status}")

    # Refresh the settings message
    lang_code = get_user_language(query.from_user.id)
    features = {
        'points_system': get_text('admin_feature_points', lang_code),
        'force_join': get_text('admin_feature_force_join', lang_code),
        'redeem_codes': get_text('admin_feature_redeem', lang_code)
    }
    keyboard = []
    for key, name in features.items():
        status_icon = get_text('status_enabled', lang_code) if is_feature_enabled(key) else get_text('status_disabled', lang_code)
        button_text = f"{name}: {status_icon}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"toggle_{key}")])
    
    keyboard.append([InlineKeyboardButton(get_text('admin_create_code_button', lang_code), callback_data="admin_instruct_create_code")])

    try:
        await query.edit_message_text(text=get_text('admin_settings_header', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))
    except BadRequest: # Message is not modified
        pass

# --- تمت إضافة دالة جديدة لزر إنشاء الكود ---
async def admin_instruct_create_code_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_USER_ID:
        await query.answer()
        return
    lang_code = get_user_language(query.from_user.id)
    await query.answer(get_text('admin_create_code_instruction', lang_code), show_alert=True)

# =================================================================================
# 6. نقطة انطلاق البوت (Main Entry Point)
# =================================================================================
def main():
    """Runs the bot."""
    print("Initializing database...")
    init_db()

    print("Building bot application...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    create_code_handler = ConversationHandler(
        entry_points=[CommandHandler("create_code", create_code_command)],
        states={
            CREATE_CODE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_code_name)],
            CREATE_CODE_POINTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_code_points)],
            CREATE_CODE_USES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_code_uses)],
        },
        fallbacks=[],
    )
    redeem_handler = ConversationHandler(
        entry_points=[CommandHandler("redeem", redeem_command)],
        states={REDEEM_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_redeem_code)]},
        fallbacks=[],
    )

    # Admin Handlers
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(create_code_handler)
    app.add_handler(CallbackQueryHandler(toggle_setting_callback, pattern='^toggle_'))
    # --- تمت إضافة معالج جديد لزر إنشاء الكود ---
    app.add_handler(CallbackQueryHandler(admin_instruct_create_code_callback, pattern='^admin_instruct_create_code$'))

    # User Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(redeem_handler)
    app.add_handler(CallbackQueryHandler(verify_join_callback, pattern='^verify_join$'))
    app.add_handler(CallbackQueryHandler(set_language_callback, pattern='^set_lang_'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
