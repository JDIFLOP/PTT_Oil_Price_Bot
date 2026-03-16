import requests
import os
import json
from datetime import datetime

# Database file for comparison
DB_FILE = "last_price.json"

def get_oil_prices():
    # เปลี่ยนมาใช้ API ของบางจากที่เสถียรกว่า (อัปเดตราคาพร้อม ปตท.)
    url = "https://interactive.bangchak.co.th/api/oil-price"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # ค้นหาข้อมูลในกลุ่มของวันพรุ่งนี้ (Tomorrow) หรือวันนี้ (Today)
        # ปกติบางจากจะส่งข้อมูลมาเป็น List ของราคาแต่ละประเภท
        oil_list = data.get('data', {}).get('items', [])
        
        if not oil_list:
            return "Error: Oil data not found from source."

        # โหลดราคาเดิมมาเทียบ
        last_prices = {}
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r") as f:
                    last_prices = json.load(f)
            except:
                last_prices = {}

        report_date = datetime.now().strftime("%d %B %Y")
        
        # จับคู่ชื่อน้ำมันที่เราต้องการ (Mapping)
        target_names = {
            'Gasohol 95 S EVO': 'Gasohol 95',
            'Gasohol 91 S EVO': 'Gasohol 91',
            'Gasohol E20 S EVO': 'E20',
            'Hi Diesel B7 S': 'Diesel B7'
        }

        msg = f"Date: {report_date}\n"
        msg += "PTT & Bangchak Oil Price Report\n"
        msg += "--------------------------\n"

        current_save = {}
        for item in oil_list:
            raw_name = item.get('name')
            if raw_name in target_names:
                name = target_names[raw_name]
                price = float(item.get('price', 0))
                current_save[name] = price
                
                # เปรียบเทียบราคา
                last_p = last_prices.get(name)
                if last_p is not None:
                    diff = price - last_p
                    if diff > 0:
                        change = f" (+{diff:.2f})"
                    elif diff < 0:
                        change = f" ({diff:.2f})"
                    else:
                        change = " (Unchanged)"
                else:
                    change = ""

                msg += f"{name}: {price:.2f} THB/L{change}\n"
        
        with open(DB_FILE, "w") as f:
            json.dump(current_save, f)
            
        return msg
    except Exception as e:
        return f"Error connecting to source: {str(e)}"

def send_telegram(content):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        return "Error: Token or Chat ID not found."

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": content}
    res = requests.post(url, data=payload)
    return res.status_code

if __name__ == "__main__":
    message = get_oil_prices()
    send_telegram(message)
