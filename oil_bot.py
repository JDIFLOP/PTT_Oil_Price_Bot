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
        
        data_part = data.get('data', {})
        today_items = data_part.get('today', {}).get('items', [])
        tomorrow_items = data_part.get('tomorrow', {}).get('items', [])

        if not today_items:
            return "❌ Error: Could not fetch today's oil prices."

        # ตรวจสอบว่าพรุ่งนี้มีการปรับราคาไหม (ดูว่ามีราคาพรุ่งนี้ที่ต่างจากวันนี้ไหม)
        has_tomorrow_announcement = False
        if tomorrow_items:
            for t_item in tomorrow_items:
                t_price = float(t_item.get('price', 0))
                if t_price > 0:
                    has_tomorrow_announcement = True
                    break

        report_date = datetime.now().strftime("%d %B %Y")
        msg = f"📅 *Oil Price Report: {report_date}*\n"
        
        if has_tomorrow_announcement:
            msg += "🚀 *[NEW] Tomorrow's Price Announced!*\n"
        else:
            msg += "✅ *Current Price (No changes for tomorrow)*\n"
        
        msg += "----------------------------------\n"

        # วนลูปแสดงราคา
        # เราจะใช้รายชื่อน้ำมันจากวันนี้เป็นหลัก
        for item in today_items:
            name = item.get('oil_name')
            try:
                today_price = float(item.get('price', 0))
            except: continue

            if today_price <= 0: continue

            # ค้นหาราคาพรุ่งนี้ที่ชื่อตรงกัน
            tomorrow_price = 0
            if has_tomorrow_announcement:
                for t_item in tomorrow_items:
                    if t_item.get('oil_name') == name:
                        tomorrow_price = float(t_item.get('price', 0))
                        break

            # ส่วนการแสดงผล
            if tomorrow_price > 0 and tomorrow_price != today_price:
                diff = tomorrow_price - today_price
                change_icon = "⬆️" if diff > 0 else "⬇️"
                msg += f"• {name}: {today_price:.2f} ➔ *{tomorrow_price:.2f}* ({change_icon} {diff:+.2f})\n"
            else:
                msg += f"• {name}: {today_price:.2f} THB\n"

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
