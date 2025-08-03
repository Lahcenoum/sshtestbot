#!/bin/bash

# ========================================================================
# سكريبت التثبيت الكامل - SSH Telegram Bot (by Lahcen)
# ========================================================================

GIT_REPO_URL="https://github.com/Lahcenoum/sshtestbot.git"
PROJECT_DIR="/home/ssh_bot"
LOG_FILE="$PROJECT_DIR/log.txt"

# التحقق من الجذر
if [ "$(id -u)" -ne 0 ]; then
  echo "❌ يجب تشغيل السكربت بصلاحيات root."
  exit 1
fi

echo "=================================================="
echo "   🔧 بدء التثبيت الكامل لبوت SSH"
echo "=================================================="

# 1. تحديث النظام وتثبيت المتطلبات
echo -e "\n[1/9] ✅ تحديث النظام وتثبيت المتطلبات..."
apt-get update
apt-get install -y git python3-venv python3-pip openssl sudo curl

# 2. استنساخ المشروع
echo -e "\n[2/9] ✅ استنساخ المشروع من GitHub..."
rm -rf "$PROJECT_DIR"
git clone "$GIT_REPO_URL" "$PROJECT_DIR"
cd "$PROJECT_DIR" || exit 1
touch "$LOG_FILE"

# 3. إدخال التوكن
echo -e "\n[3/9] ✅ إعداد توكن البوت..."
read -p "📥 أدخل توكن البوت: " BOT_TOKEN
if [ -z "$BOT_TOKEN" ]; then echo "❌ لم يتم إدخال التوكن."; exit 1; fi
sed -i 's|^TOKEN = "YOUR_TELEGRAM_BOT_TOKEN".*|TOKEN = "'"$BOT_TOKEN"'"|' "$PROJECT_DIR/bot.py"

# 4. إعداد سكربت إنشاء المستخدم
echo -e "\n[4/9] ✅ إعداد سكربت إنشاء حسابات SSH..."
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
    echo "Error: User '\$USERNAME' already exists." | tee -a "$LOG_FILE"
    exit 1
fi

EXPIRY_DATE=\$(date -d "+\$EXPIRY_DAYS days" +%Y-%m-%d)
useradd "\$USERNAME" -m -e "\$EXPIRY_DATE" -s /bin/bash
echo "\$USERNAME:\$PASSWORD" | chpasswd

if [ \$? -eq 0 ]; then
    echo -e "[$(date)] ✅ User created: \$USERNAME" >> "$LOG_FILE"
    echo "Host/IP: ${SERVER_IP}"
    echo "Username: \$USERNAME"
    echo "Password: \$PASSWORD"
    echo "Expires on: \$EXPIRY_DATE"
else
    echo "Error: Failed to create user '\$USERNAME'" | tee -a "$LOG_FILE"
    exit 1
fi
exit 0
EOL

chmod +x /usr/local/bin/create_ssh_user.sh

# 5. إعداد بيئة بايثون
echo -e "\n[5/9] ✅ إعداد البيئة الافتراضية..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install python-telegram-bot --break-system-packages
deactivate || true

# 6. إعداد خدمة systemd
echo -e "\n[6/9] ✅ إعداد الخدمة الدائمة systemd..."
cat > /etc/systemd/system/ssh_bot.service << EOL
[Unit]
Description=Telegram SSH Bot Service
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PROJECT_DIR}/venv/bin/python ${PROJECT_DIR}/bot.py
StandardOutput=append:${LOG_FILE}
StandardError=append:${LOG_FILE}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL

# 7. تشغيل الخدمة
echo -e "\n[7/9] ✅ تمكين وتشغيل الخدمة..."
systemctl daemon-reload
systemctl enable ssh_bot.service
systemctl restart ssh_bot.service
sleep 5

# 8. اختبار البوت تلقائيًا
echo -e "\n[8/9] ✅ اختبار تشغيل البوت..."
TEST_MSG="✅ تم تثبيت بوت SSH بنجاح!"
curl -s -X POST https://api.telegram.org/bot$BOT_TOKEN/sendMessage \
     -d chat_id=534428088 \
     -d text="$TEST_MSG" >/dev/null 2>&1

if systemctl is-active --quiet ssh_bot.service; then
  echo "✅ البوت يعمل بشكل صحيح ✅" | tee -a "$LOG_FILE"
else
  echo "❌ فشل في تشغيل البوت. تحقق من log.txt" | tee -a "$LOG_FILE"
fi

# 9. نهاية التثبيت
echo -e "\n[9/9] ✅ تم التثبيت بنجاح!"
echo "=================================================="
echo "📦 ملف السجل: $LOG_FILE"
echo "📌 لمراقبة الخدمة: systemctl status ssh_bot.service"
echo "📌 لمشاهدة السجل: journalctl -u ssh_bot.service -f"
echo "📌 لإعادة التشغيل: systemctl restart ssh_bot.service"
echo "=================================================="
