import sys
import subprocess
import random
import string
import sqlite3
import re
import traceback
import html
from datetime import datetime, date, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest

# =================================================================================
# 1. الإعدادات الرئيسية (Configuration)
# =================================================================================
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN" 
ADMIN_USER_ID = 5344028088 
# سيتم الآن قراءة هذه المعلومة من قاعدة البيانات، وهذه قيمة احتياطية
ADMIN_CONTACT_INFO = "@YourAdminUsername" 

SCRIPT_PATH = '/usr/local/bin/create_ssh_user.sh'
DB_FILE = 'ssh_bot_users.db'

# --- قيم نظام النقاط ---
COST_PER_ACCOUNT = 4
DAILY_LOGIN_BONUS = 1
INITIAL_POINTS = 2
JOIN_BONUS = 4
ACCOUNT_EXPIRY_DAYS = 2

# Channel and Group links and IDs (for force join)
REQUIRED_CHANNEL_ID = -1001932589296
REQUIRED_GROUP_ID = -1002218671728
CHANNEL_LINK = "https://t.me/FASTVPSVIP"
GROUP_LINK = "https://t.me/dgtliA"

# Conversation handler states
(ADD_CHANNEL_NAME, ADD_CHANNEL_LINK, ADD_CHANNEL_ID, ADD_CHANNEL_POINTS) = range(4)
(CREATE_CODE_NAME, CREATE_CODE_POINTS, CREATE_CODE_USES) = range(4, 7)
(BAN_USER_ID, UNBAN_USER_ID, REDEEM_CODE_INPUT) = range(7, 10)
(EDIT_HOSTNAME, EDIT_WS_PORTS, EDIT_SSL_PORT, EDIT_UDPCUSTOM, EDIT_ADMIN_CONTACT) = range(10, 15)

