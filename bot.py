import sys
import subprocess
import random
import string
import sqlite3
import re
import traceback
import html
import json
import uuid
import requests
import logging # تم إضافة مكتبة التسجيل
from datetime import datetime, date, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest

# =================================================================================
# 1. الإعدادات الرئيسية (Configuration)
# =================================================================================
# ⚠️ قم بتعديل هذا
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN" 
ADMIN_USER_ID = 5344028088
ADMIN_CONTACT_INFO = "@YourAdminUsername"
DB_FILE = 'ssh_bot_users.db'

# --- إعدادات SSH ---
SSH_SCRIPT_PATH = '/usr/local/bin/create_ssh_user.sh'
SSH_ACCOUNT_EXPIRY_DAYS = 2

# --- قيم نظام النقاط ---
COST_PER_ACCOUNT = 2
DAILY_LOGIN_BONUS = 1
INITIAL_POINTS = 2
JOIN_BONUS = 0
REFERRAL_BONUS = 2
AD_REWARD_POINTS = 1

# --- إعدادات الإعلانات (SSP/RichAds) ---
SSP_ENDPOINT = "http://15068.xml.adx1.com/telegram-mb"
SSP_PUBLISHER_ID = "792361"
SSP_WIDGET_ID = "351352"

# --- إعدادات القنوات ---
REQUIRED_CHANNEL_ID = -1001932589296
REQUIRED_GROUP_ID = -1002218671728
CHANNEL_LINK = "https://t.me/CLOUDVIP"
GROUP_LINK = "https://t.me/dgtliA"

# Conversation handler states
(ADD_CHANNEL_NAME, ADD_CHANNEL_LINK, ADD_CHANNEL_ID, ADD_CHANNEL_POINTS) = range(4)
(CREATE_CODE_NAME, CREATE_CODE_POINTS, CREATE_CODE_USES) = range(4, 7)
(REDEEM_CODE_INPUT,) = range(7, 8)
(EDIT_HOSTNAME, EDIT_WS_PORTS, EDIT_SSL_PORT, EDIT_UDPCUSTOM, EDIT_ADMIN_CONTACT, EDIT_PAYLOAD) = range(8, 14)

