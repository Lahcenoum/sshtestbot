#!/bin/bash

# التحقق من عدد الوسائط
if [ $# -ne 3 ]; then
  echo "❌ استخدام غير صحيح: create_ssh_user.sh <اسم_المستخدم> <كلمة_المرور> <مدة_الصلاحية_بالأيام>"
  exit 1
fi

USERNAME="$1"
PASSWORD="$2"
EXPIRY_DAYS="$3"

# التحقق من وجود المستخدم مسبقًا
if id "$USERNAME" &>/dev/null; then
  echo "❌ المستخدم '$USERNAME' موجود مسبقًا. لا يمكن تكرار الحساب."
  exit 1
fi

# إنشاء المستخدم بدون مجلد home، shell مقفل، وصلاحية مؤقتة
useradd -e "$(date -d "+$EXPIRY_DAYS days" +%Y-%m-%d)" -M -s /usr/sbin/nologin "$USERNAME"

# تعيين كلمة المرور
echo -e "$PASSWORD\n$PASSWORD" | passwd "$USERNAME" &>/dev/null

# جلب عنوان IP العام
IP=$(curl -s ifconfig.me || echo "IP-غير-معروف")
PORT=22
EXP_DATE=$(chage -l "$USERNAME" | grep "Account expires" | cut -d: -f2 | xargs)

# طباعة بيانات الحساب
echo "📄 معلومات الحساب:"
echo "👤 المستخدم: $USERNAME"
echo "🔑 كلمة المرور: $PASSWORD"
echo "📡 الهوست: $IP"
echo "🚪 المنفذ: $PORT"
echo "📅 الانتهاء: $EXP_DATE"
