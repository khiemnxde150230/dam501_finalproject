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
        """Creates the database table with additional fields for detailed location, property ID, and description."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS danang_apartments (
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
                property_id TEXT,
                posted_time TEXT,
                description TEXT,
                is_selling BOOLEAN
            );
        """)
        self.conn.commit()

    def convert_price_to_number(self, price):
        """Converts price from text format (e.g., '2.3 tỷ' or '500 triệu') to numerical format."""
        price = price.lower().strip()
        if 'tỷ' in price and 'triệu' in price:
            ty, trieu = map(float, re.findall(r'(\d+)', price))
            price = ty * 1_000_000_000 + trieu * 1_000_000
        elif 'triệu' in price:
            trieu = float(re.search(r'(\d+)', price).group(1))
            price = trieu * 1_000_000
        elif 'tỷ' in price:
            ty = float(re.search(r'(\d+)', price).group(1))
            price = ty * 1_000_000_000
        else:
            return 0  # giá ảo, return 0 để lọc bỏ
        return price

    def convert_posted_time(self, posted_time):
        """Converts date format to 'dd-mm-yyyy' for consistency."""
        posted_time = posted_time.replace("-", "/")
        if "Hôm nay" in posted_time:
            return datetime.now().strftime("%d-%m-%Y")
        elif "Hôm qua" in posted_time:
            return (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")
        else:
            return posted_time.replace("/", "-")

    def fetch_detail_data(self, detail_url):
        """Fetches additional details from an apartment's detail page."""
        response = requests.get(detail_url)
        if response.status_code != 200:
            print(f"Lỗi khi lấy dữ liệu từ {detail_url}: {response.status_code}")
            return None, None, None, None, None

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract property ID
        property_id = None
        property_id_tag = soup.find("div", class_="property-id")
        if property_id_tag:
            property_id = property_id_tag.text.strip().replace("Mã tin: ", "")

        # Extract detailed location
        location_details = soup.find("div", class_="property-location")
        street, ward, district, city = None, None, None, None
        if location_details:
            location_parts = location_details.text.strip().split(", ")
            if len(location_parts) >= 4:
                street, ward, district, city = location_parts[:4]

        # Extract full description
        description_tag = soup.find("div", class_="description")
        description = description_tag.text.strip() if description_tag else ""

        return property_id, street, ward, district, city, description

    def fetch_page_data(self, url, is_selling):
        """Crawls apartment listing pages and fetches basic details along with links to detail pages."""
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
                area = float(
                    re.findall(r'(\d+)', listing.find("ul", class_="prop-attr").find_all("li")[0].text.strip())[0])
                bedrooms = int(re.search(r'(\d+) PN', listing.text).group(1)) if re.search(r'(\d+) PN',
                                                                                           listing.text) else 0
                bathrooms = int(re.search(r'(\d+) WC', listing.text).group(1)) if re.search(r'(\d+) WC',
                                                                                            listing.text) else 0
                location = listing.find("div", class_="prop-addr").text.strip()
                posted_time = self.convert_posted_time(listing.find("div", class_="prop-created").text.strip())

                price = self.convert_price_to_number(price)

                # Extract listing detail page link
                detail_link = listing.find("a", class_="prop-title")["href"]
                full_detail_url = f"https://mogi.vn{detail_link}"

                # Fetch additional details from detail page
                property_id, street, ward, district, city, description = self.fetch_detail_data(full_detail_url)

                if bedrooms > 5 or price < 1_000_000 or area < 10 or (is_selling and price < 100_000_000):
                    continue

                print(
                    f"- {title} | {price} | {area} | {location} | {bedrooms} PN | {bathrooms} WC | {posted_time} | {'Mua' if is_selling else 'Thuê'} | {property_id}")

                self.data.append(
                    [title, price, area, location, street, ward, district, city, bedrooms, bathrooms, property_id,
                     posted_time, description, is_selling])

            except (AttributeError, IndexError):
                continue

        return True

    def save_to_database(self):
        """Saves crawled data into SQLite database."""
        self.create_table()
        for row in self.data:
            row[11] = datetime.strptime(row[11], "%d-%m-%Y").strftime("%d-%m-%Y")
            self.cursor.execute("""
                INSERT INTO danang_apartments (title, price, area, location, street, ward, district, city, bedrooms, bathrooms, property_id, posted_time, description, is_selling)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, row)
        self.conn.commit()
        print("Dữ liệu đã được lưu vào bảng danang_apartments trong cơ sở dữ liệu.")

    def start_crawling(self, base_url):
        """Starts crawling apartment listings from the base URL."""
        page_number = 1
        while True:
            url = f"{base_url}?cp={page_number}"
            if not self.fetch_page_data(url, "mua" in base_url):
                break
            page_number += 1

    def close_connection(self):
        """Closes the database connection."""
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
