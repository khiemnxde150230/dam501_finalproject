from services.visualization import Visualization

def visualize_apartment_area_data():
    selling_query = """
        SELECT 
            location,
            CASE 
                WHEN area < 30 THEN '<30'
                WHEN area BETWEEN 30 AND 50 THEN '30-50'
                WHEN area BETWEEN 50 AND 100 THEN '50-100'
                ELSE '>100'
            END AS area_group,
            COUNT(*) AS count
        FROM danang_batdongsan
        WHERE is_selling = 1
        GROUP BY location, area_group
        ORDER BY location, area_group;
    """

    renting_query = """
        SELECT 
            location,
            CASE 
                WHEN area < 30 THEN '<30'
                WHEN area BETWEEN 30 AND 50 THEN '30-50'
                WHEN area BETWEEN 50 AND 100 THEN '50-100'
                ELSE '>100'
            END AS area_group,
            COUNT(*) AS count
        FROM danang_batdongsan
        WHERE is_selling = 0
        GROUP BY location, area_group
        ORDER BY location, area_group;
    """
    visualization = Visualization()
    visualization.visualize_apartment_area_selling_data(selling_query)
    visualization.visualize_apartment_area_renting_data(renting_query)

visualize_apartment_area_data()