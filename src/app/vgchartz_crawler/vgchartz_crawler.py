import os
import re
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Literal

import pandas as pd
import requests
from bs4 import BeautifulSoup

# Email information
GMAIL_USERNAME = os.environ.get("GMAIL_USERNAME")
GMAIL_USER_EMAIL = f"{GMAIL_USERNAME}@gmail.com"
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
MAIL_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

# vgchartz configuration
VGCHARTZ_URL = "https://www.vgchartz.com/tools/hw_date.php?reg={region}&ending={ending}"
VGCHARTZ_REGION_LITERAL = Literal["Global", "USA", "Europe", "Japan"]
VGCHARTZ_ENDING_LITERAL = Literal["Monthly", "Weekly"]
VGCHARTZ_DEFAULT_REGION = "Global"
VGCHARTZ_DEFAULT_ENDING = "Monthly"

# Request configuration
HEADERS_STR = """accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
accept-encoding: gzip, deflate, br
accept-language: zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6
cache-control: max-age=0
cookie: __qca=P0-1382307012-1662978577564; PHPSESSID=9cko4pq074ej9j4mhcremhp15u; geoCountry=US; uniqueFlag=1; VGCBE=b1; __utma=154313151.1784641658.1662978577.1662978577.1662978577.1; __utmb=154313151; __utmc=154313151; __utmz=154313151.1662978577.1.1.utmccn=(referral)|utmcsr=google.com|utmcct=/|utmcmd=referral; qcSxc=1662978577566; __qca=P0-1382307012-1662978577564; _pbjs_userid_consent_data=3524755945110770; _lr_retry_request=true; _lr_env_src_ats=false; cto_bundle=bX8Qp19MQ2Fjc250Q0FYM2FId094eXFLWlc4dkdiaCUyRlN4YVZQRzdyaEZmdHpwTk9qQ25SQzZaTWxMZkZ1THA1eENPU0UyRFBCWGgwT0VHMnRKeDhxaG56bUswTjF1T0ZaZ0tYT2VYT1RKRldNQ09DRDhZNjZnbklvdEVWeDRrWnpkc2tycGs2WW4zamdjck56REF0Y0RmMjc5QSUzRCUzRA; cto_bidid=bBeOA19NJTJCb0RpdEpNSGx0U2h0Nks4N05WVGpJSDdYbmRlVGF6V3FxRWRNOXklMkZ1YWVSJTJGYmtDYWtyd3hkVFlvRzE0Q0ZrMGIxOU43MzZHMk5UaE1KMEpIJTJCZHRra29Xa3BQUENlaTNES2NOQWFqbEMwJTNE
referer: https://www.vgchartz.com/tools/hw_date.php
sec-ch-ua: "Google Chrome";v="105", "Not)A;Brand";v="8", "Chromium";v="105"
sec-ch-ua-mobile: ?1
sec-ch-ua-platform: "Android"
sec-fetch-dest: document
sec-fetch-mode: navigate
sec-fetch-site: same-origin
sec-fetch-user: ?1
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Mobile Safari/537.36"""
HEADERS = {r.split(": ")[0]: r.split(": ")[1] for r in HEADERS_STR.split("\n")}


def _e_vgchartz_html(
    region: VGCHARTZ_REGION_LITERAL,
    ending: VGCHARTZ_ENDING_LITERAL,
) -> str:
    url = VGCHARTZ_URL.format(
        region=region,
        ending=ending,
    )
    return requests.get(url, headers=HEADERS).text


def _t_vgchartz_html_to_json(vgchartz_html: str) -> dict:
    def convert_js_to_py_json_str(js_raw: str) -> str:
        js_raw_tmp = (
            js_raw.split("window.chart = new Highcharts.StockChart(")[1]
            .split(");")[0]
            .replace("\n", " ")
            .replace("\t", " ")
            .replace("'", '"')
            .replace("{", "{ ")
        )

        key_set = set(re.findall(r"[a-zA-Z0-9]*:", js_raw_tmp))

        for origin_key in key_set:
            new_key = '"' + origin_key
            new_key = new_key.replace(":", '":')
            js_raw_tmp = js_raw_tmp.replace(origin_key, new_key)

        json_raw = js_raw_tmp.replace("true", "True").replace("false", "False")

        return json_raw

    soup = BeautifulSoup(vgchartz_html, "html.parser")

    js_raw = soup.select_one('[id="chart_body"] script').text
    js_raw = " ".join([i for i in js_raw.split("\n") if "//" not in i])

    return eval(convert_js_to_py_json_str(js_raw))


