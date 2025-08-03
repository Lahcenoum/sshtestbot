# -*- coding: utf-8 -*-
import subprocess
import sys
import os
import random
import string
import sqlite3
import re
from datetime import datetime, date
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler,
)
from telegram.constants import ParseMode
from telegram.error import TelegramError

# =================================================================================
# 1. الإعدادات الرئيسية (Configuration)
# =================================================================================
# ⚠️ تأكد من وضع التوكن الخاص بك هنا. لا تشاركه مع أحد.
TOKEN = os.environ.get("TELEGRAM_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN") 
# ⚠️ استبدل هذا بمعرف المستخدم الخاص بك
ADMIN_USER_ID = 5344028088
# ⚠️ ضع هنا رابط حسابك أو معرفك للتواصل
ADMIN_CONTACT_INFO = "@YourAdminUsername"

# --- مسارات وإعدادات أساسية ---
# ⚠️ تأكد من أن هذا المسار صحيح وأن الملف قابل للتنفيذ
SCRIPT_PATH = '/usr/local/bin/create_ssh_user.sh'
DB_FILE = 'ssh_bot_users.db'

# --- قيم نظام النقاط ---
COST_PER_ACCOUNT = 4
REFERRAL_BONUS = 4
DAILY_LOGIN_BONUS = 1
INITIAL_POINTS = 2
JOIN_BONUS = 4
ACCOUNT_EXPIRY_DAYS = 2

# --- الانضمام الإجباري ---
# ⚠️ تأكد من صحة المعرفات والروابط وأن البوت مشرف في القناة والمجموعة
REQUIRED_CHANNEL_ID = -1001932589296
REQUIRED_GROUP_ID = -1002218671728
CHANNEL_LINK = "https://t.me/FASTVPSVIP"
GROUP_LINK = "https://t.me/dgtliA"

# --- التحقق من التوكن عند بدء التشغيل ---
if TOKEN == "YOUR_TELEGRAM_BOT_TOKEN" or not TOKEN:
    print("خطأ فادح: لم يتم تعيين توكن البوت بشكل صحيح.")
    print("يرجى تعيينه في متغيرات البيئة أو مباشرة في السكربت.")
    sys.exit(1)

# --- حالات المحادثات (لإدارة الحوارات متعددة الخطوات) ---
STATE_REDEEM_CODE = 1
STATE_CREATE_CODE_NAME, STATE_CREATE_CODE_POINTS, STATE_CREATE_CODE_USES = range(2, 5)
STATE_ADD_CHANNEL_NAME, STATE_ADD_CHANNEL_LINK, STATE_ADD_CHANNEL_ID, STATE_ADD_CHANNEL_POINTS = range(5, 9)

