#!/bin/bash

# =================================================================
#  سكربت لإنشاء مستخدم SSH جديد مع كلمة مرور وتاريخ انتهاء صلاحية
#  (نسخة نهائية مع مسارات كاملة لضمان التوافق مع systemd)
# =================================================================

# التحقق من أن السكربت يعمل بصلاحيات root
if [ "$(/usr/bin/id -u)" -ne 0 ]; then
  echo "Error: This script must be run as root."
  exit 1
fi

# التحقق من أن عدد المعاملات (arguments) هو 3
if [ "$#" -ne 3 ]; then
    echo "Error: Incorrect usage."
    echo "Example: $0 <username> <password> <expiry_days>"
    exit 1
fi

# تعيين المتغيرات
USERNAME=$1
PASSWORD=$2
EXPIRY_DAYS=$3

# حساب تاريخ انتهاء الصلاحية
EXPIRY_DATE=$(/usr/bin/date -d "+$EXPIRY_DAYS days" +%Y-%m-%d)

# التحقق من وجود المستخدم مسبقًا
if /usr/bin/id "$USERNAME" &>/dev/null; then
    echo "Error: User '$USERNAME' already exists."
    exit 1
fi

# --- بدء عملية الإنشاء ---

# 1. إنشاء المستخدم
/usr/sbin/useradd -m -s /bin/bash "$USERNAME"
if [ $? -ne 0 ]; then
    echo "Error: Failed to create the user."
    exit 1
fi

# 2. تعيين كلمة المرور
echo "$USERNAME:$PASSWORD" | /usr/sbin/chpasswd
if [ $? -ne 0 ]; then
    echo "Error: Failed to set the password."
    /usr/sbin/userdel -r "$USERNAME"
    exit 1
fi

# 3. تعيين تاريخ انتهاء الصلاحية
/usr/bin/chage -E "$EXPIRY_DATE" "$USERNAME"
if [ $? -ne 0 ]; then
    echo "Error: Failed to set the expiration date."
    /usr/sbin/userdel -r "$USERNAME"
    exit 1
fi

# --- عرض بيانات الحساب ---
SERVER_IP=$(/usr/bin/hostname -I | /usr/bin/awk '{print $1}')

echo "Host: $SERVER_IP"
echo "Username: $USERNAME"
echo "Password: $PASSWORD"
echo "Port: 22"
echo "Expires on: $EXPIRY_DATE"

exit 0
