import requests
import os
import json
from datetime import datetime

DB_FILE = "last_price.json"

def get_oil_prices():
    # ใช้ API ตรงของบางจาก เพราะมีข้อมูล 'tomorrow' ที่แม่นยำที่สุด
    url = "https://www.bangchak.co.th/api/oilprice"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # เจาะจงไปที่ข้อมูลของ "วันพรุ่งนี้" (Tomorrow)
        tomorrow_items = data.get('data', {}).get('tomorrow', {}).get('items', [])
        
        # เช็คว่ามีประกาศราคาใหม่หรือยัง (ถ้าราคาเป็น 0 หรือ List ว่าง แสดงว่ายังไม่ประกาศ)
        is_updated = any(float(i.get('price', 0)) > 0 for i in tomorrow_items)

        if not is_updated:
            return "📢 No price changes announced yet for tomorrow."

        # โหลดราคาเดิม (ราคาของวันนี้) มาเทียบ
        last_prices = {}
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r") as f:
                    last_prices = json.load(f)
            except: pass

        report_date = datetime.now().strftime("%d %B %Y")
        msg = f"🚀 *TOMORROW'S PRICE* ({report_date})\n"
        msg += "Effective at 05:00 AM\n"
        msg += "----------------------------------\n"

        current_save = {}
        for item in tomorrow_items:
            name = item.get('oil_name')
            try:
                price = float(item.get('price', 0))
            except: continue

            if price <= 0: continue

            current_save[name] = price
            
            # เปรียบเทียบกับราคาเดิมในระบบ
            last_p = last_prices.get(name)
            change = ""
            if last_p is not None:
                diff = price - last_p
                if diff > 0: change = f" ⬆️ *+{diff:.2f}*"
                elif diff < 0: change = f" ⬇️ *{diff:.2f}*"
                else: change = " (Stable)"
            
            msg += f"• {name}: {price:.2f} THB{change}\n"

        # บันทึกราคาพรุ่งนี้ไว้ เพื่อเป็นฐานข้อมูลไว้เทียบในวันถัดไป
        with open(DB_FILE, "w") as f:
            json.dump(current_save, f)
            
        return msg

    except Exception as e:
        return f"❌ Error: {str(e)}"

def send_telegram(content):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # ใช้ parse_mode='Markdown' เพื่อให้ตัวหนาและ Emoji แสดงผลสวยงาม
    requests.post(url, data={"chat_id": chat_id, "text": content, "parse_mode": "Markdown"}, timeout=20)

if __name__ == "__main__":
    message = get_oil_prices()
    send_telegram(message)
