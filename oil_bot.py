import requests
import os
import json
from datetime import datetime

DB_FILE = "last_price.json"

def get_oil_prices():
    # API ตรงจากบางจาก (ใช้แสดงผลราคาน้ำมันปัจจุบันและล่วงหน้า)
    url = "https://www.bangchak.co.th/api/oilprice"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # ดึงข้อมูลจากส่วนของ 'data'
        items = data.get('data', {}).get('items', [])
        if not items:
            return "Error: No oil data found in Bangchak API."

        # โหลดราคาเดิม
        last_prices = {}
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r") as f:
                    last_prices = json.load(f)
            except:
                last_prices = {}

        report_date = datetime.now().strftime("%d %B %Y")
        
        # จับคู่ชื่อน้ำมัน (Mapping)
        target_oils = {
            'Gasohol 95 S EVO': 'Gasohol 95',
            'Gasohol 91 S EVO': 'Gasohol 91',
            'Gasohol E20 S EVO': 'E20',
            'Hi Diesel B7 S': 'Diesel B7'
        }

        msg = f"Date: {report_date}\n"
        msg += "PTT & Bangchak Oil Price Report\n"
        msg += "--------------------------\n"

        current_save = {}
        for item in items:
            oil_name = item.get('oil_name')
            if oil_name in target_oils:
                display_name = target_oils[oil_name]
                # ดึงราคาวันนี้ (Price) หรือราคาพรุ่งนี้ (Next_Price)
                # ปกติถ้าหลัง 5 โมงเย็น Next_Price จะมีค่าใหม่โผล่มา
                price = float(item.get('price', 0))
                
                current_save[display_name] = price
                
                last_p = last_prices.get(display_name)
                change = ""
                if last_p is not None:
                    diff = price - last_p
                    if diff > 0: change = f" (+{diff:.2f})"
                    elif diff < 0: change = f" ({diff:.2f})"
                    else: change = " (Unchanged)"
                
                msg += f"{display_name}: {price:.2f} THB/L{change}\n"
        
        with open(DB_FILE, "w") as f:
            json.dump(current_save, f)
            
        return msg
    except Exception as e:
        return f"Source Error: {str(e)}"

def send_telegram(content):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    try:
        res = requests.post(url, data={"chat_id": chat_id, "text": content}, timeout=20)
        return res.status_code
    except:
        return "Failed to notify Telegram"

if __name__ == "__main__":
    message = get_oil_prices()
    send_telegram(message)
