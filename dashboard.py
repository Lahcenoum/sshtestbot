import sqlite3
import telegram
import asyncio
import time
from flask import Flask, render_template, request, redirect, url_for, flash, session

# =================================================================================
# 1. الإعدادات الرئيسية (Configuration)
# =================================================================================
# استخدم نفس المتغيرات من ملف البوت الخاص بك
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # ⚠️ ضع التوكن هنا
DB_FILE = 'ssh_bot_users.db'       # اسم قاعدة البيانات

# --- إعدادات لوحة التحكم ---
app = Flask(__name__)
# ⚠️ غيّر هذا المفتاح السري إلى أي جملة عشوائية قوية
app.config['SECRET_KEY'] = 'my-super-secret-dashboard-key-change-me'
# ⚠️ كلمة المرور لحماية لوحة التحكم
DASHBOARD_PASSWORD = "admin" 

# تهيئة اتصال البوت (سيستخدمه الـ Dashboard فقط للإرسال)
bot = telegram.Bot(token=TOKEN)

# =================================================================================
# 2. دوال مساعدة (Helper Functions)
# =================================================================================

# دالة للتحقق من أن الأدمن مسجل دخوله
def login_required(f):
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('يجب عليك تسجيل الدخول أولاً', 'danger')
            return redirect(url_for('login'))
    wrap.__name__ = f.__name__
    return wrap

# دالة لجلب كل معرفات المستخدمين
def get_all_user_ids():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT telegram_user_id FROM users')
        # استخراج المعرفات من الصفوف
        return [row[0] for row in cursor.fetchall()]

# دالة لجلب الإحصائيات من قاعدة البيانات
def get_stats():
    from datetime import date, timedelta
    today = date.today().isoformat()
    
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        total_users = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        active_today = cursor.execute("SELECT COUNT(*) FROM daily_activity WHERE last_seen_date = ?", (today,)).fetchone()[0]
        new_today = cursor.execute("SELECT COUNT(*) FROM users WHERE created_date = ?", (today,)).fetchone()[0]
    return {'total': total_users, 'active_today': active_today, 'new_today': new_today}

# دالة لجلب قائمة المستخدمين
def get_all_users_details():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT telegram_user_id, points, language_code, created_date FROM users ORDER BY points DESC')
        return cursor.fetchall()

# دالة الإذاعة غير المتزامنة (للرسائل والملفات)
async def broadcast(user_ids, message=None, file=None, caption=None):
    success_count = 0
    fail_count = 0
    for user_id in user_ids:
        try:
            if file:
                # إعادة المؤشر لبداية الملف لكل عملية إرسال
                file.seek(0)
                await bot.send_document(chat_id=user_id, document=file, caption=caption)
            elif message:
                await bot.send_message(chat_id=user_id, text=message, parse_mode='Markdown')
            
            success_count += 1
            await asyncio.sleep(0.1)  # تأخير بسيط لتجنب حظر تيليجرام
        except telegram.error.Forbidden:
            print(f"فشل الإرسال إلى {user_id}: المستخدم قام بحظر البوت.")
            fail_count += 1
        except Exception as e:
            print(f"فشل الإرسال إلى {user_id}: {e}")
            fail_count += 1
    return success_count, fail_count

# =================================================================================
# 3. روابط لوحة التحكم (Routes)
# =================================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == DASHBOARD_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('كلمة المرور غير صحيحة!', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        user_ids = get_all_user_ids()
        if not user_ids:
            flash('لا يوجد مستخدمين في قاعدة البيانات بعد.', 'warning')
            return redirect(url_for('index'))
            
        message = request.form.get('message')
        uploaded_file = request.files.get('file')

        if not message and not uploaded_file:
            flash('يجب كتابة رسالة أو رفع ملف على الأقل.', 'danger')
            return redirect(url_for('index'))

        # تشغيل دالة الإرسال غير المتزامنة
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        if uploaded_file:
             # إذا كان هناك ملف، الرسالة النصية ستكون كـ caption
             success, failed = loop.run_until_complete(broadcast(user_ids, file=uploaded_file, caption=message))
        else:
             success, failed = loop.run_until_complete(broadcast(user_ids, message=message))
        
        flash(f'تم إرسال الإذاعة بنجاح إلى {success} مستخدم. فشل الإرسال لـ {failed} مستخدم.', 'success')
        return redirect(url_for('index'))

    stats = get_stats()
    return render_template('index.html', stats=stats)

@app.route('/users')
@login_required
def users_list():
    users = get_all_users_details()
    return render_template('users_list.html', users=users)


if __name__ == '__main__':
    print("Dashboard is running on http://127.0.0.1:5000")
    print("Make sure your bot script (bot.py) is also running.")
    app.run(host='0.0.0.0', port=5000, debug=True)
