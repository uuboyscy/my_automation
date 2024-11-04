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
    mean_price_3mo = hist_3mo["Close"].mean()  # noqa: F841

    # Fetch stock price in the past 6 months
    hist_6mo = stock.history(period="6mo")
    high_price_6mo = hist_6mo["Close"].max()  # noqa: F841
    mean_price_6mo = hist_6mo["Close"].mean()  # noqa: F841

    # Fetch stock price in the past 1 year
    hist_1y = stock.history(period="1y")
    high_price_1y = hist_1y["Close"].max()  # noqa: F841
    mean_price_1y = hist_1y["Close"].mean()  # noqa: F841

    percentage = (current_price / high_price_3mo - 1) * 100
    return current_price, percentage


msg = "\nToday stock price:\n\n"

for stock in STOCK_LIST:
    try:
        price, percentage = get_stock_info(stock)
        msg += f"{stock}: Now {price:.2f}, relative high {percentage:.2f}%\n"
    except Exception as e:
        print(f"Fetching stock {stock} error: {e}")
        msg += f"{stock}: Unable to fetch data\n"

# Send notification
print(msg)
send_slack_notify(msg)
