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
    
    def get_apartment_area_selling(self):
        query = """
        SELECT 
            location,
            CASE 
                WHEN area < 30 THEN '<30'
                WHEN area BETWEEN 30 AND 50 THEN '30-50'
                WHEN area BETWEEN 50 AND 100 THEN '50-100'
                ELSE '>100'
            END AS area_group,
            COUNT(*) AS count
        FROM danang_apartments
        WHERE is_selling = 1
        GROUP BY location, area_group
        ORDER BY location, area_group;
        """
        return self.db.query(query)
    
    def get_apartment_area_renting(self):
        query = """
        SELECT 
            location,
            CASE 
                WHEN area < 30 THEN '<30'
                WHEN area BETWEEN 30 AND 50 THEN '30-50'
                WHEN area BETWEEN 50 AND 100 THEN '50-100'
                ELSE '>100'
            END AS area_group,
            COUNT(*) AS count
        FROM danang_apartments
        WHERE is_selling = 0
        GROUP BY location, area_group
        ORDER BY location, area_group;
        """
        return self.db.query(query)

    def close(self):
        self.db.close()