# =================================================================================
# 2. دعم اللغات (Localization)
# =================================================================================
TEXTS = {
    'ar': {
        "welcome": "أهلاً بك في بوت الخدمات!\n\nاستخدم الأزرار أدناه لطلب حساب SSH.",
        "get_account_button": "💳 طلب حساب جديد",
        "my_account_button": "👤 حساباتي",
        "balance_button": "💰 رصيدي",
        "earn_points_button": "🎁 كسب النقاط",
        "redeem_code_button": "🎁 استرداد كود",
        "daily_button": "☀️ مكافأة يومية",
        "referral_button": "👥 دعوة صديق",
        "contact_admin_button": "👨‍💻 تواصل مع الأدمن",
        "choose_account_type": "اختر نوع الحساب الذي تريده:",
        "ssh_account_button": "🌐 حساب SSH",
        "v2ray_account_button": "🚀 حساب V2Ray (قيد التطوير)",
        "udpcustom_account_button": "⚡️ حساب UDP Custom (قيد التطوير)",
        "under_development": "🚧 هذه الميزة قيد التطوير حاليًا.",
        "contact_admin_info": "للتواصل مع الأدمن، يرجى مراسلة: {contact_info}",
        "not_enough_points": "⚠️ ليس لديك نقاط كافية. التكلفة هي <b>{cost}</b> نقطة.",
        "creation_error": "❌ حدث خطأ أثناء إنشاء الحساب. قد يكون لديك حساب بالفعل أو خطأ آخر.",
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
        "your_accounts": "<b>👤 حسابات SSH الخاصة بك:</b>",
        "account_details_full": "🏷️ <b>اسم المستخدم:</b> <code>{username}</code>\n🔑 <b>كلمة المرور:</b> <code>{password}</code>\n🗓️ <b>تاريخ انتهاء الصلاحية:</b> <code>{expiry}</code>\n\n<b>Hostname:</b> <code>{hostname}</code>\n<b>Websocket Ports:</b> <code>{ws_ports}</code>\n<b>SSL Port:</b> <code>{ssl_port}</code>\n<b>UDPCUSTOM Port:</b> <code>{udpcustom_port}</code>\n\n<b>Payload:</b>\n<pre><code>{payload}</code></pre>",
        "rewards_header": "اختر طريقة لكسب النقاط:",
        "verify_join_button": "✅ تحقق من الانضمام",
        "reward_success": "🎉 رائع! لقد حصلت على {points} نقطة.",
        "reward_fail": "❌ لم تنضم بعد. حاول مرة أخرى بعد الانضمام.",
        "no_channels_available": "ℹ️ لا توجد قنوات متاحة للمكافآت حاليًا.",
        "redeem_prompt": "يرجى إرسال الكود الذي تريد استرداده.",
        "redeem_success": "🎉 تهانينا! لقد حصلت على <b>{points}</b> نقطة. رصيدك الآن هو <b>{new_balance}</b>.",
        "redeem_invalid_code": "❌ هذا الكود غير صالح أو غير موجود.",
        "redeem_limit_reached": "❌ لقد وصل هذا الكود إلى الحد الأقصى من الاستخدام.",
        "redeem_already_used": "❌ لقد قمت بالفعل باستخدام هذا الكود.",
        "referral_info": "👥 <b>نظام الإحالة</b>\n\nادعُ أصدقاءك للانضمام إلى البوت باستخدام رابط الإحالة الخاص بك، واحصل على <b>{bonus}</b> نقطة عن كل صديق ينضم!\n\n🔗 <b>رابطك الخاص:</b>\n<code>{link}</code>",
        "referral_bonus_notification": "🎉 لقد حصلت على <b>{bonus}</b> نقطة من دعوة صديق جديد!",
        "admin_panel_header": "⚙️ لوحة تحكم الأدمن",
        "admin_return_button": "⬅️ عودة",
        "admin_manage_rewards_button": "📢 إدارة قنوات الربح",
        "admin_manage_codes_button": "🎁 إدارة أكواد الهدايا",
        "admin_user_stats_button": "📊 إحصائيات المستخدمين",
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
        "admin_edit_hostname_prompt": "أرسل الـ Hostname الجديد:",
        "admin_edit_ws_ports_prompt": "أرسل بورتات Websocket الجديدة (مثال: 80, 8880):",
        "admin_edit_ssl_port_prompt": "أرسل بورت SSL الجديد:",
        "admin_edit_udpcustom_prompt": "أرسل بورت UDPCUSTOM الجديد:",
        "admin_edit_contact_prompt": "أرسل معلومات التواصل الجديدة (مثال: @username):",
        "admin_edit_payload_prompt": "أخيراً، أرسل الـ Payload الجديد:",
        "admin_info_updated_success": "✅ تم تحديث معلومات الاتصال بنجاح.",
        "user_stats_info": "<b>📊 إحصائيات المستخدمين:</b>\n\n- <b>إجمالي المستخدمين:</b> {total_users}\n- <b>النشطون اليوم:</b> {active_today}\n- <b>النشطون أمس:</b> {active_yesterday}\n- <b>المستخدمون الجدد اليوم:</b> {new_today}",
        "choose_language": "اختر لغتك المفضلة:",
        "language_set": "✅ تم تعيين اللغة إلى: {lang_name}",
        "invalid_input": "❌ إدخال غير صالح، يرجى المحاولة مرة أخرى.",
        "operation_cancelled": "✅ تم إلغاء العملية.",
        "creating_account": "جاري إنشاء الحساب...",
        "points": "نقاط",
        "watch_ad_button": "📺 شاهد إعلاناً (+{points} نقطة)",
        "watch_ad_info": "🎁 مكافأة الإعلان اليومية\n\nيمكنك مشاهدة إعلان واحد كل 24 ساعة وكسب <b>{points}</b> نقطة.\n\nاضغط على الزر أدناه لمشاهدة الإعلان والمطالبة بنقاطك.",
        "ad_claimed_already": "⏱️ لقد شاهدت الإعلان اليوم. يمكنك المحاولة مرة أخرى بعد: {time_left}.",
        "ad_server_error": "❌ خطأ في الإعلان. لم نتمكن من جلب إعلان حالياً. حاول مجدداً.",
        "ad_prompt_after_view": "⚠️ يجب عليك الضغط على زر 'Go!' في الرسالة السابقة، ثم العودة والضغط على الزر أدناه لتأكيد المشاهدة والحصول على النقاط.",
        "ad_success": "🎉 رائع! لقد حصلت على <b>{points}</b> نقطة مقابل مشاهدة الإعلان.",
        "ad_already_pending": "❌ لقد طالبت بالفعل بمشاهدة إعلان. يرجى الضغط على زر 'تحققت من الإعلان' في الرسالة السابقة.",
        "verify_ad_button": "✅ تحققت من الإعلان"
    },
    'en': {
        "welcome": "Welcome to the Services Bot!\n\nUse the buttons below to request an SSH account.",
        "get_account_button": "💳 Request New Account",
        "my_account_button": "👤 My Accounts",
        "balance_button": "💰 My Balance",
        "earn_points_button": "🎁 Earn Points",
        "redeem_code_button": "🎁 Redeem Code",
        "daily_button": "☀️ Daily Bonus",
        "referral_button": "👥 Refer a Friend",
        "contact_admin_button": "👨‍💻 Contact Admin",
        "choose_account_type": "Choose the type of account you want:",
        "ssh_account_button": "🌐 SSH Account",
        "v2ray_account_button": "🚀 V2Ray Account (Under Development)",
        "udpcustom_account_button": "⚡️ UDP Custom Account (Under Development)",
        "under_development": "🚧 This feature is currently under development.",
        "contact_admin_info": "To contact the admin, please message: {contact_info}",
        "not_enough_points": "⚠️ You don't have enough points. The cost is <b>{cost}</b> points.",
        "creation_error": "❌ An error occurred while creating the account. You might already have an account or another error occurred.",
        "force_join_prompt": "❗️To use the bot, you must first join our channel and group.\n\nAfter joining, press the '✅ I have joined' button.",
        "force_join_channel_button": "📢 Join Channel",
        "force_join_group_button": "👥 Join Group",
        "force_join_verify_button": "✅ I have joined",
        "force_join_success": "✅ Thank you for joining! You can now use the bot.",
        "force_join_fail": "❌ Your membership could not be verified. Please make sure you have joined both and try again.",
        "join_bonus_awarded": "🎉 Join bonus! You have received {bonus} points.",
        "balance_info": "💰 Your current balance is: <b>{points}</b> points.",
        "daily_bonus_claimed": "🎉 You have claimed your daily bonus: <b>{bonus}</b> points! Your new balance is <b>{new_balance}</b>.",
        "daily_bonus_already_claimed": "ℹ️ You have already claimed your daily bonus. Come back tomorrow!",
        "no_accounts_found": "ℹ️ No active accounts found for you.",
        "your_accounts": "<b>👤 Your SSH Accounts:</b>",
        "account_details_full": "🏷️ <b>Username:</b> <code>{username}</code>\n🔑 <b>Password:</b> <code>{password}</code>\n🗓️ <b>Expiry Date:</b> <code>{expiry}</code>\n\n<b>Hostname:</b> <code>{hostname}</code>\n<b>Websocket Ports:</b> <code>{ws_ports}</code>\n<b>SSL Port:</b> <code>{ssl_port}</code>\n<b>UDPCUSTOM Port:</b> <code>{udpcustom_port}</code>\n\n<b>Payload:</b>\n<pre><code>{payload}</code></pre>",
        "rewards_header": "Choose a way to earn points:",
        "verify_join_button": "✅ Verify Join",
        "reward_success": "🎉 Great! You have earned {points} points.",
        "reward_fail": "❌ You haven't joined yet. Try again after joining.",
        "no_channels_available": "ℹ️ No reward channels are available at the moment.",
        "redeem_prompt": "Please send the code you want to redeem.",
        "redeem_success": "🎉 Congratulations! You have received <b>{points}</b> points. Your new balance is <b>{new_balance}</b>.",
        "redeem_invalid_code": "❌ This code is invalid or does not exist.",
        "redeem_limit_reached": "❌ This code has reached its maximum usage limit.",
        "redeem_already_used": "❌ You have already used this code.",
        "referral_info": "👥 <b>Referral System</b>\n\nInvite your friends to join the bot using your referral link and get <b>{bonus}</b> points for each friend who joins!\n\n🔗 <b>Your Link:</b>\n<code>{link}</code>",
        "referral_bonus_notification": "🎉 You have received <b>{bonus}</b> points from a new referral!",
        "admin_panel_header": "⚙️ Admin Panel",
        "admin_return_button": "⬅️ Back",
        "admin_manage_rewards_button": "📢 Manage Reward Channels",
        "admin_manage_codes_button": "🎁 Manage Gift Codes",
        "admin_user_stats_button": "📊 User Statistics",
        "admin_edit_connection_info_button": "⚙️ Edit Connection Info",
        "admin_add_channel_button": "➕ Add Channel/Group",
        "admin_remove_channel_button": "➖ Remove Channel/Group",
        "admin_add_channel_name_prompt": "Send the channel name:",
        "admin_add_channel_link_prompt": "Now send the full channel link:",
        "admin_add_channel_id_prompt": "Send the numeric channel ID (starts with -100):",
        "admin_add_channel_points_prompt": "Finally, send the number of reward points:",
        "admin_channel_added_success": "✅ Channel added successfully.",
        "admin_remove_channel_prompt": "Choose the channel you want to remove:",
        "admin_channel_removed_success": "🗑️ Channel removed successfully.",
        "admin_create_code_button": "➕ Create New Code",
        "admin_create_code_prompt_name": "Send the new code name (e.g., WELCOME2025):",
        "admin_create_code_prompt_points": "Now send the number of points this code grants:",
        "admin_create_code_prompt_uses": "Finally, send the number of users who can use this code:",
        "admin_code_created": "✅ Code <code>{code}</code> created successfully. It grants <b>{points}</b> points and is available for <b>{uses}</b> users.",
        "admin_edit_hostname_prompt": "Send the new Hostname:",
        "admin_edit_ws_ports_prompt": "Send the new Websocket ports (e.g., 80, 8880):",
        "admin_edit_ssl_port_prompt": "Send the new SSL port:",
        "admin_edit_udpcustom_prompt": "Send the new UDPCUSTOM port:",
        "admin_edit_contact_prompt": "Send the new contact info (e.g., @username):",
        "admin_edit_payload_prompt": "Finally, send the new Payload:",
        "admin_info_updated_success": "✅ Connection info updated successfully.",
        "user_stats_info": "<b>📊 User Statistics:</b>\n\n- <b>Total Users:</b> {total_users}\n- <b>Active Today:</b> {active_today}\n- <b>Active Yesterday:</b> {active_yesterday}\n- <b>New Users Today:</b> {new_today}",
        "choose_language": "Choose your preferred language:",
        "language_set": "✅ Language set to: {lang_name}",
        "invalid_input": "❌ Invalid input, please try again.",
        "operation_cancelled": "✅ Operation cancelled.",
        "creating_account": "Creating account...",
        "points": "Points",
        "watch_ad_button": "📺 Watch Ad (+{points} Points)",
        "watch_ad_info": "🎁 Daily Ad Reward\n\nYou can watch one ad every 24 hours and earn <b>{points}</b> points.\n\nClick the button below to view the ad and claim your points.",
        "ad_claimed_already": "⏱️ You have already claimed the ad reward today. Try again after: {time_left}.",
        "ad_server_error": "❌ Ad Error. We could not fetch an ad currently. Please try again.",
        "ad_prompt_after_view": "⚠️ You must click the 'Go!' button in the previous message, then return and click the button below to confirm viewing and get the points.",
        "ad_success": "🎉 Awesome! You received <b>{points}</b> points for watching the ad.",
        "ad_already_pending": "❌ You have already claimed an ad viewing reward. Please click the 'Verify Ad' button in the previous message.",
        "verify_ad_button": "✅ Verify Ad"
    }
}