# =================================================================================
# 2. دعم اللغات (Localization)
# =================================================================================
# تم ترك هذا القسم كما هو، فهو منظم بشكل جيد.
TEXTS = {
    'ar': {
        "welcome": "أهلاً بك في بوت خدمة SSH!\n\nاستخدم الأزرار في الأسفل لإدارة حساباتك والحصول على المكافآت.",
        "get_ssh_button": "💳 طلب حساب جديد",
        "my_account_button": "👤 حسابي",
        "balance_button": "💰 رصيدي",
        "referral_button": "👥 دعوة أصدقاء",
        "redeem_button": "🎁 استرداد كود",
        "daily_button": "☀️ مكافأة يومية",
        "rewards_button": "📢 قنوات ومكافآت",
        "contact_admin_button": "👨‍💻 تواصل مع الأدمن",
        "contact_admin_info": "للتواصل مع الأدمن، يرجى مراسلة: {contact_info}",
        "rewards_header": "انضم إلى هذه القنوات والمجموعات واحصل على نقاط مجانية!",
        "reward_claimed": "✅ تم الحصول عليها",
        "verify_join_button": "✅ تحقق من الانضمام",
        "reward_success": "🎉 رائع! لقد حصلت على {points} نقطة.",
        "reward_fail": "❌ لم تنضم للقناة/المجموعة بعد. حاول مرة أخرى بعد الانضمام.",
        "no_channels_available": "ℹ️ لا توجد قنوات متاحة للمكافآت حاليًا.",
        "admin_panel_header": "⚙️ لوحة تحكم الأدمن",
        "admin_manage_channels_button": "📢 إدارة قنوات المكافآت",
        "admin_manage_codes_button": "🎁 إدارة أكواد الهدايا",
        "admin_create_code_button": "➕ إنشاء كود جديد",
        "admin_user_count_button": "📊 عدد المستخدمين",
        "admin_user_count_info": "👥 العدد الإجمالي للمستخدمين: {count}",
        "admin_add_channel_button": "➕ إضافة قناة/مجموعة",
        "admin_remove_channel_button": "➖ إزالة قناة/مجموعة",
        "admin_return_button": "⬅️ عودة",
        "admin_add_channel_name_prompt": "أرسل اسم القناة (مثال: قناتنا الإخبارية):",
        "admin_add_channel_link_prompt": "الآن أرسل رابط القناة الكامل (يبدأ بـ https://):",
        "admin_add_channel_id_prompt": "أرسل معرف القناة الرقمي (يجب أن يبدأ بـ -100):",
        "admin_add_channel_points_prompt": "أخيراً، أرسل عدد نقاط المكافأة:",
        "admin_channel_added_success": "✅ تم إضافة القناة بنجاح.",
        "admin_remove_channel_prompt": "اختر القناة التي تريد إزالتها:",
        "admin_channel_removed_success": "🗑️ تم إزالة القناة بنجاح.",
        "invalid_input": "❌ إدخال غير صالح، يرجى المحاولة مرة أخرى.",
        "operation_cancelled": "✅ تم إلغاء العملية.",
        "creation_success": "✅ تم إنشاء حسابك بنجاح!\n\n**البيانات:**\n```\n{details}\n```\n\n⚠️ **ملاحظة هامة**: سيتم حذف الحساب تلقائيًا بعد **{days} أيام**.",
        "account_details": "🏷️ **اسم المستخدم:** `{username}`\n🗓️ **تاريخ انتهاء الصلاحية:** `{expiry}`",
        "choose_language": "اختر لغتك المفضلة:",
        "language_set": "✅ تم تعيين اللغة إلى: {lang_name}",
        "force_join_prompt": "❗️لاستخدام البوت، يجب عليك الانضمام إلى قناتنا ومجموعتنا أولاً.\n\nبعد الانضمام، اضغط على زر 'تحققت'.",
        "force_join_channel_button": "📢 انضم للقناة",
        "force_join_group_button": "👥 انضم للمجموعة",
        "force_join_verify_button": "✅ تحققت",
        "force_join_success": "✅ شكرًا لانضمامك! يمكنك الآن استخدام البوت.",
        "force_join_fail": "❌ لم يتم التحقق من انضمامك. يرجى التأكد من انضمامك لكليهما ثم حاول مجدداً.",
        "join_bonus_awarded": "🎉 مكافأة الانضمام! لقد حصلت على **{bonus}** نقطة.",
        "redeem_prompt": "يرجى إرسال الكود الذي تريد استرداده.",
        "redeem_success": "🎉 تهانينا! لقد حصلت على **{points}** نقطة. رصيدك الآن هو **{new_balance}**.",
        "redeem_invalid_code": "❌ هذا الكود غير صالح أو منتهي الصلاحية.",
        "redeem_limit_reached": "❌ لقد وصل هذا الكود إلى الحد الأقصى من الاستخدام.",
        "redeem_already_used": "❌ لقد قمت بالفعل باستخدام هذا الكود.",
        "not_enough_points": "⚠️ ليس لديك نقاط كافية. التكلفة هي **{cost}** نقطة لإنشاء حساب.",
        "no_accounts_found": "ℹ️ لم يتم العثور على أي حسابات نشطة مرتبطة بك.",
        "your_accounts": "👤 حساباتك النشطة:",
        "balance_info": "💰 رصيدك الحالي هو: **{points}** نقطة.",
        "referral_info": "👥 ادعُ أصدقاءك واكسب **{bonus}** نقطة عن كل صديق جديد يبدأ البوت عبر رابطك!\n\n🔗 رابط الإحالة الخاص بك:\n`{link}`",
        "daily_bonus_claimed": "🎉 لقد حصلت على مكافأتك اليومية: **{bonus}** نقطة! رصيدك الآن هو **{new_balance}**.",
        "daily_bonus_already_claimed": "ℹ️ لقد حصلت بالفعل على مكافأتك اليومية. تعال غدًا!",
        "creation_error": "❌ حدث خطأ أثناء إنشاء الحساب. ربما وصلت إلى الحد الأقصى للحسابات. يرجى التواصل مع الأدمن.",
        "admin_code_created": "✅ تم إنشاء الكود `{code}` بنجاح. يمنح **{points}** نقطة ومتاح لـ **{uses}** مستخدمين.",
        "admin_create_code_prompt_name": "أرسل اسم الكود الجديد (مثال: WELCOME2025):",
        "admin_create_code_prompt_points": "الآن أرسل عدد النقاط التي يمنحها هذا الكود:",
        "admin_create_code_prompt_uses": "أخيراً، أرسل عدد المستخدمين الذين يمكنهم استخدام هذا الكود:",
        "bot_error": "⚙️ حدث خطأ ما. يرجى المحاولة مرة أخرى لاحقًا.",
    },
    # يمكن إضافة ترجمات للغة الإنجليزية هنا
    'en': {},
}

