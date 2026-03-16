import requests
import os
import json
from datetime import datetime

DB_FILE = "last_price.json"

def get_oil_prices():
    # 🔗 แหล่งข้อมูลหลัก (Direct API) และสำรอง (Fallback API)
    sources = [
        "https://www.bangchak.co.th/api/oilprice",
        "https://thai-oil-price.vercel.app/api/prices"
    ]
    
    data = None
    source_used = ""

    for url in sources:
        try:
            response = requests.get(url, timeout=20)
            if response.status_code == 200:
                data = response.json()
                source_used = url
                break
        except:
            continue

    if not data:
        return "❌ Error: All oil price sources are currently unavailable."

    # --- 📂 ส่วนการจัดการฐานข้อมูลราคาเดิม ---
    last_prices = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                last_prices = json.load(f)
        except: pass

    # --- 📊 ส่วนการดึงข้อมูลและจัดการรูปแบบข้อความ ---
    report_date = datetime.now().strftime("%d %B %Y")
    msg = f"📅 Date: {report_date}\n"
    msg += "⛽ PTT & Bangchak Oil Price Report\n"
    msg += "----------------------------------\n"

    items = []
    # จัดการโครงสร้าง JSON ที่ต่างกันของแต่ละ Source
    if "bangchak" in source_used:
        items_raw = data.get('data', {}).get('tomorrow', {}).get('items', [])
        if not items_raw:
            items_raw = data.get('data', {}).get('today', {}).get('items', [])
        for i in items_raw:
            items.append({'name': i.get('oil_name'), 'price': i.get('price')})
    else:
        ptt_data = data.get('data', {}).get('ptt', data.get('ptt', {}))
        for name, price in ptt_data.items():
            items.append({'name': name.replace('_', ' ').title(), 'price': price})

    current_save = {}
    for item in items:
        name = item.get('name')
        try:
            price = float(item.get('price', 0))
        except: continue

        if price <= 0 or not name: continue

        current_save[name] = price
        
        # 🔄 เปรียบเทียบราคา
        last_p = last_prices.get(name)
        change = ""
        if last_p is not None:
            diff = price - last_p
            if diff > 0: change = f" (⬆️ +{diff:.2f})"
            elif diff < 0: change = f" (⬇️ {diff:.2f})"
            else: change = " (Unchanged)"
        
        msg += f"• {name}: {price:.2f} THB{change}\n"

    # บันทึกราคาลงไฟล์
    if current_save:
        with open(DB_FILE, "w") as f:
            json.dump(current_save, f)
        return msg
    return "❌ Error: Data processing failed."

def send_telegram(content):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    try:
        requests.post(url, data={"chat_id": chat_id, "text": content}, timeout=20)
    except Exception as e:
        print(f"Failed to send: {e}")

if __name__ == "__main__":
    report = get_oil_prices()
    send_telegram(report)
