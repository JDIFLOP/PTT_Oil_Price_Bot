import requests
import os
import json
from datetime import datetime

# Database file
DB_FILE = "last_price.json"

def get_oil_prices():
    # ใช้ API ของกระทรวงพลังงานผ่านโดเมนที่มีความน่าเชื่อถือสูง
    url = "https://raw.githubusercontent.com/piti118/thai-oil-price-api/master/today.json"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # กรองข้อมูลเฉพาะ ปตท. (PTT)
        # โครงสร้างของ API นี้จะให้ข้อมูลทุกปั๊ม เราจะเจาะจงไปที่ PTT
        ptt_data = next((item for item in data if item['name'] == 'PTT'), None)
        
        if not ptt_data:
            return "Error: PTT data not found in source."

        # โหลดราคาเดิม
        last_prices = {}
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r") as f:
                    last_prices = json.load(f)
            except:
                last_prices = {}

        report_date = datetime.now().strftime("%d %B %Y")
        
        # ชื่อน้ำมันที่เราต้องการ
        oil_mapping = {
            'gasohol_95': 'Gasohol 95',
            'gasohol_91': 'Gasohol 91',
            'gasohol_e20': 'E20',
            'diesel_b7': 'Diesel B7'
        }

        msg = f"Date: {report_date}\n"
        msg += "PTT Oil Price Report\n"
        msg += "--------------------------\n"

        current_save = {}
        prices = ptt_data.get('prices', {})
        
        for key, display_name in oil_mapping.items():
            price_val = prices.get(key)
            if price_val:
                price = float(price_val)
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
        return f"System Error: {str(e)}"

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
