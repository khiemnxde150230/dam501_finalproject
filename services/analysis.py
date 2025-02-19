from services.database import Database

class Analysis:
    def __init__(self):
        self.db = Database()

    def get_apartment_demand(self, is_selling, year=None, month=None):
        query = """
        SELECT location, COUNT(*) as num_listings
        FROM danang_apartments
        WHERE is_selling = ?
        """
        params = [is_selling]

        if year:
            query += " AND substr(posted_time, 7, 4) = ?"
            params.append(str(year))

        if month:
            query += " AND substr(posted_time, 4, 2) = ?"
            params.append(f"{int(month):02d}")

        query += " GROUP BY location ORDER BY num_listings DESC;"
        return self.db.query(query, tuple(params))
    
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