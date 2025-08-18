#!/bin/bash

# ========================================================================
#  سكريبت التثبيت الشامل - SSH Telegram Bot ولوحة التحكم
# ========================================================================

# --- إعدادات أساسية ---
GIT_REPO_URL="https://github.com/Lahcenoum/sshtestbot.git"
PROJECT_DIR="/home/ssh_bot"
CONNECTION_LIMIT=2

# --- نهاية قسم الإعدادات ---

# التحقق من صلاحيات الجذر
if [ "$(id -u)" -ne 0 ]; then
  echo "❌ يجب تشغيل السكربت بصلاحيات root."
  exit 1
fi

echo "=================================================="
echo "   🔧 بدء التثبيت الكامل للبوت ولوحة التحكم"
echo "=================================================="

# الخطوة 0: حذف أي تثبيت قديم لضمان بداية نظيفة
echo -e "\n[0/11] 🗑️ حذف أي تثبيت قديم..."
systemctl stop ssh_bot.service ssh_bot_dashboard.service >/dev/null 2>&1
systemctl disable ssh_bot.service ssh_bot_dashboard.service >/dev/null 2>&1
rm -f /etc/systemd/system/ssh_bot.service
rm -f /etc/systemd/system/ssh_bot_dashboard.service
rm -rf "$PROJECT_DIR"

# 1. تحديث النظام وتثبيت المتطلبات
echo -e "\n[1/11] 📦 تحديث النظام وتثبيت المتطلبات..."
apt-get update
apt-get install -y git python3-venv python3-pip openssl sudo

# 2. استنساخ المشروع
echo -e "\n[2/11] 📥 استنساخ المشروع من GitHub..."
git clone "$GIT_REPO_URL" "$PROJECT_DIR"
cd "$PROJECT_DIR" || exit 1

# 3. إدخال توكن البوت
echo -e "\n[3/11] 🔑 إعداد توكن البوت..."
read -p "  - أدخل توكن البوت: " BOT_TOKEN
if [ -z "$BOT_TOKEN" ]; then echo "❌ لم يتم إدخال التوكن."; exit 1; fi
# تحديث التوكن في كلا الملفين
sed -i 's/^TOKEN = "YOUR_TELEGRAM_BOT_TOKEN".*/TOKEN = "'"$BOT_TOKEN"'"/' "$PROJECT_DIR/bot.py"
sed -i 's/^TOKEN = "YOUR_TELEGRAM_BOT_TOKEN".*/TOKEN = "'"$BOT_TOKEN"'"/' "$PROJECT_DIR/dashboard.py"
echo "  - ✅ تم تحديث التوكن في ملفات البوت ولوحة التحكم."

# 4. إعداد كلمة مرور لوحة التحكم
echo -e "\n[4/11] 🛡️ إعداد كلمة مرور لوحة التحكم..."
read -p "  - أدخل كلمة مرور للوحة التحكم (اتركها فارغة لاستخدام 'admin'): " DASH_PASSWORD
if [ -z "$DASH_PASSWORD" ]; then DASH_PASSWORD="admin"; fi
sed -i "s/^DASHBOARD_PASSWORD = \"admin\".*/DASHBOARD_PASSWORD = \"$DASH_PASSWORD\"/" "$PROJECT_DIR/dashboard.py"
echo "  - ✅ تم تعيين كلمة مرور لوحة التحكم."

# 5. إعداد سكربت إنشاء المستخدم
echo -e "\n[5/11] 👤 إعداد سكربت إنشاء حسابات SSH..."
read -p "  - أدخل عنوان IP الخاص بسيرفرك: " SERVER_IP
if [ -z "$SERVER_IP" ]; then echo "❌ لم يتم إدخال الآي بي."; exit 1; fi

