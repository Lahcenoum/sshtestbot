#!/bin/bash

# ==============================================================================
#  سكربت التثبيت من مستودع GitHub
# ==============================================================================

# --- إعدادات أساسية ---
# ⚠️ غيّر هذا الرابط إلى رابط المستودع الخاص بك على GitHub
GIT_REPO_URL="https://github.com/username/your-repo.git"
PROJECT_DIR="/home/ssh_bot"

# --- نهاية قسم الإعدادات ---

# التحقق من صلاحيات الجذر
if [ "$(id -u)" -ne 0 ]; then
  echo "❌ هذا السكربت يجب أن يعمل بصلاحيات الجذر (root)."
  exit 1
fi

echo "=================================================="
echo "      بدء عملية تثبيت البوت من GitHub"
echo "=================================================="

# 1. تحديث وتثبيت المتطلبات الأساسية
echo -e "\n[1/7] تحديث النظام وتثبيت المتطلبات (git, python3-venv, python3-pip)..."
apt-get update
apt-get install -y git python3-venv python3-pip

# 2. استنساخ المشروع من GitHub
echo -e "\n[2/7] استنساخ المشروع من GitHub..."
# إزالة المجلد القديم إذا كان موجودًا لضمان نسخة نظيفة
rm -rf "$PROJECT_DIR"
git clone "$GIT_REPO_URL" "$PROJECT_DIR"

if [ ! -d "$PROJECT_DIR" ] || [ ! -f "$PROJECT_DIR/bot.py" ]; then
    echo "❌ فشل استنساخ المشروع. تحقق من رابط المستودع."
    exit 1
fi
cd "$PROJECT_DIR" || exit

# 3. إعداد متغيرات البوت
echo -e "\n[3/7] إعداد متغيرات البوت..."
read -p "الرجاء إدخال توكن البوت: " BOT_TOKEN
read -p "الرجاء إدخال عنوان IP الخاص بسيرفرك: " SERVER_IP

if [ -z "$BOT_TOKEN" ] || [ -z "$SERVER_IP" ]; then
    echo "❌ لم يتم إدخال التوكن أو الآي بي. سيتوقف التثبيت."
    exit 1
fi

# استبدال القيم النائبة في الملفات
sed -i "s|YOUR_TELEGRAM_BOT_TOKEN|${BOT_TOKEN}|" "${PROJECT_DIR}/bot.py"
sed -i "s|YOUR_SERVER_IP|${SERVER_IP}|" "${PROJECT_DIR}/create_ssh_user.sh"

# 4. نقل سكريبت الإنشاء وإعطاء الصلاحيات
echo -e "\n[4/7] نقل السكريبتات وإعطاء الصلاحيات..."
mv "${PROJECT_DIR}/create_ssh_user.sh" /usr/local/bin/
chmod +x /usr/local/bin/create_ssh_user.sh

# 5. إعداد بيئة بايثون وتثبيت المكتبات
echo -e "\n[5/7] إعداد بيئة بايثون وتثبيت المكتبات من requirements.txt..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate

# 6. إعداد البوت كخدمة (systemd)
echo -e "\n[6/7] إعداد البوت كخدمة دائمة..."
cat > /etc/systemd/system/ssh_bot.service << EOL
[Unit]
Description=Telegram SSH Bot Service (GitHub)
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

# 7. تشغيل الخدمة
echo -e "\n[7/7] تشغيل الخدمة..."
systemctl daemon-reload
systemctl enable ssh_bot.service
systemctl start ssh_bot.service

echo -e "\n=================================================="
echo "✅ اكتمل التثبيت بنجاح!"
echo "=================================================="
echo -e "\n- لمراقبة حالة البوت: systemctl status ssh_bot.service"
echo "- لإعادة تشغيله: systemctl restart ssh_bot.service"
echo "--------------------------------------------------"
