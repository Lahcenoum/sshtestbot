#!/bin/bash

# ==============================================================================
#  Script to create a temporary SSH user on a Linux system.
#  It accepts username, password, and expiry days as arguments.
# ==============================================================================

# --- التحقق من المدخلات ---
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <username> <password> <expiry_days>"
    exit 1
fi

# --- تعيين المتغيرات من الوسائط ---
USERNAME=$1
PASSWORD=$2
EXPIRY_DAYS=$3

# --- التحقق مما إذا كان المستخدم موجودًا بالفعل ---
if id "$USERNAME" &>/dev/null; then
    echo "Error: User '$USERNAME' already exists."
    exit 1
fi

# --- حساب تاريخ انتهاء الصلاحية ---
# يستخدم أمر `date` لإنشاء التاريخ بالتنسيق YYYY-MM-DD
EXPIRY_DATE=$(date -d "+$EXPIRY_DAYS days" +%Y-%m-%d)

# --- إنشاء المستخدم ---
# يستخدم `openssl passwd` لتشفير كلمة المرور قبل إضافتها
# -m : يقوم بإنشاء المجلد الرئيسي للمستخدم
# -e : يحدد تاريخ انتهاء صلاحية الحساب
# -s : يحدد الشل الافتراضي (bash)
useradd "$USERNAME" -m -e "$EXPIRY_DATE" -s /bin/bash -p "$(openssl passwd -1 "$PASSWORD")"

# --- التحقق من نجاح عملية الإنشاء ---
if [ $? -eq 0 ]; then
    # --- إخراج تفاصيل الحساب لكي يلتقطها البوت ---
    # استبدل "YOUR_SERVER_IP" بالآي بي الفعلي لسيرفرك
    echo "Host/IP: YOUR_SERVER_IP"
    echo "Username: $USERNAME"
    echo "Password: $PASSWORD"
    echo "Expires on: $EXPIRY_DATE"
else
    echo "Error: Failed to create user '$USERNAME'."
    exit 1
fi

exit 0
