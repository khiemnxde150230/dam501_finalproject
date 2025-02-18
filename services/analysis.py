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

    def close(self):
        self.db.close()