if [ -f "create_ssh_user.sh" ]; then
    sed -i "s/YOUR_SERVER_IP/${SERVER_IP}/g" "create_ssh_user.sh"
    mv "create_ssh_user.sh" "/usr/local/bin/"
    chmod +x "/usr/local/bin/create_ssh_user.sh"
    echo "  - ✅ تم نقل وإعداد 'create_ssh_user.sh' بنجاح."
else
    echo "  - ⚠️ تحذير: لم يتم العثور على 'create_ssh_user.sh'."
fi

# 6. إعداد سكربت الحذف التلقائي
echo -e "\n[6/11] ⏳ إعداد سكربت الحذف التلقائي للمستخدمين..."
if [ -f "delete_expired_users.sh" ]; then
    mv "delete_expired_users.sh" "/usr/local/bin/"
    chmod +x "/usr/local/bin/delete_expired_users.sh"
    (crontab -l 2>/dev/null | grep -v -F "/usr/local/bin/delete_expired_users.sh" ; echo "0 0 * * * /usr/local/bin/delete_expired_users.sh") | crontab -
    echo "  - ✅ تم إعداد مهمة حذف الحسابات منتهية الصلاحية بنجاح."
else
    echo "  - ⚠️ تحذير: لم يتم العثور على ملف 'delete_expired_users.sh'."
fi

# 7. إعداد سكربت مراقبة الاتصالات
echo -e "\n[7/11] 🔗 إعداد سكربت مراقبة الاتصالات المتعددة..."
if [ -f "monitor_connections.sh" ]; then
    sed -i "s/CONNECTION_LIMIT=[0-9]\+/CONNECTION_LIMIT=$CONNECTION_LIMIT/" "monitor_connections.sh"
    mv "monitor_connections.sh" "/usr/local/bin/"
    chmod +x "/usr/local/bin/monitor_connections.sh"
    (crontab -l 2>/dev/null | grep -v -F "/usr/local/bin/monitor_connections.sh" ; echo "*/5 * * * * /usr/local/bin/monitor_connections.sh") | crontab -
    echo "  - ✅ تم إعداد مهمة مراقبة الاتصالات بنجاح."
else
    echo "  - ⚠️ تحذير: لم يتم العثور على ملف 'monitor_connections.sh'."
fi

# 8. إعداد بيئة بايثون
echo -e "\n[8/11] 🐍 إعداد البيئة الافتراضية وتثبيت المكتبات..."
python3 -m venv venv
(
  source venv/bin/activate
  pip install --upgrade pip
  if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "  - ✅ تم تثبيت المكتبات من requirements.txt."
  else
    pip install python-telegram-bot flask
    echo "  - ⚠️ لم يتم العثور على requirements.txt، تم تثبيت المكتبات الأساسية."
  fi
)

# 9. إعداد خدمات systemd
echo -e "\n[9/11] ⚙️ إعداد الخدمات الدائمة (systemd)..."
# --- خدمة البوت ---
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

# --- خدمة لوحة التحكم ---
cat > /etc/systemd/system/ssh_bot_dashboard.service << EOL
[Unit]
Description=Telegram SSH Bot Dashboard
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PROJECT_DIR}/venv/bin/python ${PROJECT_DIR}/dashboard.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL
echo "  - ✅ تم إنشاء ملفات الخدمات بنجاح."

# 10. تشغيل الخدمات
echo -e "\n[10/11] 🚀 تمكين وتشغيل الخدمات..."
systemctl daemon-reload
systemctl enable ssh_bot.service ssh_bot_dashboard.service
systemctl restart ssh_bot.service ssh_bot_dashboard.service

# 11. نهاية التثبيت
echo -e "\n[11/11] 🎉 تم التثبيت بنجاح!"
echo "=================================================="
echo "  - 🤖 لمراقبة البوت: systemctl status ssh_bot.service"
echo "  - 📊 لمراقبة لوحة التحكم: systemctl status ssh_bot_dashboard.service"
echo "  - 🌐 رابط لوحة التحكم: http://${SERVER_IP}:5000"
echo "=================================================="
