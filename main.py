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

# פרטי טלגרם
BOT_TOKEN = "7921226841:AAFt6Gv2XdUg4tXsid9g70A_7-p-uv7OHO0"
CHAT_ID = 683024750

# התאמה למחיר Plus500
PLUS500_FACTOR = 27
INVESTMENT_USD = 1000  # סכום השקעה קבוע

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("שגיאה בשליחת הודעה:", e)

# בדיקת תבנית Bullish Engulfing
def is_bullish_engulfing(prev, curr):
    return (
        prev['Close'] < prev['Open'] and  # נר קודם אדום
        curr['Close'] > curr['Open'] and  # נר נוכחי ירוק
        curr['Open'] < prev['Close'] and
        curr['Close'] > prev['Open']
    )

# ניתוח גרף זהב ובדיקת תנאים
def analyze_gold():
    try:
        data = yf.download(tickers="GC=F", interval="1m", period="1d")
    except Exception as e:
        print("שגיאה בשליפת נתונים:", e)
        return

    if data.empty:
        print("אין נתונים זמינים")
        return

    data = ta.add_all_ta_features(data, open="Open", high="High", low="Low", close="Close", volume="Volume")

    last = data.iloc[-1]
    prev = data.iloc[-2]
    price = float(last['Close'])
    plus500_price = round(price - PLUS500_FACTOR, 2)

    rsi = last['momentum_rsi']
    macd = last['trend_macd']
    macd_signal = last['trend_macd_signal']
    bbm = last['volatility_bbm']
    bbw = last['volatility_bbw']
    lower_band_flexible = bbm - bbw  # גמיש יותר מבולינגר קלאסי

    entry_reason = None

    # תנאי כניסה לפי אינדיקטורים
    if rsi < 60 and (macd > macd_signal or macd > 0) and price < lower_band_flexible:
        entry_reason = "איתות לפי RSI, MACD ובולינגר"

    # או לפי תבנית נר
    elif is_bullish_engulfing(prev, last):
        entry_reason = "תבנית Bullish Engulfing (נר ירוק חזק)"

    # שליחת איתות אם יש סיבה
    if entry_reason:
        quantity = round(INVESTMENT_USD / plus500_price, 2)
        tp = round(plus500_price + 5, 2)
        sl = round(plus500_price - 5, 2)

        text = (
            f"📈 איתות קנייה בזהב!\n\n"
            f"💰 מחיר כניסה: {round(price, 2)}\n"
            f"💸 מחיר בפלוס500: {plus500_price}\n\n"
            f"✅ המלצה: לקנות עכשיו\n"
            f"📊 כמות מומלצת: {quantity} יחידות (1000$)\n"
            f"🎯 יעד רווח: {tp}\n"
            f"🛑 סטופ: {sl}\n\n"
            f"📌 סיבה: {entry_reason}\n"
            f"⏱️ זמן: {datetime.now().strftime('%H:%M:%S')}"
        )
        send_telegram_message(text)

# לולאת ריצה של הבוט
def run_bot_loop():
    send_telegram_message("🤖 הבוט התחיל לפעול (איתותים גמישים + תבנית נר)")
    while True:
        analyze_gold()
        time.sleep(60)

# מסלולים לווב
@app.route('/')
def home():
    return "✅ Gold Bot is running (Flexible Alerts + Candlestick)."

@app.route('/status')
def status():
    return "Bot OK ✅"

# הפעלת הלולאה ברקע
threading.Thread(target=run_bot_loop).start()

# הרצת האפליקציה
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
