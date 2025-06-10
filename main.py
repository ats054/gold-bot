
import os
try:
    import pandas
    import yfinance
    import requests
    import ta
    from flask import Flask
except ImportError:
    os.system("pip install yfinance pandas requests ta flask")

from datetime import datetime
import pandas as pd
import yfinance as yf
import ta
import requests
import threading
import time
from flask import Flask

app = Flask(__name__)

BOT_TOKEN = "7921226841:AAFt6Gv2XdUg4tXsid9g70A_7-p-uv7OHO0"
CHAT_ID = 683024750
PLUS500_FACTOR = 20

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("שגיאה בשליחת הודעה:", e)

def send_test_message():
    text = "🔔 בדיקת תקשורת: הבוט מחובר בהצלחה לטלגרם!"
    send_telegram_message(text)

def get_indicators(data):
    data.dropna(inplace=True)
    rsi = ta.momentum.RSIIndicator(close=data['Close'].squeeze(), window=14).rsi()
    macd_ind = ta.trend.MACD(close=data['Close'].squeeze())
    bollinger = ta.volatility.BollingerBands(close=data['Close'].squeeze())

    data['RSI'] = rsi
    data['MACD'] = macd_ind.macd()
    data['MACD_signal'] = macd_ind.macd_signal()
    data['lower_band'] = bollinger.bollinger_lband()
    return data

def analyze_gold():
    try:
        data_1m = yf.download(tickers="GC=F", interval="1m", period="1d")
        data_5m = yf.download(tickers="GC=F", interval="5m", period="1d")
    except Exception as e:
        print("שגיאה בשליפת נתונים:", e)
        return

    if data_1m.empty or data_5m.empty:
        print("אין נתונים זמינים")
        return

    data_1m = get_indicators(data_1m)
    data_5m = get_indicators(data_5m)

    price_1m = float(data_1m['Close'].iloc[-1])
    adjusted_price = round(price_1m - PLUS500_FACTOR, 2)
    rsi_1m = round(data_1m['RSI'].iloc[-1], 2)
    macd_1m = round(data_1m['MACD'].iloc[-1], 2)
    signal_1m = round(data_1m['MACD_signal'].iloc[-1], 2)
    boll_1m = round(data_1m['lower_band'].iloc[-1], 2)

    rsi_5m = round(data_5m['RSI'].iloc[-1], 2)
    macd_5m = round(data_5m['MACD'].iloc[-1], 2)
    signal_5m = round(data_5m['MACD_signal'].iloc[-1], 2)

    print(f"⏱️ {datetime.now().strftime('%H:%M:%S')} | מחיר Yahoo: {round(price_1m, 2)} | Plus500 (מותאם): {adjusted_price} | RSI(1ד'): {rsi_1m} | RSI(5ד'): {rsi_5m}")

    if (
        rsi_1m < 30 and
        macd_1m > signal_1m and
        price_1m < boll_1m and
        rsi_5m < 35 and
        macd_5m > signal_5m
    ):
        text = (
            f"איתות כניסה בזהב! 🟢\n"
            f"מחיר לפי Yahoo: {round(price_1m, 2)}\n"
            f"התאמה ל-Plus500: ~{adjusted_price}\n"
            f"RSI 1ד': {rsi_1m} | RSI 5ד': {rsi_5m}\n"
            f"MACD 1ד': {macd_1m} > {signal_1m}\n"
            f"MACD 5ד': {macd_5m} > {signal_5m}\n"
            f"בולינגר תחתון (1ד'): {boll_1m}\n"
            f"זמן: {datetime.now().strftime('%H:%M:%S')}"
        )
        send_telegram_message(text)

def run_bot_loop():
    send_test_message()
    while True:
        analyze_gold()
        time.sleep(60)

@app.route('/')
def home():
    return "✅ Gold Bot is running."

@app.route('/status')
def status():
    return "Bot OK ✅"

# נריץ את הלולאה ברקע
threading.Thread(target=run_bot_loop).start()

# נריץ את ה-Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
