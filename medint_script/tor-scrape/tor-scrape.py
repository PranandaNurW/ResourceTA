import argparse
import csv
import re
import time
from datetime import datetime, timedelta
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from stem import Signal
from stem.control import Controller

CONSOLE_ARGUMENTS = None

def get_tor_session():
    with Controller.from_port(port=9051) as controller:
        controller.authenticate("tor,123")
        controller.signal(Signal.NEWNYM)

    session = requests.session()
    session.proxies = {'http':  'socks5h://127.0.0.1:9050',
                       'https': 'socks5h://127.0.0.1:9050'}
    return session

def to_csv(data):
    try:
        with open(CONSOLE_ARGUMENTS.output, 'a', newline='', encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerows(data)
    except Exception as e:
        print(e)
    print("Extracted to csv")

def extract_data(response, url):
    try:
        soup = BeautifulSoup(response, 'lxml')
        all_data = []
        isbreak = False
        for entry in soup.find_all("div", "entry"):
            news = entry.find("div", "title")
            news_url = news.a.get("href")
            news_title = str(news.h2.string)

            news_meta = entry.find("div", "meta")
            news_meta_date = re.sub(" GMT", "", news_meta.span["title"])

            date_format = "%a, %d %b %Y %H:%M:%S"
            date = datetime.strptime(news_meta_date, date_format)
            date = date + timedelta(hours=8)

            if CONSOLE_ARGUMENTS.today_only and (date.date() != datetime.now().date()):
                isbreak = True
                break

            data = [url, news_title, date, news_url]
            all_data.append(data)
        to_csv(all_data)
    except Exception as e:
        print(e)

    return isbreak

def get_next_page_url(response, url):
    try:
        url = urlparse(url)
        soup = BeautifulSoup(response, 'lxml')
        next_page = soup.find("div", "view-more-links")
        full_url = f"{url.scheme}://{url.netloc}{url.path}"
        if len(next_page) == 1:
            next_url = re.sub(url.path, next_page.contents[0].get("href"), full_url)
        else:
            next_url = re.sub(url.path, next_page.contents[1].get("href"), full_url)
    except Exception as e:
        print(e)
    finally:
        return next_url

def request_page(url):
    print(f"Scrapping {url} ...")
    try:
        t_start = time.perf_counter()
        session = get_tor_session()
        response = session.get(url)
        t_stop = time.perf_counter()
        elapsed = t_stop-t_start
        next_url = get_next_page_url(response.content, url)
    except Exception as e:
        print(e)
    finally:
        isbreak = extract_data(response.content, url)
        print("Elapsed", elapsed)
        return response, next_url, isbreak

def main(args):
    global CONSOLE_ARGUMENTS
    CONSOLE_ARGUMENTS = args

    # change the url target here
    url = CONSOLE_ARGUMENTS.url
    response, next_url, isbreak = request_page(url)
    for n in range(25):
        if isbreak:
            break
        response, next_url, isbreak = request_page(url)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TOR/onion site (teddit) scraper")
    parser.add_argument("--url", type=str, required=True)
    parser.add_argument("--output", type=str, default="tor-scrape.csv")
    parser.add_argument("--today-only", action='store_true')
    args = parser.parse_args()

    main(args)

    print("Done")