#!/bin/bash

# ========================================================================
# سكريبت التثبيت النهائي والمصحح
# ========================================================================

GIT_REPO_URL="https://github.com/Lahcenoum/sshtestbot.git"
PROJECT_DIR="/home/ssh_bot"

# التحقق من الجذر
if [ "$(id -u)" -ne 0 ]; then
  echo "❌ يجب تشغيل السكربت بصلاحيات root."
  exit 1
fi

echo "=================================================="
echo "   🔧 بدء التثبيت الكامل لبوت SSH"
echo "=================================================="

# 1. تحديث وتثبيت المتطلبات
echo -e "\n[1/7] ✅ تحديث النظام وتثبيت المتطلبات..."
apt-get update
apt-get install -y git python3-venv python3-pip openssl sudo

# 2. استنساخ المشروع
echo -e "\n[2/7] ✅ استنساخ المشروع من GitHub..."
git clone "$GIT_REPO_URL" "$PROJECT_DIR"
cd "$PROJECT_DIR" || exit 1

# 3. إدخال التوكن
echo -e "\n[3/7] ✅ إعداد توكن البوت..."
read -p "📥 أدخل توكن البوت: " BOT_TOKEN
if [ -z "$BOT_TOKEN" ]; then echo "❌ لم يتم إدخال التوكن."; exit 1; fi
# استخدام sed لتحديث التوكن في bot.py
sed -i 's/^TOKEN = "YOUR_TELEGRAM_BOT_TOKEN".*/TOKEN = "'"$BOT_TOKEN"'"/' "$PROJECT_DIR/bot.py"

# 4. إعداد سكربت إنشاء المستخدم
echo -e "\n[4/7] ✅ إعداد سكربت إنشاء حسابات SSH..."
read -p "📥 أدخل عنوان IP الخاص بسيرفرك: " SERVER_IP
if [ -z "$SERVER_IP" ]; then echo "❌ لم يتم إدخال الآي بي."; exit 1; fi

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
chmod +x /usr/local/bin/create_ssh_user.sh

# 5. إعداد بيئة بايثون (الطريقة الصحيحة التي تحل المشكلة)
echo -e "\n[5/7] ✅ إعداد البيئة الافتراضية وتثبيت المكتبات..."
python3 -m venv venv
# --- بداية الحل ---
# هذا الجزء هو الذي يحل المشكلة بشكل نهائي
(
  source venv/bin/activate
  pip install --upgrade pip
  pip install python-telegram-bot
)
# --- نهاية الحل ---

# 6. إعداد خدمة systemd
echo -e "\n[6/7] ✅ إعداد الخدمة الدائمة systemd..."
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
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL

# 7. تشغيل الخدمة
echo -e "\n[7/7] ✅ تمكين وتشغيل الخدمة..."
systemctl daemon-reload
systemctl enable ssh_bot.service
systemctl restart ssh_bot.service

echo -e "\n=================================================="
echo "✅ تم التثبيت بنجاح!"
echo "📌 لمراقبة الخدمة: systemctl status ssh_bot.service"
echo "=================================================="
