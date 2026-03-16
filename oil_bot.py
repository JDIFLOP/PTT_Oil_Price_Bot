import requests
import os
import json
from datetime import datetime

def get_oil_prices():
    url = "https://www.bangchak.co.th/api/oilprice"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # ดึงข้อมูลส่วน data
        data_part = data.get('data', {})
        
        # --- ระบบค้นหาข้อมูลแบบยืดหยุ่น ---
        # 1. ลองหาใน tomorrow ก่อน
        tomorrow_items = data_part.get('tomorrow', {}).get('items', [])
        # 2. หาใน today
        today_items = data_part.get('today', {}).get('items', [])
        # 3. ถ้ายังไม่เจออีก ให้กวาดทุกอย่างที่อยู่ใน data (เผื่อโครงสร้างเปลี่ยน)
        if not today_items and not tomorrow_items:
            # ลองหา Key อื่นๆ ที่อาจมีข้อมูล
            for key in data_part:
                if isinstance(data_part[key], dict) and 'items' in data_part[key]:
                    today_items = data_part[key]['items']
                    break

        if not today_items:
            return "❌ Error: API structure changed or data is empty."

        # ตรวจสอบว่าพรุ่งนี้มีราคาใหม่ไหม
        has_tomorrow = any(float(i.get('price', 0)) > 0 for i in tomorrow_items)

        report_date = datetime.now().strftime("%d %B %Y")
        msg = f"📅 *Oil Price Report: {report_date}*\n"
        msg += "🚀 *[Update]* Tomorrow's price check\n" if has_tomorrow else "✅ *Current Price List*\n"
        msg += "----------------------------------\n"

        # แสดงรายการน้ำมัน
        # วนลูปจากรายการที่เรามี (today_items)
        for item in today_items:
            name = item.get('oil_name')
            try:
                price = float(item.get('price', 0))
            except: continue
            
            if price <= 0: continue

            # เช็คราคาพรุ่งนี้ที่ชื่อตรงกัน
            next_price = 0
            if has_tomorrow:
                for t_item in tomorrow_items:
                    if t_item.get('oil_name') == name:
                        next_price = float(t_item.get('price', 0))
                        break

            # การแสดงผล
            if next_price > 0 and next_price != price:
                diff = next_price - price
                icon = "⬆️" if diff > 0 else "⬇️"
                msg += f"• {name}: {price:.2f} ➔ *{next_price:.2f}* ({icon} {diff:+.2f})\n"
            else:
                msg += f"• {name}: {price:.2f} THB\n"

        return msg

    except Exception as e:
        return f"❌ System Error: {str(e)}"

def send_telegram(content):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": content, "parse_mode": "Markdown"}, timeout=20)

if __name__ == "__main__":
    message = get_oil_prices()
    send_telegram(message)
