import os

import requests
import yfinance as yf

# Define ETF list
etfs = ["0050.TW", "00830.TW", "00662.TW", "00757.TW"]


def get_etf_data(symbol, period="5y"):
    etf = yf.Ticker(symbol)
    hist = etf.history(period=period)
    return hist["Close"]


def calculate_drawdown(price):
    peak = price.cummax()
    drawdown = (price - peak) / peak
    return drawdown


def analyze_etf(symbol):
    prices = get_etf_data(symbol)
    drawdown = calculate_drawdown(prices)

    # Calculate average historical drawdown and maximum drawdown
    avg_drawdown = drawdown.mean()
    max_drawdown = drawdown.min()

    # Set personalized drawdown thresholds
    light_drawdown = avg_drawdown / 3
    medium_drawdown = avg_drawdown * 2 / 3
    heavy_drawdown = (
        max_drawdown * 0.8
    )  # Use 80% of max drawdown as heavy drawdown threshold

    # Get the current price and calculate current drawdown
    current_price = prices.iloc[-1]
    current_drawdown = drawdown.iloc[-1]

    return {
        "symbol": symbol,
        "current_price": current_price,
        "current_drawdown": current_drawdown,
        "light_drawdown": light_drawdown,
        "medium_drawdown": medium_drawdown,
        "heavy_drawdown": heavy_drawdown,
    }


def send_line_notify(message):
    line_notify_token = os.environ["LINE_NOTIFY_TOKEN"]
    line_notify_api = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {line_notify_token}"}
    data = {"message": message}
    try:
        response = requests.post(line_notify_api, headers=headers, data=data)
        if response.status_code == 200:
            print(f"Line Notify sent. Status code: {response.status_code}")
        else:
            print(
                f"Failed to send Line Notify. Status code: {response.status_code}, Response: {response.text}"
            )
    except Exception as e:
        print(f"Error sending Line Notify: {e}")


def main():
    messages = []
    for etf in etfs:
        result = analyze_etf(etf)

        message = f"\nETF: {result['symbol']}\n"
        message += f"Current Price: {result['current_price']:.2f}\n"
        message += f"Current Drawdown: {result['current_drawdown']:.2%}\n"

        if result["current_drawdown"] <= result["heavy_drawdown"]:
            message += "Warning: Heavy drawdown! Consider a significant addition\n"
        elif result["current_drawdown"] <= result["medium_drawdown"]:
            message += "Notice: Medium drawdown, consider a moderate addition\n"
        elif result["current_drawdown"] <= result["light_drawdown"]:
            message += "Tip: Light drawdown, consider a small addition\n"

        messages.append(message)

    # Send Line notification
    send_line_notify("".join(messages))


if __name__ == "__main__":
    main()
