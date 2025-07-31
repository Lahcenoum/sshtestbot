#!/bin/bash

# =================================================================
#  سكربت لإنشاء مستخدم SSH جديد مع كلمة مرور وتاريخ انتهاء صلاحية
#  (نسخة محسّنة مع معالجة أفضل للأخطاء)
# =================================================================

# التحقق من أن السكربت يعمل بصلاحيات root
if [ "$(id -u)" -ne 0 ]; then
  echo "Error: This script must be run as root."
  exit 1
fi

# التحقق من أن عدد المعاملات (arguments) هو 3
if [ "$#" -ne 3 ]; then
    echo "Error: Incorrect usage."
    echo "Example: $0 <username> <password> <expiry_days>"
    exit 1
fi

# تعيين المتغيرات من المعاملات التي تم تمريرها
USERNAME=$1
PASSWORD=$2
EXPIRY_DAYS=$3

# حساب تاريخ انتهاء الصلاحية
EXPIRY_DATE=$(date -d "+$EXPIRY_DAYS days" +%Y-%m-%d)

# التحقق من وجود المستخدم مسبقًا
if id "$USERNAME" &>/dev/null; then
    echo "Error: User '$USERNAME' already exists."
    exit 1
fi

# --- بدء عملية الإنشاء ---

# 1. إنشاء المستخدم مع مجلده الشخصي وتحديد /bin/bash كـ shell افتراضي
useradd -m -s /bin/bash "$USERNAME"
if [ $? -ne 0 ]; then
    echo "Error: Failed to create the user."
    exit 1
fi

# 2. تعيين كلمة المرور للمستخدم الجديد
echo "$USERNAME:$PASSWORD" | chpasswd
if [ $? -ne 0 ]; then
    echo "Error: Failed to set the password."
    userdel -r "$USERNAME" # حذف المستخدم لتجنب المشاكل
    exit 1
fi

# 3. تعيين تاريخ انتهاء صلاحية الحساب
chage -E "$EXPIRY_DATE" "$USERNAME"
if [ $? -ne 0 ]; then
    echo "Error: Failed to set the expiration date."
    userdel -r "$USERNAME" # حذف المستخدم لتجنب المشاكل
    exit 1
fi

# --- عرض بيانات الحساب (هذه هي المخرجات التي سيقرأها البوت) ---
# الحصول على IP السيرفر
SERVER_IP=$(hostname -I | awk '{print $1}')

echo "Host: $SERVER_IP"
echo "Username: $USERNAME"
echo "Password: $PASSWORD"
echo "Port: 22"
echo "Expires on: $EXPIRY_DATE"

exit 0
