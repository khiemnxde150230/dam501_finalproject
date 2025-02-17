import time
import pandas as pd
from random import randint
from bs4 import BeautifulSoup
from selenium import webdriver
import sqlite3
import re


class RealEstateCrawler:
    def __init__(self, base_url, num_pages, table_name, db_name="data.db"):
        self.base_url = base_url
        self.num_pages = num_pages
        self.table_name = table_name
        self.db_name = db_name
        self.data = []
        self.driver = webdriver.Chrome()
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

    def create_table(self):
        self.cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                price REAL,
                area REAL,
                location TEXT
            );
        """)
        self.conn.commit()

    def convert_price_to_number(self, price):
        """Chuyển đổi giá trị tiền tệ sang số thực (vnd)"""
        price = price.replace(',', '').lower()
        if 'tỷ' in price:
            price = float(price.replace('tỷ', '').strip()) * 1_000_000_000
        elif 'triệu' in price:
            price = float(price.replace('triệu', '').strip()) * 1_000_000
        else:
            price = float(price)
        
        return price

    def convert_area_to_number(self, area):
        area = re.sub(r'[^0-9.,]', '', area)
        area = area.replace(',', '.')
        return float(area)

    def fetch_page_data(self, page_number):
        url = f"{self.base_url}/p{page_number}?avrs=1"
        print(f"Đang crawl trang: {url}")
        self.driver.get(url)
        time.sleep(randint(3, 6))  # tránh bị chặn

        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        listings = soup.find_all("div", class_="re__card-info")

        for listing in listings:
            try:
                title = listing.find("h3", class_="re__card-title").text.strip()
                price = listing.find("span", class_="re__card-config-price").text.strip()
                if price == "Giá thỏa thuận":
                    continue
                area = listing.find("span", class_="re__card-config-area").text.strip()

                location_span = listing.find("div", class_="re__card-location").find_all("span")
                if len(location_span) > 1:
                    location = location_span[1].text.strip()
                else:
                    location_div = listing.find("div", class_="re__card-location")
                    location = location_div.find("span").text.strip() if location_div else "N/A"

                price = self.convert_price_to_number(price)
                area = self.convert_area_to_number(area)

                print(f"- {title} | {price} | {area} | {location}")
                self.data.append([title, price, area, location])
            except AttributeError:
                continue

    def save_to_database(self):
        self.create_table()
        for row in self.data:
            self.cursor.execute(f"""
                INSERT INTO {self.table_name} (title, price, area, location)
                VALUES (?, ?, ?, ?);
            """, row)
        self.conn.commit()
        print(f"Dữ liệu đã được lưu vào bảng {self.table_name} trong cơ sở dữ liệu.")

    def start_crawling(self):
        for page in range(1, self.num_pages + 1):
            self.fetch_page_data(page)

        self.driver.quit()

    def close_connection(self):
        self.conn.close()


if __name__ == "__main__":
    print("CRAWL REAL ESTATE DATA from batdongsan.com.vn")
    base_url = input("Input URL to Crawl: ")
    num_pages = int(input("Input Number of Pages to Crawl: "))
    table_name = input("Input Table Name for the Data: ")

    crawler = RealEstateCrawler(base_url, num_pages, table_name, db_name="data.db")
    crawler.start_crawling()
    crawler.save_to_database()
    crawler.close_connection()