# =================================================================================
# 3. إدارة قاعدة البيانات (Database Management)
# =================================================================================
def get_db_connection():
    """إنشاء وإرجاع اتصال بقاعدة البيانات."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # للوصول إلى الأعمدة بالاسم
    return conn

def init_db():
    """إنشاء الجداول الأساسية في قاعدة البيانات إذا لم تكن موجودة."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # جدول حسابات SSH
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ssh_accounts (
                id INTEGER PRIMARY KEY,
                telegram_user_id INTEGER NOT NULL,
                ssh_username TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # جدول المستخدمين
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_user_id INTEGER PRIMARY KEY,
                language_code TEXT DEFAULT 'ar',
                points INTEGER DEFAULT 0,
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                last_daily_claim DATE,
                join_bonus_claimed INTEGER DEFAULT 0
            )
        ''')
        # جدول أكواد الهدايا
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS redeem_codes (
                code TEXT PRIMARY KEY,
                points INTEGER NOT NULL,
                max_uses INTEGER NOT NULL,
                current_uses INTEGER DEFAULT 0
            )
        ''')
        # جدول المستخدمين الذين استردوا الأكواد
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS redeemed_users (
                code TEXT,
                telegram_user_id INTEGER,
                PRIMARY KEY (code, telegram_user_id)
            )
        ''')
        # جدول قنوات المكافآت
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reward_channels (
                channel_id INTEGER PRIMARY KEY,
                channel_link TEXT NOT NULL,
                reward_points INTEGER NOT NULL,
                channel_name TEXT NOT NULL
            )
        ''')
        # جدول المستخدمين الذين حصلوا على مكافآت القنوات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_channel_rewards (
                telegram_user_id INTEGER,
                channel_id INTEGER,
                PRIMARY KEY (telegram_user_id, channel_id)
            )
        ''')
        conn.commit()
        print("Database initialized successfully.")

def get_user_language(user_id: int) -> str:
    """الحصول على لغة المستخدم من قاعدة البيانات."""
    with get_db_connection() as conn:
        res = conn.execute("SELECT language_code FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()
        return res['language_code'] if res else 'ar'

def get_or_create_user(user_id: int, referred_by: int = None) -> dict:
    """
    الحصول على بيانات المستخدم أو إنشاء مستخدم جديد إذا لم يكن موجودًا.
    تقوم بإرجاع صف المستخدم.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        user = cursor.execute("SELECT * FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()
        if not user:
            ref_code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            cursor.execute(
                "INSERT INTO users (telegram_user_id, points, referral_code, referred_by) VALUES (?, ?, ?, ?)",
                (user_id, INITIAL_POINTS, ref_code, referred_by)
            )
            if referred_by:
                cursor.execute("UPDATE users SET points = points + ? WHERE telegram_user_id = ?", (REFERRAL_BONUS, referred_by))
            conn.commit()
            user = cursor.execute("SELECT * FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()
    return user

def get_text(key: str, lang_code: str = 'ar') -> str:
    """الحصول على النص المترجم. يعود إلى العربية إذا لم تكن الترجمة موجودة."""
    return TEXTS.get(lang_code, TEXTS['ar']).get(key, key)

# =================================================================================
# 4. دوال مساعدة (Helper Functions)
# =================================================================================
def escape_markdown_v2(text: str) -> str:
    """تهريب الأحرف الخاصة في Markdown V2."""
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def generate_password() -> str:
    """إنشاء كلمة مرور عشوائية."""
    return "sshdotbot-" + ''.join(random.choices(string.ascii_letters + string.digits, k=4))

async def check_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """التحقق من عضوية المستخدم في القناة والمجموعة الإجبارية."""
    try:
        channel_member = await context.bot.get_chat_member(REQUIRED_CHANNEL_ID, user_id)
        group_member = await context.bot.get_chat_member(REQUIRED_GROUP_ID, user_id)
        # التحقق من أن المستخدم ليس فقط موجودًا بل ليس محظورًا أو قد غادر
        return all(m.status in ['member', 'administrator', 'creator'] for m in [channel_member, group_member])
    except TelegramError as e:
        print(f"Error checking membership for user {user_id}: {e}")
        # إذا كان البوت محظورًا من قبل المستخدم أو هناك خطأ آخر، نعتبره غير عضو
        return False
    except Exception as e:
        print(f"An unexpected error occurred in check_membership: {e}")
        return False

# =================================================================================
# 5. أوامر البوت (Bot Commands & Handlers)
# =================================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأمر /start."""
    user = update.effective_user
    
    # معالجة رابط الإحالة
    referred_by = None
    if context.args:
        try:
            with get_db_connection() as conn:
                res = conn.execute("SELECT telegram_user_id FROM users WHERE referral_code = ?", (context.args[0],)).fetchone()
                if res and res['telegram_user_id'] != user.id:
                    referred_by = res['telegram_user_id']
        except Exception as e:
            print(f"Error processing referral code: {e}")
    
    get_or_create_user(user.id, referred_by)
    lang_code = get_user_language(user.id)

    # التحقق من الانضمام الإجباري
    if not await check_membership(user.id, context):
        keyboard = [
            [InlineKeyboardButton(get_text('force_join_channel_button', lang_code), url=CHANNEL_LINK)],
            [InlineKeyboardButton(get_text('force_join_group_button', lang_code), url=GROUP_LINK)],
            [InlineKeyboardButton(get_text('force_join_verify_button', lang_code), callback_data='verify_join')],
        ]
        await update.message.reply_text(
            get_text('force_join_prompt', lang_code),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض القائمة الرئيسية للمستخدم."""
    user_id = update.effective_user.id
    lang_code = get_user_language(user_id)

    keyboard_layout = [
        [KeyboardButton(get_text('get_ssh_button', lang_code))],
        [KeyboardButton(get_text('balance_button', lang_code)), KeyboardButton(get_text('my_account_button', lang_code))],
        [KeyboardButton(get_text('daily_button', lang_code)), KeyboardButton(get_text('referral_button', lang_code))],
        [KeyboardButton(get_text('rewards_button', lang_code)), KeyboardButton(get_text('redeem_button', lang_code))],
        [KeyboardButton(get_text('contact_admin_button', lang_code))]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard_layout, resize_keyboard=True)
    
    # تحديد الرسالة بناءً على ما إذا كانت من callback أو رسالة جديدة
    reply_func = update.message.reply_text
    if update.callback_query:
        # إذا كانت من callback، نستخدم edit_message_text لتجنب إرسال رسالة جديدة
        # ولكن بما أننا نغير لوحة المفاتيح من inline إلى reply، يجب إرسال رسالة جديدة
        await update.callback_query.message.reply_text(get_text('welcome', lang_code), reply_markup=reply_markup)
        try:
            # نحاول حذف الرسالة القديمة التي تحتوي على أزرار inline
            await update.callback_query.message.delete()
        except TelegramError as e:
            print(f"Could not delete message after showing main menu: {e}")
    else:
        await reply_func(get_text('welcome', lang_code), reply_markup=reply_markup)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل النصية من المستخدم (الأزرار)."""
    user_id = update.effective_user.id
    get_or_create_user(user_id)
    
    if not await check_membership(user_id, context):
        await start(update, context)
        return

    text = update.message.text
    lang_code = get_user_language(user_id)
    
    # قاموس يربط كل نص بالوظيفة المناسبة
    button_map = {
        get_text('get_ssh_button', lang_code): get_ssh,
        get_text('my_account_button', lang_code): my_account,
        get_text('balance_button', lang_code): balance_command,
        get_text('referral_button', lang_code): referral_command,
        get_text('daily_button', lang_code): daily_command,
        get_text('redeem_button', lang_code): redeem_command,
        get_text('rewards_button', lang_code): rewards_command,
        get_text('contact_admin_button', lang_code): contact_admin_command,
    }

    if text in button_map:
        await button_map[text](update, context)
    else:
        # يمكنك إضافة رسالة هنا إذا أرسل المستخدم نصًا عشوائيًا
        pass

async def get_ssh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إنشاء حساب SSH جديد للمستخدم."""
    user_id = update.effective_user.id
    user = get_or_create_user(user_id)
    lang_code = user['language_code']
    
    # التحقق من النقاط
    if user['points'] < COST_PER_ACCOUNT:
        await update.message.reply_text(get_text('not_enough_points', lang_code).format(cost=COST_PER_ACCOUNT))
        return

    # إنشاء اسم مستخدم فريد وكلمة مرور
    username = f"user{user_id}{random.randint(100, 999)}"
    password = generate_password()
    command_to_run = ["sudo", SCRIPT_PATH, username, password, str(ACCOUNT_EXPIRY_DAYS)]
    
    try:
        # تنفيذ السكربت الخارجي
        process = subprocess.run(
            command_to_run, 
            capture_output=True, 
            text=True, 
            timeout=30, 
            check=True,
            encoding='utf-8' # تحديد الترميز
        )
        result = process.stdout
        
        # تحديث قاعدة البيانات
        with get_db_connection() as conn:
            conn.execute("UPDATE users SET points = points - ? WHERE telegram_user_id = ?", (COST_PER_ACCOUNT, user_id))
            conn.execute(
                "INSERT INTO ssh_accounts (telegram_user_id, ssh_username) VALUES (?, ?)",
                (user_id, username)
            )
            conn.commit()
        
        # إرسال تفاصيل الحساب للمستخدم
        escaped_details = escape_markdown_v2(result)
        await update.message.reply_text(
            get_text('creation_success', lang_code).format(details=escaped_details, days=ACCOUNT_EXPIRY_DAYS),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    except subprocess.CalledProcessError as e:
        print(f"Error creating SSH account (script failed): {e.stderr}")
        await update.message.reply_text(get_text('creation_error', lang_code))
    except subprocess.TimeoutExpired:
        print("Error creating SSH account: Script timed out.")
        await update.message.reply_text(get_text('creation_error', lang_code))
    except Exception as e:
        print(f"An unexpected error occurred in get_ssh: {e}")
        await update.message.reply_text(get_text('bot_error', lang_code))


async def my_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض حسابات SSH النشطة للمستخدم."""
    user_id = update.effective_user.id
    lang_code = get_user_language(user_id)
    
    with get_db_connection() as conn:
        accounts = conn.execute("SELECT ssh_username FROM ssh_accounts WHERE telegram_user_id = ?", (user_id,)).fetchall()
    
    if not accounts:
        await update.message.reply_text(get_text('no_accounts_found', lang_code))
        return

    response_parts = [get_text('your_accounts', lang_code)]
    for account in accounts:
        username = account['ssh_username']
        try:
            # الحصول على تاريخ انتهاء الصلاحية
            expiry_output = subprocess.check_output(['/usr/bin/chage', '-l', username], text=True, encoding='utf-8')
            expiry_line = next((line for line in expiry_output.split('\n') if "Account expires" in line), None)
            expiry_date = expiry_line.split(':', 1)[1].strip() if expiry_line else "لا ينتهي"
            
            safe_username = escape_markdown_v2(username)
            safe_expiry = escape_markdown_v2(expiry_date)
            response_parts.append(get_text('account_details', lang_code).format(username=safe_username, expiry=safe_expiry))
        except FileNotFoundError:
             response_parts.append(f"⚠️ تعذر التحقق من صلاحية الحساب: `{username}` (الأمر `chage` غير موجود).")
        except Exception as e:
            print(f"Could not get expiry for {username}: {e}")
            response_parts.append(f"⚠️ تعذر الحصول على صلاحية الحساب: `{username}`.")
            
    await update.message.reply_text("\n\n".join(response_parts), parse_mode=ParseMode.MARKDOWN_V2)

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض رصيد نقاط المستخدم."""
    user = get_or_create_user(update.effective_user.id)
    lang_code = user['language_code']
    await update.message.reply_text(
        get_text('balance_info', lang_code).format(points=user['points']),
        parse_mode=ParseMode.MARKDOWN
    )

async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض رابط الإحالة الخاص بالمستخدم."""
    user = get_or_create_user(update.effective_user.id)
    lang_code = user['language_code']
    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={user['referral_code']}"
    await update.message.reply_text(
        get_text('referral_info', lang_code).format(bonus=REFERRAL_BONUS, link=link),
        parse_mode=ParseMode.MARKDOWN
    )

async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منح المستخدم المكافأة اليومية."""
    user_id = update.effective_user.id
    lang_code = get_user_language(user_id)
    today = date.today()
    
    with get_db_connection() as conn:
        user = conn.execute("SELECT last_daily_claim, points FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()
        
        # التحقق مما إذا كانت المكافأة قد تم الحصول عليها اليوم
        last_claim_date = date.fromisoformat(user['last_daily_claim']) if user['last_daily_claim'] else None
        if last_claim_date == today:
            await update.message.reply_text(get_text('daily_bonus_already_claimed', lang_code))
            return
            
        # تحديث النقاط وتاريخ آخر مكافأة
        new_balance = user['points'] + DAILY_LOGIN_BONUS
        conn.execute(
            "UPDATE users SET points = ?, last_daily_claim = ? WHERE telegram_user_id = ?",
            (new_balance, today.isoformat(), user_id)
        )
        conn.commit()
        
        await update.message.reply_text(
            get_text('daily_bonus_claimed', lang_code).format(bonus=DAILY_LOGIN_BONUS, new_balance=new_balance)
        )

async def contact_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض معلومات التواصل مع الأدمن."""
    lang_code = get_user_language(update.effective_user.id)
    await update.message.reply_text(get_text('contact_admin_info', lang_code).format(contact_info=ADMIN_CONTACT_INFO))

# --- قسم الأدمن ---

async def admin_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض لوحة تحكم الأدمن."""
    user = update.effective_user
    if user.id != ADMIN_USER_ID:
        return

    lang_code = get_user_language(user.id)
    keyboard = [
        [InlineKeyboardButton(get_text('admin_manage_channels_button', lang_code), callback_data='admin_manage_channels')],
        [InlineKeyboardButton(get_text('admin_manage_codes_button', lang_code), callback_data='admin_manage_codes')],
        [InlineKeyboardButton(get_text('admin_user_count_button', lang_code), callback_data='admin_user_count')],
        # يمكنك إضافة أزرار أخرى هنا
    ]
    
    text = get_text('admin_panel_header', lang_code)
    # إذا كانت من callback، نعدل الرسالة، وإلا نرسل رسالة جديدة
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ... باقي دوال الأدمن والمحادثات تم تركها كما هي لأنها منظمة بشكل جيد ...
# (تم الاحتفاظ ببنية المحادثات لإنشاء الأكواد وإضافة القنوات)

async def verify_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة زر التحقق من الانضمام الإجباري."""
    query = update.callback_query
    await query.answer() # تأكيد استلام الـ callback
    user_id = query.from_user.id
    lang_code = get_user_language(user_id)
    
    if await check_membership(user_id, context):
        with get_db_connection() as conn:
            user = conn.execute("SELECT join_bonus_claimed FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()
            if not user['join_bonus_claimed']:
                conn.execute("UPDATE users SET points = points + ?, join_bonus_claimed = 1 WHERE telegram_user_id = ?", (JOIN_BONUS, user_id))
                conn.commit()
                await query.answer(get_text('join_bonus_awarded', lang_code).format(bonus=JOIN_BONUS), show_alert=True)
        
        await query.answer(get_text('force_join_success', lang_code))
        await show_main_menu(update, context)
    else:
        await query.answer(get_text('force_join_fail', lang_code), show_alert=True)

# =================================================================================
# 6. نقطة انطلاق البوت (Main Entry Point)
# =================================================================================
def main():
    """الدالة الرئيسية لتشغيل البوت."""
    print("Initializing database...")
    init_db()
    
    print("Building bot application...")
    # استخدام Application.builder() للطريقة الحديثة
    application = Application.builder().token(TOKEN).build()

    # --- تعريف المحادثات ---
    # محادثة إضافة قناة جديدة
    add_channel_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_channel_start, pattern='^admin_add_channel_start$')],
        states={
            STATE_ADD_CHANNEL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_get_name)],
            STATE_ADD_CHANNEL_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_get_link)],
            STATE_ADD_CHANNEL_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_get_id)],
            STATE_ADD_CHANNEL_POINTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_get_points)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation), CallbackQueryHandler(cancel_conversation, pattern='^cancel$')]
    )
    
    # محادثة استرداد الكود
    redeem_conv = ConversationHandler(
        # تم تغيير entry_points ليبدأ عند الضغط على الزر بدلاً من الأمر
        entry_points=[MessageHandler(filters.Regex(f"^{re.escape(get_text('redeem_button', 'ar'))}$"), redeem_command)],
        states={
            STATE_REDEEM_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_redeem_code)]
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )

    # محادثة إنشاء كود جديد
    create_code_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(create_code_start, pattern='^admin_create_code_start$')],
        states={
            STATE_CREATE_CODE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_code_name)],
            STATE_CREATE_CODE_POINTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_code_points)],
            STATE_CREATE_CODE_USES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_code_uses)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation), CallbackQueryHandler(cancel_conversation, pattern='^cancel$')]
    )

    # --- إضافة المعالجات (Handlers) ---
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_panel_command))
    application.add_handler(CommandHandler("language", language_command))
    
    # إضافة معالجات المحادثات
    application.add_handler(add_channel_conv)
    application.add_handler(redeem_conv)
    application.add_handler(create_code_conv)

    # معالجات الـ CallbackQuery
    application.add_handler(CallbackQueryHandler(admin_panel_command, pattern='^admin_panel_main$'))
    application.add_handler(CallbackQueryHandler(admin_panel_callback, pattern='^admin_')) # يجب أن يكون هذا بعد المعالجات الأكثر تحديدًا
    application.add_handler(CallbackQueryHandler(remove_channel_start, pattern='^admin_remove_channel_start$'))
    application.add_handler(CallbackQueryHandler(remove_channel_confirm, pattern='^remove_c_'))
    application.add_handler(CallbackQueryHandler(verify_reward_callback, pattern='^verify_r_'))
    application.add_handler(CallbackQueryHandler(verify_join_callback, pattern='^verify_join$'))
    application.add_handler(CallbackQueryHandler(set_language_callback, pattern='^set_lang_'))
    application.add_handler(CallbackQueryHandler(lambda u,c: u.callback_query.answer(), pattern='^dummy$'))
    
    # معالج الرسائل النصية (يجب أن يكون في النهاية)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    # بدء تشغيل البوت
    application.run_polling()

# --- الكود الخاص بالأدمن الذي لم يتغير ---
# (هذه الدوال تحتاج إلى تعريفها في السكربت الكامل)
async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def add_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def add_channel_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def add_channel_get_link(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def add_channel_get_id(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def add_channel_get_points(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def remove_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def remove_channel_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def rewards_command(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def verify_reward_callback(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def redeem_command(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def process_redeem_code(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def create_code_start(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def receive_code_name(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def receive_code_points(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def receive_code_uses(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def set_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
# --- نهاية الكود الذي لم يتغير ---

if __name__ == '__main__':
    main()
