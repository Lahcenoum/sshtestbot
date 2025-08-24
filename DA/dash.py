#!/bin/bash

# ========================================================================
#         السكريبت الشامل للصيانة والنسخ الاحتياطي
# ========================================================================

# --- [!] إعدادات مهمة ---
# معرف القناة الخاصة بالنسخ الاحتياطي (يجب أن يبدأ بـ -100)
BACKUP_CHANNEL_ID="-1001002902787778"

# المسار الكامل لملف قاعدة البيانات
DB_PATH="/home/ssh_bot/ssh_bot_users.db"
BOT_FILE_PATH="/home/ssh_bot/bot.py"

# --- نهاية قسم الإعدادات ---


# --- لا تقم بتعديل أي شيء بعد هذا السطر ---

# --- دوال الألوان ---
red() { echo -e "\e[31m$*\e[0m"; }
green() { echo -e "\e[32m$*\e[0m"; }
yellow() { echo -e "\e[33m$*\e[0m"; }

# التحقق من صلاحيات الجذر
if [ "$(id -u)" -ne 0 ]; then
    red "[-] يجب تشغيل السكربت بصلاحيات root."
    exit 1
fi

# --- الحصول على توكن البوت تلقائيًا ---
echo ">> جاري قراءة توكن البوت من الملف..."
BOT_TOKEN=$(grep '^TOKEN =' "$BOT_FILE_PATH" | cut -d '"' -f 2)

if [ -z "$BOT_TOKEN" ] || [[ "$BOT_TOKEN" == "YOUR_TELEGRAM_BOT_TOKEN" ]]; then
    red "[-] خطأ: لم يتم العثور على توكن صالح في ملف bot.py."
    red "   يرجى التأكد من تشغيل سكربت التثبيت وإدخال التوكن أولاً."
    exit 1
fi
green "  - [+] تم العثور على التوكن بنجاح."


# --- 1. إرسال رسالة الإذاعة ---

# تعريف الرسالة
MAINTENANCE_MESSAGE=$(cat <<'END_MESSAGE'
**إشعار صيانة وتحديث | Maintenance & Update Notice**

**بالعربية:**
مرحباً، سيتم إيقاف البوت مؤقتاً لإجراء تحديثات وإصلاحات.
للاشتراك في السيرفرات المدفوعة بسعر **2 دولار**، يرجى الانضمام إلى قناتنا والتواصل مع الأدمن من هناك:
https://t.me/CLOUDVIP

**English:**
Hello, the bot will be temporarily down for maintenance and bug fixes.
To subscribe to our premium servers for **$2**, please join our channel and contact the admin there:
https://t.me/CLOUDVIP
END_MESSAGE
)

echo ">> بدء إرسال رسالة الصيانة للمستخدمين..."

# الحصول على قائمة المستخدمين من قاعدة البيانات
USER_IDS=$(sqlite3 "$DB_PATH" "SELECT telegram_user_id FROM users;")

SUCCESS_COUNT=0
FAIL_COUNT=0

for user_id in $USER_IDS; do
    # إرسال الرسالة باستخدام cURL
    response=$(curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
    -d "chat_id=$user_id" \
    -d "text=$MAINTENANCE_MESSAGE" \
    -d "parse_mode=Markdown")

    if [[ $(echo "$response" | grep '"ok":true') ]]; then
        ((SUCCESS_COUNT++))
    else
        ((FAIL_COUNT++))
    fi
    sleep 0.1 # لتجنب إغراق واجهة تليجرام
done

green "[+] اكتملت الإذاعة: نجح الإرسال لـ $SUCCESS_COUNT مستخدم، وفشل لـ $FAIL_COUNT."

---

# --- 2. إنشاء وإرسال النسخة الاحتياطية ---

echo -e "\n>> بدء عملية النسخ الاحتياطي لقاعدة البيانات..."

if [ ! -f "$DB_PATH" ]; then
    red "[-] خطأ: لم يتم العثور على ملف قاعدة البيانات في المسار المحدد."
    exit 1
fi

# إنشاء نسخة مؤقتة
BACKUP_FILE="/tmp/db_backup_$(date +%F_%H-%M-%S).db"
cp "$DB_PATH" "$BACKUP_FILE"
green "  - تم إنشاء نسخة احتياطية مؤقتة."

# إرسال الملف إلى القناة
CAPTION="نسخة احتياطية لقاعدة البيانات - $(date)"
echo "  - >> جاري إرسال الملف إلى القناة..."
curl -s -F "chat_id=${BACKUP_CHANNEL_ID}" -F "document=@${BACKUP_FILE}" -F "caption=${CAPTION}" "https://api.telegram.org/bot${BOT_TOKEN}/sendDocument" > /dev/null

# حذف الملف المؤقت
rm "$BACKUP_FILE"
green "  - [+] تم إرسال النسخة الاحتياطية بنجاح."

echo -e "\n=========================================="
green "[+] اكتملت جميع المهام بنجاح!"
echo "=========================================="

exit 0
