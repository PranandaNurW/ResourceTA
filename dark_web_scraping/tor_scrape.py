from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse
import re
from datetime import datetime, timedelta
import csv
import time
from pathlib import Path
from stem import Signal
from stem.control import Controller

RESULT_DIR = "tor_result"

def get_tor_session():
    with Controller.from_port(port=9051) as controller:
        controller.authenticate("16:DAC157C0F2BF5AAB60C0FFB601CC75FA93C4FE0AF65595C8D1B002FB77")
        controller.signal(Signal.NEWNYM)
    
    session = requests.session()
    session.proxies = {'http':  'socks5h://127.0.0.1:9150',
                       'https': 'socks5h://127.0.0.1:9150'}
    return session

def to_csv(data):
    try:
        with open('tor-scrape.csv', 'a', newline='', encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerows(data)
    except Exception as e:
        print(e)
    print("Extracted to csv")

# extract data on teddit page
def extract_data(response, url, elapsed):
    try:
        soup = BeautifulSoup(response, 'lxml')
        all_data = []
        for entry in soup.find_all("div", "entry"):
            news = entry.find("div", "title")
            news_url = news.a.get("href")
            news_title = str(news.h2.string)

            news_meta = entry.find("div", "meta")
            news_meta_date = re.sub(" GMT", "", news_meta.span["title"])

            date_format = "%a, %d %b %Y %H:%M:%S"
            date = datetime.strptime(news_meta_date, date_format)
            date = date + timedelta(hours=8)

            data = [url, news_title, date, news_url, elapsed]
            all_data.append(data)
        to_csv(all_data)
    except Exception as e:
        print(e)

# get next teddit page url
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
        print("Elapsed", elapsed)
        extract_data(response.content, url, elapsed)
        return response, next_url

if __name__ == "__main__":
    # change the url target here
    url = "https://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/" #duckduckgo.onion
    response, next_url = request_page(url)
    for n in range(10):
        response, next_url = request_page(next_url)
    print("Done")