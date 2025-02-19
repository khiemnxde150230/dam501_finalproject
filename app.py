from flask import Flask, render_template, jsonify, request
from services.analysis import Analysis

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
        "sale": [{"district": row[0], "count": row[1]} for row in data_sale],
        "rent": [{"district": row[0], "count": row[1]} for row in data_rent]
    })

@app.route('/apartment-average-data')
def apartment_average_data():
    return render_template('apartment_average_data.html')

# Q2
@app.route('/api/apartment-average-data')
def api_apartment_average_data():
    analysis = Analysis()
    data_sale = analysis.get_avg_price_data()
    analysis.close()

    return jsonify({
        "average_price_data": [
            {"year_month": row[0], "bedrooms": row[1], "avg_price": row[2]} for row in data_sale
        ]
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

if __name__ == '__main__':
    app.run(debug=True)