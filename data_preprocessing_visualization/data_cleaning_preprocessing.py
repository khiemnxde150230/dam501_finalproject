#!/usr/bin/env python3
"""
Data Cleaning & Preprocessing for Danang Real Estate Database
Senior Data Engineer Approach
"""

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import re
from typing import Tuple, List, Dict
import warnings
warnings.filterwarnings('ignore')

# Set Vietnamese locale for better display
plt.rcParams['font.family'] = ['DejaVu Sans']
sns.set_style("whitegrid")

class DanangRealEstateCleaner:
    def __init__(self, db_path: str):
        """Initialize the data cleaner with database path"""
        self.db_path = db_path
        self.df = None
        self.original_shape = None
        
    def load_data(self) -> pd.DataFrame:
        """Load data from SQLite database"""
        print("=== 1. KHẢO SÁT SƠ BỘ (DATA PROFILING) ===")
        
        conn = sqlite3.connect(self.db_path)
        query = "SELECT * FROM danang_batdongsan"
        self.df = pd.read_sql_query(query, conn)
        conn.close()
        
        self.original_shape = self.df.shape
        print(f"✓ Đã tải {self.original_shape[0]} bản ghi với {self.original_shape[1]} cột")
        
        return self.df
    
    def data_profiling(self):
        """Step 1: Khảo sát sơ bộ dữ liệu"""
        print("\n--- 1.1. Thống kê cơ bản ---")
        print(f"Tổng số bản ghi: {len(self.df):,}")
        print(f"Số cột: {len(self.df.columns)}")
        
        # Kiểm tra null values
        print("\n--- 1.2. Kiểm tra giá trị null ---")
        null_counts = self.df.isnull().sum()
        null_percentages = (null_counts / len(self.df)) * 100
        
        null_summary = pd.DataFrame({
            'Null Count': null_counts,
            'Null Percentage': null_percentages
        })
        print(null_summary[null_summary['Null Count'] > 0])
        
        # Phân tích các cột số
        numeric_cols = ['price', 'area', 'bedrooms', 'bathrooms']
        print(f"\n--- 1.3. Phân tích cột số: {numeric_cols} ---")
        
        for col in numeric_cols:
            if col in self.df.columns:
                print(f"\n{col.upper()}:")
                print(f"  - Min: {self.df[col].min():,.0f}")
                print(f"  - Max: {self.df[col].max():,.0f}")
                print(f"  - Mean: {self.df[col].mean():,.2f}")
                print(f"  - Median: {self.df[col].median():,.2f}")
                print(f"  - Std: {self.df[col].std():,.2f}")
                
                # Kiểm tra giá trị 0 và âm
                zero_count = (self.df[col] == 0).sum()
                negative_count = (self.df[col] < 0).sum()
                print(f"  - Giá trị = 0: {zero_count}")
                print(f"  - Giá trị < 0: {negative_count}")
        
        # Phân tích outliers bằng IQR
        self._analyze_outliers()
        
    def _analyze_outliers(self):
        """Phân tích outliers sử dụng IQR method"""
        print("\n--- 1.4. Phân tích Outliers (IQR Method) ---")
        
        numeric_cols = ['price', 'area', 'bedrooms', 'bathrooms']
        
        for col in numeric_cols:
            if col in self.df.columns:
                Q1 = self.df[col].quantile(0.25)
                Q3 = self.df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers = self.df[(self.df[col] < lower_bound) | (self.df[col] > upper_bound)]
                outlier_count = len(outliers)
                outlier_percentage = (outlier_count / len(self.df)) * 100
                
                print(f"\n{col.upper()}:")
                print(f"  - Q1: {Q1:,.2f}")
                print(f"  - Q3: {Q3:,.2f}")
                print(f"  - IQR: {IQR:,.2f}")
                print(f"  - Lower bound: {lower_bound:,.2f}")
                print(f"  - Upper bound: {upper_bound:,.2f}")
                print(f"  - Outliers: {outlier_count} ({outlier_percentage:.2f}%)")
    
    def handle_missing_invalid_data(self):
        """Step 2: Xử lý dữ liệu thiếu/không hợp lệ"""
        print("\n=== 2. XỬ LÝ DỮ LIỆU THIẾU / KHÔNG HỢP LỆ ===")
        
        # Lưu trạng thái ban đầu
        initial_count = len(self.df)
        
        # 2.1. Xử lý giá trị null/empty cho tất cả các cột
        print("\n--- 2.1. Xử lý giá trị null/empty ---")
        
        # Thay thế null và empty values bằng "N/A"
        for col in self.df.columns:
            if self.df[col].dtype == 'object':  # Text columns
                # Thay thế null và empty strings bằng "N/A"
                self.df[col] = self.df[col].fillna("N/A")
                self.df[col] = self.df[col].replace('', "N/A")
                self.df[col] = self.df[col].replace('nan', "N/A")
                self.df[col] = self.df[col].replace('None', "N/A")
            else:  # Numeric columns
                # Giữ nguyên giá trị null cho numeric columns
                self.df[col] = self.df[col].fillna(0)
                self.df[col] = self.df[col].replace('', 0)
                self.df[col] = self.df[col].replace('nan', 0)
                self.df[col] = self.df[col].replace('None', 0)
        
        # 2.2. Xử lý giá trị 0 (không loại bỏ giá trị âm)
        print("\n--- 2.2. Xử lý giá trị 0 (giữ nguyên giá trị âm) ---")
        
        # Chỉ xử lý giá trị = 0, giữ nguyên giá trị âm
        for col in ['price', 'area']:
            if col in self.df.columns:
                zero_count = (self.df[col] == 0).sum()
                negative_count = (self.df[col] < 0).sum()
                if zero_count > 0:
                    print(f"  - {col}: {zero_count} giá trị = 0 → Thay thế bằng NaN")
                    self.df[col] = self.df[col].replace(0, np.nan)
                if negative_count > 0:
                    print(f"  - {col}: {negative_count} giá trị âm → Giữ nguyên")
        
        # Bedrooms và bathrooms - giữ nguyên giá trị âm
        for col in ['bedrooms', 'bathrooms']:
            if col in self.df.columns:
                negative_count = (self.df[col] < 0).sum()
                if negative_count > 0:
                    print(f"  - {col}: {negative_count} giá trị âm → Giữ nguyên")
        
        # 2.3. Chuẩn hóa kiểu dữ liệu
        print("\n--- 2.3. Chuẩn hóa kiểu dữ liệu ---")
        
        # Chuyển posted_time từ TEXT sang datetime
        if 'posted_time' in self.df.columns:
            print("  - Chuyển posted_time từ TEXT sang datetime")
            # Chỉ xử lý các giá trị không phải "N/A"
            mask = self.df['posted_time'] != "N/A"
            self.df.loc[mask, 'posted_time'] = pd.to_datetime(
                self.df.loc[mask, 'posted_time'], 
                format='%d-%m-%Y', 
                errors='coerce'
            )
            # Thay thế các giá trị không hợp lệ bằng "N/A"
            invalid_dates = self.df['posted_time'].isnull().sum()
            if invalid_dates > 0:
                print(f"    → Thay thế {invalid_dates} bản ghi có ngày không hợp lệ bằng 'N/A'")
                self.df['posted_time'] = self.df['posted_time'].fillna("N/A")
        
        # Chuyển is_selling từ BOOLEAN sang INTEGER
        if 'is_selling' in self.df.columns:
            print("  - Chuyển is_selling sang INTEGER (0/1)")
            # Chỉ xử lý các giá trị hợp lệ
            mask = self.df['is_selling'].notna()
            self.df.loc[mask, 'is_selling'] = self.df.loc[mask, 'is_selling'].astype(int)
        
        # 2.4. Tách cột coordinates
        if 'coordinates' in self.df.columns:
            print("  - Tách cột coordinates thành latitude và longitude")
            # Chỉ xử lý các giá trị không phải "N/A"
            mask = self.df['coordinates'] != "N/A"
            coords_data = self.df.loc[mask, 'coordinates'].str.extract(r'([\d.-]+),([\d.-]+)')
            
            # Khởi tạo cột latitude và longitude với "N/A"
            self.df['latitude'] = "N/A"
            self.df['longitude'] = "N/A"
            
            # Cập nhật các giá trị hợp lệ
            if not coords_data.empty:
                self.df.loc[mask, 'latitude'] = pd.to_numeric(coords_data[0], errors='coerce')
                self.df.loc[mask, 'longitude'] = pd.to_numeric(coords_data[1], errors='coerce')
                
                # Thay thế các giá trị không hợp lệ bằng "N/A"
                invalid_coords = self.df.loc[mask, 'latitude'].isnull().sum()
                if invalid_coords > 0:
                    print(f"    → Thay thế {invalid_coords} bản ghi có tọa độ không hợp lệ bằng 'N/A'")
                    self.df.loc[mask, 'latitude'] = self.df.loc[mask, 'latitude'].fillna("N/A")
                    self.df.loc[mask, 'longitude'] = self.df.loc[mask, 'longitude'].fillna("N/A")
        
        print(f"\n✓ Đã xử lý: {initial_count - len(self.df)} bản ghi bị loại bỏ")
        print(f"✓ Còn lại: {len(self.df)} bản ghi")
    
    def normalize_address_fields(self):
        """Step 3: Chuẩn hóa trường địa chỉ"""
        print("\n=== 3. CHUẨN HÓA TRƯỜNG ĐỊA CHỈ ===")
        
        # 3.1. Loại bỏ khoảng trắng dư thừa và chuẩn hóa chữ hoa/thường
        address_cols = ['location', 'street', 'ward', 'district', 'city']
        
        for col in address_cols:
            if col in self.df.columns:
                print(f"  - Chuẩn hóa {col}")
                # Loại bỏ khoảng trắng dư thừa
                self.df[col] = self.df[col].str.strip()
                # Chuẩn hóa chữ hoa/thường
                self.df[col] = self.df[col].str.title()
        
        # 3.2. Chuẩn hóa tên quận/huyện
        print("  - Chuẩn hóa tên quận/huyện")
        
        # Loại bỏ tiền tố Quận/Huyện ở đầu chuỗi: "Quận ", "Huyện ", "Q.", "H." (không ảnh hưởng vị trí khác)
        self.df['district'] = self.df['district'].astype(str).str.strip()
        self.df['district'] = self.df['district'].str.replace(r'^\s*(Quận|Huyện)\s+', '', regex=True)
        self.df['district'] = self.df['district'].str.replace(r'^\s*(Q\.|H\.)\s*', '', regex=True)
        # Chuẩn hóa lại khoảng trắng và chữ hoa/thường sau khi thay thế
        self.df['district'] = self.df['district'].str.strip().str.title()

        # 3.3. Chuẩn hóa tên phường
        print("  - Chuẩn hóa tên phường")
        
        # Loại bỏ từ "Phường" và chuẩn hóa
        self.df['ward'] = self.df['ward'].str.replace('Phường ', '', regex=False)
        self.df['ward'] = self.df['ward'].str.replace('P.', '', regex=False)
        
        print("✓ Hoàn thành chuẩn hóa địa chỉ")
    
    def remove_duplicates(self):
        """Step 4: Loại bỏ bản ghi trùng lặp"""
        print("\n=== 4. LOẠI BỎ BẢN GHI TRÙNG LẶP ===")
        
        initial_count = len(self.df)
        
        # 4.1. Kiểm tra trùng lặp dựa trên property_code
        if 'property_code' in self.df.columns:
            duplicates_by_code = self.df.duplicated(subset=['property_code'], keep=False)
            duplicate_count = duplicates_by_code.sum()
            print(f"  - Trùng lặp theo property_code: {duplicate_count} bản ghi")
            
            if duplicate_count > 0:
                # Giữ lại bản ghi có ít null nhất
                self.df = self.df.sort_values('property_code').drop_duplicates(
                    subset=['property_code'], 
                    keep='first'
                )
        
        # 4.2. Kiểm tra trùng lặp dựa trên tổ hợp (title + street + posted_time)
        duplicate_cols = ['title', 'street', 'posted_time']
        if all(col in self.df.columns for col in duplicate_cols):
            duplicates_by_combination = self.df.duplicated(subset=duplicate_cols, keep=False)
            duplicate_count = duplicates_by_combination.sum()
            print(f"  - Trùng lặp theo tổ hợp (title + street + posted_time): {duplicate_count} bản ghi")
            
            if duplicate_count > 0:
                # Giữ lại bản ghi có ít null nhất
                self.df = self.df.sort_values(duplicate_cols).drop_duplicates(
                    subset=duplicate_cols, 
                    keep='first'
                )
        
        final_count = len(self.df)
        removed_count = initial_count - final_count
        
        print(f"✓ Đã loại bỏ {removed_count} bản ghi trùng lặp")
        print(f"✓ Còn lại: {final_count} bản ghi")
    
    def handle_outliers_and_transformations(self):
        """Step 5: Xử lý outlier & chuyển đổi thêm"""
        print("\n=== 5. XỬ LÝ OUTLIER & CHUYỂN ĐỔI THÊM ===")
        
        # 5.1. Xác định và xử lý outliers cho price và area (không loại bỏ giá trị âm)
        print("\n--- 5.1. Xử lý outliers cho price và area (giữ nguyên giá trị âm) ---")
        
        for col in ['price', 'area']:
            if col in self.df.columns:
                # Chỉ xử lý các giá trị dương cho outlier detection
                positive_mask = self.df[col] > 0
                if positive_mask.sum() > 0:
                    positive_data = self.df.loc[positive_mask, col]
                    # Sử dụng percentile method (1% - 99%) chỉ cho giá trị dương
                    lower_percentile = positive_data.quantile(0.01)
                    upper_percentile = positive_data.quantile(0.99)
                    
                    # Chỉ xử lý outliers cho giá trị dương
                    outlier_mask = positive_mask & ((self.df[col] < lower_percentile) | (self.df[col] > upper_percentile))
                    outlier_count = outlier_mask.sum()
                    
                    print(f"  - {col}: {outlier_count} outliers dương (1%-99%: {lower_percentile:,.0f} - {upper_percentile:,.0f})")
                    
                    # Thay thế outliers bằng NaN thay vì loại bỏ
                    self.df.loc[outlier_mask, col] = np.nan
                else:
                    print(f"  - {col}: Không có giá trị dương để xử lý outliers")
        
        # 5.2. Tạo cột dẫn xuất
        print("\n--- 5.2. Tạo cột dẫn xuất ---")
        
        # Price per square meter (chỉ tính cho giá trị dương)
        if all(col in self.df.columns for col in ['price', 'area']):
            # Chỉ tính cho các bản ghi có cả price và area > 0
            valid_mask = (self.df['price'] > 0) & (self.df['area'] > 0)
            self.df['price_per_sqm'] = np.nan
            self.df.loc[valid_mask, 'price_per_sqm'] = self.df.loc[valid_mask, 'price'] / self.df.loc[valid_mask, 'area']
            print("  - Tạo cột price_per_sqm (giá/m²) - chỉ cho giá trị dương")
        
        # Log transformation cho price và area (chỉ cho giá trị dương)
        for col in ['price', 'area']:
            if col in self.df.columns:
                self.df[f'{col}_log'] = np.nan
                positive_mask = self.df[col] > 0
                if positive_mask.sum() > 0:
                    self.df.loc[positive_mask, f'{col}_log'] = np.log1p(self.df.loc[positive_mask, col])
                print(f"  - Tạo cột {col}_log (log transformation) - chỉ cho giá trị dương")
        
        # 5.3. Tạo cột thời gian
        if 'posted_time' in self.df.columns:
            # Chỉ xử lý cho các giá trị datetime hợp lệ
            datetime_mask = pd.to_datetime(self.df['posted_time'], errors='coerce').notna()
            self.df['posted_year'] = "N/A"
            self.df['posted_month'] = "N/A"
            self.df['posted_day'] = "N/A"
            
            if datetime_mask.sum() > 0:
                posted_time_dt = pd.to_datetime(self.df.loc[datetime_mask, 'posted_time'])
                self.df.loc[datetime_mask, 'posted_year'] = posted_time_dt.dt.year
                self.df.loc[datetime_mask, 'posted_month'] = posted_time_dt.dt.month
                self.df.loc[datetime_mask, 'posted_day'] = posted_time_dt.dt.day
            print("  - Tạo cột thời gian (year, month, day) - chỉ cho ngày hợp lệ")
        
        print("✓ Hoàn thành xử lý outliers và tạo cột dẫn xuất")
        
        # 5.4. Chuẩn hoá các trường dẫn xuất bị null (giữ kiểu số)
        for col in ['price_per_sqm', 'price_log', 'area_log']:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)
    
    def generate_cleaning_report(self):
        """Tạo báo cáo tổng hợp về quá trình cleaning"""
        print("\n" + "="*60)
        print("BÁO CÁO TỔNG HỢP DATA CLEANING & PREPROCESSING")
        print("="*60)
        
        print(f"\n📊 THỐNG KÊ TỔNG QUAN:")
        print(f"  - Bản ghi ban đầu: {self.original_shape[0]:,}")
        print(f"  - Bản ghi sau cleaning: {len(self.df):,}")
        print(f"  - Bản ghi bị loại bỏ: {self.original_shape[0] - len(self.df):,}")
        print(f"  - Tỷ lệ giữ lại: {(len(self.df) / self.original_shape[0]) * 100:.2f}%")
        
        print(f"\n📈 THỐNG KÊ SAU CLEANING:")
        numeric_cols = ['price', 'area', 'bedrooms', 'bathrooms']
        for col in numeric_cols:
            if col in self.df.columns:
                # Chỉ tính thống kê cho các giá trị số hợp lệ
                numeric_data = pd.to_numeric(self.df[col], errors='coerce')
                valid_data = numeric_data.dropna()
                
                if len(valid_data) > 0:
                    print(f"  - {col}:")
                    print(f"    Min: {valid_data.min():,.0f}")
                    print(f"    Max: {valid_data.max():,.0f}")
                    print(f"    Mean: {valid_data.mean():,.2f}")
                    print(f"    Median: {valid_data.median():,.2f}")
                    print(f"    Valid records: {len(valid_data):,}")
                    print(f"    Invalid/NA records: {len(self.df) - len(valid_data):,}")
                else:
                    print(f"  - {col}: Không có giá trị số hợp lệ")
        
        if 'price_per_sqm' in self.df.columns:
            # Chỉ tính cho các giá trị hợp lệ
            price_per_sqm_numeric = pd.to_numeric(self.df['price_per_sqm'], errors='coerce')
            valid_price_per_sqm = price_per_sqm_numeric.dropna()
            
            if len(valid_price_per_sqm) > 0:
                print(f"\n💰 GIÁ TRUNG BÌNH:")
                print(f"  - Giá/m² (mean): {valid_price_per_sqm.mean():,.0f} VND/m²")
                print(f"  - Giá/m² (median): {valid_price_per_sqm.median():,.0f} VND/m²")
                print(f"  - Valid price/m² records: {len(valid_price_per_sqm):,}")
            else:
                print(f"\n💰 GIÁ TRUNG BÌNH: Không có dữ liệu hợp lệ")
        
        print(f"\n🗺️ PHÂN BỐ THEO QUẬN:")
        if 'district' in self.df.columns:
            district_counts = self.df['district'].value_counts()
            for district, count in district_counts.head().items():
                print(f"  - {district}: {count:,} bản ghi")
        
        print("\n✅ HOÀN THÀNH DATA CLEANING & PREPROCESSING!")
    
    def save_cleaned_data(self, output_path: str = None):
        """Lưu dữ liệu đã được cleaning"""
        if output_path is None:
            output_path = "cleaned_danang_real_estate.csv"
        
        # Tạo bản sao để xử lý datetime trước khi lưu
        df_to_save = self.df.copy()
        
        # Chuyển đổi datetime thành string để lưu vào CSV
        if 'posted_time' in df_to_save.columns:
            df_to_save['posted_time'] = df_to_save['posted_time'].astype(str)
        
        df_to_save.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\n💾 Đã lưu dữ liệu đã cleaning vào: {output_path}")
        
        # Cũng lưu vào SQLite
        sqlite_output = output_path.replace('.csv', '.db')
        conn = sqlite3.connect(sqlite_output)
        
        # Chuyển đổi datetime thành string cho SQLite
        if 'posted_time' in df_to_save.columns:
            df_to_save['posted_time'] = df_to_save['posted_time'].replace('NaT', 'N/A')
        
        df_to_save.to_sql('cleaned_danang_batdongsan', conn, if_exists='replace', index=False)
        conn.close()
        print(f"💾 Đã lưu dữ liệu đã cleaning vào SQLite: {sqlite_output}")
    
    def run_complete_cleaning(self):
        """Chạy toàn bộ quy trình cleaning"""
        # Load data
        self.load_data()
        
        # Step 1: Data profiling
        self.data_profiling()
        
        # Step 2: Handle missing/invalid data
        self.handle_missing_invalid_data()
        
        # Step 3: Normalize address fields
        self.normalize_address_fields()
        
        # Step 4: Remove duplicates
        self.remove_duplicates()
        
        # Step 5: Handle outliers and transformations
        self.handle_outliers_and_transformations()
        
        # Generate report
        self.generate_cleaning_report()
        
        # Save cleaned data
        self.save_cleaned_data()
        
        return self.df

def main():
    """Main function to run the data cleaning process"""
    print("🏠 DATA CLEANING & PREPROCESSING - DANANG REAL ESTATE")
    print("="*60)
    
    # Initialize cleaner
    cleaner = DanangRealEstateCleaner("../../../FinalReport/data.db")
    
    # Run complete cleaning process
    cleaned_df = cleaner.run_complete_cleaning()
    
    print("\n🎉 Quá trình Data Cleaning & Preprocessing đã hoàn thành!")
    return cleaned_df

if __name__ == "__main__":
    cleaned_data = main() 