# =================================================================================
# 2. دعم اللغات (Localization)
# =================================================================================
TEXTS = {
    'ar': {
        "welcome": "أهلاً بك في بوت خدمة SSH!\n\nاستخدم الأزرار أدناه للتفاعل.",
        "get_ssh_button": "💳 طلب حساب جديد",
        "my_account_button": "👤 حسابي",
        "balance_button": "💰 رصيدي",
        "earn_points_button": "🎁 كسب النقاط",
        "redeem_code_button": "🎁 استرداد كود",
        "daily_button": "☀️ مكافأة يومية",
        "contact_admin_button": "👨‍💻 تواصل مع الأدمن",
        "contact_admin_info": "للتواصل مع الأدمن، يرجى مراسلة: {contact_info}",
        "not_enough_points": "⚠️ ليس لديك نقاط كافية. التكلفة هي <b>{cost}</b> نقطة.",
        "creation_error": "❌ حدث خطأ أثناء إنشاء الحساب. قد يكون لديك حساب بالفعل أو خطأ آخر.",
        "creation_wait": "⏳ لا يمكنك إنشاء حساب جديد الآن. يرجى الانتظار <b>{time_left}</b>.",
        "force_join_prompt": "❗️لاستخدام البوت، يجب عليك الانضمام إلى قناتنا ومجموعتنا أولاً.\n\nبعد الانضمام، اضغط على زر '✅ تحققت'.",
        "force_join_channel_button": "📢 انضم للقناة",
        "force_join_group_button": "👥 انضم للمجموعة",
        "force_join_verify_button": "✅ تحققت",
        "force_join_success": "✅ شكرًا لانضمامك! يمكنك الآن استخدام البوت.",
        "force_join_fail": "❌ لم يتم التحقق من انضمامك. يرجى التأكد من انضمامك لكليهما والمحاولة مرة أخرى.",
        "join_bonus_awarded": "🎉 مكافأة الانضمام! لقد حصلت على {bonus} نقطة.",
        "balance_info": "💰 رصيدك الحالي هو: <b>{points}</b> نقطة.",
        "daily_bonus_claimed": "🎉 لقد حصلت على مكافأتك اليومية: <b>{bonus}</b> نقطة! رصيدك الآن هو <b>{new_balance}</b>.",
        "daily_bonus_already_claimed": "ℹ️ لقد حصلت بالفعل على مكافأتك اليومية. تعال غدًا!",
        "no_accounts_found": "ℹ️ لم يتم العثور على أي حسابات نشطة مرتبطة بك.",
        "your_accounts": "<b>👤 حساباتك النشطة:</b>",
        "account_details": "🏷️ <b>اسم المستخدم:</b> <code>{username}</code>\n🗓️ <b>تاريخ انتهاء الصلاحية:</b> <code>{expiry}</code>",
        "banned_message": "❌ لقد تم حظرك من استخدام هذا البوت.",
        "rewards_header": "انضم إلى هذه القنوات والمجموعات واحصل على نقاط!",
        "verify_join_button": "✅ تحقق من الانضمام",
        "reward_success": "🎉 رائع! لقد حصلت على {points} نقطة.",
        "reward_fail": "❌ لم تنضم بعد. حاول مرة أخرى بعد الانضمام.",
        "no_channels_available": "ℹ️ لا توجد قنوات متاحة للمكافآت حاليًا.",
        "redeem_prompt": "يرجى إرسال الكود الذي تريد استرداده.",
        "redeem_success": "🎉 تهانينا! لقد حصلت على <b>{points}</b> نقطة. رصيدك الآن هو <b>{new_balance}</b>.",
        "redeem_invalid_code": "❌ هذا الكود غير صالح أو غير موجود.",
        "redeem_limit_reached": "❌ لقد وصل هذا الكود إلى الحد الأقصى من الاستخدام.",
        "redeem_already_used": "❌ لقد قمت بالفعل باستخدام هذا الكود.",
        "admin_panel_header": "⚙️ لوحة تحكم الأدمن",
        "admin_return_button": "⬅️ عودة",
        "admin_manage_rewards_button": "📢 إدارة قنوات الربح",
        "admin_manage_codes_button": "🎁 إدارة أكواد الهدايا",
        "admin_manage_users_button": "👥 إدارة المستخدمين",
        "admin_edit_connection_info_button": "⚙️ تعديل معلومات الاتصال",
        "admin_add_channel_button": "➕ إضافة قناة/مجموعة",
        "admin_remove_channel_button": "➖ إزالة قناة/مجموعة",
        "admin_add_channel_name_prompt": "أرسل اسم القناة:",
        "admin_add_channel_link_prompt": "الآن أرسل رابط القناة الكامل:",
        "admin_add_channel_id_prompt": "أرسل معرف القناة الرقمي (يبدأ بـ -100):",
        "admin_add_channel_points_prompt": "أخيراً، أرسل عدد نقاط المكافأة:",
        "admin_channel_added_success": "✅ تم إضافة القناة بنجاح.",
        "admin_remove_channel_prompt": "اختر القناة التي تريد إزالتها:",
        "admin_channel_removed_success": "🗑️ تم إزالة القناة بنجاح.",
        "admin_create_code_button": "➕ إنشاء كود جديد",
        "admin_create_code_prompt_name": "أرسل اسم الكود الجديد (مثال: WELCOME2025):",
        "admin_create_code_prompt_points": "الآن أرسل عدد النقاط التي يمنحها هذا الكود:",
        "admin_create_code_prompt_uses": "أخيراً، أرسل عدد المستخدمين الذين يمكنهم استخدام هذا الكود:",
        "admin_code_created": "✅ تم إنشاء الكود <code>{code}</code> بنجاح. يمنح <b>{points}</b> نقطة ومتاح لـ <b>{uses}</b> مستخدمين.",
        "admin_ban_user_button": "🚫 حظر مستخدم",
        "admin_unban_user_button": "✅ إلغاء حظر مستخدم",
        "admin_ban_user_prompt": "أرسل المعرف الرقمي (ID) للمستخدم الذي تريد حظره:",
        "admin_unban_user_prompt": "أرسل المعرف الرقمي (ID) للمستخدم الذي تريد إلغاء حظره:",
        "admin_user_banned_success": "✅ تم حظر المستخدم بنجاح.",
        "admin_user_unbanned_success": "✅ تم إلغاء حظر المستخدم بنجاح.",
        "admin_edit_hostname_prompt": "أرسل الـ Hostname الجديد:",
        "admin_edit_ws_ports_prompt": "أرسل بورتات Websocket الجديدة (مثال: 80, 8880):",
        "admin_edit_ssl_port_prompt": "أرسل بورت SSL الجديد:",
        "admin_edit_udpcustom_prompt": "أرسل بورت UDPCUSTOM الجديد:",
        "admin_edit_contact_prompt": "أرسل معلومات التواصل الجديدة (مثال: @username):",
        "admin_info_updated_success": "✅ تم تحديث معلومات الاتصال بنجاح.",
        "invalid_input": "❌ إدخال غير صالح، يرجى المحاولة مرة أخرى.",
        "operation_cancelled": "✅ تم إلغاء العملية.",
    },
}

def get_text(key, lang_code='ar'):
    # Fetches text for the given key and language.
    return TEXTS.get(lang_code, TEXTS['ar']).get(key, key)

