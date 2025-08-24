# -*- coding: utf-8 -*-

# ========================================================================
#         ملف dash.py بعد تصحيح خطأ SyntaxError
# ========================================================================

# تعريف متغير الرسالة كنص متعدد الأسطر باستخدام ثلاث علامات اقتباس
# هذا هو التصحيح الرئيسي للمشكلة
MAINTENANCE_MESSAGE = """
**إشعار صيانة وتحديث | Maintenance & Update Notice**

**بالعربية:**
مرحباً، سيتم إيقاف البوت مؤقتاً لإجراء تحديثات وإصلاحات.
للاشتراك في السيرفرات المدفوعة بسعر **2 دولار**، يرجى الانضمام إلى قناتنا والتواصل مع الأدمن من هناك:
https://t.me/CLOUDVIP

**English:**
Hello, the bot will be temporarily down for maintenance and bug fixes.
To subscribe to our premium servers for **$2**, please join our channel and contact the admin there:
https://t.me/CLOUDVIP
"""

# --- مثال لكيفية استخدام المتغير ---

def send_broadcast_message():
    """
    دالة وهمية لطباعة الرسالة لإظهار أن المتغير يعمل بشكل صحيح.
    يمكنك استبدال هذا الجزء بالكود الفعلي الخاص بك لإرسال الرسالة.
    """
    print("--- سيتم إرسال الرسالة التالية ---")
    print(MAINTENANCE_MESSAGE)
    print("---------------------------------")
    # هنا تضع الكود الخاص بك لإرسال الرسالة للمستخدمين
    # مثلاً: bot.send_message(chat_id=user_id, text=MAINTENANCE_MESSAGE)


# --- نقطة بداية البرنامج ---
if __name__ == "__main__":
    # استدعاء الدالة كمثال
    print("بدء تشغيل السكربت...")
    send_broadcast_message()
    print("اكتمل السكربت بنجاح.")