def get_text(key, lang_code='ar'):
    if lang_code not in TEXTS:
        lang_code = 'ar'
    return TEXTS[lang_code].get(key, TEXTS['ar'].get(key, key))

# =================================================================================
# 3. إدارة قاعدة البيانات (Database Management)
# =================================================================================
def init_db():
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('CREATE TABLE IF NOT EXISTS users (telegram_user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 0, last_daily_claim DATE, join_bonus_claimed INTEGER DEFAULT 0, language_code TEXT DEFAULT "ar", created_date DATE, referrer_id INTEGER, ad_claim_pending INTEGER DEFAULT 0)')
            cursor.execute('CREATE TABLE IF NOT EXISTS ssh_accounts (id INTEGER PRIMARY KEY, telegram_user_id INTEGER NOT NULL, ssh_username TEXT NOT NULL, ssh_password TEXT NOT NULL, created_at TIMESTAMP NOT NULL)')
            cursor.execute('CREATE TABLE IF NOT EXISTS reward_channels (channel_id INTEGER PRIMARY KEY, channel_link TEXT NOT NULL, reward_points INTEGER NOT NULL, channel_name TEXT NOT NULL)')
            cursor.execute('CREATE TABLE IF NOT EXISTS user_channel_rewards (telegram_user_id INTEGER, channel_id INTEGER, PRIMARY KEY (telegram_user_id, channel_id))')
            cursor.execute('CREATE TABLE IF NOT EXISTS redeem_codes (code TEXT PRIMARY KEY, points INTEGER, max_uses INTEGER, current_uses INTEGER DEFAULT 0)')
            cursor.execute('CREATE TABLE IF NOT EXISTS redeemed_users (code TEXT, telegram_user_id INTEGER, PRIMARY KEY (code, telegram_user_id))')
            cursor.execute('CREATE TABLE IF NOT EXISTS daily_activity (user_id INTEGER PRIMARY KEY, last_seen_date DATE NOT NULL)')
            cursor.execute('CREATE TABLE IF NOT EXISTS connection_settings (key TEXT PRIMARY KEY, value TEXT)')
            cursor.execute('CREATE TABLE IF NOT EXISTS ad_claims (telegram_user_id INTEGER PRIMARY KEY, last_ad_claim TIMESTAMP)')
            
            default_settings = {
                "hostname": "your.hostname.com", "ws_ports": "80, 8880, 8888, 2053",
                "ssl_port": "443", "udpcustom_port": "7300", "admin_contact": ADMIN_CONTACT_INFO,
                "payload": "your.default.payload"
            }
            for key, value in default_settings.items():
                cursor.execute("INSERT OR IGNORE INTO connection_settings (key, value) VALUES (?, ?)", (key, value))
            conn.commit()
        logging.info("Database initialization successful.")
    except Exception as e:
        logging.error(f"FATAL ERROR during database initialization: {e}")
        # إذا فشلت تهيئة القاعدة، لا يمكن تشغيل البوت
        sys.exit(1)


