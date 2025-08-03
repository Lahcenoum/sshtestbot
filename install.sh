#!/bin/bash

# ==============================================================================
#  سكربت تثبيت مخصص لمستودع Lahcenoum/sshtestbot
#  - يقوم بتحميل الملفات من GitHub.
#  - يقوم بإصلاح سكربت create_ssh_user.sh ليعمل بشكل صحيح.
#  - يقوم بتثبيت المكتبات المطلوبة مباشرة.
# ==============================================================================

# --- إعدادات أساسية ---
GIT_REPO_URL="https://github.com/Lahcenoum/sshtestbot.git"
PROJECT_DIR="/home/ssh_bot"

# --- نهاية قسم الإعدادات ---

# التحقق من صلاحيات الجذر
if [ "$(id -u)" -ne 0 ]; then
  echo "❌ هذا السكربت يجب أن يعمل بصلاحيات الجذر (root)."
  exit 1
fi

echo "=================================================="
echo "      بدء تثبيت البوت من مستودعك المحدد"
echo "=================================================="

# 1. تحديث وتثبيت المتطلبات
echo -e "\n[1/8] تحديث النظام وتثبيت المتطلبات (git, python3-venv, python3-pip, sqlite3)..."
apt-get update
apt-get install -y git python3-venv python3-pip sqlite3

# 2. استنساخ المشروع من GitHub
echo -e "\n[2/8] استنساخ المشروع من GitHub..."
rm -rf "$PROJECT_DIR"
git clone "$GIT_REPO_URL" "$PROJECT_DIR"
if [ ! -d "$PROJECT_DIR" ]; then echo "❌ فشل استنساخ المشروع."; exit 1; fi
cd "$PROJECT_DIR" || exit

# 3. إعداد متغيرات البوت
echo -e "\n[3/8] إعداد متغيرات البوت..."
read -p "الرجاء إدخال توكن البوت: " BOT_TOKEN
if [ -z "$BOT_TOKEN" ]; then echo "❌ لم يتم إدخال التوكن."; exit 1; fi
# استخدام sed لتحديث التوكن في bot.py
sed -i 's/^TOKEN = "YOUR_TELEGRAM_BOT_TOKEN".*/TOKEN = "'"$BOT_TOKEN"'"/' "${PROJECT_DIR}/bot.py"


# 4. **تصحيح وإعادة كتابة سكربت create_ssh_user.sh**
echo -e "\n[4/8] تصحيح سكربت create_ssh_user.sh..."
read -p "الرجاء إدخال عنوان IP الخاص بسيرفرك: " SERVER_IP
if [ -z "$SERVER_IP" ]; then echo "❌ لم يتم إدخال الآي بي."; exit 1; fi

# نقوم بكتابة النسخة الصحيحة من السكربت التي تقبل تاريخ الانتهاء
cat > /usr/local/bin/create_ssh_user.sh << EOL
#!/bin/bash
if [ "\$#" -ne 3 ]; then
    echo "Usage: \$0 <username> <password> <expiry_days>"
    exit 1
fi
USERNAME=\$1
PASSWORD=\$2
EXPIRY_DAYS=\$3
if id "\$USERNAME" &>/dev/null; then
    echo "Error: User '\$USERNAME' already exists."
    exit 1
fi
EXPIRY_DATE=\$(date -d "+\$EXPIRY_DAYS days" +%Y-%m-%d)
useradd "\$USERNAME" -m -e "\$EXPIRY_DATE" -s /bin/bash -p "\$(openssl passwd -1 "\$PASSWORD")"
if [ \$? -eq 0 ]; then
    echo "Host/IP: ${SERVER_IP}"
    echo "Username: \$USERNAME"
    echo "Password: \$PASSWORD"
    echo "Expires on: \$EXPIRY_DATE"
else
    echo "Error: Failed to create user '\$USERNAME'."
    exit 1
fi
exit 0
EOL


# 5. إعطاء صلاحيات التنفيذ
echo -e "\n[5/8] إعطاء صلاحيات التنفيذ للسكربتات..."
chmod +x /usr/local/bin/create_ssh_user.sh


# 6. إعداد بيئة بايثون وتثبيت المكتبات
echo -e "\n[6/8] إعداد بيئة بايثون وتثبيت المكتبات المطلوبة..."
python3 -m venv venv
# تثبيت المكتبات مباشرة لأن ملف requirements.txt غير موجود
(
  source venv/bin/activate
  pip install python-telegram-bot
)


# 7. إعداد البوت كخدمة (systemd)
echo -e "\n[7/8] إعداد البوت كخدمة دائمة..."
cat > /etc/systemd/system/ssh_bot.service << EOL
[Unit]
Description=Telegram SSH Bot Service (Lahcenoum)
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


# 8. تشغيل الخدمة
echo -e "\n[8/8] تشغيل الخدمة..."
systemctl daemon-reload
systemctl enable ssh_bot.service
systemctl start ssh_bot.service

echo -e "\n=================================================="
echo "✅ اكتمل التثبيت بنجاح!"
echo "   تم تحميل مشروعك وتصحيح الملفات اللازمة تلقائياً."
echo "=================================================="
echo -e "\n- لمراقبة حالة البوت: systemctl status ssh_bot.service"
echo "- لإعادة تشغيله: systemctl restart ssh_bot.service"
echo "--------------------------------------------------"
