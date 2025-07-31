#!/bin/bash

# ==============================================================================
#  سكربت التثبيت الشامل لمشروع بوت SSH (نسخة GitHub)
#  يقوم هذا السكربت بأتمتة جميع خطوات الإعداد على خادم Ubuntu/Debian جديد.
# ==============================================================================

# --- إعدادات أساسية (⚠️ يرجى تعديل هذا المتغير قبل التشغيل) ---

# 1. رابط مستودع المشروع على GitHub
GIT_REPO_URL="https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git" # ⚠️ استبدل هذا برابط المستودع الخاص بك

# 2. اسم مجلد المشروع الذي سيتم إنشاؤه
PROJECT_DIR="/opt/ssh_bot"

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
# تم إضافة 'git' للمتطلبات
echo -e "\n[1/7] تحديث النظام وتثبيت المتطلبات (git, python3, pip, sqlite3)..."
apt-get update
apt-get install -y git python3 python3-pip sqlite3

# الخطوة 2: استنساخ المشروع من GitHub
echo -e "\n[2/7] استنساخ المشروع من GitHub إلى '$PROJECT_DIR'..."
# حذف المجلد القديم إذا كان موجودًا لضمان نسخة نظيفة
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
echo -e "\n[3/7] تنظيم الملفات ونقل السكربتات إلى المسار الصحيح..."
# التأكد من وجود الملفات قبل نقلها
if [ -f "create_ssh_user.sh" ]; then mv create_ssh_user.sh /usr/local/bin/; fi
if [ -f "monitor_ssh.sh" ]; then mv monitor_ssh.sh /usr/local/bin/; fi
if [ -f "delete_expired_users.sh" ]; then mv delete_expired_users.sh /usr/local/bin/; fi

# الخطوة 4: تثبيت مكتبات بايثون
echo -e "\n[4/7] تثبيت مكتبات بايثون المطلوبة..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
else
    # في حال عدم وجود ملف المتطلبات، سيقوم البوت بمحاولة التثبيت
    python3 bot.py &
    BOT_PID=$!
    sleep 15 # إعطاء وقت كافٍ للبوت لتثبيت المكتبات
    kill $BOT_PID
fi
echo "-> تم إكمال محاولة تثبيت المكتبات."

# الخطوة 5: إعطاء صلاحيات التنفيذ للسكربتات
echo -e "\n[5/7] إعطاء صلاحيات التنفيذ للسكربتات..."
chmod +x /usr/local/bin/create_ssh_user.sh
chmod +x /usr/local/bin/monitor_ssh.sh
chmod +x /usr/local/bin/delete_expired_users.sh

# الخطوة 6: إعداد المهام المجدولة (Cron Jobs)
echo -e "\n[6/7] إعداد المهام المجدولة..."
(crontab -l 2>/dev/null | grep -v -F "/usr/local/bin/monitor_ssh.sh" ; echo "*/5 * * * * /usr/local/bin/monitor_ssh.sh") | crontab -
(crontab -l 2>/dev/null | grep -v -F "/usr/local/bin/delete_expired_users.sh" ; echo "0 0 * * * /usr/local/bin/delete_expired_users.sh") | crontab -

# الخطوة 7: إعداد البوت كخدمة دائمة (systemd) - الطريقة الاحترافية
echo -e "\n[7/7] إعداد البوت كخدمة دائمة (systemd)..."
# إنشاء ملف الخدمة
cat > /etc/systemd/system/ssh_bot.service << EOL
[Unit]
Description=Telegram SSH Bot Service
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=${PROJECT_DIR}
ExecStart=/usr/bin/python3 ${PROJECT_DIR}/bot.py
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
echo "1. **إضافة التوكن:** إذا لم تكن تستخدم متغيرات البيئة، تأكد من تعديل ملف 'bot.py' وإضافة التوكن ومعرف المدير."
echo "   - استخدم الأمر: nano ${PROJECT_DIR}/bot.py"
echo ""
echo "2. **لمراقبة حالة البوت أو رؤية الأخطاء:**"
echo "   - استخدم الأمر: systemctl status ssh_bot.service"
echo ""
echo "3. **لإعادة تشغيل البوت بعد أي تعديل:**"
echo "   - استخدم الأمر: systemctl restart ssh_bot.service"
echo "--------------------------------------------------"
