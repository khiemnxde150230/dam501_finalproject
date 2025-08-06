import requests
import sqlite3
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time

class RealEstateCrawler:
    def __init__(self, db_name="data.db"):
        self.db_name = db_name
        self.data = []
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

    def create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS danang_batdongsan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                price REAL,
                area REAL,
                location TEXT,
                street TEXT,
                ward TEXT,
                district TEXT,
                city TEXT,
                bedrooms INTEGER,
                bathrooms INTEGER,
                posted_time TEXT,
                is_selling BOOLEAN,
                property_code TEXT,
                coordinates TEXT
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
        try:
            response = requests.get(detail_url, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Lỗi khi lấy dữ liệu chi tiết từ {detail_url}: {e}")
            return '', '', '', '', '', ''

        soup = BeautifulSoup(response.text, "html.parser")

        coordinates = ''
        iframe_tag = soup.find("iframe", title="map")
        if iframe_tag:
            iframe_src = iframe_tag.get("data-src")
            if iframe_src and "q=" in iframe_src:
                coords = iframe_src.split("q=")[-1].split("&")[0]
                coordinates = coords

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
        street, ward, district, city = None, None, None, None
        if detailed_address:
            location_parts = detailed_address.split(", ")
            if len(location_parts) >= 4:
                street, ward, district, city = location_parts[:4]

        return property_code, street, ward, district, city, coordinates

    def fetch_page_data(self, url, is_selling):
        print(f"Đang crawl trang: {url}")
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Lỗi khi lấy dữ liệu từ {url}: {e}")
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

                if bedrooms > 5 or price < 1_000_000 or area < 10 or (is_selling and price < 100_000_000):
                    continue

                detail_url = listing.find("a", class_="link-overlay")["href"]
                property_code, street, ward, district, city, coordinates = self.fetch_details(detail_url)

                print(f"- {title} | {price} | {area} | {location} | {street} | {ward} | {district} | {city} | {bedrooms} PN | {bathrooms} WC | {posted_time} | {'Mua' if is_selling else 'Thuê'} | Mã BĐS: {property_code} | Tọa độ: {coordinates}")
                self.data.append([title, price, area, location, street, ward, district, city, bedrooms, bathrooms, posted_time, is_selling, property_code, coordinates])
            except (AttributeError, IndexError, TypeError, ValueError) as e:
                print(f"Lỗi khi xử lý 1 tin đăng: {e}")
                continue
            time.sleep(1)

        return True

    def save_to_database(self):
        self.create_table()
        for row in self.data:
            row[10] = datetime.strptime(row[10], "%d-%m-%Y").strftime("%d-%m-%Y")
            self.cursor.execute("""
                INSERT INTO danang_batdongsan (title, price, area, location, street, ward, district, city, bedrooms, bathrooms, posted_time, is_selling, property_code, coordinates)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, row)
        self.conn.commit()
        print("Dữ liệu đã được lưu vào bảng danang_batdongsan trong cơ sở dữ liệu.")

    def start_crawling(self, base_url):
        page_number = 1
        while True:
            url = f"{base_url}?cp={page_number}"
            if not self.fetch_page_data(url, "mua" in base_url):
                break
            page_number += 1
            time.sleep(2)

    def close_connection(self):
        self.conn.close()

if __name__ == "__main__":
    print("CRAWL REAL ESTATE DATA from mogi.vn")
    base_url_buy = "https://mogi.vn/da-nang/mua-nha-dat"
    base_url_rent = "https://mogi.vn/da-nang/thue-nha-dat"

    crawler = RealEstateCrawler()
    crawler.start_crawling(base_url_buy)
    crawler.start_crawling(base_url_rent)
    crawler.save_to_database()
    crawler.close_connection()
