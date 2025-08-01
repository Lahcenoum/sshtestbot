import subprocess
import sys
import os
import random
import string
import sqlite3
import re
from datetime import datetime, date, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest

# =================================================================================
# 1. الإعدادات الرئيسية (Configuration)
# =================================================================================
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
ADMIN_USER_ID = 5344028088 # ⚠️ استبدل هذا بمعرف المستخدم الخاص بك
ADMIN_CONTACT_INFO = "@YourAdminUsername" # ⚠️ ضع هنا رابط حسابك أو معرفك

SCRIPT_PATH = '/usr/local/bin/create_ssh_user.sh'
DB_FILE = 'ssh_bot_users.db'

# --- قيم نظام النقاط ---
COST_PER_ACCOUNT = 4
REFERRAL_BONUS = 4
DAILY_LOGIN_BONUS = 1
INITIAL_POINTS = 2
JOIN_BONUS = 4
ACCOUNT_EXPIRY_DAYS = 2

# Channel and Group links and IDs (for force join)
REQUIRED_CHANNEL_ID = -1001932589296
REQUIRED_GROUP_ID = -1002218671728
CHANNEL_LINK = "https://t.me/FASTVPSVIP"
GROUP_LINK = "https://t.me/dgtliA"

if TOKEN == "YOUR_TELEGRAM_BOT_TOKEN" or not TOKEN:
    print("Fatal Error: Bot token is not set correctly in bot.py.")
    sys.exit(1)

