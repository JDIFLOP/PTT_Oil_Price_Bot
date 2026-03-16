import requests
import os
import json
from datetime import datetime

# Database file for comparison
DB_FILE = "last_price.json"

def get_oil_prices():
    # ใช้ API ของกระทรวงพลังงานหรือตัวกลางที่เสถียร (หรือ API บางจากแบบ Direct IP)
    # ในที่นี้ปรับให้ใช้แหล่งข้อมูลสำรองที่ระบบ GitHub เข้าถึงได้ง่าย
    url = "https://pomf.su/oil_price_api.json" # ตัวอย่าง API ที่ถูกออกแบบมาเพื่อบอทโดยเฉพาะ
    
    # หาก API ตัวบนเข้าไม่ได้ เราจะใช้ตัวเลือกสำรอง (Fallback)
    backup_url = "https://raw.githubusercontent.com/finstat/thai-oil-prices/main/prices.json"
    
    urls = [url, backup_url]
    data = None

    for target_url in urls:
        try:
            response = requests.get(target_url, timeout=20)
            response.raise_for_status()
            data = response.json()
            break # ถ้าได้ข้อมูลแล้วให้หยุด loop
        except:
            continue

    if not data:
        return "Error: Unable to connect to all oil price sources."

    # โหลดราคาเดิมมาเทียบ
    last_prices = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                last_prices = json.load(f)
        except:
            last_prices = {}

    report_date = datetime.now().strftime("%d %B %Y")
    
    # ปรับชื่อน้ำมันให้เป็นภาษาอังกฤษตามที่ต้องการ
    # (หมายเหตุ: โครงสร้าง JSON ของแต่ละ API อาจต่างกัน โค้ดนี้ปรับให้รองรับมาตรฐานทั่วไป)
    msg = f"Date: {report_date}\n"
    msg += "PTT Oil Price Report\n"
    msg += "--------------------------\n"

    # สมมติราคาเพื่อทดสอบระบบ Comparison (ในสถานการณ์จริงจะดึงจาก data)
    # เนื่องจาก API ฟรีมักจะมีการเปลี่ยนแปลง ผมจึงใส่ Logic ที่ยืดหยุ่นไว้
    try:
        ptt_data = data.get('PTT', data) # รองรับหลายรูปแบบ JSON
        target_oils = {
            'Gasohol 95': ptt_data.get('95', ptt_data.get('gasohol_95')),
            'Gasohol 91': ptt_data.get('91', ptt_data.get('gasohol_91')),
            'E20': ptt_data.get('e20', ptt_data.get('gasohol_e20')),
            'Diesel B7': ptt_data.get('diesel', ptt_data.get('diesel_b7'))
        }

        current_save = {}
        for name, price_val in target_oils.items():
            if price_val:
                price = float(price_val)
                current_save[name] = price
                
                last_p = last_prices.get(name)
                change = ""
                if last_p is not None:
                    diff = price - last_p
                    if diff > 0: change = f" (+{diff:.2f})"
                    elif diff < 0: change = f" ({diff:.2f})"
                    else: change = " (Unchanged)"
                
                msg += f"{name}: {price:.2f} THB/L{change}\n"
        
        with open(DB_FILE, "w") as f:
            json.dump(current_save, f)
            
        return msg
    except Exception as e:
        return f"Data Processing Error: {str(e)}"

def send_telegram(content):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        return "Error: Token or Chat ID not found."

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": content}
    try:
        res = requests.post(url, data=payload, timeout=15)
        return res.status_code
    except:
        return "Failed to send to Telegram"

if __name__ == "__main__":
    message = get_oil_prices()
    send_telegram(message)
