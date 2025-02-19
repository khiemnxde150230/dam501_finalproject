from services.database import Database

class Analysis:
    def __init__(self):
        self.db = Database()

    def get_apartment_demand(self, is_selling):
        query = """
        SELECT location, COUNT(*) as num_listings
        FROM danang_apartments
        WHERE is_selling = ?
        GROUP BY location
        ORDER BY num_listings DESC;
        """
        return self.db.query(query, (is_selling,))

    def get_avg_price_data(self):
        query = """
        SELECT posted_time AS year_month, bedrooms, AVG(price) as avg_price
        FROM danang_apartments
        GROUP BY year_month, bedrooms
        ORDER BY year_month DESC;
        """
        return self.db.query(query)

    def close(self):
        self.db.close()

