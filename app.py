from flask import Flask, render_template, jsonify, request, send_file
from services.analysis import Analysis
import matplotlib.pyplot as plt
import io
import base64
import sqlite3
import numpy as np
from wordcloud import WordCloud

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/apartment-demand')
def apartment_demand():
    return render_template('apartment_demand.html')

@app.route('/apartment-area')
def apartment_area():
    return render_template('apartment_area.html')

# Q1
@app.route('/api/apartment-demand')
def api_apartment_demand():
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)

    analysis = Analysis()
    data_sale = analysis.get_apartment_demand(is_selling=1, year=year, month=month)
    data_rent = analysis.get_apartment_demand(is_selling=0, year=year, month=month)
    analysis.close()

    return jsonify({
        "sale": [{"district": (row[0]).replace("Quận ", "").replace(", Đà Nẵng", ""), "count": row[1]} for row in data_sale],
        "rent": [{"district": (row[0]).replace("Quận ", "").replace(", Đà Nẵng", ""), "count": row[1]} for row in data_rent]
    })

@app.route('/apartment-price-per-sqm')
def apartment_price_per_sqm():
    return render_template('apartment_price_per_sqm.html')

# Q2
@app.route('/api/average-sale-price-per-sqm')
def api_apartment_sale_price_per_sqm():
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    district = request.args.get('district')
    if district == "Tất cả Quận": district = None

    analysis = Analysis()
    data_sale = analysis.get_avg_price_data(is_selling=1, year=year, month=month, district=district)
    analysis.close()

    return jsonify({
        "average_price_data_sale": [
            {"year_month": row[0], "avg_price": row[1]} for row in data_sale
        ]
    })

@app.route('/api/average-rent-price-per-sqm')
def api_apartment_rent_price_per_sqm():
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    district = request.args.get('district')
    if district == "Tất cả Quận": district = None

    analysis = Analysis()
    data_rent = analysis.get_avg_price_data(is_selling=0, year=year, month=month, district=district)
    analysis.close()

    return jsonify({
        "average_price_data_rent": [
            {"year_month": row[0], "avg_price": row[1]} for row in data_rent
        ]
    })

@app.route('/api/apartment-area-selling')
def api_apartment_area_selling():
    analysis = Analysis()
    data = analysis.get_apartment_area_selling()
    analysis.close()

    result = {}
    for location, area_group, count in data:
        trimmed_location = location.replace("Quận ", "").replace(", Đà Nẵng", "")
        if trimmed_location not in result:
            result[trimmed_location] = {}
        result[trimmed_location][area_group] = count

    return jsonify(result)

@app.route('/api/apartment-area-renting')
def api_apartment_area_renting():
    analysis = Analysis()
    data = analysis.get_apartment_area_renting()
    analysis.close()

    result = {}
    for location, area_group, count in data:
        trimmed_location = location.replace("Quận ", "").replace(", Đà Nẵng", "")
        if trimmed_location not in result:
            result[trimmed_location] = {}
        result[trimmed_location][area_group] = count

    return jsonify(result)

@app.route('/api/apartment_demand_wordcloud')
def api_apartment_demand_wordcloud():
    is_selling = request.args.get('is_selling', type=int)
    analysis = Analysis()
    data = analysis.get_apartment_demand(is_selling=is_selling)
    analysis.close()

    district_counts = {(row[0]).replace("Quận ", "").replace(", Đà Nẵng", ""): row[1] for row in data}

    wordcloud = WordCloud(width=800, height=400, background_color="white").generate_from_frequencies(district_counts)

    img_io = io.BytesIO()
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.savefig(img_io, format="PNG", bbox_inches="tight")
    img_io.seek(0)

    return send_file(img_io, mimetype="image/png")

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

data = get_data_from_db()
selling_stats, renting_stats = analyze_data(data)
selling_plot = plot_data(selling_stats)
renting_plot = plot_data(renting_stats)

@app.route('/index3')
def index3():
    return render_template('index3.html',
                           selling_stats=selling_stats,
                           renting_stats=renting_stats,
                           selling_plot=selling_plot,
                           renting_plot=renting_plot)

@app.route('/api/available-districts')
def api_available_districts():
    analysis = Analysis()
    districts = [row[0] for row in analysis.api_available_districts()]
    analysis.close()

    return jsonify({"districts": districts})

if __name__ == '__main__':
    app.run(debug=True)