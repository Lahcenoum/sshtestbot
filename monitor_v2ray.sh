#!/bin/bash
# ========================================================================
#  سكريبت لمراقبة اتصالات V2Ray وحذف المستخدمين الذين يتجاوزون الحد
# ========================================================================

# ===================== الإعدادات =====================
# الحد الأقصى للاتصالات (عدد عناوين IP المختلفة) المسموح بها لكل مستخدم
CONNECTION_LIMIT=1

# المسار الكامل لملف إعدادات Xray/V2Ray
V2RAY_CONFIG="/usr/local/etc/xray/config.json"
# المسار الكامل لملف سجلات الوصول
V2RAY_LOG="/var/log/xray/access.log"
# ملف لتسجيل عمليات الحذف
DELETION_LOG="/var/log/xray/deletions.log"
# ====================================================

# دالة لكتابة سجلات
log_action() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$DELETION_LOG"
}

# التحقق من وجود ملف السجل
if [ ! -f "$V2RAY_LOG" ]; then
    log_action "خطأ: ملف السجل $V2RAY_LOG غير موجود. تأكد من تفعيله في إعدادات Xray."
    exit 1
fi

# استخراج معرفات المستخدمين (UUIDs) المخالفين
# يبحث في سجلات الدقيقتين الأخيرتين ويعدّ عدد الـ IPs الفريدة لكل UUID
EXCEEDED_USERS=$(tail -n 5000 "$V2RAY_LOG" | \
    grep "accepted" | \
    awk -v time_limit=$(date -d '2 minutes ago' +%s) '
    {
        # Extract IP and UUID
        ip = ""; uuid = "";
        for (i=1; i<=NF; i++) {
            if ($i == "email:") {
                uuid = $(i+1);
            }
            if (match($i, /^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/)) {
                ip = $i;
                sub(/:[0-9]+$/, "", ip);
            }
        }
        
        # Extract timestamp and check if it is within the last 2 minutes
        gsub(/"/, "", $1);
        gsub(/\[|\]/, "", $2);
        split($2, dt, ":");
        event_time_str = dt[1]" "dt[2]":"dt[3]":"dt[4];
        cmd = "date -d \"" event_time_str "\" +%s";
        cmd | getline event_time;
        close(cmd);

        if (event_time > time_limit && uuid != "" && ip != "") {
            print uuid, ip
        }
    }' | \
    sort | uniq | \
    awk '{ count[$1]++ } END { for (user in count) if (count[user] > '"$CONNECTION_LIMIT"') print user }')


# إذا لم يكن هناك مستخدمون مخالفون، قم بالخروج
if [ -z "$EXCEEDED_USERS" ]; then
    exit 0
fi

CONFIG_CHANGED=false

# المرور على كل مستخدم مخالف وحذفه
for USER_ID in $EXCEEDED_USERS; do
    # التأكد من أن المستخدم لا يزال موجوداً في الملف قبل محاولة حذفه
    if jq -e '(.inbounds[] | select(.protocol == "vless") .settings.clients[] | select(.id == "'$USER_ID'"))' "$V2RAY_CONFIG" > /dev/null; then
        log_action "تنبيه: المستخدم $USER_ID تجاوز الحد المسموح به ($CONNECTION_LIMIT). يتم الآن حذفه."
        
        # استخدام jq لحذف المستخدم من الملف
        jq '(.inbounds[] | select(.protocol == "vless") .settings.clients) |= map(select(.id != "'$USER_ID'"))' "$V2RAY_CONFIG" > "${V2RAY_CONFIG}.tmp" && mv "${V2RAY_CONFIG}.tmp" "$V2RAY_CONFIG"
        
        CONFIG_CHANGED=true
    fi
done

# إذا تم إجراء تغييرات، أعد تشغيل Xray
if [ "$CONFIG_CHANGED" = true ]; then
    log_action "تم حذف مستخدم واحد أو أكثر. إعادة تشغيل Xray..."
    if systemctl restart xray; then
        log_action "تمت إعادة تشغيل Xray بنجاح."
    else
        log_action "فشل في إعادة تشغيل Xray."
    fi
fi

exit 0