async def get_or_create_user(user_id, lang_code='ar', referrer_id=None, context: ContextTypes.DEFAULT_TYPE = None):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            is_new_user = not cursor.execute("SELECT 1 FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()
            if is_new_user:
                today = date.today().isoformat()
                cursor.execute("INSERT INTO users (telegram_user_id, points, language_code, created_date, referrer_id) VALUES (?, ?, ?, ?, ?)", (user_id, INITIAL_POINTS, lang_code, today, referrer_id))
                conn.commit()
                logging.info(f"New user {user_id} created.")
                if referrer_id and context:
                    try:
                        cursor.execute("UPDATE users SET points = points + ? WHERE telegram_user_id = ?", (REFERRAL_BONUS, referrer_id))
                        conn.commit()
                        referrer_lang = get_user_lang(referrer_id)
                        await context.bot.send_message(
                            chat_id=referrer_id,
                            text=get_text('referral_bonus_notification', referrer_lang).format(bonus=REFERRAL_BONUS),
                            parse_mode=ParseMode.HTML
                        )
                        logging.info(f"Referral bonus awarded to {referrer_id}.")
                    except Exception as e:
                        logging.error(f"Error awarding referral bonus to {referrer_id}: {e}")
    except Exception as e:
        logging.error(f"Database error in get_or_create_user for {user_id}: {e}")


def get_user_lang(user_id):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            res = conn.execute("SELECT language_code FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()
            return res[0] if res else 'ar'
    except Exception as e:
        logging.error(f"Database error in get_user_lang for {user_id}: {e}")
        return 'ar'

def get_user_ad_status(user_id):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            ad_pending = conn.execute("SELECT ad_claim_pending FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()
            return ad_pending[0] if ad_pending else 0
    except Exception as e:
        logging.error(f"Database error in get_user_ad_status for {user_id}: {e}")
        return 0

def set_user_ad_status(user_id, status: int):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("UPDATE users SET ad_claim_pending = ? WHERE telegram_user_id = ?", (status, user_id))
            conn.commit()
    except Exception as e:
        logging.error(f"Database error in set_user_ad_status for {user_id}: {e}")

def set_user_lang(user_id, lang_code):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("UPDATE users SET language_code = ? WHERE telegram_user_id = ?", (lang_code, user_id))
            conn.commit()
    except Exception as e:
        logging.error(f"Database error in set_user_lang for {user_id}: {e}")

def get_connection_setting(key):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            result = conn.execute("SELECT value FROM connection_settings WHERE key = ?", (key,)).fetchone()
            return result[0] if result else ""
    except Exception as e:
        logging.error(f"Database error in get_connection_setting for key {key}: {e}")
        return ""

def set_connection_setting(key, value):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("INSERT OR REPLACE INTO connection_settings (key, value) VALUES (?, ?)", (key, value))
            conn.commit()
            logging.info(f"Connection setting {key} updated.")
    except Exception as e:
        logging.error(f"Database error in set_connection_setting for key {key}: {e}")

# =================================================================================
# 4. دوال مساعدة (Helpers)
# =================================================================================
def log_activity(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        today = date.today().isoformat()
        try:
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("INSERT OR REPLACE INTO daily_activity (user_id, last_seen_date) VALUES (?, ?)", (user_id, today))
                conn.commit()
        except Exception as e:
            logging.error(f"Database error in log_activity for {user_id}: {e}")
        return await func(update, context, *args, **kwargs)
    return wrapper

async def check_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        channel_member = await context.bot.get_chat_member(REQUIRED_CHANNEL_ID, user_id)
        group_member = await context.bot.get_chat_member(REQUIRED_GROUP_ID, user_id)
        if channel_member.status not in ['member', 'administrator', 'creator']: return False
        if group_member.status not in ['member', 'administrator', 'creator']: return False
        return True
    except Exception as e:
        logging.warning(f"Error checking membership for {user_id}: {e}")
        return False
        
# =================================================================================
# 5. دالة طلب وعرض الإعلان (AD Integration Function)
# =================================================================================

async def get_ad_eligibility(user_id: int):
    """التحقق مما إذا كان المستخدم مؤهلاً لبدء طلب الإعلان اليوم."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            result = conn.execute("SELECT last_ad_claim FROM ad_claims WHERE telegram_user_id = ?", (user_id,)).fetchone()
            if not result:
                return True, None

            last_claim_time = datetime.fromisoformat(result[0])
            time_since_claim = datetime.now() - last_claim_time
            
            if time_since_claim >= timedelta(hours=24):
                return True, None
            
            time_left = timedelta(hours=24) - time_since_claim
            hours = int(time_left.total_seconds() // 3600)
            minutes = int((time_left.total_seconds() % 3600) // 60)
            
            time_left_str = f"{hours}h {minutes}m"
            return False, time_left_str
    except Exception as e:
        logging.error(f"Database error in get_ad_eligibility for {user_id}: {e}")
        return True, None # افتراض الصلاحية في حالة خطأ القاعدة

async def get_and_send_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_code = get_user_lang(user_id)
    chat_id = update.effective_chat.id
    
    # 1. التحقق من حالة المكافأة والوقت
    is_eligible, time_left = await get_ad_eligibility(user_id)
    ad_pending = get_user_ad_status(user_id)
    
    if ad_pending:
        logging.warning(f"User {user_id} tried to claim ad while pending.")
        await context.bot.send_message(chat_id=chat_id, text=get_text('ad_already_pending', lang_code), parse_mode=ParseMode.HTML); return
        
    if not is_eligible:
        logging.info(f"User {user_id} is not eligible for ad claim yet.")
        await context.bot.send_message(
            chat_id=chat_id,
            text=get_text('ad_claimed_already', lang_code).format(time_left=time_left),
            parse_mode=ParseMode.HTML
        )
        return

    # 2. إعداد طلب الإعلان (SSP/RichAds)
    payload = {
        "language_code": lang_code,
        "publisher_id": SSP_PUBLISHER_ID,
        "widget_id": SSP_WIDGET_ID,
        "bid_floor": 0.0001,
        "telegram_id": str(user_id),
        "production": False # False للاختبار، True للإنتاج
    }
    
    headers = {"Content-Type": "application/json"}
    
    await context.bot.send_chat_action(chat_id=chat_id, action='upload_photo')

    try:
        # إرسال طلب SSP
        ssp_response = requests.post(SSP_ENDPOINT, json=payload, headers=headers, timeout=10)
        ssp_response.raise_for_status()
        ad_data = ssp_response.json()
        
        if not ad_data or not isinstance(ad_data, list) or len(ad_data) == 0:
            logging.warning(f"SSP returned empty response for user {user_id}. Status: {ssp_response.status_code}")
            await context.bot.send_message(chat_id=chat_id, text=get_text('ad_server_error', lang_code))
            return
            
        ad = ad_data[0]
        
        # 3. إرسال الإعلان المستلم إلى تليجرام (sendPhoto)
        caption_text = (
            f"*{html.escape(ad.get('title', 'Ad'))}*\n\n"
            f"{html.escape(ad.get('message', ''))}\n\n"
            f"Brand: {html.escape(ad.get('brand', ''))}"
        )
        
        ad_inline_keyboard = {
            "inline_keyboard": [
                [
                    {"text": html.escape(ad.get('button', 'Go!')), "url": ad.get('link', 'https://t.me/telegram')}
                ]
            ]
        }
        
        TELEGRAM_URL = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        
        telegram_payload = {
            'chat_id': chat_id,
            'photo': ad.get('image', 'https://placehold.co/600x400/AAAAAA/FFFFFF?text=AD'),
            'caption': caption_text,
            'parse_mode': 'Markdown',
            'reply_markup': json.dumps(ad_inline_keyboard)
        }
        
        telegram_response = requests.post(TELEGRAM_URL, data=telegram_payload)
        telegram_response.raise_for_status()
        
        # 4. إرسال رسالة التأكيد والمكافأة (رسالة منفصلة)
        verification_keyboard = [[InlineKeyboardButton(get_text('verify_ad_button', lang_code), callback_data='verify_ad_click')]]
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=get_text('ad_prompt_after_view', lang_code),
            reply_markup=InlineKeyboardMarkup(verification_keyboard),
            parse_mode=ParseMode.HTML
        )

        # 5. تسجيل حالة انتظار المكافأة
        set_user_ad_status(user_id, 1)
        logging.info(f"Ad sent to {user_id}. Pending verification.")

        
    except requests.exceptions.RequestException as e:
        logging.error(f"AD Request/Telegram API Error for user {user_id}: {e}", exc_info=True)
        await context.bot.send_message(chat_id=chat_id, text=get_text('ad_server_error', lang_code))

async def verify_ad_claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يمنح النقطة بعد ضغط المستخدم على زر 'تحققت'."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang_code = get_user_lang(user_id)
    
    if get_user_ad_status(user_id) == 0:
        await query.edit_message_text("ℹ️ لا توجد مطالبة إعلان قيد الانتظار حالياً.")
        return
        
    # 1. منح المكافأة وتسجيل المطالبة
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET points = points + ?, ad_claim_pending = 0 WHERE telegram_user_id = ?", (AD_REWARD_POINTS, user_id))
            cursor.execute("INSERT OR REPLACE INTO ad_claims (telegram_user_id, last_ad_claim) VALUES (?, ?)", (user_id, datetime.now().isoformat()))
            new_balance = cursor.execute("SELECT points FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
            conn.commit()
            
        logging.info(f"Ad reward of {AD_REWARD_POINTS} granted to user {user_id}.")
        
        await query.edit_message_text(
            get_text('ad_success', lang_code).format(points=AD_REWARD_POINTS),
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        logging.error(f"Error processing ad reward for {user_id}: {e}", exc_info=True)
        await query.edit_message_text(f"❌ حدث خطأ أثناء منح المكافأة: {e}")
        
    # تحديث قائمة كسب النقاط
    await earn_points_command(update, context, from_callback=True)


# =================================================================================
# 6. أوامر البوت الأساسية
# =================================================================================
@log_activity
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback: bool = False):
    user = update.effective_user
    message = update.message if not from_callback else update.callback_query.message
    
    user_lang = user.language_code if user.language_code in TEXTS else 'ar'
    referrer_id = None
    if context.args and context.args[0].startswith('ref_'):
        try:
            referrer_id = int(context.args[0].split('_')[1])
            if referrer_id == user.id: referrer_id = None
        except (ValueError, IndexError):
            referrer_id = None

    await get_or_create_user(user.id, lang_code=user_lang, referrer_id=referrer_id, context=context)
    lang_code = get_user_lang(user.id)

    if not await check_membership(user.id, context):
        keyboard = [
            [InlineKeyboardButton(get_text('force_join_channel_button', lang_code), url=CHANNEL_LINK)],
            [InlineKeyboardButton(get_text('force_join_group_button', lang_code), url=GROUP_LINK)],
            [InlineKeyboardButton(get_text('force_join_verify_button', lang_code), callback_data='verify_join')],
        ]
        await message.reply_text(get_text('force_join_prompt', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))
        return

    keyboard_layout = [
        [KeyboardButton(get_text('get_account_button', lang_code))],
        [KeyboardButton(get_text('balance_button', lang_code)), KeyboardButton(get_text('my_account_button', lang_code))],
        [KeyboardButton(get_text('daily_button', lang_code)), KeyboardButton(get_text('earn_points_button', lang_code))],
        [KeyboardButton(get_text('redeem_code_button', lang_code)), KeyboardButton(get_text('contact_admin_button', lang_code))]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard_layout, resize_keyboard=True)
    await message.reply_text(get_text('welcome', lang_code), reply_markup=reply_markup)

@log_activity
async def request_new_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_code = get_user_lang(user_id)
    
    try:
        with sqlite3.connect(DB_FILE) as conn:
            user_points = conn.execute("SELECT points FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
    except Exception as e:
        logging.error(f"DB Error fetching points for {user_id}: {e}")
        await update.message.reply_text("❌ خطأ داخلي في قاعدة البيانات.")
        return
    
    if user_points < COST_PER_ACCOUNT:
        await update.message.reply_text(get_text('not_enough_points', lang_code).format(cost=COST_PER_ACCOUNT), parse_mode=ParseMode.HTML)
        return

    keyboard = [
        [InlineKeyboardButton(get_text('ssh_account_button', lang_code), callback_data='create_ssh')],
        [InlineKeyboardButton(get_text('v2ray_account_button', lang_code), callback_data='under_development')],
        [InlineKeyboardButton(get_text('udpcustom_account_button', lang_code), callback_data='under_development')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(get_text('choose_account_type', lang_code), reply_markup=reply_markup)

async def under_development_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lang_code = get_user_lang(query.from_user.id)
    await query.answer(text=get_text('under_development', lang_code), show_alert=True)

async def account_creation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    lang_code = get_user_lang(user_id)

    try:
        with sqlite3.connect(DB_FILE) as conn:
            user_points = conn.execute("SELECT points FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
    except Exception as e:
        logging.error(f"DB Error fetching points for {user_id} before creation: {e}")
        await query.edit_message_text(get_text('creation_error', lang_code))
        return
    
    if user_points < COST_PER_ACCOUNT:
        await query.edit_message_text(get_text('not_enough_points', lang_code).format(cost=COST_PER_ACCOUNT), parse_mode=ParseMode.HTML)
        return

    await query.edit_message_text(text=get_text('creating_account', lang_code))

    if query.data == 'create_ssh':
        await create_ssh_account(update, context)

async def create_ssh_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    lang_code = get_user_lang(user_id)

    try:
        username = f"sshdatbot{user_id}"
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        command_to_run = ["sudo", SSH_SCRIPT_PATH, username, password, str(SSH_ACCOUNT_EXPIRY_DAYS)]

        # تنفيذ سكريبت SSH
        process = subprocess.run(command_to_run, capture_output=True, text=True, timeout=30, check=True)
        
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("UPDATE users SET points = points - ? WHERE telegram_user_id = ?", (COST_PER_ACCOUNT, user_id))
            conn.execute("INSERT INTO ssh_accounts (telegram_user_id, ssh_username, ssh_password, created_at) VALUES (?, ?, ?, ?)", (user_id, username, password, datetime.now()))
            conn.commit()

        hostname = get_connection_setting("hostname")
        ws_ports = get_connection_setting("ws_ports")
        ssl_port = get_connection_setting("ssl_port")
        udpcustom_port = get_connection_setting("udpcustom_port")
        payload = get_connection_setting("payload")
        
        try:
            expiry_output = subprocess.check_output(['/usr/bin/chage', '-l', username], text=True, stderr=subprocess.DEVNULL)
            expiry_line = next((line for line in expiry_output.split('\n') if "Account expires" in line), None)
            expiry = expiry_line.split(':', 1)[1].strip() if expiry_line else "N/A"
        except Exception:
            expiry = "N/A"

        account_info = get_text('account_details_full', lang_code).format(
            username=html.escape(username), password=html.escape(password), expiry=html.escape(expiry),
            hostname=html.escape(hostname), ws_ports=html.escape(ws_ports),
            ssl_port=html.escape(ssl_port), udpcustom_port=html.escape(udpcustom_port),
            payload=html.escape(payload)
        )
        logging.info(f"SSH account created for user {user_id}. Output: {process.stdout}")
        await query.edit_message_text(account_info, parse_mode=ParseMode.HTML)

    except subprocess.CalledProcessError as e:
        logging.error(f"SSH Script execution failed for {user_id}. Stderr: {e.stderr}")
        await query.edit_message_text(get_text('creation_error', lang_code) + f"\n\nDetails: SSH Script Error.")
    except Exception as e:
        logging.error(f"SSH Creation Error for {user_id}: {e}"); traceback.print_exc()
        await query.edit_message_text(get_text('creation_error', lang_code))

@log_activity
async def my_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_code = get_user_lang(user_id)
    
    response_parts = []
    
    try:
        with sqlite3.connect(DB_FILE) as conn:
            ssh_accounts = conn.execute("SELECT ssh_username, ssh_password FROM ssh_accounts WHERE telegram_user_id = ?", (user_id,)).fetchall()
    except Exception as e:
        logging.error(f"DB Error fetching accounts for {user_id}: {e}")
        await update.message.reply_text("❌ خطأ داخلي في قاعدة البيانات.")
        return

    if ssh_accounts:
        response_parts.append(get_text('your_accounts', lang_code))
        hostname = get_connection_setting("hostname")
        ws_ports = get_connection_setting("ws_ports")
        ssl_port = get_connection_setting("ssl_port")
        udpcustom_port = get_connection_setting("udpcustom_port")
        payload = get_connection_setting("payload")
        for username, password in ssh_accounts:
            try:
                expiry_output = subprocess.check_output(['/usr/bin/chage', '-l', username], text=True, stderr=subprocess.DEVNULL)
                expiry_line = next((line for line in expiry_output.split('\n') if "Account expires" in line), None)
                expiry = expiry_line.split(':', 1)[1].strip() if expiry_line else "N/A"
            except Exception:
                expiry = "N/A"
            response_parts.append(get_text('account_details_full', lang_code).format(
                username=html.escape(username), password=html.escape(password), expiry=html.escape(expiry),
                hostname=html.escape(hostname), ws_ports=html.escape(ws_ports),
                ssl_port=html.escape(ssl_port), udpcustom_port=html.escape(udpcustom_port),
                payload=html.escape(payload)
            ))

    if not response_parts:
        await update.message.reply_text(get_text('no_accounts_found', lang_code))
        return

    full_response = "\n\n---\n\n".join(response_parts)
    await update.message.reply_text(full_response, parse_mode=ParseMode.HTML)

@log_activity
async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_code = get_user_lang(user_id)
    try:
        with sqlite3.connect(DB_FILE) as conn:
            points = conn.execute("SELECT points FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
    except Exception as e:
        logging.error(f"DB Error fetching balance for {user_id}: {e}")
        points = 0
    await update.message.reply_text(get_text('balance_info', lang_code).format(points=points), parse_mode=ParseMode.HTML)

@log_activity
async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_code = get_user_lang(user_id)
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            today = date.today()
            last_claim_str = cursor.execute("SELECT last_daily_claim FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
            
            if last_claim_str and date.fromisoformat(last_claim_str) >= today:
                await update.message.reply_text(get_text('daily_bonus_already_claimed', lang_code)); return
                
            cursor.execute("UPDATE users SET points = points + ?, last_daily_claim = ? WHERE telegram_user_id = ?", (DAILY_LOGIN_BONUS, today.isoformat(), user_id))
            conn.commit()
            new_balance = cursor.execute("SELECT points FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
            logging.info(f"Daily bonus claimed by {user_id}.")
            await update.message.reply_text(get_text('daily_bonus_claimed', lang_code).format(bonus=DAILY_LOGIN_BONUS, new_balance=new_balance), parse_mode=ParseMode.HTML)
    except Exception as e:
        logging.error(f"DB Error in daily_command for {user_id}: {e}")
        await update.message.reply_text("❌ خطأ داخلي في قاعدة البيانات.")

@log_activity
async def earn_points_command(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback: bool = False):
    user_id = update.effective_user.id
    lang_code = get_user_lang(user_id)
    try:
        with sqlite3.connect(DB_FILE) as conn:
            all_channels = conn.execute("SELECT channel_id, channel_link, reward_points, channel_name FROM reward_channels").fetchall()
            claimed_ids = {row[0] for row in conn.execute("SELECT channel_id FROM user_channel_rewards WHERE telegram_user_id = ?", (user_id,))}
    except Exception as e:
        logging.error(f"DB Error fetching reward channels for {user_id}: {e}")
        all_channels = []
        claimed_ids = set()

    keyboard = []
    
    is_eligible, ad_time_left = await get_ad_eligibility(user_id)
    ad_button_text = get_text('watch_ad_button', lang_code).format(points=AD_REWARD_POINTS)
    
    ad_pending = get_user_ad_status(user_id)

    if ad_pending:
        keyboard.append([InlineKeyboardButton(get_text('verify_ad_button', lang_code), callback_data='verify_ad_click')])
    elif is_eligible:
        keyboard.append([InlineKeyboardButton(ad_button_text, callback_data='watch_ad')])
    else:
        ad_info = get_text('ad_claimed_already', lang_code).format(time_left=ad_time_left)
        keyboard.append([InlineKeyboardButton(ad_info, callback_data='dummy')])
        
    keyboard.append([InlineKeyboardButton("-------------------------------------", callback_data="dummy")])
    
    for cid, link, points, name in all_channels:
        if cid in claimed_ids:
            button_text = f"✅ {name}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data="dummy")])
        else:
            button_text = f"{name} (+{points} {get_text('points', lang_code)})"
            keyboard.append([InlineKeyboardButton(button_text, url=link)])
            keyboard.append([InlineKeyboardButton(get_text('verify_join_button', lang_code), callback_data=f"verify_r_{cid}_{points}")])
            
    if all_channels:
        keyboard.append([InlineKeyboardButton("-----------", callback_data="dummy")])
        
    keyboard.append([InlineKeyboardButton(get_text('referral_button', lang_code), callback_data='get_referral_link')])

    if from_callback:
        try:
            reply_func = update.callback_query.edit_message_text
            await reply_func(get_text('rewards_header', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            logging.warning(f"Error editing message for earn_points: {e}. Sending new message.")
            await update.callback_query.message.reply_text(get_text('rewards_header', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(get_text('rewards_header', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))

@log_activity
async def contact_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = get_user_lang(update.effective_user.id)
    contact_info = get_connection_setting("admin_contact")
    await update.message.reply_text(get_text('contact_admin_info', lang_code).format(contact_info=contact_info))

@log_activity
async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = get_user_lang(update.effective_user.id)
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data='set_lang_en')],
        [InlineKeyboardButton("🇸🇦 العربية", callback_data='set_lang_ar')],
    ]
    await update.message.reply_text(get_text('choose_language', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))

async def set_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang_code = query.data.split('_')[-1]
    set_user_lang(user_id, lang_code)
    lang_map = {'en': 'English', 'ar': 'العربية'}
    await query.edit_message_text(text=get_text('language_set', lang_code).format(lang_name=lang_map.get(lang_code)))
    await start(update, context, from_callback=True)

# =================================================================================
# 7. Admin Panel & Features
# =================================================================================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID: return
    lang_code = get_user_lang(user_id)
    keyboard = [
        [InlineKeyboardButton(get_text('admin_manage_rewards_button', lang_code), callback_data='admin_manage_rewards')],
        [InlineKeyboardButton(get_text('admin_manage_codes_button', lang_code), callback_data='admin_manage_codes')],
        [InlineKeyboardButton(get_text('admin_user_stats_button', lang_code), callback_data='admin_user_stats')],
        [InlineKeyboardButton(get_text('admin_edit_connection_info_button', lang_code), callback_data='admin_edit_connection_info')],
    ]
    await update.message.reply_text(get_text('admin_panel_header', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))

async def show_user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang_code = get_user_lang(query.from_user.id)
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    try:
        with sqlite3.connect(DB_FILE) as conn:
            total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            active_today = conn.execute("SELECT COUNT(*) FROM daily_activity WHERE last_seen_date = ?", (today,)).fetchone()[0]
            active_yesterday = conn.execute("SELECT COUNT(*) FROM daily_activity WHERE last_seen_date = ?", (yesterday,)).fetchone()[0]
            new_today = conn.execute("SELECT COUNT(*) FROM users WHERE created_date = ?", (today,)).fetchone()[0]
    except Exception as e:
        logging.error(f"DB Error in user_stats: {e}")
        total_users, active_today, active_yesterday, new_today = 0, 0, 0, 0
    
    stats_text = get_text('user_stats_info', lang_code).format(
        total_users=total_users,
        active_today=active_today,
        active_yesterday=active_yesterday,
        new_today=new_today
    )
    keyboard = [[InlineKeyboardButton(get_text('admin_return_button', lang_code), callback_data='admin_panel_main')]]
    await query.edit_message_text(stats_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id != ADMIN_USER_ID: return
    
    data = query.data
    lang_code = get_user_lang(user_id)
    
    if data == 'admin_panel_main':
        keyboard = [
            [InlineKeyboardButton(get_text('admin_manage_rewards_button', lang_code), callback_data='admin_manage_rewards')],
            [InlineKeyboardButton(get_text('admin_manage_codes_button', lang_code), callback_data='admin_manage_codes')],
            [InlineKeyboardButton(get_text('admin_user_stats_button', lang_code), callback_data='admin_user_stats')],
            [InlineKeyboardButton(get_text('admin_edit_connection_info_button', lang_code), callback_data='admin_edit_connection_info')],
        ]
        await query.edit_message_text(get_text('admin_panel_header', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == 'admin_manage_rewards':
        keyboard = [
            [InlineKeyboardButton(get_text('admin_add_channel_button', lang_code), callback_data='admin_add_channel_start')],
            [InlineKeyboardButton(get_text('admin_remove_channel_button', lang_code), callback_data='admin_remove_channel_start')],
            [InlineKeyboardButton(get_text('admin_return_button', lang_code), callback_data='admin_panel_main')]
        ]
        await query.edit_message_text(get_text('admin_manage_rewards_button', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == 'admin_manage_codes':
        keyboard = [
            [InlineKeyboardButton(get_text('admin_create_code_button', lang_code), callback_data='admin_create_code_start')],
            [InlineKeyboardButton(get_text('admin_return_button', lang_code), callback_data='admin_panel_main')]
        ]
        await query.edit_message_text(get_text('admin_manage_codes_button', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == 'admin_user_stats':
        await show_user_stats(update, context)

async def add_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    lang_code = get_user_lang(query.from_user.id)
    await query.edit_message_text(get_text('admin_add_channel_name_prompt', lang_code))
    return ADD_CHANNEL_NAME

async def add_channel_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['channel_name'] = update.message.text
    lang_code = get_user_lang(update.effective_user.id)
    await update.message.reply_text(get_text('admin_add_channel_link_prompt', lang_code))
    return ADD_CHANNEL_LINK

async def add_channel_get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['channel_link'] = update.message.text
    lang_code = get_user_lang(update.effective_user.id)
    await update.message.reply_text(get_text('admin_add_channel_id_prompt', lang_code))
    return ADD_CHANNEL_ID

async def add_channel_get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = get_user_lang(update.effective_user.id)
    try:
        context.user_data['channel_id'] = int(update.message.text)
        await update.message.reply_text(get_text('admin_add_channel_points_prompt', lang_code))
        return ADD_CHANNEL_POINTS
    except ValueError:
        await update.message.reply_text(get_text('invalid_input', lang_code)); return ADD_CHANNEL_ID

async def add_channel_get_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = get_user_lang(update.effective_user.id)
    try:
        points = int(update.message.text)
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("INSERT OR REPLACE INTO reward_channels (channel_id, channel_link, reward_points, channel_name) VALUES (?, ?, ?, ?)",
                         (context.user_data['channel_id'], context.user_data['channel_link'], points, context.user_data['channel_name']))
        await update.message.reply_text(get_text('admin_channel_added_success', lang_code))
        context.user_data.clear()
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(get_text('invalid_input', lang_code)); return ADD_CHANNEL_POINTS

async def remove_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    lang_code = get_user_lang(query.from_user.id)
    with sqlite3.connect(DB_FILE) as conn:
        channels = conn.execute("SELECT channel_id, channel_name FROM reward_channels").fetchall()
    if not channels:
        await query.edit_message_text(get_text('no_channels_available', lang_code), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text('admin_return_button', lang_code), callback_data='admin_manage_rewards')]])); return
    keyboard = [[InlineKeyboardButton(name, callback_data=f"remove_c_{cid}")] for cid, name in channels]
    keyboard.append([InlineKeyboardButton(get_text('admin_return_button', lang_code), callback_data='admin_manage_rewards')])
    await query.edit_message_text(get_text('admin_remove_channel_prompt', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))

async def remove_channel_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    lang_code = get_user_lang(query.from_user.id)
    channel_id = int(query.data.split('_')[-1])
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("DELETE FROM reward_channels WHERE channel_id = ?", (channel_id,))
        conn.execute("DELETE FROM user_channel_rewards WHERE channel_id = ?", (channel_id,))
    await query.edit_message_text(get_text('admin_channel_removed_success', lang_code))
    await remove_channel_start(update, context)

async def create_code_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    lang_code = get_user_lang(query.from_user.id)
    await query.edit_message_text(get_text('admin_create_code_prompt_name', lang_code))
    return CREATE_CODE_NAME

async def receive_code_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['code_name'] = update.message.text
    lang_code = get_user_lang(update.effective_user.id)
    await update.message.reply_text(get_text('admin_create_code_prompt_points', lang_code))
    return CREATE_CODE_POINTS

async def receive_code_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = get_user_lang(update.effective_user.id)
    try:
        context.user_data['code_points'] = int(update.message.text)
        await update.message.reply_text(get_text('admin_create_code_prompt_uses', lang_code))
        return CREATE_CODE_USES
    except ValueError:
        await update.message.reply_text(get_text('invalid_input', lang_code)); return CREATE_CODE_POINTS

async def receive_code_uses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = get_user_lang(update.effective_user.id)
    try:
        uses = int(update.message.text)
        name = context.user_data['code_name']
        points = context.user_data['code_points']
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("INSERT OR REPLACE INTO redeem_codes (code, points, max_uses, current_uses) VALUES (?, ?, ?, 0)", (name, points, uses))
        await update.message.reply_text(get_text('admin_code_created', lang_code).format(code=name, points=points, uses=uses), parse_mode=ParseMode.HTML)
        context.user_data.clear()
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(get_text('invalid_input', lang_code)); return CREATE_CODE_USES

async def edit_connection_info_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    lang_code = get_user_lang(query.from_user.id)
    await query.edit_message_text(get_text('admin_edit_hostname_prompt', lang_code))
    return EDIT_HOSTNAME

async def edit_hostname_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['hostname'] = update.message.text
    lang_code = get_user_lang(update.effective_user.id)
    await update.message.reply_text(get_text('admin_edit_ws_ports_prompt', lang_code))
    return EDIT_WS_PORTS

async def edit_ws_ports_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ws_ports'] = update.message.text
    lang_code = get_user_lang(update.effective_user.id)
    await update.message.reply_text(get_text('admin_edit_ssl_port_prompt', lang_code))
    return EDIT_SSL_PORT

async def edit_ssl_port_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ssl_port'] = update.message.text
    lang_code = get_user_lang(update.effective_user.id)
    await update.message.reply_text(get_text('admin_edit_udpcustom_prompt', lang_code))
    return EDIT_UDPCUSTOM

async def edit_udpcustom_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['udpcustom_port'] = update.message.text
    lang_code = get_user_lang(update.effective_user.id)
    await update.message.reply_text(get_text('admin_edit_contact_prompt', lang_code))
    return EDIT_ADMIN_CONTACT

async def edit_admin_contact_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['admin_contact'] = update.message.text
    lang_code = get_user_lang(update.effective_user.id)
    await update.message.reply_text(get_text('admin_edit_payload_prompt', lang_code))
    return EDIT_PAYLOAD

async def edit_payload_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = get_user_lang(update.effective_user.id)
    set_connection_setting('hostname', context.user_data['hostname'])
    set_connection_setting('ws_ports', context.user_data['ws_ports'])
    set_connection_setting('ssl_port', context.user_data['ssl_port'])
    set_connection_setting('udpcustom_port', context.user_data['udpcustom_port'])
    set_connection_setting('admin_contact', context.user_data['admin_contact'])
    set_connection_setting('payload', update.message.text)
    await update.message.reply_text(get_text('admin_info_updated_success', lang_code))
    context.user_data.clear()
    return ConversationHandler.END

@log_activity
async def redeem_code_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = get_user_lang(update.effective_user.id)
    await update.message.reply_text(get_text('redeem_prompt', lang_code))
    return REDEEM_CODE_INPUT

async def redeem_code_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_code = get_user_lang(user_id)
    code = update.message.text
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            code_data = cursor.execute("SELECT points, max_uses, current_uses FROM redeem_codes WHERE code = ?", (code,)).fetchone()
            
            if not code_data:
                await update.message.reply_text(get_text('redeem_invalid_code', lang_code)); return ConversationHandler.END
            
            points, max_uses, current_uses = code_data
            if current_uses >= max_uses:
                await update.message.reply_text(get_text('redeem_limit_reached', lang_code)); return ConversationHandler.END
            
            if cursor.execute("SELECT 1 FROM redeemed_users WHERE code = ? AND telegram_user_id = ?", (code, user_id)).fetchone():
                await update.message.reply_text(get_text('redeem_already_used', lang_code)); return ConversationHandler.END
                
            cursor.execute("UPDATE users SET points = points + ? WHERE telegram_user_id = ?", (points, user_id))
            cursor.execute("UPDATE redeem_codes SET current_uses = current_uses + 1 WHERE code = ?", (code,))
            cursor.execute("INSERT INTO redeemed_users (code, telegram_user_id) VALUES (?, ?)", (code, user_id))
            new_balance = cursor.execute("SELECT points FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
            await update.message.reply_text(get_text('redeem_success', lang_code).format(points=points, new_balance=new_balance), parse_mode=ParseMode.HTML)
            logging.info(f"User {user_id} redeemed code {code}.")
        return ConversationHandler.END
    except Exception as e:
        logging.error(f"DB Error in redeem_code_received for {user_id}: {e}")
        await update.message.reply_text("❌ خطأ داخلي في قاعدة البيانات.")
        return ConversationHandler.END

async def get_referral_link_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang_code = get_user_lang(user_id)
    bot_username = (await context.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    message_text = get_text('referral_info', lang_code).format(
        bonus=REFERRAL_BONUS,
        link=referral_link
    )
    await query.message.reply_text(message_text, parse_mode=ParseMode.HTML)

async def verify_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    user_id = query.from_user.id
    lang_code = get_user_lang(user_id)

    if await check_membership(user_id, context):
        try:
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                claimed = cursor.execute("SELECT join_bonus_claimed FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
                if not claimed:
                    cursor.execute("UPDATE users SET points = points + ?, join_bonus_claimed = 1 WHERE telegram_user_id = ?", (JOIN_BONUS, user_id))
                    conn.commit()
                    await query.answer(get_text('join_bonus_awarded', lang_code).format(bonus=JOIN_BONUS), show_alert=True)
                
            await query.edit_message_text(get_text('force_join_success', lang_code))
            await start(update, context, from_callback=True)
        except Exception as e:
            logging.error(f"DB Error in verify_join_callback for {user_id}: {e}")
            await query.answer("❌ خطأ في منح المكافأة.", show_alert=True)
    else:
        await query.answer(get_text('force_join_fail', lang_code), show_alert=True)

async def verify_reward_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    user_id = query.from_user.id
    lang_code = get_user_lang(user_id)
    
    try:
        _, _, channel_id_str, points_str = query.data.split('_')
        channel_id, points = int(channel_id_str), int(points_str)
    except (ValueError, IndexError):
        await query.answer("Data error.", show_alert=True); return

    try:
        member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        if member.status not in ['member', 'administrator', 'creator']:
            await query.answer(get_text('reward_fail', lang_code), show_alert=True); return
    except Exception as e:
        logging.warning(f"Verification error for channel {channel_id} and user {user_id}: {e}")
        await query.answer(f"Error: Could not verify. Make sure the bot is an admin in the channel.", show_alert=True); return
    
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            if cursor.execute("SELECT 1 FROM user_channel_rewards WHERE telegram_user_id = ? AND channel_id = ?", (user_id, channel_id)).fetchone():
                await query.answer("You have already claimed this reward.", show_alert=True); return
            
            cursor.execute("UPDATE users SET points = points + ? WHERE telegram_user_id = ?", (points, user_id))
            cursor.execute("INSERT INTO user_channel_rewards (telegram_user_id, channel_id) VALUES (?, ?)", (user_id, channel_id))
            conn.commit()
        
        logging.info(f"User {user_id} claimed reward from channel {channel_id}.")
        await query.answer(get_text('reward_success', lang_code).format(points=points), show_alert=True)
        await earn_points_command(update, context, from_callback=True)
    except Exception as e:
        logging.error(f"DB Error processing channel reward for {user_id}: {e}")
        await query.answer("❌ خطأ في قاعدة البيانات أثناء منح المكافأة.", show_alert=True)

async def watch_ad_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("جاري جلب الإعلان...")
    
    await get_and_send_ad(update, context)
    
    await earn_points_command(update, context, from_callback=True)

async def verify_ad_claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await verify_ad_claim_implementation(update, context)

async def verify_ad_claim_implementation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يمنح النقطة بعد ضغط المستخدم على زر 'تحققت'."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang_code = get_user_lang(user_id)
    
    if get_user_ad_status(user_id) == 0:
        await query.edit_message_text("ℹ️ لا توجد مطالبة إعلان قيد الانتظار حالياً.")
        return
        
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET points = points + ?, ad_claim_pending = 0 WHERE telegram_user_id = ?", (AD_REWARD_POINTS, user_id))
            cursor.execute("INSERT OR REPLACE INTO ad_claims (telegram_user_id, last_ad_claim) VALUES (?, ?)", (user_id, datetime.now().isoformat()))
            new_balance = cursor.execute("SELECT points FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
            conn.commit()
            
        logging.info(f"Ad reward of {AD_REWARD_POINTS} granted to user {user_id}.")
        
        await query.edit_message_text(
            get_text('ad_success', lang_code).format(points=AD_REWARD_POINTS),
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        logging.error(f"Error processing ad reward for {user_id}: {e}", exc_info=True)
        await query.edit_message_text(f"❌ حدث خطأ أثناء منح المكافأة: {e}")
        
    await earn_points_command(update, context, from_callback=True)

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = get_user_lang(update.effective_user.id)
    await update.message.reply_text(get_text('operation_cancelled', lang_code))
    context.user_data.clear()
    return ConversationHandler.END

# =================================================================================
# 8. نقطة انطلاق البوت (Main Entry Point)
# =================================================================================
def main():
    # ====================================================================
    # 📌 تهيئة نظام تسجيل الأخطاء (LOGGING)
    # ====================================================================
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("bot_errors.log", encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info("Starting bot initialization...")
    
    init_db()
    
    if "YOUR_TELEGRAM_BOT_TOKEN" in TOKEN:
        logging.error("FATAL ERROR: Bot token is not set in the script file.")
        sys.exit(1)

    try:
        app = ApplicationBuilder().token(TOKEN).build()
    except Exception as e:
        logging.critical(f"FATAL ERROR: Could not build Application. Token problem? {e}")
        sys.exit(1)
    
    conv_defaults = {'per_user': True, 'per_message': False, 'allow_reentry': True}

    # ====================================================================
    # 📌 Conversational Handlers
    # ====================================================================
    edit_info_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_connection_info_start, pattern='^admin_edit_connection_info$')],
        states={
            EDIT_HOSTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, edit_hostname_received)],
            EDIT_WS_PORTS: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, edit_ws_ports_received)],
            EDIT_SSL_PORT: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, edit_ssl_port_received)],
            EDIT_UDPCUSTOM: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, edit_udpcustom_received)],
            EDIT_ADMIN_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, edit_admin_contact_received)],
            EDIT_PAYLOAD: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, edit_payload_received)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)],
        **conv_defaults
    )
    add_channel_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_channel_start, pattern='^admin_add_channel_start$')],
        states={
            ADD_CHANNEL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, add_channel_get_name)],
            ADD_CHANNEL_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, add_channel_get_link)],
            ADD_CHANNEL_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, add_channel_get_id)],
            ADD_CHANNEL_POINTS: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, add_channel_get_points)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)],
        **conv_defaults
    )
    create_code_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(create_code_start, pattern='^admin_create_code_start$')],
        states={
            CREATE_CODE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, receive_code_name)],
            CREATE_CODE_POINTS: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, receive_code_points)],
            CREATE_CODE_USES: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, receive_code_uses)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)],
        **conv_defaults
    )
    
    def create_lang_regex(key):
        texts = [re.escape(get_text(key, lang)) for lang in TEXTS.keys()]
        return f"^({'|'.join(texts)})$"

    redeem_code_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(create_lang_regex('redeem_code_button')) & filters.ChatType.PRIVATE, redeem_code_start)],
        states={REDEEM_CODE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, redeem_code_received)]},
        fallbacks=[CommandHandler('cancel', cancel_conversation)],
        **conv_defaults
    )
    
    # ====================================================================
    # 📌 Handlers Registration
    # ====================================================================
    app.add_handler(CommandHandler("start", start, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("admin", admin_panel, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("language", language_command, filters=filters.ChatType.PRIVATE))

    app.add_handler(add_channel_conv)
    app.add_handler(create_code_conv)
    app.add_handler(redeem_code_conv)
    app.add_handler(edit_info_conv)

    app.add_handler(MessageHandler(filters.Regex(create_lang_regex('get_account_button')) & filters.ChatType.PRIVATE, request_new_account))
    app.add_handler(MessageHandler(filters.Regex(create_lang_regex('my_account_button')) & filters.ChatType.PRIVATE, my_accounts))
    app.add_handler(MessageHandler(filters.Regex(create_lang_regex('balance_button')) & filters.ChatType.PRIVATE, balance_command))
    app.add_handler(MessageHandler(filters.Regex(create_lang_regex('daily_button')) & filters.ChatType.PRIVATE, daily_command))
    app.add_handler(MessageHandler(filters.Regex(create_lang_regex('earn_points_button')) & filters.ChatType.PRIVATE, earn_points_command))
    app.add_handler(MessageHandler(filters.Regex(create_lang_regex('contact_admin_button')) & filters.ChatType.PRIVATE, contact_admin_command))
    
    app.add_handler(CallbackQueryHandler(account_creation_callback, pattern='^create_ssh$'))
    app.add_handler(CallbackQueryHandler(under_development_callback, pattern='^under_development$'))
    app.add_handler(CallbackQueryHandler(verify_join_callback, pattern='^verify_join$'))
    app.add_handler(CallbackQueryHandler(verify_reward_callback, pattern='^verify_r_'))
    app.add_handler(CallbackQueryHandler(remove_channel_confirm, pattern='^remove_c_'))
    app.add_handler(CallbackQueryHandler(set_language_callback, pattern='^set_lang_'))
    app.add_handler(CallbackQueryHandler(get_referral_link_callback, pattern='^get_referral_link$'))
    app.add_handler(CallbackQueryHandler(watch_ad_callback, pattern='^watch_ad$')) 
    app.add_handler(CallbackQueryHandler(verify_ad_claim, pattern='^verify_ad_click$')) 
    app.add_handler(CallbackQueryHandler(lambda u,c: u.callback_query.answer(), pattern='^dummy$'))
    app.add_handler(CallbackQueryHandler(admin_panel_callback, pattern='^admin_'))

    logging.info("Bot is running with logging enabled. Check bot_errors.log for details.")
    try:
        app.run_polling(poll_interval=1.0)
    except Exception as e:
        logging.critical(f"FATAL ERROR: Polling failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
