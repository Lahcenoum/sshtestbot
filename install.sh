#!/bin/bash

# ========================================================================
# سكريبت التثبيت الكامل والنهائي - SSH Telegram Bot
# - يحل مشكلة البيئة الافتراضية (PEP 668)
# - يضمن تشغيل المشروع بشكل صحيح ومعزول
# ========================================================================

# --- إعدادات أساسية ---
GIT_REPO_URL="https://github.com/Lahcenoum/sshtestbot.git"
PROJECT_DIR="/home/ssh_bot"

# --- نهاية قسم الإعدادات ---

# التحقق من صلاحيات الجذر
if [ "$(id -u)" -ne 0 ]; then
  echo "❌ يجب تشغيل السكربت بصلاحيات root."
  exit 1
fi

echo "=================================================="
echo "   🔧 بدء التثبيت الكامل لبوت SSH"
echo "=================================================="

# الخطوة 0: حذف أي تثبيت قديم لضمان بداية نظيفة
echo -e "\n[0/8] ✅ حذف أي تثبيت قديم..."
sudo systemctl stop ssh_bot.service >/dev/null 2>&1
sudo rm -rf "$PROJECT_DIR"

# 1. تحديث النظام وتثبيت المتطلبات
echo -e "\n[1/8] ✅ تحديث النظام وتثبيت المتطلبات..."
apt-get update
apt-get install -y git python3-venv python3-pip openssl sudo

# 2. استنساخ المشروع
echo -e "\n[2/8] ✅ استنساخ المشروع من GitHub..."
git clone "$GIT_REPO_URL" "$PROJECT_DIR"
cd "$PROJECT_DIR" || exit 1

# 3. إدخال التوكن
echo -e "\n[3/8] ✅ إعداد توكن البوت..."
read -p "📥 أدخل توكن البوت: " BOT_TOKEN
if [ -z "$BOT_TOKEN" ]; then echo "❌ لم يتم إدخال التوكن."; exit 1; fi
# استخدام sed لتحديث التوكن في bot.py
sed -i 's/^TOKEN = "YOUR_TELEGRAM_BOT_TOKEN".*/TOKEN = "'"$BOT_TOKEN"'"/' "$PROJECT_DIR/bot.py"

# 4. إعداد سكربت إنشاء المستخدم
echo -e "\n[4/8] ✅ إعداد سكربت إنشاء حسابات SSH..."
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
echo -e "\n[5/8] ✅ إعداد البيئة الافتراضية وتثبيت المكتبات..."
python3 -m venv venv
# --- بداية الحل ---
# هذا الجزء هو الذي يحل مشكلة PEP 668 بشكل نهائي
(
  source venv/bin/activate
  pip install --upgrade pip
  pip install python-telegram-bot
)
# --- نهاية الحل ---

# 6. إعداد خدمة systemd
echo -e "\n[6/8] ✅ إعداد الخدمة الدائمة systemd..."
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
echo -e "\n[7/8] ✅ تمكين وتشغيل الخدمة..."
systemctl daemon-reload
systemctl enable ssh_bot.service
systemctl restart ssh_bot.service

# 8. نهاية التثبيت
echo -e "\n[8/8] ✅ تم التثبيت بنجاح!"
echo "=================================================="
echo "📌 لمراقبة الخدمة: systemctl status ssh_bot.service"
echo "📌 لإعادة التشغيل: systemctl restart ssh_bot.service"
echo "=================================================="
