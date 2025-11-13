import requests
import datetime
import time
import os
import html

# === Ambil token dan chat_id dari GitHub Secrets ===
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # bisa langsung -1003270248632 atau pakai secret

# === Waktu sekarang ===
now_utc = datetime.datetime.utcnow()
now_wib = now_utc + datetime.timedelta(hours=7)
today_str = now_utc.date().isoformat()

# === URL API ===
url = f"https://flowscan-builder-data-production.up.railway.app/api/builders/all-daily-revenue?startDate={today_str}&endDate={today_str}"

data = None

# === Fetch API dengan retry 3x ===
for attempt in range(3):
    try:
        print(f"📡 Fetching data... (Attempt {attempt+1}/3)")
        response = requests.get(url, timeout=90)
        response.raise_for_status()
        data = response.json()
        print("✅ Data fetched successfully")
        break
    except Exception as e:
        print(f"⚠️ Attempt {attempt+1} failed: {e}")
        if attempt < 2:
            print("🔁 Retrying in 10 seconds...")
            time.sleep(10)
        else:
            print("❌ API failed after 3 attempts.")
            data = None

if not data:
    print("🚫 No data fetched. Exiting gracefully.")
    exit(0)

# === Target builders ===
target_builders = ["metamask", "phantom", "basedapp"]
daily_revenue = data.get("data", {}).get("dailyRevenue", {})

# === Format pesan ===
rows = []
for date, builders in daily_revenue.items():
    row = f"📅 {date}\n"
    for b in target_builders:
        value = builders.get(b)
        row += f"• {b.capitalize()}: ${value:,.2f}\n" if value else f"• {b.capitalize()}: ❌ not found\n"
    rows.append(row)

text = (
    "🚀 Daily Revenue Update\n\n"
    + "\n".join(rows)
    + f"\n⏰ Last updated:\nUTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}\nWIB: {now_wib.strftime('%Y-%m-%d %H:%M:%S')}"
)

# === Escape HTML special characters & batas panjang pesan ===
def safe_text(txt):
    return html.escape(txt)[:4000]  # Telegram max 4096

# === Kirim ke Telegram ===
try:
    send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": safe_text(text), "parse_mode": "HTML"}
    res = requests.post(send_url, data=payload, timeout=30)
    res.raise_for_status()
    print("📩 Sent to Telegram successfully")
except Exception as e:
    print(f"❌ Error sending message to Telegram: {e}")
    exit(0)
