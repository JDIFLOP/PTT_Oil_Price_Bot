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
        json_data = response.json()
        
        data_part = json_data.get('data', {})
        
        # ลองดึงข้อมูลพรุ่งนี้ก่อน (Tomorrow) ถ้ายังไม่มีค่อยเอาวันนี้ (Today)
        items = data_part.get('tomorrow', {}).get('items', [])
        status_label = "Tomorrow's Price"
        if not items:
            items = data_part.get('today', {}).get('items', [])
            status_label = "Today's Price"

        if not items:
            return "Error: Could not find oil data in API."

        # โหลดราคาเดิมมาเทียบ
        last_prices = {}
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r") as f:
                    last_prices = json.load(f)
            except: pass

        report_date = datetime.now().strftime("%d %B %Y")
        msg = f"Date: {report_date}\n"
        msg += f"Status: {status_label}\n"
        msg += "--------------------------\n"

        current_save = {}
        for item in items:
            # ดึงชื่อและราคา (ถ้าไม่มีราคาหรือราคาเป็น 0.00 ให้ข้าม)
            oil_name = item.get('oil_name', 'Unknown')
            try:
                price = float(item.get('price', 0))
            except:
                continue
                
            if price <= 0:
                continue

            # เก็บข้อมูลลง Database
            current_save[oil_name] = price
            
            # คำนวณส่วนต่างราคา
            last_p = last_prices.get(oil_name)
            change = ""
            if last_p is not None:
                diff = price - last_p
                if diff > 0: change = f" (+{diff:.2f})"
                elif diff < 0: change = f" ({diff:.2f})"
                else: change = " (Unchanged)"
            
            # เพิ่มข้อมูลลงในข้อความ
            msg += f"{oil_name}: {price:.2f} THB{change}\n"
        
        # บันทึกราคาปัจจุบันลงไฟล์
        if current_save:
            with open(DB_FILE, "w") as f:
                json.dump(current_save, f)
            return msg
        else:
            return "Error: No oil data available to report."
            
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
