import requests
import os
import json
from datetime import datetime

DB_FILE = "last_price.json"

def get_oil_prices():
    url = "https://www.bangchak.co.th/api/oilprice"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        items = data.get('data', {}).get('items', [])
        
        if not items:
            return "Error: No oil data found."

        last_prices = {}
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r") as f:
                    last_prices = json.load(f)
            except: pass

        report_date = datetime.now().strftime("%d %B %Y")
        
        # ค้นหาด้วย Keyword เพื่อป้องกันชื่อ API เปลี่ยน
        msg = f"Date: {report_date}\n"
        msg += "PTT & Oil Price Report\n"
        msg += "--------------------------\n"

        current_save = {}
        # รายการที่เราต้องการค้นหา
        targets = {
            "95": "Gasohol 95",
            "91": "Gasohol 91",
            "E20": "E20",
            "Diesel B7": "Diesel B7"
        }

        for item in items:
            oil_name = item.get('oil_name', '')
            price = float(item.get('price', 0))
            
            found_key = None
            # เช็คว่าชื่อน้ำมันจาก API มีคำที่เราต้องการไหม
            if "95" in oil_name and "Gasohol" in oil_name: found_key = "Gasohol 95"
            elif "91" in oil_name and "Gasohol" in oil_name: found_key = "Gasohol 91"
            elif "E20" in oil_name: found_key = "E20"
            elif "B7" in oil_name and "Diesel" in oil_name: found_key = "Diesel B7"

            if found_key:
                current_save[found_key] = price
                last_p = last_prices.get(found_key)
                
                change = ""
                if last_p is not None:
                    diff = price - last_p
                    if diff > 0: change = f" (+{diff:.2f})"
                    elif diff < 0: change = f" ({diff:.2f})"
                    else: change = " (Unchanged)"
                
                msg += f"{found_key}: {price:.2f} THB/L{change}\n"
        
        with open(DB_FILE, "w") as f:
            json.dump(current_save, f)
            
        return msg
    except Exception as e:
        return f"Source Error: {str(e)}"

def send_telegram(content):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": content}, timeout=20)

if __name__ == "__main__":
    message = get_oil_prices()
    send_telegram(message)
