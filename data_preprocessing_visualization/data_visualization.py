#!/usr/bin/env python3
"""
Data Visualization for Cleaned Danang Real Estate Data
Senior Data Engineer Approach
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set Vietnamese locale for better display
plt.rcParams['font.family'] = ['DejaVu Sans']
sns.set_style("whitegrid")

class DanangRealEstateVisualizer:
    def __init__(self, data_path: str):
        """Initialize the visualizer with cleaned data path"""
        self.data_path = data_path
        self.df = None
        
    def load_cleaned_data(self):
        """Load the cleaned data"""
        print("📊 LOADING CLEANED DATA FOR VISUALIZATION")
        print("="*50)
        
        try:
            # Try to load from CSV first
            self.df = pd.read_csv(self.data_path)
        except:
            # If CSV doesn't exist, try SQLite
            import sqlite3
            conn = sqlite3.connect(self.data_path.replace('.csv', '.db'))
            self.df = pd.read_sql_query("SELECT * FROM cleaned_danang_batdongsan", conn)
            conn.close()
        
        print(f"✓ Loaded {len(self.df)} records with {len(self.df.columns)} columns")
        print(f"✓ Columns: {list(self.df.columns)}")
        
        return self.df
    
    def create_comprehensive_visualizations(self):
        """Create comprehensive visualizations for the cleaned data"""
        print("\n🎨 CREATING COMPREHENSIVE VISUALIZATIONS")
        print("="*50)
        
        # Set up the plotting style
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 3, figsize=(20, 12))
        fig.suptitle('DANANG REAL ESTATE MARKET ANALYSIS', fontsize=16, fontweight='bold')
        
        # 1. Price Distribution
        print("1. Creating price distribution plot...")
        axes[0, 0].hist(self.df['price'] / 1e9, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
        axes[0, 0].set_title('Price Distribution (Billion VND)', fontweight='bold')
        axes[0, 0].set_xlabel('Price (Billion VND)')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Area Distribution
        print("2. Creating area distribution plot...")
        axes[0, 1].hist(self.df['area'], bins=50, alpha=0.7, color='lightgreen', edgecolor='black')
        axes[0, 1].set_title('Area Distribution (m²)', fontweight='bold')
        axes[0, 1].set_xlabel('Area (m²)')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. Price per Square Meter
        print("3. Creating price per sqm plot...")
        if 'price_per_sqm' in self.df.columns:
            axes[0, 2].hist(self.df['price_per_sqm'] / 1e6, bins=50, alpha=0.7, color='orange', edgecolor='black')
            axes[0, 2].set_title('Price per m² (Million VND/m²)', fontweight='bold')
            axes[0, 2].set_xlabel('Price per m² (Million VND/m²)')
            axes[0, 2].set_ylabel('Frequency')
            axes[0, 2].grid(True, alpha=0.3)
        
        # 4. District Distribution
        print("4. Creating district distribution plot...")
        district_counts = self.df['district'].value_counts()
        axes[1, 0].bar(range(len(district_counts)), district_counts.values, 
                       color=plt.cm.Set3(np.linspace(0, 1, len(district_counts))))
        axes[1, 0].set_title('Properties by District', fontweight='bold')
        axes[1, 0].set_xlabel('District')
        axes[1, 0].set_ylabel('Number of Properties')
        axes[1, 0].set_xticks(range(len(district_counts)))
        axes[1, 0].set_xticklabels(district_counts.index, rotation=45, ha='right')
        axes[1, 0].grid(True, alpha=0.3)
        
        # 5. Bedrooms vs Bathrooms
        print("5. Creating bedrooms vs bathrooms plot...")
        bedroom_counts = self.df['bedrooms'].value_counts().sort_index()
        bathroom_counts = self.df['bathrooms'].value_counts().sort_index()
        
        # Get common range for both
        all_rooms = sorted(set(bedroom_counts.index) | set(bathroom_counts.index))
        bedroom_data = [bedroom_counts.get(i, 0) for i in all_rooms]
        bathroom_data = [bathroom_counts.get(i, 0) for i in all_rooms]
        
        x = np.arange(len(all_rooms))
        width = 0.35
        
        axes[1, 1].bar(x - width/2, bedroom_data, width, label='Bedrooms', alpha=0.7)
        axes[1, 1].bar(x + width/2, bathroom_data, width, label='Bathrooms', alpha=0.7)
        axes[1, 1].set_title('Bedrooms vs Bathrooms Distribution', fontweight='bold')
        axes[1, 1].set_xlabel('Number of Rooms')
        axes[1, 1].set_ylabel('Count')
        axes[1, 1].set_xticks(x)
        axes[1, 1].set_xticklabels(all_rooms)
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        # 6. Price vs Area Scatter
        print("6. Creating price vs area scatter plot...")
        scatter = axes[1, 2].scatter(self.df['area'], self.df['price'] / 1e9, 
                                    alpha=0.6, c=self.df['bedrooms'], cmap='viridis')
        axes[1, 2].set_title('Price vs Area (colored by bedrooms)', fontweight='bold')
        axes[1, 2].set_xlabel('Area (m²)')
        axes[1, 2].set_ylabel('Price (Billion VND)')
        axes[1, 2].grid(True, alpha=0.3)
        
        # Add colorbar
        cbar = plt.colorbar(scatter, ax=axes[1, 2])
        cbar.set_label('Bedrooms')
        
        plt.tight_layout()
        plt.savefig('danang_real_estate_analysis.png', dpi=300, bbox_inches='tight')
        print("✓ Saved comprehensive analysis plot: danang_real_estate_analysis.png")
        
        return fig
    
    def create_price_analysis(self):
        """Create detailed price analysis"""
        print("\n💰 CREATING DETAILED PRICE ANALYSIS")
        print("="*50)
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('DETAILED PRICE ANALYSIS', fontsize=16, fontweight='bold')
        
        # 1. Price by District
        print("1. Creating price by district plot...")
        price_by_district = self.df.groupby('district')['price'].agg(['mean', 'median', 'count']).sort_values('mean', ascending=False)
        
        axes[0, 0].bar(range(len(price_by_district)), price_by_district['mean'] / 1e9, 
                       color=plt.cm.Set3(np.linspace(0, 1, len(price_by_district))))
        axes[0, 0].set_title('Average Price by District', fontweight='bold')
        axes[0, 0].set_xlabel('District')
        axes[0, 0].set_ylabel('Average Price (Billion VND)')
        axes[0, 0].set_xticks(range(len(price_by_district)))
        axes[0, 0].set_xticklabels(price_by_district.index, rotation=45, ha='right')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Price per Square Meter by District
        print("2. Creating price per sqm by district plot...")
        if 'price_per_sqm' in self.df.columns:
            price_per_sqm_by_district = self.df.groupby('district')['price_per_sqm'].mean().sort_values(ascending=False)
            
            axes[0, 1].bar(range(len(price_per_sqm_by_district)), price_per_sqm_by_district / 1e6, 
                           color=plt.cm.Set3(np.linspace(0, 1, len(price_per_sqm_by_district))))
            axes[0, 1].set_title('Average Price per m² by District', fontweight='bold')
            axes[0, 1].set_xlabel('District')
            axes[0, 1].set_ylabel('Average Price per m² (Million VND/m²)')
            axes[0, 1].set_xticks(range(len(price_per_sqm_by_district)))
            axes[0, 1].set_xticklabels(price_per_sqm_by_district.index, rotation=45, ha='right')
            axes[0, 1].grid(True, alpha=0.3)
        
        # 3. Price Distribution by Bedrooms
        print("3. Creating price distribution by bedrooms plot...")
        bedroom_price_data = [self.df[self.df['bedrooms'] == i]['price'] / 1e9 for i in sorted(self.df['bedrooms'].unique())]
        bedroom_labels = [f'{i} BR' for i in sorted(self.df['bedrooms'].unique())]
        
        axes[1, 0].boxplot(bedroom_price_data, labels=bedroom_labels)
        axes[1, 0].set_title('Price Distribution by Bedrooms', fontweight='bold')
        axes[1, 0].set_xlabel('Number of Bedrooms')
        axes[1, 0].set_ylabel('Price (Billion VND)')
        axes[1, 0].grid(True, alpha=0.3)
        
        # 4. Price vs Area with District Colors
        print("4. Creating price vs area with district colors plot...")
        districts = self.df['district'].unique()
        colors = plt.cm.Set3(np.linspace(0, 1, len(districts)))
        
        for i, district in enumerate(districts):
            district_data = self.df[self.df['district'] == district]
            axes[1, 1].scatter(district_data['area'], district_data['price'] / 1e9, 
                              alpha=0.6, label=district, color=colors[i])
        
        axes[1, 1].set_title('Price vs Area by District', fontweight='bold')
        axes[1, 1].set_xlabel('Area (m²)')
        axes[1, 1].set_ylabel('Price (Billion VND)')
        axes[1, 1].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('danang_price_analysis.png', dpi=300, bbox_inches='tight')
        print("✓ Saved price analysis plot: danang_price_analysis.png")
        
        return fig
    
    def create_statistical_summary(self):
        """Create statistical summary tables"""
        print("\n📊 CREATING STATISTICAL SUMMARY")
        print("="*50)
        
        # Basic statistics
        print("\n📈 BASIC STATISTICS:")
        numeric_cols = ['price', 'area', 'bedrooms', 'bathrooms']
        if 'price_per_sqm' in self.df.columns:
            numeric_cols.append('price_per_sqm')
        
        stats_df = self.df[numeric_cols].describe()
        print(stats_df.round(2))
        
        # District summary
        print("\n🗺️ DISTRICT SUMMARY:")
        district_summary = self.df.groupby('district').agg({
            'price': ['count', 'mean', 'median'],
            'area': ['mean', 'median'],
            'bedrooms': ['mean', 'median'],
            'bathrooms': ['mean', 'median']
        }).round(2)
        
        if 'price_per_sqm' in self.df.columns:
            price_per_sqm_by_district = self.df.groupby('district')['price_per_sqm'].agg(['mean', 'median']).round(0)
            district_summary[('price_per_sqm', 'mean')] = price_per_sqm_by_district['mean']
            district_summary[('price_per_sqm', 'median')] = price_per_sqm_by_district['median']
        
        print(district_summary)
        
        # Save summary to CSV
        summary_file = 'danang_real_estate_summary.csv'
        district_summary.to_csv(summary_file)
        print(f"\n✓ Saved statistical summary to: {summary_file}")
        
        return stats_df, district_summary
    
    def generate_insights_report(self):
        """Generate insights report"""
        print("\n💡 GENERATING INSIGHTS REPORT")
        print("="*50)
        
        insights = []
        
        # Price insights
        avg_price = self.df['price'].mean() / 1e9
        median_price = self.df['price'].median() / 1e9
        insights.append(f"💰 Average property price: {avg_price:.2f} billion VND")
        insights.append(f"💰 Median property price: {median_price:.2f} billion VND")
        
        # Area insights
        avg_area = self.df['area'].mean()
        median_area = self.df['area'].median()
        insights.append(f"🏠 Average property area: {avg_area:.1f} m²")
        insights.append(f"🏠 Median property area: {median_area:.1f} m²")
        
        # Price per sqm insights
        if 'price_per_sqm' in self.df.columns:
            avg_price_per_sqm = self.df['price_per_sqm'].mean() / 1e6
            median_price_per_sqm = self.df['price_per_sqm'].median() / 1e6
            insights.append(f"📊 Average price per m²: {avg_price_per_sqm:.1f} million VND/m²")
            insights.append(f"📊 Median price per m²: {median_price_per_sqm:.1f} million VND/m²")
        
        # District insights
        most_expensive_district = self.df.groupby('district')['price'].mean().idxmax()
        most_expensive_price = self.df.groupby('district')['price'].mean().max() / 1e9
        insights.append(f"🏆 Most expensive district: {most_expensive_district} ({most_expensive_price:.2f} billion VND avg)")
        
        least_expensive_district = self.df.groupby('district')['price'].mean().idxmin()
        least_expensive_price = self.df.groupby('district')['price'].mean().min() / 1e9
        insights.append(f"💰 Most affordable district: {least_expensive_district} ({least_expensive_price:.2f} billion VND avg)")
        
        # Bedroom insights
        most_common_bedrooms = self.df['bedrooms'].mode().iloc[0]
        insights.append(f"🛏️ Most common number of bedrooms: {most_common_bedrooms}")
        
        # Data quality insights
        total_records = len(self.df)
        insights.append(f"📊 Total properties analyzed: {total_records:,}")
        
        # Print insights
        for insight in insights:
            print(f"  {insight}")
        
        # Save insights to file
        with open('danang_real_estate_insights.txt', 'w', encoding='utf-8') as f:
            f.write("DANANG REAL ESTATE MARKET INSIGHTS\n")
            f.write("="*50 + "\n\n")
            for insight in insights:
                f.write(f"{insight}\n")
        
        print(f"\n✓ Saved insights to: danang_real_estate_insights.txt")
        
        return insights
    
    def run_complete_visualization(self):
        """Run complete visualization process"""
        print("🎨 DANANG REAL ESTATE DATA VISUALIZATION")
        print("="*60)
        
        # Load data
        self.load_cleaned_data()
        
        # Create visualizations
        self.create_comprehensive_visualizations()
        self.create_price_analysis()
        
        # Generate summaries
        self.create_statistical_summary()
        self.generate_insights_report()
        
        print("\n🎉 Data visualization completed successfully!")
        print("📁 Generated files:")
        print("  - danang_real_estate_analysis.png")
        print("  - danang_price_analysis.png")
        print("  - danang_real_estate_summary.csv")
        print("  - danang_real_estate_insights.txt")

def main():
    """Main function to run the visualization process"""
    # Try to load from CSV first, then SQLite
    try:
        visualizer = DanangRealEstateVisualizer("cleaned_danang_real_estate.csv")
    except:
        visualizer = DanangRealEstateVisualizer("cleaned_danang_real_estate.db")
    
    visualizer.run_complete_visualization()

if __name__ == "__main__":
    main() 