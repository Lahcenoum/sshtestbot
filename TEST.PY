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
(ADD_CHANNEL_NAME, ADD_CHANNEL_LINK, ADD_CHANNEL_ID, ADD_CHANNEL_POINTS) = range(4)


# =================================================================================
# 2. دعم اللغات (Localization)
# =================================================================================
TEXTS = {
    'ar': {
        "welcome": "أهلاً بك!\nاستخدم الأزرار أدناه.",
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
        "no_channels_available": "ℹ️ لا توجد قنوات متاحة للمكافآت حاليًا. تحقق مرة أخرى لاحقًا.",
        "admin_panel_header": "⚙️ لوحة تحكم الأدمن",
        "admin_manage_channels_button": " إدارة قنوات المكافآت",
        "admin_user_count_button": "👤 عدد المستخدمين",
        "admin_user_count_info": "📊 العدد الإجمالي للمستخدمين: {count}",
        "admin_add_channel_button": "➕ إضافة قناة",
        "admin_remove_channel_button": "➖ إزالة قناة",
        "admin_return_button": "⬅️ عودة",
        "admin_add_channel_name_prompt": "أرسل اسم القناة (مثال: قناتي الإخبارية):",
        "admin_add_channel_link_prompt": "الآن أرسل رابط القناة الكامل (https://t.me/....):",
        "admin_add_channel_id_prompt": "أرسل معرف القناة الرقمي (يجب أن يبدأ بـ -100):",
        "admin_add_channel_points_prompt": "أخيراً، أرسل عدد نقاط المكافأة لهذا الانضمام:",
        "admin_channel_added_success": "✅ تم إضافة القناة بنجاح.",
        "admin_remove_channel_prompt": "اختر القناة التي تريد إزالتها:",
        "admin_channel_removed_success": "🗑️ تم إزالة القناة بنجاح.",
        "invalid_input": "❌ إدخال غير صالح، يرجى المحاولة مرة أخرى.",
        "operation_cancelled": "✅ تم إلغاء العملية.",
        "creation_success": "✅ تم إنشاء حسابك بنجاح!\n\n**البيانات:**\n```\n{details}\n```\n\n⚠️ **ملاحظة**: سيتم حذفه تلقائيًا بعد **{days} أيام**.",
        "account_details": "🏷️ **اسم المستخدم:** `{username}`\n🗓️ **تاريخ انتهاء الصلاحية:** `{expiry}`",
        # ... (بقية النصوص من النسخة السابقة)
    },
    # 'en': { ... }
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
        conn.commit()

def get_or_create_user(user_id, referred_by=None):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_user_id = ?", (user_id,))
        user_data = cursor.fetchone()
        if not user_data:
            ref_code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            cursor.execute("INSERT INTO users (telegram_user_id, points, referral_code, referred_by) VALUES (?, ?, ?, ?)", (user_id, INITIAL_POINTS, ref_code, referred_by))
            if referred_by:
                cursor.execute("UPDATE users SET points = points + ? WHERE telegram_user_id = ?", (REFERRAL_BONUS, referred_by))
            conn.commit()
        return cursor.execute("SELECT * FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()

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

# =================================================================================
# 5. أوامر البوت (Bot Commands & Handlers)
# =================================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_or_create_user(user.id)
    lang_code = 'ar'
    keyboard_layout = [
        [KeyboardButton(get_text('get_ssh_button', lang_code))],
        [KeyboardButton(get_text('balance_button', lang_code)), KeyboardButton(get_text('my_account_button', lang_code))],
        [KeyboardButton(get_text('daily_button', lang_code)), KeyboardButton(get_text('referral_button', lang_code))],
        [KeyboardButton(get_text('rewards_button', lang_code)), KeyboardButton(get_text('redeem_button', lang_code))],
        [KeyboardButton(get_text('contact_admin_button', lang_code))]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard_layout, resize_keyboard=True)
    await update.message.reply_text(get_text('welcome', lang_code), reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    lang_code = 'ar'
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

async def get_ssh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_code = 'ar'
    with sqlite3.connect(DB_FILE) as conn:
        points = conn.execute("SELECT points FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
    if points < COST_PER_ACCOUNT:
        await update.message.reply_text(f"⚠️ ليس لديك نقاط كافية. التكلفة هي **{COST_PER_ACCOUNT}** نقطة.", parse_mode=ParseMode.MARKDOWN)
        return

    username = f"user{user_id}"
    password = generate_password()
    command_to_run = [SCRIPT_PATH, username, password, str(ACCOUNT_EXPIRY_DAYS)]
    
    try:
        process = subprocess.run(command_to_run, capture_output=True, text=True, timeout=30, check=True)
        result = process.stdout
        with sqlite3.connect(DB_FILE) as conn:
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
        await update.message.reply_text("❌ حدث خطأ أثناء إنشاء الحساب. يرجى التواصل مع الأدمن.")

async def my_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with sqlite3.connect(DB_FILE) as conn:
        accounts = conn.execute("SELECT ssh_username FROM ssh_accounts WHERE telegram_user_id = ?", (user_id,)).fetchall()
    
    if not accounts:
        await update.message.reply_text("ℹ️ لم يتم العثور على أي حسابات مرتبطة بك.")
        return

    response = ["👤 حساباتك النشطة:"]
    for (username,) in accounts:
        try:
            expiry_output = subprocess.check_output(['/usr/bin/chage', '-l', username], text=True)
            expiry = next((line.split(':', 1)[1].strip() for line in expiry_output.split('\n') if "Account expires" in line), "Never")
            safe_username = escape_markdown_v2(username)
            safe_expiry = escape_markdown_v2(expiry)
            response.append(get_text('account_details', 'ar').format(username=safe_username, expiry=safe_expiry))
        except Exception as e:
            print(f"Could not get expiry for {username}: {e}")
    await update.message.reply_text("\n\n".join(response), parse_mode=ParseMode.MARKDOWN_V2)

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with sqlite3.connect(DB_FILE) as conn:
        points = conn.execute("SELECT points FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
    await update.message.reply_text(f"💰 رصيدك الحالي هو: **{points}** نقطة.", parse_mode=ParseMode.MARKDOWN)

async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with sqlite3.connect(DB_FILE) as conn:
        ref_code = conn.execute("SELECT referral_code FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={ref_code}"
    await update.message.reply_text(f"👥 ادعُ أصدقاءك واكسب **{REFERRAL_BONUS}** نقطة لكل صديق جديد!\n\n🔗 رابط الإحالة الخاص بك:\n`{link}`", parse_mode=ParseMode.MARKDOWN)

async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        today = date.today()
        last_claim_str = cursor.execute("SELECT last_daily_claim FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
        if last_claim_str and date.fromisoformat(last_claim_str) == today:
            await update.message.reply_text("ℹ️ لقد حصلت بالفعل على مكافأتك اليومية. تعال غدًا!")
            return
        cursor.execute("UPDATE users SET points = points + ?, last_daily_claim = ? WHERE telegram_user_id = ?", (DAILY_LOGIN_BONUS, today.isoformat(), user_id))
        conn.commit()
        new_balance = cursor.execute("SELECT points FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
        await update.message.reply_text(f"🎉 لقد حصلت على مكافأتك اليومية: **{DAILY_LOGIN_BONUS}** نقطة! رصيدك الآن هو **{new_balance}**.")

async def redeem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This should be part of a ConversationHandler, but for simplicity, we'll keep it basic.
    await update.message.reply_text("هذه الميزة قيد التطوير.")

async def contact_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_text('contact_admin_info', 'ar').format(contact_info=ADMIN_CONTACT_INFO))

# --- Admin Panel ---
async def admin_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID: return
    keyboard = [
        [InlineKeyboardButton(get_text('admin_manage_channels_button', 'ar'), callback_data='admin_manage_channels')],
        [InlineKeyboardButton(get_text('admin_user_count_button', 'ar'), callback_data='admin_user_count')]
    ]
    await update.message.reply_text(get_text('admin_panel_header', 'ar'), reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_USER_ID: return

    data = query.data
    lang_code = 'ar'

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
        keyboard = [
            [InlineKeyboardButton(get_text('admin_manage_channels_button', lang_code), callback_data='admin_manage_channels')],
            [InlineKeyboardButton(get_text('admin_user_count_button', lang_code), callback_data='admin_user_count')]
        ]
        await query.edit_message_text(get_text('admin_panel_header', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))

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
    with sqlite3.connect(DB_FILE) as conn:
        all_channels = conn.execute("SELECT channel_id, channel_link, reward_points, channel_name FROM reward_channels").fetchall()
        claimed_ids = {row[0] for row in conn.execute("SELECT channel_id FROM user_channel_rewards WHERE telegram_user_id = ?", (user_id,))}
    if not all_channels:
        await update.message.reply_text(get_text('no_channels_available', 'ar'))
        return
    keyboard = []
    for cid, link, points, name in all_channels:
        if cid in claimed_ids:
            button = InlineKeyboardButton(f"✅ {name}", callback_data="dummy")
        else:
            button = InlineKeyboardButton(f"{name} (+{points} نقطة)", url=link)
        keyboard.append([button])
        if cid not in claimed_ids:
             keyboard.append([InlineKeyboardButton(get_text('verify_join_button', 'ar'), callback_data=f"verify_r_{cid}")])
    await update.message.reply_text(get_text('rewards_header', 'ar'), reply_markup=InlineKeyboardMarkup(keyboard))

async def verify_reward_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    channel_id = int(query.data.split('_')[-1])
    try:
        member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        if member.status not in ['member', 'administrator', 'creator']:
            await query.answer(get_text('reward_fail', 'ar'), show_alert=True)
            return
    except Exception as e:
        await query.answer(f"خطأ: لا يمكن التحقق. تأكد من أن البوت مشرف في القناة. {e}", show_alert=True)
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
    await query.answer(get_text('reward_success', 'ar').format(points=points), show_alert=True)
    await rewards_command(query, context) # Refresh the message

# =================================================================================
# 6. نقطة انطلاق البوت (Main Entry Point)
# =================================================================================
def main():
    print("Initializing database...")
    init_db()
    print("Building bot application...")
    app = ApplicationBuilder().token(TOKEN).build()

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

    app.add_handler(CommandHandler("admin", admin_panel_command))
    app.add_handler(CallbackQueryHandler(admin_panel_callback, pattern='^admin_'))
    app.add_handler(add_channel_conv)
    app.add_handler(CallbackQueryHandler(remove_channel_start, pattern='^admin_remove_channel_start$'))
    app.add_handler(CallbackQueryHandler(remove_channel_confirm, pattern='^remove_c_'))

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(verify_reward_callback, pattern='^verify_r_'))
    app.add_handler(CallbackQueryHandler(lambda u,c: u.callback_query.answer(), pattern='^dummy$'))

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
