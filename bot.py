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
BOT_TOKEN = 'BOT_TOKEN'
ADMIN_USER_ID = 5344028088 # ⚠️ استبدل هذا بمعرف المستخدم الخاص بك

SCRIPT_PATH = '/usr/local/bin/create_ssh_user.sh'
DB_FILE = 'ssh_bot_users.db'

# --- قيم نظام النقاط ---
COST_PER_ACCOUNT = 4
REFERRAL_BONUS = 4
DAILY_LOGIN_BONUS = 1
INITIAL_POINTS = 2
ACCOUNT_EXPIRY_DAYS = 2

if not BOT_TOKEN:
    print("Fatal Error: BOT_TOKEN environment variable not set.")
    exit()

# حالات معالج المحادثة
REDEEM_CODE = range(1)
CREATE_CODE_NAME, CREATE_CODE_POINTS, CREATE_CODE_USES = range(3)
ADD_CHANNEL_TYPE, ADD_CHANNEL_ID, ADD_CHANNEL_LINK, ADD_CHANNEL_POINTS = range(4)

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
        "earn_points_button": "🎁 كسب النقاط",
        "force_join_prompt": "❗️لاستخدام البوت، يجب عليك الانضمام إلى القنوات الإجبارية التالية:",
        "force_join_verify_button": "✅ تحققت من الانضمام",
        "earn_points_prompt": "✨ انضم إلى هذه القنوات لكسب نقاط إضافية:",
        "earn_points_verify_button": "🔍 تحقق من الانضمام",
        "earn_points_already_joined": "✅ (تم الانضمام)",
        "earn_points_success": "🎉 تهانينا! لقد حصلت على **{points}** نقطة.",
        "no_bonus_channels": "ℹ️ لا توجد قنوات متاحة لكسب النقاط حالياً. تحقق لاحقاً!",
        "admin_settings_header": "⚙️ لوحة تحكم الأدمن",
        "admin_add_channel_prompt_type": "اختر نوع القناة التي تريد إضافتها:",
        "admin_add_channel_type_mandatory": "إجبارية",
        "admin_add_channel_type_bonus": "لكسب النقاط",
        "add_channel_prompt_points": "أرسل عدد النقاط التي سيحصل عليها المستخدم عند الانضمام:",
        # ... باقي النصوص ...
    },
    'en': {
        "welcome": "Welcome!\nUse the buttons below.",
        "get_ssh_button": "💳 Request New Account",
        "my_account_button": "👤 My Account",
        "balance_button": "💰 My Balance",
        "referral_button": "👥 Referral",
        "redeem_button": "🎁 Redeem Code",
        "daily_button": "☀️ Daily Bonus",
        "earn_points_button": "🎁 Earn Points",
        "force_join_prompt": "❗️To use this bot, you must first join the following mandatory channels:",
        "force_join_verify_button": "✅ I Have Joined",
        "earn_points_prompt": "✨ Join these channels to earn extra points:",
        "earn_points_verify_button": "🔍 Verify Join",
        "earn_points_already_joined": "✅ (Joined)",
        "earn_points_success": "🎉 Congratulations! You have earned **{points}** points.",
        "no_bonus_channels": "ℹ️ No channels are available to earn points right now. Check back later!",
        "admin_settings_header": "⚙️ Admin Control Panel",
        "admin_add_channel_prompt_type": "Select the type of channel to add:",
        "admin_add_channel_type_mandatory": "Mandatory",
        "admin_add_channel_type_bonus": "For Earning Points",
        "add_channel_prompt_points": "Send the number of points the user will get for joining:",
        # ... rest of the texts ...
    },
}

