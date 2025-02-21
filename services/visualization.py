from services.database import Database
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

class Visualization:
    def __init__(self):
        self.db = Database()

    def visualize_apartment_area_selling_data(self, selling_query):
        # Fetch data from database
        df = pd.DataFrame(self.db.query(selling_query), columns=['location', 'area_group', 'count'])
        df['location'] = df['location'].str[5:-9]
        df['type'] = 'Bán'

        sns.set_theme(style="whitegrid")
        
        # Create a bar plot
        plt.figure(figsize=(12, 6))
        sns.barplot(data=df, x='location', y='count', hue='area_group', palette='viridis')
        
        plt.xlabel("Quận")
        plt.ylabel("Số lượng")
        plt.title("Thống kê diện tích các căn hộ cần bán theo quận")
        plt.legend(title="Diện tích")
        
        plt.xticks(rotation=45)
        plt.show()

    def visualize_apartment_area_renting_data(self, renting_query):
        # Fetch data from database
        df = pd.DataFrame(self.db.query(renting_query), columns=['location', 'area_group', 'count'])
        df['location'] = df['location'].str[5:-9]
        df['type'] = 'Cho thuê'
        
        # Set visualization style
        sns.set_theme(style="whitegrid")
        
        # Create a bar plot
        plt.figure(figsize=(12, 6))
        sns.barplot(data=df, x='location', y='count', hue='area_group', palette='viridis')
        
        plt.xlabel("Quận")
        plt.ylabel("Số lượng")
        plt.title("Thống kê diện tích các căn hộ cần cho thuê theo quận")
        plt.legend(title="Diện tích")
        
        plt.xticks(rotation=45)
        plt.show()