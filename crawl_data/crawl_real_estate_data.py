import requests
import sqlite3
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

class RealEstateCrawler:
    def __init__(self, db_name="data.db"):
        self.db_name = db_name
        self.data = []
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

    def create_table(self):
        self.cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS danang_apartments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                price REAL,
                area REAL,
                location TEXT,
                bedrooms INTEGER,
                bathrooms INTEGER,
                posted_time TEXT,
                is_selling BOOLEAN
            );
        """)
        self.conn.commit()

    def convert_price_to_number(self, price):
        price = price.lower().strip()
        if 'tỷ' in price and 'triệu' in price:
            tỷ, triệu = map(float, re.findall(r'(\d+)', price))
            price = tỷ * 1_000_000_000 + triệu * 1_000_000
        elif 'triệu' in price and 'nghìn' in price:
            triệu, nghìn = map(float, re.findall(r'(\d+)', price))
            price = triệu * 1_000_000 + nghìn * 1_000
        elif 'tỷ' in price:
            tỷ = float(re.search(r'(\d+)', price).group(1))
            price = tỷ * 1_000_000_000
        elif 'triệu' in price:
            triệu = float(re.search(r'(\d+)', price).group(1))
            price = triệu * 1_000_000
        else:
            return 0  # giá ảo, return 0 để lọc bỏ
        return price

    def convert_posted_time(self, posted_time):
        posted_time = posted_time.replace("-", "/")
        if "Hôm nay" in posted_time:
            return datetime.now().strftime("%d-%m-%Y")
        elif "Hôm qua" in posted_time:
            return (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")
        else:
            return posted_time.replace("/", "-")

    def fetch_page_data(self, url, is_selling):
        print(f"Đang crawl trang: {url}")

        response = requests.get(url)
        if response.status_code != 200:
            print(f"Lỗi khi lấy dữ liệu từ {url}: {response.status_code}")
            return False

        soup = BeautifulSoup(response.text, "html.parser")
        listings = soup.find("ul", class_="props")

        if listings is None or not listings.find_all("li"):
            print("Không còn dữ liệu nào trên trang này.")
            return False

        for listing in listings.find_all("li"):
            try:
                title = listing.find("h2", class_="prop-title").text.strip()
                price = listing.find("div", class_="price").text.strip()
                area = float(re.findall(r'(\d+)', listing.find("ul", class_="prop-attr").find_all("li")[0].text.strip())[0])
                bedrooms = int(re.search(r'(\d+) PN', listing.text).group(1)) if re.search(r'(\d+) PN', listing.text) else 0
                bathrooms = int(re.search(r'(\d+) WC', listing.text).group(1)) if re.search(r'(\d+) WC', listing.text) else 0
                location = listing.find("div", class_="prop-addr").text.strip()
                posted_time = self.convert_posted_time(listing.find("div", class_="prop-created").text.strip())

                price = self.convert_price_to_number(price)

                if bedrooms > 5 or price < 1_000_000 or area < 10 or (is_selling and price < 100_000_000): #lọc bỏ mấy bài vô lý
                    continue

                print(f"- {title} | {price} | {area} | {location} | {bedrooms} PN | {bathrooms} WC | {posted_time} | {'Mua' if is_selling else 'Thuê'}")
                self.data.append([title, price, area, location, bedrooms, bathrooms, posted_time, is_selling])
            except (AttributeError, IndexError):
                continue

        return True

    def save_to_database(self):
        self.create_table()
        for row in self.data:
            row[6] = datetime.strptime(row[6], "%d-%m-%Y").strftime("%d-%m-%Y")
            self.cursor.execute(f"""
                INSERT INTO danang_apartments (title, price, area, location, bedrooms, bathrooms, posted_time, is_selling)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, row)
        self.conn.commit()
        print("Dữ liệu đã được lưu vào bảng danang_apartments trong cơ sở dữ liệu.")

    def start_crawling(self, base_url):
        page_number = 1
        while True:
            url = f"{base_url}?cp={page_number}"
            if not self.fetch_page_data(url, "mua" in base_url):
                break
            page_number += 1

    def close_connection(self):
        self.conn.close()

if __name__ == "__main__":
    print("CRAWL REAL ESTATE DATA from mogi.vn")
    base_url_buy = "https://mogi.vn/da-nang/mua-can-ho"
    base_url_rent = "https://mogi.vn/da-nang/thue-can-ho"

    crawler = RealEstateCrawler()
    crawler.start_crawling(base_url_buy)
    crawler.start_crawling(base_url_rent)
    crawler.save_to_database()
    crawler.close_connection()