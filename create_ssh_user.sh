#!/bin/bash

# =================================================================
#  سكربت لإنشاء مستخدم SSH جديد مع كلمة مرور وتاريخ انتهاء صلاحية
# =================================================================

# التحقق من أن عدد المعاملات (arguments) هو 3
if [ "$#" -ne 3 ]; then
    echo "خطأ: طريقة الاستخدام غير صحيحة."
    echo "مثال: $0 <username> <password> <expiry_days>"
    exit 1
fi

# تعيين المتغيرات من المعاملات التي تم تمريرها
USERNAME=$1
PASSWORD=$2
EXPIRY_DAYS=$3

# حساب تاريخ انتهاء الصلاحية
# سيتم تحويل عدد الأيام إلى تاريخ بصيغة YYYY-MM-DD
EXPIRY_DATE=$(date -d "+$EXPIRY_DAYS days" +%Y-%m-%d)

# التحقق من وجود المستخدم مسبقًا
if id "$USERNAME" &>/dev/null; then
    echo "خطأ: المستخدم '$USERNAME' موجود بالفعل."
    exit 1
fi

# --- بدء عملية الإنشاء ---

# 1. إنشاء المستخدم مع مجلده الشخصي (/home/username)
useradd -m "$USERNAME"
if [ $? -ne 0 ]; then
    echo "فشل إنشاء المستخدم."
    exit 1
fi

# 2. تعيين كلمة المرور للمستخدم الجديد
echo "$USERNAME:$PASSWORD" | chpasswd
if [ $? -ne 0 ]; then
    echo "فشل تعيين كلمة المرور."
    # حذف المستخدم الذي تم إنشاؤه للتو لتجنب المشاكل
    userdel -r "$USERNAME"
    exit 1
fi

# 3. تعيين تاريخ انتهاء صلاحية الحساب
chage -E "$EXPIRY_DATE" "$USERNAME"
if [ $? -ne 0 ]; then
    echo "فشل تعيين تاريخ انتهاء الصلاحية."
    userdel -r "$USERNAME"
    exit 1
fi

# --- عرض بيانات الحساب (هذه هي المخرجات التي سيقرأها البوت) ---
# يمكنك تعديل هذه المخرجات لتناسبك
echo "Host: $(hostname -I | awk '{print $1}')"
echo "Username: $USERNAME"
echo "Password: $PASSWORD"
echo "Port: 22"
echo "Expires on: $EXPIRY_DATE"

exit 0