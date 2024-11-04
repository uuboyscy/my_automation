import os

import requests
import yfinance as yf

STOCK_NEWS_SLACK_NOTIFY_WEBHOOK = os.environ["STOCK_NEWS_SLACK_NOTIFY_WEBHOOK"]
STOCK_LIST = [
    "0050.TW",
    "00830.TW",
    "00662.TW",
    "00757.TW",
    "2330.TW",
    "00631L.TW",
    "00675L.TW",
]


def send_slack_notify(msg):
    slack_notify_webhook = STOCK_NEWS_SLACK_NOTIFY_WEBHOOK
    data = {"text": msg}
    try:
        res = requests.post(slack_notify_webhook, json=data)
        res.raise_for_status()
    except Exception as e:
        print(f"Error sending Slack Notify: {e}")

    print("Slack Notify sent.")


def get_stock_info(symbol):
    stock = yf.Ticker(symbol)

    # Fetch latest stock price
    hist = stock.history(period="1d")
    current_price = hist["Close"].iloc[-1]

    # Fetch stock price in the past 3 months
    hist_3mo = stock.history(period="3mo")
    high_price_3mo = hist_3mo["Close"].max()
    mean_price_3mo = hist_3mo["Close"].mean()

    # Fetch stock price in the past 6 months
    hist_6mo = stock.history(period="6mo")
    high_price_6mo = hist_6mo["Close"].max()
    mean_price_6mo = hist_6mo["Close"].mean()

    # Fetch stock price in the past 1 year
    hist_1yr = stock.history(period="1y")
    high_price_1yr = hist_1yr["Close"].max()
    mean_price_1yr = hist_1yr["Close"].mean()

    relative_high_percentage_3mo = (current_price / high_price_3mo - 1) * 100
    relative_high_percentage_6mo = (current_price / high_price_6mo - 1) * 100
    relative_high_percentage_1yr = (current_price / high_price_1yr - 1) * 100
    relative_mean_percentage_3mo = (current_price / mean_price_3mo - 1) * 100
    relative_mean_percentage_6mo = (current_price / mean_price_6mo - 1) * 100
    relative_mean_percentage_1yr = (current_price / mean_price_1yr - 1) * 100

    return {
        "current_price": current_price,
        "relative_high_percentage_3mo": relative_high_percentage_3mo,
        "relative_high_percentage_6mo": relative_high_percentage_6mo,
        "relative_high_percentage_1yr": relative_high_percentage_1yr,
        "relative_mean_percentage_3mo": relative_mean_percentage_3mo,
        "relative_mean_percentage_6mo": relative_mean_percentage_6mo,
        "relative_mean_percentage_1yr": relative_mean_percentage_1yr,
    }


msg = "\nToday stock relative price:\n\n"

for stock in STOCK_LIST:
    try:
        stock_info = get_stock_info(stock)
        msg += f"{stock}: Now {stock_info['current_price']:.2f}\n"
        msg += f"  [3mo] high {stock_info.get('relative_high_percentage_3mo', 'NaN'):.1f}%, mean {stock_info.get('relative_mean_percentage_3mo', 'NaN'):.1f}%\n"
        msg += f"  [6mo] high {stock_info.get('relative_high_percentage_6mo', 'NaN'):.1f}%, mean {stock_info.get('relative_mean_percentage_6mo', 'NaN'):.1f}%\n"
        msg += f"  [1yr] high {stock_info.get('relative_high_percentage_1yr', 'NaN'):.1f}%, mean {stock_info.get('relative_mean_percentage_1yr', 'NaN'):.1f}%\n"
    except Exception as e:
        print(f"Fetching stock {stock} error: {e}")
        msg += f"{stock}: Unable to fetch data\n"

# Send notification
print(msg)
send_slack_notify(msg)
