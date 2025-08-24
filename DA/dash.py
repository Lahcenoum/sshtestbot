# -*- coding: utf-8 -*-

# ========================================================================
#         ملف dash.py - نسخة كاملة لإرسال الإذاعة
# ========================================================================
# ملاحظة: تأكد من تثبيت مكتبة requests لتشغيل هذا السكربت
# يمكنك تثبيتها عبر الأمر: pip install requests
# ========================================================================

import sqlite3
import requests
import time
import re

# --- [!] إعدادات مهمة ---
DB_PATH = "/home/ssh_bot/ssh_bot_users.db"
BOT_FILE_PATH = "/home/ssh_bot/bot.py"

# --- تعريف متغير الرسالة ---
MAINTENANCE_MESSAGE = """
**إشعار صيانة وتحديث | Maintenance & Update Notice**

**بالعربية:**
مرحباً، سيتم إيقاف البوت مؤقتاً لإجراء تحديثات وإصلاحات.
للاشتراك في السيرفرات المدفوعة بسعر **2 دولار**، يرجى الانضمام إلى قناتنا والتواصل مع الأدمن من هناك:
https://t.me/CLOUDVIP

**English:**
Hello, the bot will be temporarily down for maintenance and bug fixes.
To subscribe to our premium servers for **$2**, please join our channel and contact the admin there:
https://t.me/CLOUDVIP
"""

def get_bot_token():
    """
    تقوم هذه الدالة بقراءة ملف البوت واستخراج التوكن.
    """
    print(">> جاري قراءة توكن البوت من الملف...")
    try:
        with open(BOT_FILE_PATH, 'r') as f:
            content = f.read()
            # استخدام تعبير نمطي للبحث عن التوكن بشكل آمن
            match = re.search(r'^TOKEN\s*=\s*["\'](.*?)["\']', content, re.MULTILINE)
            if match:
                token = match.group(1)
                if token and token != "YOUR_TELEGRAM_BOT_TOKEN":
                    print("  - [+] تم العثور على التوكن بنجاح.")
                    return token
    except FileNotFoundError:
        print(f"[-] خطأ: لم يتم العثور على ملف البوت في المسار: {BOT_FILE_PATH}")
        return None
    
    print("[-] خطأ: لم يتم العثور على توكن صالح في ملف bot.py.")
    return None

def get_user_ids():
    """
    تتصل بقاعدة البيانات وتجلب قائمة بمعرفات المستخدمين.
    """
    print(">> جاري الاتصال بقاعدة البيانات لجلب المستخدمين...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_user_id FROM users WHERE telegram_user_id IS NOT NULL")
        # استخراج النتائج في قائمة
        user_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        print(f"  - [+] تم العثور على {len(user_ids)} مستخدم.")
        return user_ids
    except sqlite3.Error as e:
        print(f"[-] خطأ في قاعدة البيانات: {e}")
        return []
    except Exception as e:
        print(f"[-] خطأ غير متوقع: {e}")
        return []

def send_broadcast_message():
    """
    الدالة الرئيسية التي تقوم بتنفيذ عملية الإذاعة.
    """
    bot_token = get_bot_token()
    if not bot_token:
        return

    user_ids = get_user_ids()
    if not user_ids:
        print(">> لا يوجد مستخدمين لإرسال الرسالة لهم.")
        return

    print(f"\n>> بدء إرسال رسالة الصيانة لـ {len(user_ids)} مستخدم...")
    
    success_count = 0
    fail_count = 0
    
    # بناء رابط الإرسال
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    for user_id in user_ids:
        payload = {
            'chat_id': user_id,
            'text': MAINTENANCE_MESSAGE,
            'parse_mode': 'Markdown'
        }
        try:
            # إرسال الطلب مع مهلة 10 ثواني
            response = requests.post(api_url, data=payload, timeout=10)
            if response.status_code == 200 and response.json().get("ok"):
                success_count += 1
            else:
                fail_count += 1
                # طباعة الخطأ للمساعدة في التشخيص
                # print(f"  - فشل الإرسال للمستخدم {user_id}: {response.text}")
        except requests.exceptions.RequestException as e:
            # في حال حدوث خطأ في الاتصال
            fail_count += 1
            # print(f"  - فشل الاتصال للمستخدم {user_id}: {e}")
        
        # انتظار بسيط لتجنب إغراق واجهة تليجرام
        time.sleep(0.1)

    print("\n---------------------------------")
    print(f"[+] اكتملت الإذاعة:")
    print(f"  - نجح الإرسال لـ: {success_count} مستخدم.")
    if fail_count > 0:
        print(f"  - فشل الإرسال لـ: {fail_count} مستخدم.")
    print("---------------------------------")


# --- نقطة بداية البرنامج ---
if __name__ == "__main__":
    send_broadcast_message()
    print("\n[+] اكتمل السكربت بنجاح.")
