import requests
import datetime
import time
import os
import json

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

today = datetime.date.today()
today_str = today.strftime("%Y-%m-%d")

url = f"https://flowscan-builder-data-production.up.railway.app/api/builders/all-daily-revenue?startDate={today_str}&endDate={today_str}"

data = None

# === Fetch API (max 3x retry) ===
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
            time.sleep(10)
        else:
            data = None

if not data:
    print("🚫 No data fetched. Exiting gracefully.")
    exit(0)

# === Format pesan ===
message = f"📊 Daily Revenue Report — {today_str}\n\n"

# Pastikan data berupa list
if isinstance(data, list):
    for item in data:
        if isinstance(item, dict):
            name = item.get("builderName", "Unknown")
            revenue = item.get("revenueUSD", 0)
            message += f"• {name}: ${revenue:,.2f}\n"
        elif isinstance(item, str):
            message += f"• {item}\n"
else:
    # Kalau bukan list, kirim mentah
    message += f"{json.dumps(data, indent=2)}\n"

# === Kirim ke Telegram ===
try:
    send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    r = requests.post(send_url, data=payload)
    r.raise_for_status()
    print("📩 Sent to Telegram successfully")
except Exception as e:
    print(f"❌ Error sending to Telegram: {e}")
