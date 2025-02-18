from flask import Flask, render_template, jsonify
from services.analysis import Analysis

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/apartment-demand')
def apartment_demand():
    return render_template('apartment_demand.html')

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

if __name__ == '__main__':
    app.run(debug=True)