#!/bin/bash

# ==============================================================================
#  سكربت التثبيت الشامل لمشروع بوت SSH (نسخة GitHub)
#  يقوم هذا السكربت بأتمتة جميع خطوات الإعداد على خادم Ubuntu/Debian جديد.
#  - يتضمن تقييد الحسابات باتصالين (2) فقط.
#  - يتضمن تثبيت المكتبات الإضافية اللازمة (pytz).
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
echo -e "\n[1/11] تحديث النظام وتثبيت المتطلبات (git, python3-full, python3-venv)..."
apt-get update
apt-get install -y git python3-full python3-venv sqlite3

# الخطوة 2: تهيئة نظام تقييد الجلسات
echo -e "\n[2/11] تهيئة نظام تقييد الجلسات (اتصالان لكل مستخدم)..."
groupadd ssh_bot_users &>/dev/null
LIMIT_RULE="@ssh_bot_users - maxlogins 2"
sed -i '/@ssh_bot_users - maxlogins/d' /etc/security/limits.conf
echo "$LIMIT_RULE" >> /etc/security/limits.conf
echo "-> تمت إضافة قاعدة تقييد الجلسات لـ 2 مستخدمين بنجاح."

if grep -q "UsePAM no" /etc/ssh/sshd_config; then
    sed -i 's/UsePAM no/UsePAM yes/' /etc/ssh/sshd_config
    systemctl restart sshd
    echo "-> تم تفعيل UsePAM في إعدادات SSH."
fi

# الخطوة 3: استنساخ المشروع من GitHub
echo -e "\n[3/11] استنساخ المشروع من GitHub إلى '$PROJECT_DIR'..."
rm -rf "$PROJECT_DIR"
git clone "$GIT_REPO_URL" "$PROJECT_DIR"

# التحقق من نجاح الاستنساخ
if [ ! -d "$PROJECT_DIR" ] || [ ! -f "$PROJECT_DIR/bot.py" ]; then
    echo "❌ فشل استنساخ المشروع. يرجى التحقق من رابط المستودع وصلاحياته."
    exit 1
fi

# الانتقال إلى مجلد المشروع
cd "$PROJECT_DIR" || exit

# الخطوة 4: تنظيم الملفات ونقل السكربتات
echo -e "\n[4/11] تنظيم الملفات ونقل السكربتات إلى المسار الصحيح..."
if [ -f "create_ssh_user.sh" ]; then mv create_ssh_user.sh /usr/local/bin/; fi
if [ -f "monitor_ssh.sh" ]; then mv monitor_ssh.sh /usr/local/bin/; fi
if [ -f "delete_expired_users.sh" ]; then mv delete_expired_users.sh /usr/local/bin/; fi

# الخطوة 5: إنشاء بيئة بايثون الافتراضية
echo -e "\n[5/11] إنشاء بيئة بايثون الافتراضية (venv)..."
python3 -m venv venv

# الخطوة 6: تثبيت مكتبات بايثون المطلوبة
echo -e "\n[6/11] تثبيت مكتبات بايثون المطلوبة..."
if [ -f "requirements.txt" ]; then
    source venv/bin/activate
    pip install -r requirements.txt
    deactivate
    echo "-> تم تثبيت المكتبات من requirements.txt بنجاح."
else
    echo "❌ خطأ: لم يتم العثور على ملف 'requirements.txt' في المستودع."
    exit 1
fi

# ✨ الخطوة 7: تثبيت المكتبات الإضافية وتحديث المتطلبات
echo -e "\n[7/11] تثبيت المكتبات الإضافية (pytz)..."
source venv/bin/activate
pip install pytz
# إضافة المكتبة إلى ملف المتطلبات لضمان تثبيتها في المستقبل
if ! grep -qF "pytz" requirements.txt; then
    echo "pytz" >> requirements.txt
fi
deactivate
echo "-> تم تثبيت pytz بنجاح."

# الخطوة 8: إعداد توكن البوت
echo -e "\n[8/11] إعداد توكن بوت تليجرام..."
echo "الرجاء إدخال توكن البوت الذي حصلت عليه من BotFather."
read -p "Enter Bot Token: " BOT_TOKEN

if [ -z "$BOT_TOKEN" ]; then
    echo "❌ خطأ: لم يتم إدخال التوكن. التثبيت سيتوقف."
    exit 1
fi

PLACEHOLDER="YOUR_TELEGRAM_BOT_TOKEN"
if grep -q "$PLACEHOLDER" "$PROJECT_DIR/bot.py"; then
    sed -i "s/$PLACEHOLDER/$BOT_TOKEN/g" "$PROJECT_DIR/bot.py"
    echo "-> تم حفظ التوكن بنجاح في ملف bot.py."
else
    echo "⚠️ تحذير: لم يتم العثور على الكلمة المحددة ($PLACEHOLDER) في ملف bot.py. قد تحتاج لإضافته يدويًا."
fi

# الخطوة 9: إعطاء صلاحيات التنفيذ للسكربتات
echo -e "\n[9/11] إعطاء صلاحيات التنفيذ للسكربتات..."
chmod +x /usr/local/bin/create_ssh_user.sh
chmod +x /usr/local/bin/monitor_ssh.sh
chmod +x /usr/local/bin/delete_expired_users.sh

# الخطوة 10: إعداد المهام المجدولة (Cron Jobs)
echo -e "\n[10/11] إعداد المهام المجدولة..."
(crontab -l 2>/dev/null | grep -v -F "/usr/local/bin/monitor_ssh.sh" ; echo "*/5 * * * * /usr/local/bin/monitor_ssh.sh") | crontab -
(crontab -l 2>/dev/null | grep -v -F "/usr/local/bin/delete_expired_users.sh" ; echo "0 0 * * * /usr/local/bin/delete_expired_users.sh") | crontab -

# الخطوة 11: إعداد البوت كخدمة دائمة (systemd)
echo -e "\n[11/11] إعداد البوت كخدمة دائمة (systemd)..."
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
echo "1. **معرف المدير (Admin ID):** لا تنسَ تعديل ملف 'bot.py' وإضافة معرف المستخدم الخاص بك."
echo "   - استخدم الأمر: nano ${PROJECT_DIR}/bot.py"
echo ""
echo "2. **لمراقبة حالة البوت أو رؤية الأخطاء:**"
echo "   - استخدم الأمر: systemctl status ssh_bot.service"
echo ""
echo "3. **لإعادة تشغيل البوت بعد أي تعديل:**"
echo "   - استخدم الأمر: systemctl restart ssh_bot.service"
echo "--------------------------------------------------"