# =================================================================================
# 3. إدارة قاعدة البيانات (Database Management)
# =================================================================================
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # ... (other tables) ...
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                chat_id INTEGER PRIMARY KEY,
                chat_link TEXT NOT NULL,
                channel_type TEXT NOT NULL, -- 'mandatory' or 'bonus'
                points INTEGER DEFAULT 0
            )''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_joined_channels (
                user_id INTEGER,
                chat_id INTEGER,
                PRIMARY KEY (user_id, chat_id)
            )''')
        # ... (other tables) ...
        conn.commit()

def get_channels(channel_type):
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("SELECT chat_id, chat_link, points FROM channels WHERE channel_type = ?", (channel_type,)).fetchall()

def add_channel(chat_id, chat_link, channel_type, points=0):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT OR REPLACE INTO channels (chat_id, chat_link, channel_type, points) VALUES (?, ?, ?, ?)", 
                     (chat_id, chat_link, channel_type, points))
        conn.commit()

def delete_channel(chat_id):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("DELETE FROM channels WHERE chat_id = ?", (chat_id,))
        conn.commit()

def get_user_joined_bonus_channels(user_id):
    with sqlite3.connect(DB_FILE) as conn:
        rows = conn.execute("SELECT chat_id FROM user_joined_channels WHERE user_id = ?", (user_id,)).fetchall()
        return {row[0] for row in rows}

def mark_user_joined_bonus_channel(user_id, chat_id):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT OR IGNORE INTO user_joined_channels (user_id, chat_id) VALUES (?, ?)", (user_id, chat_id))
        conn.commit()
# ... (rest of db functions) ...

# =================================================================================
# 4. دوال مساعدة (Helper Functions)
# =================================================================================
async def check_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE, specific_chat_id=None) -> bool:
    if specific_chat_id:
        channels_to_check = [(specific_chat_id,)]
    else: # Check only mandatory channels
        if not is_feature_enabled('force_join'):
            return True
        channels_to_check = get_channels('mandatory')
        if not channels_to_check:
            return True

    try:
        for chat_id, *_ in channels_to_check:
            member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        return True
    except Exception as e:
        print(f"Error during membership check for user {user_id}: {e}")
        return False
# ... (rest of helper functions) ...

# =================================================================================
# 5. أوامر البوت (Bot Commands & Handlers)
# =================================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False):
    # ... (user creation and referral logic) ...
    lang_code = get_user_language(update.effective_user.id)
    
    if is_feature_enabled('force_join'):
        is_member = await check_membership(update.effective_user.id, context)
        if not is_member:
            mandatory_channels = get_channels('mandatory')
            keyboard = []
            for _, chat_link, _ in mandatory_channels:
                keyboard.append([InlineKeyboardButton(f"📢 {chat_link.split('/')[-1]}", url=chat_link)])
            keyboard.append([InlineKeyboardButton(get_text('force_join_verify_button', lang_code), callback_data='verify_join')])
            await update.effective_message.reply_text(get_text('force_join_prompt', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))
            return
    
    # Show main menu
    keyboard_layout = [
        [KeyboardButton(get_text('get_ssh_button', lang_code))],
        [KeyboardButton(get_text('balance_button', lang_code)), KeyboardButton(get_text('my_account_button', lang_code))],
        [KeyboardButton(get_text('daily_button', lang_code)), KeyboardButton(get_text('referral_button', lang_code)), KeyboardButton(get_text('earn_points_button', lang_code))]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard_layout, resize_keyboard=True)
    await update.effective_message.reply_text(get_text('welcome', lang_code), reply_markup=reply_markup)

async def earn_points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_code = get_user_language(user_id)
    
    bonus_channels = get_channels('bonus')
    user_joined_channels = get_user_joined_bonus_channels(user_id)
    
    available_channels = [ch for ch in bonus_channels if ch[0] not in user_joined_channels]

    if not available_channels:
        await update.message.reply_text(get_text('no_bonus_channels', lang_code))
        return

    keyboard = []
    for chat_id, chat_link, points in available_channels:
        keyboard.append([
            InlineKeyboardButton(f"🔗 {chat_link.split('/')[-1]} (+{points} pts)", url=chat_link),
            InlineKeyboardButton(get_text('earn_points_verify_button', lang_code), callback_data=f"earn_{chat_id}")
        ])
    
    await update.message.reply_text(get_text('earn_points_prompt', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))

async def earn_points_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    lang_code = get_user_language(user_id)
    chat_id_to_check = int(query.data.split('_')[1])
    
    is_member = await check_membership(user_id, context, specific_chat_id=chat_id_to_check)
    
    if is_member:
        bonus_channels = get_channels('bonus')
        points_to_add = 0
        for chat_id, _, points in bonus_channels:
            if chat_id == chat_id_to_check:
                points_to_add = points
                break
        
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("UPDATE users SET points = points + ? WHERE telegram_user_id = ?", (points_to_add, user_id))
        mark_user_joined_bonus_channel(user_id, chat_id_to_check)
        
        await query.message.reply_text(get_text('earn_points_success', lang_code, points=points_to_add))
        
        # Refresh the list of channels
        await earn_points_command(query, context)
        await query.message.delete()
    else:
        await query.answer(get_text('force_join_fail', lang_code), show_alert=True)

# --- Admin Commands ---
async def add_channel_command(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    user_id = update_or_query.from_user.id
    if not is_admin(user_id): return
    lang_code = get_user_language(user_id)
    
    keyboard = [
        [InlineKeyboardButton(get_text('admin_add_channel_type_mandatory', lang_code), callback_data="addtype_mandatory")],
        [InlineKeyboardButton(get_text('admin_add_channel_type_bonus', lang_code), callback_data="addtype_bonus")]
    ]
    await update_or_query.message.reply_text(get_text('admin_add_channel_prompt_type', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_CHANNEL_TYPE

async def receive_channel_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['new_channel_type'] = query.data.split('_')[1]
    lang_code = get_user_language(query.from_user.id)
    await query.message.edit_text(get_text('add_channel_prompt_id', lang_code))
    return ADD_CHANNEL_ID

async def receive_channel_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (logic remains the same, but transitions to get points if type is 'bonus')
    chat_id = int(update.message.text)
    context.user_data['new_channel_id'] = chat_id
    if context.user_data['new_channel_type'] == 'bonus':
        await update.message.reply_text(get_text('add_channel_prompt_points', lang_code))
        return ADD_CHANNEL_POINTS
    else:
        await update.message.reply_text(get_text('add_channel_prompt_link', lang_code))
        return ADD_CHANNEL_LINK

async def receive_channel_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_channel_points'] = int(update.message.text)
    lang_code = get_user_language(update.effective_user.id)
    await update.message.reply_text(get_text('add_channel_prompt_link', lang_code))
    return ADD_CHANNEL_LINK

async def receive_channel_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = get_user_language(update.effective_user.id)
    chat_link = update.message.text
    chat_id = context.user_data['new_channel_id']
    channel_type = context.user_data['new_channel_type']
    points = context.user_data.get('new_channel_points', 0)
    
    add_channel(chat_id, chat_link, channel_type, points)
    await update.message.reply_text(get_text('add_channel_success', lang_code))
    return ConversationHandler.END

# ... (rest of the code)

# =================================================================================
# 6. نقطة انطلاق البوت (Main Entry Point)
# =================================================================================
def main():
    """Runs the bot."""
    print("Initializing database...")
    init_db()

    print("Building bot application...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    add_channel_handler = ConversationHandler(
        entry_points=[CommandHandler("addchannel", add_channel_command)],
        states={
            ADD_CHANNEL_TYPE: [CallbackQueryHandler(receive_channel_type, pattern='^addtype_')],
            ADD_CHANNEL_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_channel_id)],
            ADD_CHANNEL_POINTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_channel_points)],
            ADD_CHANNEL_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_channel_link)],
        },
        fallbacks=[],
    )
    
    # User Handlers
    app.add_handler(CommandHandler("earnpoints", earn_points_command))
    app.add_handler(CallbackQueryHandler(earn_points_callback, pattern='^earn_'))
    # ... (other handlers)

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
