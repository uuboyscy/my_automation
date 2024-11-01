import json
import os
import re
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from bs4 import BeautifulSoup


def shorten_url(url: str) -> str:
    try:
        res = requests.get(f"http://tinyurl.com/api-create.php?url={url}")
        res.raise_for_status()
    except requests.HTTPError:
        return url

    return res.text


def get_tw_stock_info() -> str:
    url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ETWII"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Latest closing price
        price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]

        # Get price change
        previous_close = data["chart"]["result"][0]["meta"]["chartPreviousClose"]
        change_percent = (price - previous_close) / previous_close * 100

        # Set the color based on rise or fall
        color = "red" if change_percent >= 0 else "green"

        return f"<strong>TAIEX (Taiwan Weighted Index)</strong>: {price:.2f} (<span style='color:{color};'>{change_percent:+.2f}%</span>)"
    except Exception as e:
        print(f"Unable to fetch TAIEX information: {e}")
        return "<strong>TAIEX (Taiwan Weighted Index)</strong>: Unable to retrieve data"


def get_us_stock_info():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = json.loads(response.text)

        # Latest closing price
        price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]

        # Get price change
        previous_close = data["chart"]["result"][0]["meta"]["chartPreviousClose"]
        change_percent = (price - previous_close) / previous_close * 100

        # Set the color based on rise or fall
        color = "red" if change_percent >= 0 else "green"

        return f"<strong>S&P 500</strong>: {price:.2f} (<span style='color:{color};'>{change_percent:+.2f}%</span>)"
    except Exception as e:
        print(f"Unable to fetch S&P 500 information: {e}")
        return "<strong>S&P 500</strong>: Unable to retrieve data"


def get_tw_news() -> str:
    url = "https://tw.stock.yahoo.com/tw-market/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Fetch the first 5 news
    news_items = soup.find_all("div", {"class": "Py(14px)"})[:5]

    news = []
    for item in news_items:
        title = item.find("h3").text.strip()
        link = item.find("a")["href"]
        short_link = shorten_url(link)
        news.append(f"{title}\n{short_link}\n")

    return "\n".join(news) if news else "Unable to fetch TW stock news"


def get_us_news() -> str:
    url = "https://finance.yahoo.com/topic/stock-market-news/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Fetch the first 5 news
    news_items = soup.find_all("div", {"class": "Py(14px)"})[:5]

    news = []
    for item in news_items:
        title = item.find("h3").text.strip()
        link = item.find("a")["href"]
        if not link.startswith("http"):
            link = "https://finance.yahoo.com" + link
        short_link = shorten_url(link)
        news.append(f"{title}\n{short_link}\n")

    return "\n".join(news) if news else "Unable to fetch US stock news"


def send_slack_notify(message: str) -> None:
    slack_notify_webhook = os.environ.get("STOCK_NEWS_SLACK_NOTIFY_WEBHOOK")
    data = {"text": message}

    try:
        res = requests.post(slack_notify_webhook, json=data)
        res.raise_for_status()
    except requests.HTTPError as e:
        print("Error sending Slack Notify:", e)


def send_email(content):
    sender_email = os.environ["STOCK_NEWS_SENDER_EMAIL"]
    receiver_email = os.environ["STOCK_NEWS_RECEIVER_EMAIL"]
    password = os.environ["STOCK_NEWS_EMAIL_PASSWORD"]

    message = MIMEMultipart("alternative")
    message["Subject"] = (
        f"Daily stock information and news - {datetime.now().strftime('%Y-%m-%d')}"
    )
    message["From"] = sender_email
    message["To"] = receiver_email

    # 轉換純文本內容為HTML
    html = f"""\
    <html>
      <body>
        {content}
      </body>
    </html>
    """

    part = MIMEText(html, "html")
    message.attach(part)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent successfully")
    except Exception as e:
        print(f"Error sending email: {e}")


def generate_notification_content() -> str:
    content = "<h2>Today's Stock Information and News:</h2>"

    try:
        tw_info = get_tw_stock_info()
        content += f"<p>{tw_info}</p>"
    except Exception as e:
        print(f"Error fetching Taiwan stock information: {e}")
        content += "<p><strong>TAIEX Index</strong>: Information retrieval failed</p>"

    try:
        us_info = get_us_stock_info()
        content += f"<p>{us_info}</p>"
    except Exception as e:
        print(f"Error fetching US stock information: {e}")
        content += "<p><strong>S&P 500 Index</strong>: Information retrieval failed</p>"

    content += "<h3>Taiwan Stock Market Hot News:</h3>"
    try:
        tw_news = get_tw_news()
        content += f"<p>{tw_news.replace('\n', '<br>')}</p>"
    except Exception as e:
        print(f"Error fetching Taiwan stock news: {e}")
        content += "<p>Failed to retrieve Taiwan stock news</p>"

    content += "<h3>US Stock Market Hot News:</h3>"
    try:
        us_news = get_us_news()
        content += f"<p>{us_news.replace('\n', '<br>')}</p>"
    except Exception as e:
        print(f"Error fetching US stock news: {e}")
        content += "<p>Failed to retrieve US stock news</p>"

    return content


def send_notifications(content):
    # Prepare Slack message
    line_message = content.replace("<strong>", "").replace("</strong>", "")
    line_message = line_message.replace("<br>", "\n")
    line_message = line_message.replace("<p>", "").replace("</p>", "\n")
    line_message = line_message.replace("<h2>", "\n").replace("</h2>", "\n")
    line_message = line_message.replace("<h3>", "\n").replace("</h3>", "\n")
    line_message = re.sub(r"<span.*?>", "", line_message)
    line_message = re.sub(r"</span>", "", line_message)

    # Send notification
    send_email(content)
    send_slack_notify(line_message)


def main():
    content = generate_notification_content()

    print(content)
    send_notifications(content)


if __name__ == "__main__":
    main()
