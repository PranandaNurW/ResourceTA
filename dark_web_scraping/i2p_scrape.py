import asyncio
import i2plib
import time
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import csv
import re
from datetime import datetime, timedelta
from pathlib import Path
import csv

BUFLEN = 1000
RESULT_DIR = "i2p_result"

def to_html(n, url, response):
    try:
        dirpath = Path(RESULT_DIR)
        dirpath.mkdir(parents=True, exist_ok=True)
        filename = f"page_{n+1}_{url.netloc}_r_Health.html"
        
        filepath = dirpath / filename
        with filepath.open("w") as f:
            f.write(response)
    except Exception as e:
        print(e)
    print("Extracted to html")

def to_csv(data):
    try:
        with open('i2p-scrape.csv', 'a', newline='', encoding="utf-8") as file:
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

async def request_page(session_name, url, sam_address, loop):
    print(f"Scrapping {url} ...")
    parse_url = urlparse(url)
    async with i2plib.Session(session_name, sam_address=sam_address, loop=loop):        
        async with i2plib.StreamConnection(session_name, parse_url.netloc, loop=loop, sam_address=sam_address) as c:
            try:
                t_start = time.perf_counter()
                c.write(f"GET {url} HTTP/1.1\nHost: {parse_url.netloc}\r\n\r\n".encode())
                chunk = await c.read(1000)
                
                text = chunk.decode()
                eol = text.find('\n')
                head = text[:eol]
                print(head)
                status = int(head.split(' ')[1])
                
                response = ""
                if status==200:
                    response = await c.read()
                else:
                    print("Nothing fetched, http status not ok")
            except Exception as e:
                pass
            else:
                t_stop = time.perf_counter()
                elapsed = t_stop-t_start
                next_url = get_next_page_url(response.decode(), url)
                print("Elapsed", elapsed)
                extract_data(response.decode(), url, elapsed)
                return next_url

async def connect_test(sam_address, loop, url):
    next_url = await request_page(f"test-i2p2_-1", url, sam_address, loop)
    for n in range(10):
        print("Establishing connection...")
        session_name = f"test-i2p2_{n}"
        next_url = await request_page(session_name, next_url, sam_address, loop)
        
    await asyncio.sleep(0.01)
    print(f"Done scrape")
        
if __name__ == "__main__":
    # change the url target here
    url = "udhdrtrcetjm5sxzskjyr5ztpeszydbh4dpl3pl4utgqqw2v4jna.b32.i2p/en/faq" #i2p-projekt.i2p
    sam_address = i2plib.get_sam_address()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(connect_test(sam_address=sam_address, loop=loop, url=url))
    loop.stop()
    loop.close()
