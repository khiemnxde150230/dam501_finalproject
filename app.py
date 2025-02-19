from flask import Flask, render_template, jsonify, request, send_file
from services.analysis import Analysis
import matplotlib.pyplot as plt
import io
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

@app.route('/api/apartment-area-selling')
def api_apartment_area_selling():
    analysis = Analysis()
    data = analysis.get_apartment_area_selling()
    analysis.close()

    result = {}
    for location, area_group, count in data:
        if location not in result:
            result[location] = {}
        result[location][area_group] = count

    return jsonify(result)

@app.route('/api/apartment-area-renting')
def api_apartment_area_renting():
    analysis = Analysis()
    data = analysis.get_apartment_area_renting()
    analysis.close()

    result = {}
    for location, area_group, count in data:
        if location not in result:
            result[location] = {}
        result[location][area_group] = count

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

if __name__ == '__main__':
    app.run(debug=True)