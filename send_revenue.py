import requests
import datetime
import json
import os

# === 1. Ambil waktu sekarang (UTC & WIB) ===
now_utc = datetime.datetime.utcnow()
now_wib = now_utc + datetime.timedelta(hours=7)
today_str = now_utc.date().isoformat()

# === 2. Ambil data dari API ===
url = f"https://flowscan-builder-data-production.up.railway.app/api/builders/all-daily-revenue?startDate={today_str}&endDate={today_str}"
try:
    response = requests.get(url, timeout=40)
    response.raise_for_status()
    data = response.json()
except Exception as e:
    message = f"❌ Error fetching API: {e}"
    print(message)
    exit(1)

daily_revenue = data.get("data", {}).get("dailyRevenue", {})

# === 3. Target builder ===
target_builders = ["metamask", "phantom", "basedapp"]

# === 4. Loop semua tanggal dan ambil revenue builder yang diinginkan ===
filtered = {}
for date, builders in daily_revenue.items():
    filtered[date] = {}
    for b in target_builders:
        value = builders.get(b)
        filtered[date][b] = f"${value:,.2f}" if value else "❌ not found"

# === 5. Format pesan Telegram ===
rows = []
for date, items in filtered.items():
    rows.append(
        f"📅 <b>{date}</b>\n"
        f"• MetaMask: {items['metamask']}\n"
        f"• Phantom: {items['phantom']}\n"
        f"• BasedApp: {items['basedapp']}\n"
    )

text = (
    "🚀 <b>Daily Revenue Update</b>\n\n"
    + "\n".join(rows)
    + f"\n\n⏰ <b>Last updated:</b>\nUTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S')} "
      f"\nWIB: {now_wib.strftime('%Y-%m-%d %H:%M:%S')}"
)

# === 6. Kirim ke Telegram ===
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    print("❌ Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID environment variable.")
    exit(1)

send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}

try:
    res = requests.post(send_url, json=payload, timeout=20)
    res.raise_for_status()
    print("✅ Message sent successfully to Telegram group!")
except Exception as e:
    print(f"❌ Error sending message to Telegram: {e}")
