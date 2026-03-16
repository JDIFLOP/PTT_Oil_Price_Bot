import requests
import os
from datetime import datetime

def get_oil_prices():
    # 🔗 รายชื่อ API ที่เสถียรที่สุดในตอนนี้ (เรียงลำดับความสำคัญ)
    # 1. บางจาก (Direct) 2. สรุปราคากลาง (Mirror)
    sources = [
        "https://www.bangchak.co.th/api/oilprice",
        "https://thai-oil-price.vercel.app/api/prices"
    ]
    
    report_date = datetime.now().strftime("%d %B %Y")
    msg = f"📅 *Oil Price Report: {report_date}*\n"
    
    for url in sources:
        try:
            response = requests.get(url, timeout=20)
            if response.status_code != 200: continue
            data = response.json()
            
            items = []
            # --- กรณีเป็น API ของบางจาก ---
            if "bangchak" in url:
                data_part = data.get('data', {})
                items = data_part.get('tomorrow', {}).get('items', [])
                # ถ้าพรุ่งนี้ไม่มีราคาใหม่ (ไม่มีประกาศขึ้น/ลง) ให้เอาราคาวันนี้มาโชว์แทน
                if not any(float(i.get('price', 0)) > 0 for i in items):
                    items = data_part.get('today', {}).get('items', [])
            
            # --- กรณีเป็น API สำรอง (Vercel/Mirror) ---
            else:
                ptt_data = data.get('data', {}).get('ptt', data.get('ptt', {}))
                for name, price in ptt_data.items():
                    items.append({'oil_name': name.replace('_', ' ').upper(), 'price': price})

            # ถ้าได้ข้อมูลมาแล้ว ให้เริ่มสร้างข้อความ
            if items:
                msg += "✅ *Latest Price Verified*\n"
                msg += "----------------------------------\n"
                found_valid = False
                for item in items:
                    name = item.get('oil_name', item.get('name'))
                    price = float(item.get('price', 0))
                    if price > 0:
                        msg += f"• {name}: {price:.2f} THB/L\n"
                        found_valid = True
                
                if found_valid: return msg # สำเร็จและส่งคืนค่าทันที
                
        except:
            continue # ถ้า Source นี้ล่ม ให้ลอง Source ถัดไป
            
    return "❌ Error: All data sources are currently unavailable. Please try again later."

def send_telegram(content):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # ใช้ Markdown เพื่อความสวยงาม
    requests.post(url, data={"chat_id": chat_id, "text": content, "parse_mode": "Markdown"}, timeout=20)

if __name__ == "__main__":
    message = get_oil_prices()
    send_telegram(message)