# Conversation handler states
REDEEM_CODE = range(1)
CREATE_CODE_NAME, CREATE_CODE_POINTS, CREATE_CODE_USES = range(3)
(ADD_CHANNEL_NAME, ADD_CHANNEL_LINK, ADD_CHANNEL_ID, ADD_CHANNEL_POINTS) = range(4)


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
        "rewards_button": "📢 قنوات ومكافآت",
        "contact_admin_button": "👨‍💻 تواصل مع الأدمن",
        "contact_admin_info": "للتواصل مع الأدمن، يرجى مراسلة: {contact_info}",
        "rewards_header": "انضم إلى هذه القنوات واحصل على نقاط!",
        "reward_claimed": "✅ تم الحصول عليها",
        "verify_join_button": "✅ تحقق من الانضمام",
        "reward_success": "🎉 رائع! لقد حصلت على {points} نقطة.",
        "reward_fail": "❌ لم تنضم للقناة بعد. حاول مرة أخرى بعد الانضمام.",
        "no_channels_available": "ℹ️ لا توجد قنوات متاحة للمكافآت حاليًا.",
        "admin_panel_header": "⚙️ لوحة تحكم الأدمن",
        "admin_manage_channels_button": " إدارة قنوات المكافآت",
        "admin_user_count_button": "👤 عدد المستخدمين",
        "admin_user_count_info": "📊 العدد الإجمالي للمستخدمين: {count}",
        "admin_add_channel_button": "➕ إضافة قناة",
        "admin_remove_channel_button": "➖ إزالة قناة",
        "admin_return_button": "⬅️ عودة",
        "admin_add_channel_name_prompt": "أرسل اسم القناة:",
        "admin_add_channel_link_prompt": "الآن أرسل رابط القناة الكامل:",
        "admin_add_channel_id_prompt": "أرسل معرف القناة الرقمي (يبدأ بـ -100):",
        "admin_add_channel_points_prompt": "أخيراً، أرسل عدد نقاط المكافأة:",
        "admin_channel_added_success": "✅ تم إضافة القناة بنجاح.",
        "admin_remove_channel_prompt": "اختر القناة التي تريد إزالتها:",
        "admin_channel_removed_success": "🗑️ تم إزالة القناة بنجاح.",
        "invalid_input": "❌ إدخال غير صالح، يرجى المحاولة مرة أخرى.",
        "operation_cancelled": "✅ تم إلغاء العملية.",
        "creation_success": "✅ تم إنشاء حسابك بنجاح!\n\n**البيانات:**\n```\n{details}\n```\n\n⚠️ **ملاحظة**: سيتم حذفه تلقائيًا بعد **{days} أيام**.",
        "account_details": "🏷️ **اسم المستخدم:** `{username}`\n🗓️ **تاريخ انتهاء الصلاحية:** `{expiry}`",
        "choose_language": "اختر لغتك المفضلة:",
        "language_set": "✅ تم تعيين اللغة إلى: {lang_name}",
        "force_join_prompt": "❗️لاستخدام البوت، يجب عليك الانضمام إلى قناتنا ومجموعتنا أولاً.\n\nبعد الانضمام، اضغط على زر 'تحققت'.",
        "force_join_channel_button": "📢 انضم للقناة",
        "force_join_group_button": "👥 انضم للمجموعة",
        "force_join_verify_button": "✅ تحققت",
        "force_join_success": "✅ شكرًا لانضمامك! يمكنك الآن استخدام البوت.",
        "force_join_fail": "❌ لم يتم التحقق من انضمامك. يرجى التأكد من انضمامك لكليهما.",
        "join_bonus_awarded": "🎉 مكافأة الانضمام! لقد حصلت على **{bonus}** نقطة.",
        "redeem_prompt": "يرجى إرسال الكود الذي تريد استرداده.",
        "redeem_success": "🎉 تهانينا! لقد حصلت على **{points}** نقطة. رصيدك الآن هو **{new_balance}**.",
        "redeem_invalid_code": "❌ هذا الكود غير صالح أو غير موجود.",
        "redeem_limit_reached": "❌ لقد وصل هذا الكود إلى الحد الأقصى من الاستخدام.",
        "redeem_already_used": "❌ لقد قمت بالفعل باستخدام هذا الكود.",
        "admin_settings_header": "⚙️ لوحة تحكم إعدادات البوت",
        "admin_feature_points": "نظام النقاط",
        "admin_feature_force_join": "الانضمام الإجباري",
        "admin_feature_redeem": "أكواد المكافآت",
        "status_enabled": "🟢 مفعل",
        "status_disabled": "🔴 معطل",
        "not_enough_points": "⚠️ ليس لديك نقاط كافية. التكلفة هي **{cost}** نقطة.",
        "no_accounts_found": "ℹ️ لم يتم العثور على أي حسابات مرتبطة بك.",
        "your_accounts": "👤 حساباتك النشطة:",
        "balance_info": "💰 رصيدك الحالي هو: **{points}** نقطة.",
        "referral_info": "👥 ادعُ أصدقاءك واكسب **{bonus}** نقطة لكل صديق جديد يبدأ البوت عبر رابطك!\n\n🔗 رابط الإحالة الخاص بك:\n`{link}`",
        "daily_bonus_claimed": "🎉 لقد حصلت على مكافأتك اليومية: **{bonus}** نقطة! رصيدك الآن هو **{new_balance}**.",
        "daily_bonus_already_claimed": "ℹ️ لقد حصلت بالفعل على مكافأتك اليومية. تعال غدًا!",
        "creation_error": "❌ حدث خطأ أثناء إنشاء الحساب. يرجى التواصل مع الأدمن.",
    },
    'en': {
        # Full English translations can be added here
    },
}

