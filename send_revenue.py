import requests
import datetime
import os
import json
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import time

# --- 1. Waktu sekarang ---
now_utc = datetime.datetime.utcnow()
now_wib = now_utc + datetime.timedelta(hours=7)
today_str = now_utc.date().isoformat()

# --- 2. Ambil data dari API dengan retry ---
url = f"https://flowscan-builder-data-production.up.railway.app/api/builders/all-daily-revenue?startDate={today_str}&endDate={today_str}"

daily_revenue = {}
success = False
for i in range(3):
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        data = response.json()
        daily_revenue = data.get("data", {}).get("dailyRevenue", {})
        success = True
        break
    except Exception as e:
        print(f"Attempt {i+1} failed: {e}")
        if i < 2:
            time.sleep(5)
        else:
            print("❌ Failed to fetch data after 3 attempts.")

# --- 3. Target builder ---
target_builders = ["metamask", "phantom", "basedapp"]

# --- 4. Filter revenue atau kasih not found kalau gagal ---
filtered = {}
if success and daily_revenue:
    for date, builders in daily_revenue.items():
        filtered[date] = {}
        for b in target_builders:
            value = builders.get(b)
            filtered[date][b] = f"${value:,.2f}" if value else "❌ not found"
else:
    filtered[today_str] = {b: "❌ data not available" for b in target_builders}

# --- 5. Format HTML email ---
table_rows = ""
for date, items in filtered.items():
    table_rows += f"""
    <tr>
      <td>{date}</td>
      <td>{items['metamask']}</td>
      <td>{items['phantom']}</td>
      <td>{items['basedapp']}</td>
    </tr>
    """

html_content = f"""
<html>
  <body style="font-family:Arial, sans-serif; background-color:#f8f9fa; padding:20px;">
    <h2 style="color:#1a73e8;">📊 Hourly Revenue Update</h2>
    <p>Latest revenue for <b>MetaMask</b>, <b>Phantom</b>, and <b>BasedApp</b>.</p>
    <table border="1" cellspacing="0" cellpadding="8" style="border-collapse:collapse; width:100%; text-align:center;">
      <tr style="background-color:#e3f2fd;">
        <th>Date</th>
        <th>MetaMask</th>
        <th>Phantom</th>
        <th>BasedApp</th>
      </tr>
      {table_rows}
    </table>
    <p>⏰ Last updated:<br>UTC: {now_utc.strftime("%Y-%m-%d %H:%M:%S")}<br>WIB: {now_wib.strftime("%Y-%m-%d %H:%M:%S")}</p>
    <p style="font-size:13px; color:#666;">Automatically sent via SendGrid 💌</p>
  </body>
</html>
"""

plain_text_content = "Hourly Revenue Update for MetaMask, Phantom, BasedApp."

# --- 6. Kirim email ---
SENDGRID_API_KEY = os.environ["SENDGRID_API_KEY"]
FROM_EMAIL = os.environ["FROM_EMAIL"]
TO_EMAIL = os.environ["TO_EMAIL"]

message = Mail(
    from_email=FROM_EMAIL,
    to_emails=TO_EMAIL,
    subject=f"💰 Hourly Revenue — {today_str} (UTC+7 WIB)",
    plain_text_content=plain_text_content,
    html_content=html_content
)

try:
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    response = sg.send(message)
    print(f"✅ Email sent! Status code: {response.status_code}")
except Exception as e:
    print("❌ Error sending email:", e)
