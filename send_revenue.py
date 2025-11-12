import requests
import datetime
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# --- 1. Ambil waktu sekarang ---
now_utc = datetime.datetime.utcnow()
now_wib = now_utc + datetime.timedelta(hours=7)
today_str = now_utc.date().isoformat()

# --- 2. Ambil data dari API ---
url = f"https://flowscan-builder-data-production.up.railway.app/api/builders/all-daily-revenue?startDate={today_str}&endDate={today_str}"
response = requests.get(url, timeout=20)
response.raise_for_status()
data = response.json()
daily_revenue = data.get("data", {}).get("dailyRevenue", {})

# --- 3. Target builder ---
target_builders = ["metamask", "phantom", "basedapp"]

# --- 4. Loop semua tanggal dan ambil revenue builder yang diinginkan ---
filtered = {}
for date, builders in daily_revenue.items():
    filtered[date] = {}
    for b in target_builders:
        value = builders.get(b)
        filtered[date][b] = f"${value:,.2f}" if value else "❌ not found"

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
    <h2 style="color:#1a73e8;">📊 Daily Revenue Update</h2>
    <p>Here’s the latest revenue data for <b>MetaMask</b>, <b>Phantom</b>, and <b>BasedApp</b>.</p>
    
    <table border="1" cellspacing="0" cellpadding="8" style="border-collapse:collapse; width:100%; text-align:center;">
      <tr style="background-color:#e3f2fd;">
        <th>Date</th>
        <th>MetaMask</th>
        <th>Phantom</th>
        <th>BasedApp</th>
      </tr>
      {table_rows}
    </table>

    <p>⏰ <b>Last updated</b><br>
    UTC: {now_utc.strftime("%Y-%m-%d %H:%M:%S")} <br>
    WIB: {now_wib.strftime("%Y-%m-%d %H:%M:%S")}</p>

    <p style="font-size:13px; color:#666;">Sent via SendGrid 💌</p>
  </body>
</html>
"""

# --- 6. Kirim email pakai SendGrid ---
SENDGRID_API_KEY = os.environ["SENDGRID_API_KEY"]
FROM_EMAIL = os.environ["FROM_EMAIL"]
TO_EMAIL = os.environ["TO_EMAIL"]

plain_text_content = "Daily Revenue Update for MetaMask, Phantom, BasedApp."

message = Mail(
    from_email=FROM_EMAIL,
    to_emails=TO_EMAIL,
    subject=f"💰 Revenue Update — {today_str} (UTC+7 WIB)",
    plain_text_content=plain_text_content,
    html_content=html_content
)

try:
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    response = sg.send(message)
    print(f"✅ Email sent! Status code: {response.status_code}")
except Exception as e:
    print("❌ Error sending email:", e)
