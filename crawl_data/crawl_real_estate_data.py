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
                detailed_address TEXT,
                bedrooms INTEGER,
                bathrooms INTEGER,
                posted_time TEXT,
                is_selling BOOLEAN,
                real_estate_code TEXT
            );
        """)
        self.conn.commit()


    def convert_price_to_number(self, price):
        price = price.lower().strip()
        if 'tỷ' in price and 'triệu' in price:
            ty, trieu = map(float, re.findall(r'(\d+)', price))
            price = ty * 1_000_000_000 + trieu * 1_000_000
        elif 'triệu' in price and 'nghìn' in price:
            trieu, nghin = map(float, re.findall(r'(\d+)', price))
            price = trieu * 1_000_000 + nghin * 1_000
        elif 'tỷ' in price:
            ty = float(re.search(r'(\d+)', price).group(1))
            price = ty * 1_000_000_000
        elif 'triệu' in price:
            trieu = float(re.search(r'(\d+)', price).group(1))
            price = trieu * 1_000_000
        else:
            return 0
        return price

    def convert_posted_time(self, posted_time):
        posted_time = posted_time.replace("-", "/")
        if "Hôm nay" in posted_time:
            return datetime.now().strftime("%d-%m-%Y")
        elif "Hôm qua" in posted_time:
            return (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")
        else:
            return posted_time.replace("/", "-")

    def fetch_details(self, detail_url):
        response = requests.get(detail_url)
        if response.status_code != 200:
            print(f"Lỗi khi lấy dữ liệu chi tiết từ {detail_url}: {response.status_code}")
            return '', ''

        soup = BeautifulSoup(response.text, "html.parser")

        property_code = ''
        info_attrs = soup.find("div", class_="info-attrs")
        if info_attrs:
            for info_attr in info_attrs.find_all("div", class_="info-attr"):
                label = info_attr.find("span", text="Mã BĐS")
                if label:
                    property_code = info_attr.find_all("span")[1].text.strip()
                    break

        address_tag = soup.find("div", class_="address")
        detailed_address = address_tag.text.strip() if address_tag else ''

        return property_code, detailed_address


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

                detail_url = listing.find("a", class_="link-overlay")["href"]
                property_code, detailed_address = self.fetch_details(detail_url)

                print(f"- {title} | {price} | {area} | {location} | {detailed_address} | {bedrooms} PN | {bathrooms} WC | {posted_time} | {'Mua' if is_selling else 'Thuê'} | Mã BĐS: {property_code}")
                self.data.append([title, price, area, location, detailed_address, bedrooms, bathrooms, posted_time, is_selling, property_code])
            except (AttributeError, IndexError):
                continue

        return True

    def save_to_database(self):
        self.create_table()
        for row in self.data:
            row[7] = datetime.strptime(row[7], "%d-%m-%Y").strftime("%d-%m-%Y")
            self.cursor.execute(f"""
                INSERT INTO danang_apartments (title, price, area, location, detailed_address, bedrooms, bathrooms, posted_time, is_selling, real_estate_code)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
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