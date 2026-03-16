import requests
import os
import json
from datetime import datetime

# Database file for comparison
DB_FILE = "last_price.json"

def get_oil_prices():
    url = "https://api.sumit603.com/gas_price"
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        ptt = data.get('PTT', {})
        
        if not ptt:
            return "Error: PTT data not found."

        # Load previous prices
        last_prices = {}
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r") as f:
                    last_prices = json.load(f)
            except:
                last_prices = {}

        report_date = datetime.now().strftime("%d %B %Y")
        target_oils = {
            '95': 'Gasohol 95',
            '91': 'Gasohol 91',
            'e20': 'E20',
            'diesel': 'Diesel B7'
        }

        msg = f"Date: {report_date}\n"
        msg += "PTT Oil Price Report\n"
        msg += "--------------------------\n"

        current_save = {}
        for key, name in target_oils.items():
            price_val = ptt.get(key, 0)
            price = float(price_val) if price_val else 0.0
            current_save[key] = price
            
            # Comparison Logic
            last_p = last_prices.get(key)
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
        
        # Save current prices
        with open(DB_FILE, "w") as f:
            json.dump(current_save, f)
            
        return msg
    except Exception as e:
        return f"Error: {str(e)}"

def send_telegram(content):
    # This gets values from GitHub Secrets
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