def _t_vgchartz_json_to_df(vgchartz_json: dict) -> pd.DataFrame:
    df_list = list()
    for device_info_dict in vgchartz_json["series"]:
        device_name = device_info_dict["name"]
        data = device_info_dict["data"]

        df = pd.DataFrame(data=data)
        df.columns = ["timestamp_ms", "value"]

        df["device_name"] = device_name
        df["datetime"] = df["timestamp_ms"].apply(
            lambda ts_ms: pd.to_datetime(ts_ms, unit="ms")
        )
        df["year"] = df["datetime"].apply(lambda dt: dt.year)
        df["month"] = df["datetime"].apply(lambda dt: dt.month)

        df_list.append(df)

    return pd.concat(df_list)


def vgchartz_crawler(
    region: VGCHARTZ_REGION_LITERAL = VGCHARTZ_DEFAULT_REGION,
    ending: VGCHARTZ_ENDING_LITERAL = VGCHARTZ_DEFAULT_ENDING,
) -> str:
    """Return file name."""
    vgchartz_html = _e_vgchartz_html(region=region, ending=ending)
    vgchartz_json = _t_vgchartz_html_to_json(vgchartz_html)
    vgchartz_df = _t_vgchartz_json_to_df(vgchartz_json)

    output_file_folder = Path("./tmp")
    output_file_folder.mkdir(exist_ok=True)
    output_file_name = f"vgchartz_{region}_{ending}.xlsx"
    output_file_path = output_file_folder / output_file_name
    vgchartz_df.to_excel(output_file_path, index=False)

    return str(output_file_path)


def send_email(
    receiver_email: str,
    subject: str,
    msg: str,
    file_path: str | None = None,
) -> bool:
    """send_email."""
    # Create a multipart message
    message = MIMEMultipart()
    message["From"] = GMAIL_USER_EMAIL
    message["To"] = receiver_email
    message["Subject"] = subject

    # Add body to email
    message.attach(MIMEText(msg, "plain"))

    if file_path:
        # Attach file
        attachment = open(file_path, "rb")

        # Instance of MIMEBase and named as part
        part = MIMEBase("application", "octet-stream")
        part.set_payload((attachment).read())

        # Encode file in ASCII characters to send by email
        encoders.encode_base64(part)

        # Add header as key/value pair to attachment part
        part.add_header("Content-Disposition", f"attachment; filename= {file_path}")

        # Attach the instance 'part' to 'message'
        message.attach(part)

        attachment.close()

    try:
        # Connect to the SMTP server
        with smtplib.SMTP_SSL(MAIL_SERVER, SMTP_PORT) as server:
            # server.starttls()  # Secure the connection with TLS
            server.login(GMAIL_USERNAME, GMAIL_APP_PASSWORD)
            text = message.as_string()
            server.sendmail(GMAIL_USERNAME, receiver_email, text)

            print("Email sent!")

            return True
    except smtplib.SMTPResponseException:
        print("Failed to send email!")
        return False


def main() -> None:
    for region in VGCHARTZ_REGION_LITERAL.__args__:
        for ending in VGCHARTZ_ENDING_LITERAL.__args__:
            file_path = vgchartz_crawler(region=region, ending=ending)

            print(file_path)

            send_email(
                GMAIL_USER_EMAIL,
                file_path,
                "",
                file_path,
            )

            send_email(
                os.getenv("RECEIVER_EMAIL_1"),
                file_path,
                "",
                file_path,
            )

            send_email(
                os.getenv("RECEIVER_EMAIL_2"),
                file_path,
                "",
                file_path,
            )


if __name__ == "__main__":
    main()