# =================================================================================
# 3. إدارة قاعدة البيانات (Database Management)
# =================================================================================
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS ssh_accounts (id INTEGER PRIMARY KEY, telegram_user_id INTEGER, ssh_username TEXT, created_at TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (telegram_user_id INTEGER PRIMARY KEY, language_code TEXT DEFAULT 'ar', points INTEGER DEFAULT 0, referral_code TEXT, referred_by INTEGER, last_daily_claim DATE, join_bonus_claimed INTEGER DEFAULT 0)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS redeem_codes (code TEXT PRIMARY KEY, points INTEGER, max_uses INTEGER, current_uses INTEGER DEFAULT 0)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS redeemed_users (code TEXT, telegram_user_id INTEGER, PRIMARY KEY (code, telegram_user_id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS reward_channels (channel_id INTEGER PRIMARY KEY, channel_link TEXT NOT NULL, reward_points INTEGER NOT NULL, channel_name TEXT NOT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_channel_rewards (telegram_user_id INTEGER, channel_id INTEGER, PRIMARY KEY (telegram_user_id, channel_id))''')
        
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

def get_user_language(user_id):
    with sqlite3.connect(DB_FILE) as conn:
        res = conn.execute("SELECT language_code FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()
        return res[0] if res else 'ar'

def set_user_language(user_id, lang_code):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("UPDATE users SET language_code = ? WHERE telegram_user_id = ?", (lang_code, user_id))
        conn.commit()

def get_or_create_user(user_id, referred_by=None):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        if not cursor.execute("SELECT 1 FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone():
            ref_code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            cursor.execute("INSERT INTO users (telegram_user_id, points, referral_code, referred_by) VALUES (?, ?, ?, ?)", (user_id, INITIAL_POINTS, ref_code, referred_by))
            if referred_by and is_feature_enabled('points_system'):
                cursor.execute("UPDATE users SET points = points + ? WHERE telegram_user_id = ?", (REFERRAL_BONUS, referred_by))
            conn.commit()

def get_text(key, lang_code='ar'):
    return TEXTS.get(lang_code, TEXTS['ar']).get(key, key)

# =================================================================================
# 4. دوال مساعدة (Helper Functions)
# =================================================================================
def escape_markdown_v2(text: str) -> str:
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def generate_password():
    return "sshdotbot-" + ''.join(random.choices(string.ascii_letters + string.digits, k=4))

async def check_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not is_feature_enabled('force_join'): return True
    try:
        channel = await context.bot.get_chat_member(REQUIRED_CHANNEL_ID, user_id)
        group = await context.bot.get_chat_member(REQUIRED_GROUP_ID, user_id)
        return all(m.status in ['member', 'administrator', 'creator'] for m in [channel, group])
    except Exception:
        return False

# =================================================================================
# 5. أوامر البوت (Bot Commands & Handlers)
# =================================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False):
    user = update.effective_user
    message = update.message if not from_callback else update.callback_query.message
    
    referred_by = None
    if context.args:
        try:
            with sqlite3.connect(DB_FILE) as conn:
                res = conn.execute("SELECT telegram_user_id FROM users WHERE referral_code = ?", (context.args[0],)).fetchone()
                if res and res[0] != user.id: referred_by = res[0]
        except Exception: pass
    
    get_or_create_user(user.id, referred_by)
    lang_code = get_user_language(user.id)

    if not await check_membership(user.id, context):
        keyboard = [
            [InlineKeyboardButton(get_text('force_join_channel_button', lang_code), url=CHANNEL_LINK)],
            [InlineKeyboardButton(get_text('force_join_group_button', lang_code), url=GROUP_LINK)],
            [InlineKeyboardButton(get_text('force_join_verify_button', lang_code), callback_data='verify_join')],
        ]
        await message.reply_text(get_text('force_join_prompt', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))
        return

    keyboard_layout = [
        [KeyboardButton(get_text('get_ssh_button', lang_code))],
        [KeyboardButton(get_text('balance_button', lang_code)), KeyboardButton(get_text('my_account_button', lang_code))],
        [KeyboardButton(get_text('daily_button', lang_code)), KeyboardButton(get_text('referral_button', lang_code))],
        [KeyboardButton(get_text('rewards_button', lang_code)), KeyboardButton(get_text('redeem_button', lang_code))],
        [KeyboardButton(get_text('contact_admin_button', lang_code))]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard_layout, resize_keyboard=True)
    await message.reply_text(get_text('welcome', lang_code), reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_membership(user_id, context):
        await start(update, context)
        return

    text = update.message.text
    lang_code = get_user_language(user_id)
    
    # This is a robust way to handle buttons in multiple languages
    button_map = {
        'get_ssh_button': get_ssh,
        'my_account_button': my_account,
        'balance_button': balance_command,
        'referral_button': referral_command,
        'daily_button': daily_command,
        'redeem_button': redeem_command,
        'rewards_button': rewards_command,
        'contact_admin_button': contact_admin_command,
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

    username = f"user{user_id}"
    password = generate_password()
    command_to_run = [SCRIPT_PATH, username, password, str(ACCOUNT_EXPIRY_DAYS)]
    
    try:
        process = subprocess.run(command_to_run, capture_output=True, text=True, timeout=30, check=True)
        result = process.stdout
        with sqlite3.connect(DB_FILE) as conn:
            if is_feature_enabled('points_system'):
                conn.execute("UPDATE users SET points = points - ? WHERE telegram_user_id = ?", (COST_PER_ACCOUNT, user_id))
            conn.execute("INSERT INTO ssh_accounts (telegram_user_id, ssh_username, created_at) VALUES (?, ?, ?)", (user_id, username, datetime.now()))
            conn.commit()
        
        escaped_details = escape_markdown_v2(result)
        await update.message.reply_text(
            get_text('creation_success', lang_code).format(details=escaped_details, days=ACCOUNT_EXPIRY_DAYS),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    except Exception as e:
        print(f"Error creating SSH account: {e}")
        await update.message.reply_text(get_text('creation_error', lang_code))

async def my_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_code = get_user_language(user_id)
    with sqlite3.connect(DB_FILE) as conn:
        accounts = conn.execute("SELECT ssh_username FROM ssh_accounts WHERE telegram_user_id = ?", (user_id,)).fetchall()
    
    if not accounts:
        await update.message.reply_text(get_text('no_accounts_found', lang_code))
        return

    response = [get_text('your_accounts', lang_code)]
    for (username,) in accounts:
        try:
            expiry_output = subprocess.check_output(['/usr/bin/chage', '-l', username], text=True)
            expiry = next((line.split(':', 1)[1].strip() for line in expiry_output.split('\n') if "Account expires" in line), "Never")
            safe_username = escape_markdown_v2(username)
            safe_expiry = escape_markdown_v2(expiry)
            response.append(get_text('account_details', lang_code).format(username=safe_username, expiry=safe_expiry))
        except Exception as e:
            print(f"Could not get expiry for {username}: {e}")
    await update.message.reply_text("\n\n".join(response), parse_mode=ParseMode.MARKDOWN_V2)

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

async def contact_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = get_user_language(update.effective_user.id)
    await update.message.reply_text(get_text('contact_admin_info', lang_code).format(contact_info=ADMIN_CONTACT_INFO))

# --- Admin Panel & Features ---
async def admin_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID: return
    lang_code = get_user_language(update.effective_user.id)
    keyboard = [
        [InlineKeyboardButton(get_text('admin_manage_channels_button', lang_code), callback_data='admin_manage_channels')],
        [InlineKeyboardButton(get_text('admin_user_count_button', lang_code), callback_data='admin_user_count')]
    ]
    await update.message.reply_text(get_text('admin_panel_header', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_USER_ID: return

    data = query.data
    lang_code = get_user_language(query.from_user.id)

    if data == 'admin_user_count':
        with sqlite3.connect(DB_FILE) as conn:
            count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        await query.edit_message_text(get_text('admin_user_count_info', lang_code).format(count=count), reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(get_text('admin_return_button', lang_code), callback_data='admin_panel_main')]
        ]))
    
    elif data == 'admin_manage_channels':
        keyboard = [
            [InlineKeyboardButton(get_text('admin_add_channel_button', lang_code), callback_data='admin_add_channel_start')],
            [InlineKeyboardButton(get_text('admin_remove_channel_button', lang_code), callback_data='admin_remove_channel_start')],
            [InlineKeyboardButton(get_text('admin_return_button', lang_code), callback_data='admin_panel_main')]
        ]
        await query.edit_message_text("إدارة قنوات المكافآت:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'admin_panel_main':
        await admin_panel_command(query, context) # Re-show main admin panel

# --- Add/Remove Channel Logic ---
async def add_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(get_text('admin_add_channel_name_prompt', 'ar'))
    return ADD_CHANNEL_NAME

async def add_channel_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['channel_name'] = update.message.text
    await update.message.reply_text(get_text('admin_add_channel_link_prompt', 'ar'))
    return ADD_CHANNEL_LINK

async def add_channel_get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['channel_link'] = update.message.text
    await update.message.reply_text(get_text('admin_add_channel_id_prompt', 'ar'))
    return ADD_CHANNEL_ID

async def add_channel_get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['channel_id'] = int(update.message.text)
        await update.message.reply_text(get_text('admin_add_channel_points_prompt', 'ar'))
        return ADD_CHANNEL_POINTS
    except ValueError:
        await update.message.reply_text(get_text('invalid_input', 'ar'))
        return ADD_CHANNEL_ID

async def add_channel_get_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        points = int(update.message.text)
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("INSERT OR REPLACE INTO reward_channels VALUES (?, ?, ?, ?)",
                         (context.user_data['channel_id'], context.user_data['channel_link'], points, context.user_data['channel_name']))
        await update.message.reply_text(get_text('admin_channel_added_success', 'ar'))
        context.user_data.clear()
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(get_text('invalid_input', 'ar'))
        return ADD_CHANNEL_POINTS

async def remove_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    with sqlite3.connect(DB_FILE) as conn:
        channels = conn.execute("SELECT channel_id, channel_name FROM reward_channels").fetchall()
    if not channels:
        await query.message.reply_text("لا توجد قنوات لإزالتها.")
        return
    keyboard = [[InlineKeyboardButton(name, callback_data=f"remove_c_{cid}")] for cid, name in channels]
    keyboard.append([InlineKeyboardButton(get_text('admin_return_button', 'ar'), callback_data='admin_manage_channels')])
    await query.edit_message_text(get_text('admin_remove_channel_prompt', 'ar'), reply_markup=InlineKeyboardMarkup(keyboard))

async def remove_channel_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    channel_id = int(query.data.split('_')[-1])
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("DELETE FROM reward_channels WHERE channel_id = ?", (channel_id,))
        conn.execute("DELETE FROM user_channel_rewards WHERE channel_id = ?", (channel_id,))
    await query.edit_message_text(get_text('admin_channel_removed_success', 'ar'))

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_text('operation_cancelled', 'ar'))
    context.user_data.clear()
    return ConversationHandler.END

# --- Rewards Logic ---
async def rewards_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_code = get_user_language(user_id)
    with sqlite3.connect(DB_FILE) as conn:
        all_channels = conn.execute("SELECT channel_id, channel_link, reward_points, channel_name FROM reward_channels").fetchall()
        claimed_ids = {row[0] for row in conn.execute("SELECT channel_id FROM user_channel_rewards WHERE telegram_user_id = ?", (user_id,))}
    if not all_channels:
        await update.message.reply_text(get_text('no_channels_available', lang_code))
        return
    keyboard = []
    for cid, link, points, name in all_channels:
        if cid in claimed_ids:
            button = InlineKeyboardButton(f"✅ {name}", callback_data="dummy")
        else:
            button = InlineKeyboardButton(f"{name} (+{points} نقطة)", url=link)
        keyboard.append([button])
        if cid not in claimed_ids:
             keyboard.append([InlineKeyboardButton(get_text('verify_join_button', lang_code), callback_data=f"verify_r_{cid}")])
    await update.message.reply_text(get_text('rewards_header', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))

async def verify_reward_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    lang_code = get_user_language(user_id)
    channel_id = int(query.data.split('_')[-1])
    try:
        member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        if member.status not in ['member', 'administrator', 'creator']:
            await query.answer(get_text('reward_fail', lang_code), show_alert=True)
            return
    except Exception as e:
        await query.answer(f"خطأ: لا يمكن التحقق. تأكد من أن البوت مشرف في القناة.", show_alert=True)
        return
    
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        if cursor.execute("SELECT 1 FROM user_channel_rewards WHERE telegram_user_id = ? AND channel_id = ?", (user_id, channel_id)).fetchone():
            await query.answer("لقد حصلت على هذه المكافأة بالفعل.", show_alert=True)
            return
        points = cursor.execute("SELECT reward_points FROM reward_channels WHERE channel_id = ?", (channel_id,)).fetchone()[0]
        cursor.execute("UPDATE users SET points = points + ? WHERE telegram_user_id = ?", (points, user_id))
        cursor.execute("INSERT INTO user_channel_rewards (telegram_user_id, channel_id) VALUES (?, ?)", (user_id, channel_id))
        conn.commit()
    await query.answer(get_text('reward_success', lang_code).format(points=points), show_alert=True)
    await rewards_command(query, context) # Refresh the message

# --- Redeem Code Conversation ---
async def redeem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_text('redeem_prompt', get_user_language(update.effective_user.id)))
    return REDEEM_CODE

async def process_redeem_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Full logic for redeeming a code
    pass

# --- Settings Command ---
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Full logic for the settings panel
    pass

# --- Language Command ---
async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data='set_lang_en')],
        [InlineKeyboardButton("🇸🇦 العربية", callback_data='set_lang_ar')],
    ]
    await update.message.reply_text(get_text('choose_language', get_user_language(update.effective_user.id)), reply_markup=InlineKeyboardMarkup(keyboard))

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
            if not cursor.execute("SELECT join_bonus_claimed FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]:
                cursor.execute("UPDATE users SET points = points + ?, join_bonus_claimed = 1 WHERE telegram_user_id = ?", (JOIN_BONUS, user_id))
                conn.commit()
                await query.answer(get_text('join_bonus_awarded', lang_code).format(bonus=JOIN_BONUS), show_alert=True)
        
        await query.answer(get_text('force_join_success', lang_code))
        await query.delete_message()
        await start(update, context, from_callback=True)
    else:
        await query.answer(get_text('force_join_fail', lang_code), show_alert=True)

async def toggle_setting_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Full logic for toggling settings
    pass

# =================================================================================
# 6. نقطة انطلاق البوت (Main Entry Point)
# =================================================================================
def main():
    print("Initializing database...")
    init_db()
    print("Building bot application...")
    app = ApplicationBuilder().token(TOKEN).build()

    # Conversation Handlers
    add_channel_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_channel_start, pattern='^admin_add_channel_start$')],
        states={
            ADD_CHANNEL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_get_name)],
            ADD_CHANNEL_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_get_link)],
            ADD_CHANNEL_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_get_id)],
            ADD_CHANNEL_POINTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_get_points)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )
    
    redeem_conv = ConversationHandler(
        entry_points=[CommandHandler("redeem", redeem_command)],
        states={REDEEM_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_redeem_code)]},
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )

    # Add all handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel_command))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("language", language_command))
    
    app.add_handler(add_channel_conv)
    app.add_handler(redeem_conv)

    app.add_handler(CallbackQueryHandler(admin_panel_callback, pattern='^admin_'))
    app.add_handler(CallbackQueryHandler(remove_channel_start, pattern='^admin_remove_channel_start$'))
    app.add_handler(CallbackQueryHandler(remove_channel_confirm, pattern='^remove_c_'))
    app.add_handler(CallbackQueryHandler(verify_reward_callback, pattern='^verify_r_'))
    app.add_handler(CallbackQueryHandler(verify_join_callback, pattern='^verify_join$'))
    app.add_handler(CallbackQueryHandler(set_language_callback, pattern='^set_lang_'))
    app.add_handler(CallbackQueryHandler(toggle_setting_callback, pattern='^toggle_'))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
