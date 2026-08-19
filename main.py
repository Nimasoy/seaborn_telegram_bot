import datetime
import time
import requests

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
BOT_TOKEN = "8500561345:AAEeD7hW8lcauqm5BMdUouF6BHcvYFTS55Y"
CHAT_ID = "-5517519729"

# Target: August 22, 2026 at 00:00:00 Iran Time (UTC+3:30)
# Converted to UTC: August 21, 2026 at 20:30:00 UTC
TARGET_TIME_UTC = datetime.datetime(
    2026, 8, 21, 20, 30, 0, tzinfo=datetime.timezone.utc
)

# 10:00 AM Iran Time = 06:30 AM UTC
TARGET_UTC_HOUR = 6
TARGET_UTC_MINUTE = 30

DAILY_QUOTES = [
    "گەشەکردن لەو شوێنەوە دەست پێدەکات کە ناوچەی ئارامیت تەواو دەبێت. 🌱",
    "هەر هەنگاوێکی بچووک ئەمڕۆ، دەبێتە سەرکەوتنێکی گەورەی بەیانی. 🚀",
    "تەواوی تواناکانت لە بیرۆکەکانتدا شاراوەن، تەنها بڕوایان پێ بهێنە. ✨",
    "سەرکەوتن بەرهەمی بەردەوامییە، نەگۆڕیی ئامانجەکانت بپارێزە. 💡",
    "هیچ سنوورێک نییە بۆ ئەوەی کە دەتوانیت پێی بگەیت. 🌌",
    "هەموو ڕۆژێک دەرفەتێکە بۆ نووسینەوەی بەشێکی باشتر لە ژیانت. 📖",
    "هێزی ڕاستەقینە لەناوەوەی خۆتدایە، تەنها پێویستت بە کشفکردنیەتی. 🔥",
]

session = requests.Session()


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------
def safe_post(url, json_payload):
    """Posts safely with auto-retry and quiet error logging."""
    while True:
        try:
            res = session.post(url, json=json_payload, timeout=15)
            data = res.json()
            if data.get("ok"):
                return data
            else:
                print("⚠️ Telegram API Warning:", data.get("description"))
                return data
        except Exception:
            print("🔄 Proxy connection paused. Retrying in 15s...")
            time.sleep(15)


def send_new_message(quote):
    """Sends a brand new message to create a daily notification bump."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    text = (
        f"💭 *بیرۆکەی ئەمرۆ:*\n_{quote}_\n\n"
        f"🎂 *COUNTDOWN TO YOUR SPECIAL DAY* 🎈\n"
        f"⏳ `Initializing...`"
    )
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    res = safe_post(url, payload)
    if res and res.get("ok"):
        return res["result"]["message_id"]
    return None


# ---------------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------------
active_message_id = None
current_day = None

print("🚀 Birthday Countdown Bot is active and running...")

while True:
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    diff = TARGET_TIME_UTC - now_utc
    total_seconds = diff.total_seconds()

    # 1. Midnight Reached (August 22 Iran Time)
    if total_seconds <= 0:
        final_message = (
            "🎉 *HAPPY BIRTHDAY!* 🎂🥳🎁\n\n"
            "ڕۆژی لەدایکبوونت پیرۆز بێت! هەموو ساڵێک دەرفەتێکی نوێیە "
            "بۆ بڕینی ڕێگەی نوێ و کشفکردنی تواناکانت. 🚀✨"
        )
        if active_message_id:
            safe_post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText",
                {
                    "chat_id": CHAT_ID,
                    "message_id": active_message_id,
                    "text": final_message,
                    "parse_mode": "Markdown",
                },
            )
        else:
            safe_post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                {
                    "chat_id": CHAT_ID,
                    "text": final_message,
                    "parse_mode": "Markdown",
                },
            )
        print("🎉 Birthday message delivered!")
        break

    # 2. Trigger new daily message at 10:00 AM Iran Time (06:30 UTC)
    if now_utc.day != current_day and (
        now_utc.hour > TARGET_UTC_HOUR
        or (
            now_utc.hour == TARGET_UTC_HOUR
            and now_utc.minute >= TARGET_UTC_MINUTE
        )
    ):
        current_day = now_utc.day
        quote = DAILY_QUOTES[now_utc.timetuple().tm_yday % len(DAILY_QUOTES)]
        active_message_id = send_new_message(quote)

    # 3. Initial run fallback
    if active_message_id is None:
        current_day = now_utc.day
        quote = DAILY_QUOTES[now_utc.timetuple().tm_yday % len(DAILY_QUOTES)]
        active_message_id = send_new_message(quote)

    # 4. Live Update Current Active Message
    if active_message_id:
        days = diff.days
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        time_str = (
            f"`{days}d : {hours:02d}h : {minutes:02d}m : {seconds:02d}s`"
            if days > 0
            else f"`{hours:02d}h : {minutes:02d}m : {seconds:02d}s`"
        )

        quote = DAILY_QUOTES[now_utc.timetuple().tm_yday % len(DAILY_QUOTES)]

        formatted_text = (
            f"💭 *بیرۆکەی ئەمرۆ:*\n_{quote}_\n\n"
            f"🎂 *COUNTDOWN TO YOUR SPECIAL DAY* 🎈\n\n"
            f"⏳ {time_str} remaining!"
        )

        safe_post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText",
            {
                "chat_id": CHAT_ID,
                "message_id": active_message_id,
                "text": formatted_text,
                "parse_mode": "Markdown",
            },
        )

    # 5. Sleep Interval Control
    # Final 5 minutes: Update fast (every 3 seconds)
    # Normal operation: Update every 3 minutes (180s) to avoid PythonAnywhere proxy throttling
    if total_seconds <= 300:
        time.sleep(3)
    else:
        time.sleep(180)