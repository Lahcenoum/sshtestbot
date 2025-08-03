#!/bin/bash

# إعدادات
GIT_REPO_URL="https://github.com/Lahcenoum/sshtestbot.git"
PROJECT_DIR="/home/ssh_bot"
CREATE_SSH_SCRIPT="/usr/local/bin/create_ssh_user.sh"
BOT_USER=$(logname)

# تأكد من صلاحيات root
if [ "$(id -u)" -ne 0 ]; then
  echo "❌ يجب تشغيل السكربت كـ root."
  exit 1
fi

echo "✅ بدء التثبيت..."

# 1. تثبيت المتطلبات
apt-get update && apt-get install -y git python3-venv python3-pip curl

# 2. استنساخ المشروع
rm -rf "$PROJECT_DIR"
git clone "$GIT_REPO_URL" "$PROJECT_DIR" || { echo "❌ فشل في الاستنساخ."; exit 1; }

# 3. إدخال التوكن
read -p "🤖 أدخل توكن البوت: " BOT_TOKEN
[ -z "$BOT_TOKEN" ] && echo "❌ التوكن فارغ." && exit 1
sed -i 's|^TOKEN = "YOUR_TELEGRAM_BOT_TOKEN".*|TOKEN = "'"$BOT_TOKEN"'"|' "$PROJECT_DIR/bot.py"

# 4. إنشاء سكربت SSH
read -p "📡 أدخل IP السيرفر (أو اتركه فارغًا): " SERVER_IP

cat > "$CREATE_SSH_SCRIPT" << EOL
#!/bin/bash
if [ \$# -ne 3 ]; then echo "❌ استخدام غير صحيح."; exit 1; fi
USERNAME="\$1"; PASSWORD="\$2"; EXPIRY_DAYS="\$3"
if id "\$USERNAME" &>/dev/null; then echo "❌ المستخدم موجود."; exit 1; fi
useradd -e \$(date -d "+\$EXPIRY_DAYS days" +%Y-%m-%d) -M -s /usr/sbin/nologin "\$USERNAME"
echo -e "\$PASSWORD\n\$PASSWORD" | passwd "\$USERNAME" &>/dev/null
IP="${SERVER_IP}"; [ -z "\$IP" ] && IP=\$(curl -s ifconfig.me)
PORT=22
EXP_DATE=\$(chage -l "\$USERNAME" | grep "Account expires" | cut -d: -f2 | xargs)
echo "📄 معلومات الحساب:"
echo "👤 المستخدم: \$USERNAME"
echo "🔑 كلمة المرور: \$PASSWORD"
echo "📡 الهوست: \$IP"
echo "🚪 المنفذ: \$PORT"
echo "📅 الانتهاء: \$EXP_DATE"
EOL

chmod +x "$CREATE_SSH_SCRIPT"
echo "$BOT_USER ALL=(ALL) NOPASSWD: $CREATE_SSH_SCRIPT" > /etc/sudoers.d/ssh_bot
chmod 440 /etc/sudoers.d/ssh_bot

# 5. إنشاء البيئة الافتراضية وتثبيت المكتبات داخلها
cd "$PROJECT_DIR" || exit 1
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install python-telegram-bot
deactivate

# 6. إنشاء خدمة systemd تعمل ببيئة venv
cat > /etc/systemd/system/ssh_bot.service << EOL
[Unit]
Description=Telegram SSH Bot
After=network.target

[Service]
Type=simple
User=$BOT_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL

# 7. تفعيل الخدمة
systemctl daemon-reload
systemctl enable ssh_bot.service
systemctl restart ssh_bot.service

echo "✅ تم التثبيت بنجاح!"
echo "📌 راقب البوت عبر: journalctl -u ssh_bot.service -f"
