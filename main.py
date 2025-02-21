import sqlite3
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from flask import Flask, render_template

def get_data_from_db():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    query = """
        SELECT id, title, price, location, is_selling FROM danang_apartments
    """
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    return data

def categorize_price(price, is_selling):
    if is_selling:
        if price < 3e9:
            return "1-3 tỷ"
        elif price < 5e9:
            return "3-5 tỷ"
        elif price < 10e9:
            return "5-10 tỷ"
        else:
            return ">10 tỷ"
    else:
        if price < 5e6:
            return "Dưới 5 triệu"
        elif price < 10e6:
            return "5-10 triệu"
        elif price < 20e6:
            return "10-20 triệu"
        else:
            return ">20 triệu"

def count_listings_by_price_and_location(data, is_selling):
    locations = [
        "Quận Sơn Trà, Đà Nẵng",
        "Quận Ngũ Hành Sơn, Đà Nẵng",
        "Quận Hải Châu, Đà Nẵng",
        "Quận Liên Chiểu, Đà Nẵng",
        "Quận Thanh Khê, Đà Nẵng"
    ]
    if is_selling:
        price_categories = ["1-3 tỷ", "3-5 tỷ", "5-10 tỷ", ">10 tỷ"]
    else:
        price_categories = ["Dưới 5 triệu", "5-10 triệu", "10-20 triệu", ">20 triệu"]
    
    stats = {loc: {cat: 0 for cat in price_categories} for loc in locations}
    
    for _, _, price, location, selling in data:
        if location in locations and selling == is_selling:
            category = categorize_price(price, is_selling)
            stats[location][category] += 1
    
    return stats

def analyze_data(data):
    selling_stats = count_listings_by_price_and_location(data, is_selling=1)
    renting_stats = count_listings_by_price_and_location(data, is_selling=0)
    return selling_stats, renting_stats

def plot_data(stats):
    plt.figure(figsize=(10, 6))
    price_categories = list(next(iter(stats.values())).keys())

    for location, values in stats.items():
        y_values = [values[cat] for cat in price_categories]
        plt.plot(price_categories, y_values, marker='o', label=location)
    
    plt.xlabel("Mức giá")
    plt.ylabel("Số lượng tin")
    plt.title("Phân bố số lượng tin rao bán/cho thuê theo mức giá và khu vực")
    plt.legend()
    plt.grid()
    
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    encoded_img = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()
    return encoded_img

app = Flask(__name__)

data = get_data_from_db()
selling_stats, renting_stats = analyze_data(data)
selling_plot = plot_data(selling_stats)
renting_plot = plot_data(renting_stats)

@app.route('/')
def index():
    return render_template('index3.html', 
                           selling_stats=selling_stats, 
                           renting_stats=renting_stats, 
                           selling_plot=selling_plot, 
                           renting_plot=renting_plot)

if __name__ == '__main__':
    print("Thống kê số lượng tin theo phân khúc giá và khu vực:")
    print("\nBán:")
    for location, categories in selling_stats.items():
        print(f"\n{location}:")
        for category, count in categories.items():
            print(f"  {category}: {count} tin")
    
    print("\nThuê:")
    for location, categories in renting_stats.items():
        print(f"\n{location}:")
        for category, count in categories.items():
            print(f"  {category}: {count} tin")
    
    app.run(debug=True)