# =================================================================================
# 3. إدارة قاعدة البيانات (Database Management)
# =================================================================================
def init_db():
    # Initializes the database and creates tables if they don't exist.
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS ssh_accounts (id INTEGER PRIMARY KEY, telegram_user_id INTEGER NOT NULL, ssh_username TEXT NOT NULL, created_at TIMESTAMP NOT NULL)')
        cursor.execute('CREATE TABLE IF NOT EXISTS users (telegram_user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 0, last_daily_claim DATE, join_bonus_claimed INTEGER DEFAULT 0)')
        cursor.execute('CREATE TABLE IF NOT EXISTS reward_channels (channel_id INTEGER PRIMARY KEY, channel_link TEXT NOT NULL, reward_points INTEGER NOT NULL, channel_name TEXT NOT NULL)')
        cursor.execute('CREATE TABLE IF NOT EXISTS user_channel_rewards (telegram_user_id INTEGER, channel_id INTEGER, PRIMARY KEY (telegram_user_id, channel_id))')
        cursor.execute('CREATE TABLE IF NOT EXISTS redeem_codes (code TEXT PRIMARY KEY, points INTEGER, max_uses INTEGER, current_uses INTEGER DEFAULT 0)')
        cursor.execute('CREATE TABLE IF NOT EXISTS redeemed_users (code TEXT, telegram_user_id INTEGER, PRIMARY KEY (code, telegram_user_id))')
        cursor.execute('CREATE TABLE IF NOT EXISTS banned_users (telegram_user_id INTEGER PRIMARY KEY)')
        cursor.execute('CREATE TABLE IF NOT EXISTS connection_settings (key TEXT PRIMARY KEY, value TEXT)')
        
        # Add default settings if they don't exist
        default_settings = {
            "hostname": "your.hostname.com",
            "ws_ports": "80, 8880, 8888, 2053",
            "ssl_port": "443",
            "udpcustom_port": "7300",
            "admin_contact": ADMIN_CONTACT_INFO
        }
        for key, value in default_settings.items():
            cursor.execute("INSERT OR IGNORE INTO connection_settings (key, value) VALUES (?, ?)", (key, value))
            
        conn.commit()

def get_or_create_user(user_id):
    # Gets a user from the database or creates a new one.
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        if not cursor.execute("SELECT 1 FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone():
            cursor.execute("INSERT INTO users (telegram_user_id, points) VALUES (?, ?)", (user_id, INITIAL_POINTS))
            conn.commit()

def is_user_banned(user_id):
    # Checks if a user is in the banned list.
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("SELECT 1 FROM banned_users WHERE telegram_user_id = ?", (user_id,)).fetchone() is not None

def get_connection_setting(key):
    # Retrieves a specific connection setting from the database.
    with sqlite3.connect(DB_FILE) as conn:
        result = conn.execute("SELECT value FROM connection_settings WHERE key = ?", (key,)).fetchone()
        return result[0] if result else ""

def set_connection_setting(key, value):
    # Updates a specific connection setting in the database.
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT OR REPLACE INTO connection_settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()

# =================================================================================
# 4. دوال مساعدة وديكورات (Helpers & Decorators)
# =================================================================================
def check_banned(func):
    # Decorator to block banned users from using commands.
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if is_user_banned(user_id):
            await update.message.reply_text(get_text('banned_message'))
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def generate_password():
    # Generates a new random password.
    return "bot" + ''.join(random.choices(string.ascii_letters + string.digits, k=6))

async def check_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    # Checks if the user is a member of the required channel and group.
    try:
        channel_member = await context.bot.get_chat_member(REQUIRED_CHANNEL_ID, user_id)
        group_member = await context.bot.get_chat_member(REQUIRED_GROUP_ID, user_id)
        if channel_member.status not in ['member', 'administrator', 'creator']: return False
        if group_member.status not in ['member', 'administrator', 'creator']: return False
        return True
    except Exception as e:
        print(f"Error checking membership for {user_id}: {e}")
        return False

# =================================================================================
# 5. أوامر البوت الأساسية (Core Bot Commands)
# =================================================================================
@check_banned
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback: bool = False):
    # Handles the /start command.
    user = update.effective_user
    message = update.message if not from_callback else update.callback_query.message
    get_or_create_user(user.id)

    if not await check_membership(user.id, context):
        keyboard = [
            [InlineKeyboardButton(get_text('force_join_channel_button'), url=CHANNEL_LINK)],
            [InlineKeyboardButton(get_text('force_join_group_button'), url=GROUP_LINK)],
            [InlineKeyboardButton(get_text('force_join_verify_button'), callback_data='verify_join')],
        ]
        await message.reply_text(get_text('force_join_prompt'), reply_markup=InlineKeyboardMarkup(keyboard))
        return

    keyboard_layout = [
        [KeyboardButton(get_text('get_ssh_button'))],
        [KeyboardButton(get_text('balance_button')), KeyboardButton(get_text('my_account_button'))],
        [KeyboardButton(get_text('daily_button')), KeyboardButton(get_text('earn_points_button'))],
        [KeyboardButton(get_text('redeem_code_button')), KeyboardButton(get_text('contact_admin_button'))]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard_layout, resize_keyboard=True)
    await message.reply_text(get_text('welcome'), reply_markup=reply_markup)

