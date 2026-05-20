import os
import time
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import re

# ========================= CONFIG =========================
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')

# Your 8 channels
CHANNELS = [
    '@bazarfelez',
    '@tasisat_mechanic_sakhteman',
    '@civilmashhadd',
    '@civilejra',
    '@atifoolad',
    '@PipeBazaar',
    '@mihansazan',
    '@Bahrami_Steel',
]

SHEET_ID = '1X9ptoKcrK7o0sOvz_NngBxxgfgLehqnEqu0Ouk2PdHE'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# ========================================================

def clean_html(text):
    text = re.sub(r'<[^>]+>', ' ', text)
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&#39;', "'").replace('&quot;', '"')
    return ' '.join(text.split()).strip()

def extract_prices(text):
    persian_to_eng = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
    text = text.translate(persian_to_eng)
    
    patterns = [
        r'\b\d{1,3}(?:,\d{3})+\b',
        r'\b\d{1,3}(?:[،]\d{3})+\b',
        r'\b\d{4,}\b',
    ]
    
    prices = []
    for p in patterns:
        prices.extend(re.findall(p, text))
    
    valid = []
    seen = set()
    for p in prices:
        num = int(p.replace(',', '').replace('،', ''))
        if num > 1000 and p not in seen:
            seen.add(p)
            valid.append(p)
    return valid

def fetch_channel(channel):
    channel_name = channel.replace('@', '')
    url = f'https://t.me/s/{channel_name}'
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return None, f"HTTP {response.status_code}"
        
        html = response.text
        if 'tgme_widget_message_text' not in html:
            return None, "No messages found"
        
        messages = re.findall(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
        return messages, "ok"
    except Exception as e:
        return None, str(e)

# ====================== MAIN ======================
print("Starting Price Tracker...")

print("Connecting to Google Sheets...")
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1
print("Connected to Google Sheets")

today = datetime.now().strftime('%Y-%m-%d %H:%M')
saved_count = 0

for CHANNEL in CHANNELS:
    print(f"\nFetching from {CHANNEL}...")
    
    messages, status = fetch_channel(CHANNEL)
    
    if messages is None:
        print(f"Failed: {status}")
        continue
    
    print(f"Found {len(messages)} messages")
    
    channel_saved = 0
    for msg in messages:
        clean = clean_html(msg)
        if len(clean) < 10:
            continue
        
        prices = extract_prices(clean)
        if prices:
            for price in prices:
                try:
                    sheet.append_row([today, CHANNEL, price, clean[:500]])
                    saved_count += 1
                    channel_saved += 1
                    print(f"Saved: {price} | {clean[:60]}...")
                except Exception as e:
                    print(f"Error: {e}")
    
    print(f"Saved {channel_saved} prices from this channel")
    time.sleep(3)

print(f"\nDone! Total: {saved_count} prices saved.")