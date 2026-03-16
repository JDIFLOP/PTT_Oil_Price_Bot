import requests
import os
import json
from datetime import datetime

DB_FILE = "last_price.json"

def get_oil_prices():
    # 🔗 Sources
    sources = [
        "https://www.bangchak.co.th/api/oilprice",
        "https://thai-oil-price.vercel.app/api/prices"
    ]
    
    raw_data = None
    source_used = ""

    for url in sources:
        try:
            response = requests.get(url, timeout=20)
            if response.status_code == 200:
                raw_data = response.json()
                source_used = url
                break
        except: continue

    if not raw_data:
        return "❌ Error: All oil price sources are currently unavailable."

    # --- 📂 Load History ---
    last_prices = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                last_prices = json.load(f)
        except: pass

    # --- 📊 Data Processing ---
    report_date = datetime.now().strftime("%d %B %Y")
    msg = f"📅 Date: {report_date}\n"
    msg += "⛽ PTT & Bangchak Oil Price Report\n"
    msg += "----------------------------------\n"

    items = []
    
    # 🔍 Extraction Logic
    if "bangchak" in source_used:
        data_part = raw_data.get('data', {})
        # ลองหาพรุ่งนี้ก่อน ถ้าไม่มีเอาวันนี้
        raw_list = data_part.get('tomorrow', {}).get('items', [])
        if not raw_list:
            raw_list = data_part.get('today', {}).get('items', [])
        
        for i in raw_list:
            items.append({'name': i.get('oil_name'), 'price': i.get('price')})
    else:
        # สำหรับ API สำรอง (Vercel)
        # พยายามหา Key ที่ชื่อ PTT หรือข้อมูลชั้นนอกสุด
        d = raw_data.get('data', raw_data)
        ptt = d.get('ptt', d.get('PTT', d))
        
        if isinstance(ptt, dict):
            for k, v in ptt.items():
                items.append({'name': k.replace('_', ' ').title(), 'price': v})

    # --- 📝 Build Message ---
    current_save = {}
    valid_count = 0
    
    for item in items:
        name = item.get('name')
        try:
            price = float(item.get('price', 0))
        except: continue

        if price <= 0 or not name: continue

        valid_count += 1
        current_save[name] = price
        
        last_p = last_prices.get(name)
        change = ""
        if last_p is not None:
            diff = price - last_p
            if diff > 0: change = f" (⬆️ +{diff:.2f})"
            elif diff < 0: change = f" (⬇️ {diff:.2f})"
            else: change = " (Unchanged)"
        
        msg += f"• {name}: {price:.2f} THB{change}\n"

    if valid_count > 0:
        with open(DB_FILE, "w") as f:
            json.dump(current_save, f)
        return msg
    
    return "❌ Error: Data extraction failed. (No valid items found)"

def send_telegram(content):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, data={"chat_id": chat_id, "text": content}, timeout=20)
    except: pass

if __name__ == "__main__":
    report = get_oil_prices()
    send_telegram(report)