@check_banned
async def get_ssh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Handles the request for a new SSH account.
    user_id = update.effective_user.id
    
    # Check for one account per 24 hours limit.
    with sqlite3.connect(DB_FILE) as conn:
        last_creation = conn.execute("SELECT MAX(created_at) FROM ssh_accounts WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
    
    if last_creation:
        last_creation_time = datetime.strptime(last_creation, '%Y-%m-%d %H:%M:%S.%f')
        if datetime.now() - last_creation_time < timedelta(hours=24):
            time_left = timedelta(hours=24) - (datetime.now() - last_creation_time)
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            await update.message.reply_text(get_text('creation_wait').format(time_left=f"{hours} ساعة و {minutes} دقيقة"), parse_mode=ParseMode.HTML)
            return

    await update.message.reply_text("⏳ جاري إنشاء الحساب...")

    with sqlite3.connect(DB_FILE) as conn:
        user_points = conn.execute("SELECT points FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
    
    if user_points < COST_PER_ACCOUNT:
        await update.message.reply_text(get_text('not_enough_points').format(cost=COST_PER_ACCOUNT), parse_mode=ParseMode.HTML)
        return

    try:
        username = f"sshdatbot{user_id}"
        password = generate_password()
        command_to_run = ["sudo", SCRIPT_PATH, username, password, str(ACCOUNT_EXPIRY_DAYS)]

        process = subprocess.run(command_to_run, capture_output=True, text=True, timeout=30, check=True)
        
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("UPDATE users SET points = points - ? WHERE telegram_user_id = ?", (COST_PER_ACCOUNT, user_id))
            conn.execute("INSERT INTO ssh_accounts (telegram_user_id, ssh_username, created_at) VALUES (?, ?, ?)", (user_id, username, datetime.now()))
            conn.commit()

        result_details = process.stdout
        
        # Fetch connection info from DB to build the message.
        hostname = get_connection_setting("hostname")
        ws_ports = get_connection_setting("ws_ports")
        ssl_port = get_connection_setting("ssl_port")
        udpcustom_port = get_connection_setting("udpcustom_port")

        # Format the success message using HTML.
        account_info = (
            f"<b>✅ تم إنشاء حسابك بنجاح!</b>\n\n"
            f"<b>البيانات الأساسية:</b>\n"
            f"<pre><code>{html.escape(result_details.strip())}</code></pre>\n\n"
            f"<b>Hostname:</b> <code>{html.escape(hostname)}</code>\n\n"
            f"<b> Websocket Ports:</b> <code>{html.escape(ws_ports)}</code>\n"
            f"<b> SSL Port:</b> <code>{html.escape(ssl_port)}</code>\n"
            f"<b> Websocket SSL Port:</b> <code>{html.escape(ssl_port)}</code>\n"
            f"<b> UDPCUSTOM Port:</b> <code>{html.escape(udpcustom_port)}</code>\n\n"
            f"⚠️ <b>ملاحظة</b>: الحساب صالح لمستخدم واحد فقط للحفاظ على السرعة."
        )
        await update.message.reply_text(account_info, parse_mode=ParseMode.HTML)

    except Exception as e:
        print("--- AN UNEXPECTED ERROR OCCURRED ---"); traceback.print_exc()
        await update.message.reply_text(get_text('creation_error'))

@check_banned
async def my_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Shows the user's active accounts.
    user_id = update.effective_user.id
    with sqlite3.connect(DB_FILE) as conn:
        accounts = conn.execute("SELECT ssh_username FROM ssh_accounts WHERE telegram_user_id = ?", (user_id,)).fetchall()
    
    if not accounts:
        await update.message.reply_text(get_text('no_accounts_found')); return

    response_parts = [get_text('your_accounts')]
    for (username,) in accounts:
        try:
            expiry_output = subprocess.check_output(['/usr/bin/chage', '-l', username], text=True, stderr=subprocess.DEVNULL)
            expiry_line = next((line for line in expiry_output.split('\n') if "Account expires" in line), None)
            expiry = expiry_line.split(':', 1)[1].strip() if expiry_line else "N/A"
            response_parts.append(get_text('account_details').format(username=html.escape(username), expiry=html.escape(expiry)))
        except Exception as e: print(f"Could not get expiry for {username}: {e}")
    
    await update.message.reply_text("\n\n".join(response_parts), parse_mode=ParseMode.HTML)

@check_banned
async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Shows the user's point balance.
    user_id = update.effective_user.id
    with sqlite3.connect(DB_FILE) as conn:
        points = conn.execute("SELECT points FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
    await update.message.reply_text(get_text('balance_info').format(points=points), parse_mode=ParseMode.HTML)

@check_banned
async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Gives the user a daily point bonus.
    user_id = update.effective_user.id
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        today = date.today()
        last_claim_str = cursor.execute("SELECT last_daily_claim FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
        
        if last_claim_str and date.fromisoformat(last_claim_str) >= today:
            await update.message.reply_text(get_text('daily_bonus_already_claimed')); return
            
        cursor.execute("UPDATE users SET points = points + ?, last_daily_claim = ? WHERE telegram_user_id = ?", (DAILY_LOGIN_BONUS, today.isoformat(), user_id))
        conn.commit()
        new_balance = cursor.execute("SELECT points FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
        await update.message.reply_text(get_text('daily_bonus_claimed').format(bonus=DAILY_LOGIN_BONUS, new_balance=new_balance), parse_mode=ParseMode.HTML)

@check_banned
async def contact_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Shows the admin's contact info.
    contact_info = get_connection_setting("admin_contact")
    await update.message.reply_text(get_text('contact_admin_info').format(contact_info=contact_info))

# =================================================================================
# 6. Admin Panel & Features
# =================================================================================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Displays the main admin panel.
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID: return

    keyboard = [
        [InlineKeyboardButton(get_text('admin_manage_rewards_button'), callback_data='admin_manage_rewards')],
        [InlineKeyboardButton(get_text('admin_manage_codes_button'), callback_data='admin_manage_codes')],
        [InlineKeyboardButton(get_text('admin_manage_users_button'), callback_data='admin_manage_users')],
        [InlineKeyboardButton(get_text('admin_edit_connection_info_button'), callback_data='admin_edit_connection_info')],
    ]
    await update.message.reply_text(get_text('admin_panel_header'), reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Handles all callbacks from the admin panel buttons.
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id != ADMIN_USER_ID: return
    
    data = query.data
    if data == 'admin_panel_main':
        keyboard = [
            [InlineKeyboardButton(get_text('admin_manage_rewards_button'), callback_data='admin_manage_rewards')],
            [InlineKeyboardButton(get_text('admin_manage_codes_button'), callback_data='admin_manage_codes')],
            [InlineKeyboardButton(get_text('admin_manage_users_button'), callback_data='admin_manage_users')],
            [InlineKeyboardButton(get_text('admin_edit_connection_info_button'), callback_data='admin_edit_connection_info')],
        ]
        await query.edit_message_text(get_text('admin_panel_header'), reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == 'admin_manage_rewards':
        keyboard = [
            [InlineKeyboardButton(get_text('admin_add_channel_button'), callback_data='admin_add_channel_start')],
            [InlineKeyboardButton(get_text('admin_remove_channel_button'), callback_data='admin_remove_channel_start')],
            [InlineKeyboardButton(get_text('admin_return_button'), callback_data='admin_panel_main')]
        ]
        await query.edit_message_text(get_text('admin_manage_rewards_button'), reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == 'admin_manage_codes':
        keyboard = [
            [InlineKeyboardButton(get_text('admin_create_code_button'), callback_data='admin_create_code_start')],
            [InlineKeyboardButton(get_text('admin_return_button'), callback_data='admin_panel_main')]
        ]
        await query.edit_message_text(get_text('admin_manage_codes_button'), reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == 'admin_manage_users':
        keyboard = [
            [InlineKeyboardButton(get_text('admin_ban_user_button'), callback_data='admin_ban_user_start')],
            [InlineKeyboardButton(get_text('admin_unban_user_button'), callback_data='admin_unban_user_start')],
            [InlineKeyboardButton(get_text('admin_return_button'), callback_data='admin_panel_main')]
        ]
        await query.edit_message_text(get_text('admin_manage_users_button'), reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == 'admin_edit_connection_info':
        await query.edit_message_text(get_text('admin_edit_hostname_prompt'))
        context.user_data.clear() 
        return EDIT_HOSTNAME

# --- Conversations for Admin ---
async def add_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    await query.edit_message_text(get_text('admin_add_channel_name_prompt'))
    return ADD_CHANNEL_NAME

async def add_channel_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['channel_name'] = update.message.text
    await update.message.reply_text(get_text('admin_add_channel_link_prompt'))
    return ADD_CHANNEL_LINK

async def add_channel_get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['channel_link'] = update.message.text
    await update.message.reply_text(get_text('admin_add_channel_id_prompt'))
    return ADD_CHANNEL_ID

async def add_channel_get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['channel_id'] = int(update.message.text)
        await update.message.reply_text(get_text('admin_add_channel_points_prompt'))
        return ADD_CHANNEL_POINTS
    except ValueError:
        await update.message.reply_text(get_text('invalid_input')); return ADD_CHANNEL_ID

async def add_channel_get_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        points = int(update.message.text)
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("INSERT OR REPLACE INTO reward_channels (channel_id, channel_link, reward_points, channel_name) VALUES (?, ?, ?, ?)",
                         (context.user_data['channel_id'], context.user_data['channel_link'], points, context.user_data['channel_name']))
        await update.message.reply_text(get_text('admin_channel_added_success'))
        context.user_data.clear()
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(get_text('invalid_input')); return ADD_CHANNEL_POINTS

async def remove_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    with sqlite3.connect(DB_FILE) as conn:
        channels = conn.execute("SELECT channel_id, channel_name FROM reward_channels").fetchall()
    if not channels:
        await query.edit_message_text("لا توجد قنوات لإزالتها.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text('admin_return_button'), callback_data='admin_manage_rewards')]])); return
    keyboard = [[InlineKeyboardButton(name, callback_data=f"remove_c_{cid}")] for cid, name in channels]
    keyboard.append([InlineKeyboardButton(get_text('admin_return_button'), callback_data='admin_manage_rewards')])
    await query.edit_message_text(get_text('admin_remove_channel_prompt'), reply_markup=InlineKeyboardMarkup(keyboard))

async def remove_channel_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    channel_id = int(query.data.split('_')[-1])
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("DELETE FROM reward_channels WHERE channel_id = ?", (channel_id,))
        conn.execute("DELETE FROM user_channel_rewards WHERE channel_id = ?", (channel_id,))
    await query.edit_message_text(get_text('admin_channel_removed_success'))
    await admin_panel_callback(update, context) 

async def create_code_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    await query.edit_message_text(get_text('admin_create_code_prompt_name'))
    return CREATE_CODE_NAME

async def receive_code_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['code_name'] = update.message.text
    await update.message.reply_text(get_text('admin_create_code_prompt_points'))
    return CREATE_CODE_POINTS

async def receive_code_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['code_points'] = int(update.message.text)
        await update.message.reply_text(get_text('admin_create_code_prompt_uses'))
        return CREATE_CODE_USES
    except ValueError:
        await update.message.reply_text(get_text('invalid_input')); return CREATE_CODE_POINTS

async def receive_code_uses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uses = int(update.message.text)
        name = context.user_data['code_name']
        points = context.user_data['code_points']
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("INSERT OR REPLACE INTO redeem_codes (code, points, max_uses) VALUES (?, ?, ?)", (name, points, uses))
        await update.message.reply_text(get_text('admin_code_created').format(code=name, points=points, uses=uses), parse_mode=ParseMode.HTML)
        context.user_data.clear()
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(get_text('invalid_input')); return CREATE_CODE_USES

async def ban_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    await query.edit_message_text(get_text('admin_ban_user_prompt'))
    return BAN_USER_ID

async def ban_user_id_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id_to_ban = int(update.message.text)
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("INSERT OR IGNORE INTO banned_users (telegram_user_id) VALUES (?)", (user_id_to_ban,))
        await update.message.reply_text(get_text('admin_user_banned_success'))
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(get_text('invalid_input')); return BAN_USER_ID

async def unban_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    await query.edit_message_text(get_text('admin_unban_user_prompt'))
    return UNBAN_USER_ID

async def unban_user_id_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id_to_unban = int(update.message.text)
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("DELETE FROM banned_users WHERE telegram_user_id = ?", (user_id_to_unban,))
        await update.message.reply_text(get_text('admin_user_unbanned_success'))
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(get_text('invalid_input')); return UNBAN_USER_ID

# Conversation for editing connection info
async def edit_hostname_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['hostname'] = update.message.text
    await update.message.reply_text(get_text('admin_edit_ws_ports_prompt'))
    return EDIT_WS_PORTS

async def edit_ws_ports_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ws_ports'] = update.message.text
    await update.message.reply_text(get_text('admin_edit_ssl_port_prompt'))
    return EDIT_SSL_PORT

async def edit_ssl_port_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ssl_port'] = update.message.text
    await update.message.reply_text(get_text('admin_edit_udpcustom_prompt'))
    return EDIT_UDPCUSTOM

async def edit_udpcustom_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['udpcustom_port'] = update.message.text
    await update.message.reply_text(get_text('admin_edit_contact_prompt'))
    return EDIT_ADMIN_CONTACT

async def edit_admin_contact_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    set_connection_setting('hostname', context.user_data['hostname'])
    set_connection_setting('ws_ports', context.user_data['ws_ports'])
    set_connection_setting('ssl_port', context.user_data['ssl_port'])
    set_connection_setting('udpcustom_port', context.user_data['udpcustom_port'])
    set_connection_setting('admin_contact', update.message.text)
    await update.message.reply_text(get_text('admin_info_updated_success'))
    context.user_data.clear()
    return ConversationHandler.END

# =================================================================================
# 7. User Rewards and Codes
# =================================================================================
@check_banned
async def earn_points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with sqlite3.connect(DB_FILE) as conn:
        all_channels = conn.execute("SELECT channel_id, channel_link, reward_points, channel_name FROM reward_channels").fetchall()
        claimed_ids = {row[0] for row in conn.execute("SELECT channel_id FROM user_channel_rewards WHERE telegram_user_id = ?", (user_id,))}
    
    if not all_channels:
        await update.message.reply_text(get_text('no_channels_available')); return

    keyboard = []
    for cid, link, points, name in all_channels:
        if cid in claimed_ids:
            button_text = f"✅ {name}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data="dummy")])
        else:
            button_text = f"{name} (+{points} نقطة)"
            keyboard.append([InlineKeyboardButton(button_text, url=link)])
            keyboard.append([InlineKeyboardButton(get_text('verify_join_button'), callback_data=f"verify_r_{cid}_{points}")])
    
    reply_func = update.callback_query.edit_message_text if update.callback_query else update.message.reply_text
    await reply_func(get_text('rewards_header'), reply_markup=InlineKeyboardMarkup(keyboard))

async def verify_reward_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    user_id = query.from_user.id
    
    try:
        _, _, channel_id_str, points_str = query.data.split('_')
        channel_id, points = int(channel_id_str), int(points_str)
    except (ValueError, IndexError):
        await query.answer("خطأ في البيانات.", show_alert=True); return

    try:
        member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        if member.status not in ['member', 'administrator', 'creator']:
            await query.answer(get_text('reward_fail'), show_alert=True); return
    except Exception as e:
        await query.answer(f"خطأ: لا يمكن التحقق. تأكد من أن البوت مشرف في القناة.", show_alert=True); return
    
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        if cursor.execute("SELECT 1 FROM user_channel_rewards WHERE telegram_user_id = ? AND channel_id = ?", (user_id, channel_id)).fetchone():
            await query.answer("لقد حصلت على هذه المكافأة بالفعل.", show_alert=True); return
        
        cursor.execute("UPDATE users SET points = points + ? WHERE telegram_user_id = ?", (points, user_id))
        cursor.execute("INSERT INTO user_channel_rewards (telegram_user_id, channel_id) VALUES (?, ?)", (user_id, channel_id))
    await query.answer(get_text('reward_success').format(points=points), show_alert=True)
    await earn_points_command(update, context)

@check_banned
async def redeem_code_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_text('redeem_prompt'))
    return REDEEM_CODE_INPUT

async def redeem_code_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    code = update.message.text
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        code_data = cursor.execute("SELECT points, max_uses, current_uses FROM redeem_codes WHERE code = ?", (code,)).fetchone()
        
        if not code_data:
            await update.message.reply_text(get_text('redeem_invalid_code')); return ConversationHandler.END
        
        points, max_uses, current_uses = code_data
        if current_uses >= max_uses:
            await update.message.reply_text(get_text('redeem_limit_reached')); return ConversationHandler.END
        
        if cursor.execute("SELECT 1 FROM redeemed_users WHERE code = ? AND telegram_user_id = ?", (code, user_id)).fetchone():
            await update.message.reply_text(get_text('redeem_already_used')); return ConversationHandler.END
            
        cursor.execute("UPDATE users SET points = points + ? WHERE telegram_user_id = ?", (points, user_id))
        cursor.execute("UPDATE redeem_codes SET current_uses = current_uses + 1 WHERE code = ?", (code,))
        cursor.execute("INSERT INTO redeemed_users (code, telegram_user_id) VALUES (?, ?)", (code, user_id))
        new_balance = cursor.execute("SELECT points FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
        await update.message.reply_text(get_text('redeem_success').format(points=points, new_balance=new_balance), parse_mode=ParseMode.HTML)
    return ConversationHandler.END

# =================================================================================
# 8. Callbacks and Conversations
# =================================================================================
async def verify_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    user_id = query.from_user.id

    if await check_membership(user_id, context):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            claimed = cursor.execute("SELECT join_bonus_claimed FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
            if not claimed:
                cursor.execute("UPDATE users SET points = points + ?, join_bonus_claimed = 1 WHERE telegram_user_id = ?", (JOIN_BONUS, user_id))
                conn.commit()
                await query.answer(get_text('join_bonus_awarded').format(bonus=JOIN_BONUS), show_alert=True)
        
        await query.edit_message_text(get_text('force_join_success'))
        await start(update, context, from_callback=True)
    else:
        await query.answer(get_text('force_join_fail'), show_alert=True)

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_text('operation_cancelled'))
    context.user_data.clear()
    return ConversationHandler.END

# =================================================================================
# 9. نقطة انطلاق البوت (Main Entry Point)
# =================================================================================
def main():
    init_db()
    
    if "YOUR_TELEGRAM_BOT_TOKEN" in TOKEN:
        print("FATAL ERROR: Bot token is not set.")
        sys.exit(1)

    app = ApplicationBuilder().token(TOKEN).build()

    # --- FIX for ConversationHandler Warnings ---
    # By setting per_message=True, each button click is handled correctly.
    # allow_reentry=True is good practice for menu-based conversations.
    conv_defaults = {'per_message': True, 'allow_reentry': True}

    # Conversation Handlers
    edit_info_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_panel_callback, pattern='^admin_edit_connection_info$')],
        states={
            EDIT_HOSTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_hostname_received)],
            EDIT_WS_PORTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_ws_ports_received)],
            EDIT_SSL_PORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_ssl_port_received)],
            EDIT_UDPCUSTOM: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_udpcustom_received)],
            EDIT_ADMIN_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_admin_contact_received)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)],
        **conv_defaults
    )
    add_channel_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_channel_start, pattern='^admin_add_channel_start$')],
        states={
            ADD_CHANNEL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_get_name)],
            ADD_CHANNEL_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_get_link)],
            ADD_CHANNEL_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_get_id)],
            ADD_CHANNEL_POINTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_get_points)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)],
        **conv_defaults
    )
    create_code_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(create_code_start, pattern='^admin_create_code_start$')],
        states={
            CREATE_CODE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_code_name)],
            CREATE_CODE_POINTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_code_points)],
            CREATE_CODE_USES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_code_uses)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)],
        **conv_defaults
    )
    ban_user_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(ban_user_start, pattern='^admin_ban_user_start$')],
        states={BAN_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, ban_user_id_received)]},
        fallbacks=[CommandHandler('cancel', cancel_conversation)],
        **conv_defaults
    )
    unban_user_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(unban_user_start, pattern='^admin_unban_user_start$')],
        states={UNBAN_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, unban_user_id_received)]},
        fallbacks=[CommandHandler('cancel', cancel_conversation)],
        **conv_defaults
    )
    redeem_code_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f"^{get_text('redeem_code_button')}$"), redeem_code_start)],
        states={REDEEM_CODE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, redeem_code_received)]},
        fallbacks=[CommandHandler('cancel', cancel_conversation)]
    )

    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))

    # Add conversation handlers
    app.add_handler(add_channel_conv)
    app.add_handler(create_code_conv)
    app.add_handler(ban_user_conv)
    app.add_handler(unban_user_conv)
    app.add_handler(redeem_code_conv)
    app.add_handler(edit_info_conv)

    # Add message handlers for main menu buttons
    app.add_handler(MessageHandler(filters.Regex(f"^{get_text('get_ssh_button')}$"), get_ssh))
    app.add_handler(MessageHandler(filters.Regex(f"^{get_text('my_account_button')}$"), my_account))
    app.add_handler(MessageHandler(filters.Regex(f"^{get_text('balance_button')}$"), balance_command))
    app.add_handler(MessageHandler(filters.Regex(f"^{get_text('daily_button')}$"), daily_command))
    app.add_handler(MessageHandler(filters.Regex(f"^{get_text('earn_points_button')}$"), earn_points_command))
    app.add_handler(MessageHandler(filters.Regex(f"^{get_text('contact_admin_button')}$"), contact_admin_command))

    # Add callback query handlers
    app.add_handler(CallbackQueryHandler(verify_join_callback, pattern='^verify_join$'))
    app.add_handler(CallbackQueryHandler(verify_reward_callback, pattern='^verify_r_'))
    app.add_handler(CallbackQueryHandler(admin_panel_callback, pattern='^admin_'))
    app.add_handler(CallbackQueryHandler(remove_channel_confirm, pattern='^remove_c_'))
    app.add_handler(CallbackQueryHandler(lambda u,c: u.callback_query.answer(), pattern='^dummy$'))

    print("Bot is running with FULL features...")
    app.run_polling()

if __name__ == '__main__':
    main()
