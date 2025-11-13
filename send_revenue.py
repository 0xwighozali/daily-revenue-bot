import requests
import datetime
import time
import os

# === Variabel dari GitHub Secrets ===
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

today = datetime.date.today()
today_str = today.strftime("%Y-%m-%d")

url = f"https://flowscan-builder-data-production.up.railway.app/api/builders/all-daily-revenue?startDate={today_str}&endDate={today_str}"

data = None

# === Coba ambil data API max 3x ===
for attempt in range(3):
    try:
        print(f"📡 Fetching data... (Attempt {attempt + 1}/3)")
        response = requests.get(url, timeout=90)
        response.raise_for_status()
        data = response.json()
        print("✅ Data fetched successfully")
        break
    except Exception as e:
        print(f"⚠️ Attempt {attempt + 1} failed: {e}")
        if attempt < 2:
            print("🔁 Retrying in 10 seconds...")
            time.sleep(10)
        else:
            print("❌ API failed after 3 attempts.")
            data = None

# === Kalau gagal ambil data, selesai tanpa error fatal ===
if not data:
    print("🚫 No data fetched. Exiting workflow gracefully.")
    exit(0)

# === Format pesan ===
message = f"📊 Daily Revenue Report — {today_str}\n\n"

for builder in data:
    name = builder.get("builderName", "Unknown")
    revenue = builder.get("revenueUSD", 0)
    message += f"• {name}: ${revenue:,.2f}\n"

# === Kirim ke Telegram ===
try:
    send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    response = requests.post(send_url, data=payload)
    response.raise_for_status()
    print("📩 Sent to Telegram successfully")
except Exception as e:
    print(f"❌ Error sending message to Telegram: {e}")
    exit(0)
