#!/bin/bash

# ==============================================================================
#  سكربت التثبيت الشامل لمشروع بوت SSH (نسخة GitHub)
#  يقوم هذا السكربت بأتمتة جميع خطوات الإعداد على خادم Ubuntu/Debian جديد.
# ==============================================================================

# --- إعدادات أساسية ---

# 1. رابط مستودع المشروع على GitHub
GIT_REPO_URL="https://github.com/Lahcenoum/sshtestbot.git"

# 2. اسم مجلد المشروع الذي سيتم إنشاؤه
PROJECT_DIR="/home/ssh_bot"

# --- نهاية قسم الإعدادات ---


# التحقق من أن السكربت يتم تشغيله بصلاحيات الجذر (root)
if [ "$(id -u)" -ne 0 ]; then
  echo "❌ هذا السكربت يجب أن يعمل بصلاحيات الجذر (root). يرجى استخدام 'sudo'."
  exit 1
fi

echo "=================================================="
echo "      بدء عملية تثبيت وإعداد بوت SSH من GitHub"
echo "=================================================="

# الخطوة 1: تحديث النظام وتثبيت المتطلبات الأساسية
echo -e "\n[1/9] تحديث النظام وتثبيت المتطلبات (git, python3-full, python3-venv)..."
apt-get update
apt-get install -y git python3-full python3-venv sqlite3

# الخطوة 2: استنساخ المشروع من GitHub
echo -e "\n[2/9] استنساخ المشروع من GitHub إلى '$PROJECT_DIR'..."
rm -rf "$PROJECT_DIR"
git clone "$GIT_REPO_URL" "$PROJECT_DIR"

# التحقق من نجاح الاستنساخ
if [ ! -d "$PROJECT_DIR" ] || [ ! -f "$PROJECT_DIR/bot.py" ]; then
    echo "❌ فشل استنساخ المشروع. يرجى التحقق من رابط المستودع وصلاحياته."
    exit 1
fi

# الانتقال إلى مجلد المشروع
cd "$PROJECT_DIR" || exit

# الخطوة 3: تنظيم الملفات ونقل السكربتات
echo -e "\n[3/9] تنظيم الملفات ونقل السكربتات إلى المسار الصحيح..."
if [ -f "create_ssh_user.sh" ]; then mv create_ssh_user.sh /usr/local/bin/; fi
if [ -f "monitor_ssh.sh" ]; then mv monitor_ssh.sh /usr/local/bin/; fi
if [ -f "delete_expired_users.sh" ]; then mv delete_expired_users.sh /usr/local/bin/; fi

# الخطوة 4: إنشاء بيئة بايثون الافتراضية
echo -e "\n[4/9] إنشاء بيئة بايثون الافتراضية (venv)..."
python3 -m venv venv

# الخطوة 5: تثبيت مكتبات بايثون داخل البيئة الافتراضية
echo -e "\n[5/9] تثبيت مكتبات بايثون المطلوبة..."
if [ -f "requirements.txt" ]; then
    source venv/bin/activate
    pip install -r requirements.txt
    deactivate
    echo "-> تم تثبيت المكتبات من requirements.txt بنجاح."
else
    echo "❌ خطأ: لم يتم العثور على ملف 'requirements.txt' في المستودع."
    exit 1
fi

# الخطوة 6: إعداد توكن البوت
echo -e "\n[6/9] إعداد توكن بوت تليجرام..."
echo "الرجاء إدخال توكن البوت الذي حصلت عليه من BotFather."
read -p "Enter Bot Token: " BOT_TOKEN

if [ -z "$BOT_TOKEN" ]; then
    echo "❌ خطأ: لم يتم إدخال التوكن. التثبيت سيتوقف."
    exit 1
fi

# استبدال التوكن في ملف bot.py
# نفترض أن الملف يحتوي على سطر مثل: TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
# سيقوم السكربت بالبحث عن هذا السطر واستبداله بالتوكن الذي أدخلته
if grep -q 'TOKEN = ".*"' "$PROJECT_DIR/bot.py"; then
    sed -i 's/TOKEN = ".*"/TOKEN = "'"$BOT_TOKEN"'"/' "$PROJECT_DIR/bot.py"
    echo "-> تم حفظ التوكن بنجاح في ملف bot.py."
else
    echo "⚠️ تحذير: لم يتم العثور على السطر الخاص بالتوكن (TOKEN = \"...\") في ملف bot.py. يرجى إضافته يدويًا."
fi


# الخطوة 7: إعطاء صلاحيات التنفيذ للسكربتات
echo -e "\n[7/9] إعطاء صلاحيات التنفيذ للسكربتات..."
chmod +x /usr/local/bin/create_ssh_user.sh
chmod +x /usr/local/bin/monitor_ssh.sh
chmod +x /usr/local/bin/delete_expired_users.sh

# الخطوة 8: إعداد المهام المجدولة (Cron Jobs)
echo -e "\n[8/9] إعداد المهام المجدولة..."
(crontab -l 2>/dev/null | grep -v -F "/usr/local/bin/monitor_ssh.sh" ; echo "*/5 * * * * /usr/local/bin/monitor_ssh.sh") | crontab -
(crontab -l 2>/dev/null | grep -v -F "/usr/local/bin/delete_expired_users.sh" ; echo "0 0 * * * /usr/local/bin/delete_expired_users.sh") | crontab -

# الخطوة 9: إعداد البوت كخدمة دائمة (systemd)
echo -e "\n[9/9] إعداد البوت كخدمة دائمة (systemd)..."
cat > /etc/systemd/system/ssh_bot.service << EOL
[Unit]
Description=Telegram SSH Bot Service
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PROJECT_DIR}/venv/bin/python ${PROJECT_DIR}/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

# إعادة تحميل systemd، تفعيل الخدمة، وتشغيلها
systemctl daemon-reload
systemctl enable ssh_bot.service
systemctl start ssh_bot.service

# عرض التعليمات النهائية
echo -e "\n=================================================="
echo "✅ اكتمل التثبيت بنجاح!"
echo "   البوت يعمل الآن كخدمة دائمة في الخلفية."
echo "=================================================="
echo -e "\n**ملاحظات هامة:**\n"
echo "1. **معرف المدير (Admin ID):** تم حفظ توكن البوت تلقائيًا. إذا كان البوت يتطلب معرف مدير،"
echo "   لا تنسَ تعديل ملف 'bot.py' وإضافة معرف المستخدم الخاص بك."
echo "   - استخدم الأمر: nano ${PROJECT_DIR}/bot.py"
echo ""
echo "2. **لمراقبة حالة البوت أو رؤية الأخطاء:**"
echo "   - استخدم الأمر: systemctl status ssh_bot.service"
echo ""
echo "3. **لإعادة تشغيل البوت بعد أي تعديل:**"
echo "   - استخدم الأمر: systemctl restart ssh_bot.service"
echo "--------------------------------------------------"
