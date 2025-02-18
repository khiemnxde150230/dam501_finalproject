from flask import Flask, render_template, jsonify
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

@app.route('/api/apartment-demand')
def api_apartment_demand():
    analysis = Analysis()
    data_sale = analysis.get_apartment_demand(is_selling=1)
    data_rent = analysis.get_apartment_demand(is_selling=0)
    analysis.close()

    return jsonify({
        "sale": [{"district": row[0], "count": row[1]} for row in data_sale],
        "rent": [{"district": row[0], "count": row[1]} for row in data_rent]
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