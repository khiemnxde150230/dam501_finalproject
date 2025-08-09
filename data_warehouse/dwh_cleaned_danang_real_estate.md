# Data Warehouse cho `cleaned_danang_real_estate.db`

## Tổng quan
- Đã áp dụng **Data Warehouse** (mô hình **Star Schema**) cho dữ liệu bất động sản Đà Nẵng.
- Script triển khai: `FinalReport/dam501_finalproject/warehouse/create_dw.sql`.

## Star Schema
- **Dimensions**: `dim_date`, `dim_location`, `dim_property`
- **Fact**: `fact_listing`  
  - **Measures**: `price`, `price_per_sqm`, …

## Kết quả nạp dữ liệu
| Bảng          | Số dòng |
|---------------|---------|
| `dim_date`    | 1282    |
| `dim_location`| 5029    |
| `dim_property`| 15526   |
| `fact_listing`| 15526   |

> Đã chạy và nạp dữ liệu thành công; xác thực bằng **row counts** như bảng trên.

---

## Một số câu truy vấn mẫu

**Giá trung bình theo tháng**
```sql
SELECT d.year, d.month, AVG(f.price) AS avg_price
FROM fact_listing f
JOIN dim_date d ON f.date_id = d.date_id
GROUP BY d.year, d.month
ORDER BY d.year, d.month;
```

**Giá/m² theo quận theo tháng**
```sql
SELECT d.year, d.month, l.district, AVG(f.price_per_sqm) AS avg_ppsqm
FROM fact_listing f
JOIN dim_date d ON f.date_id = d.date_id
JOIN dim_location l ON f.location_id = l.location_id
GROUP BY d.year, d.month, l.district
ORDER BY d.year, d.month, l.district;
```

**Top phường theo số tin đăng**
```sql
SELECT l.district, l.ward, COUNT(*) AS listings
FROM fact_listing f
JOIN dim_location l ON f.location_id = l.location_id
GROUP BY l.district, l.ward
ORDER BY listings DESC
LIMIT 20;
```

**So sánh bán/thuê theo quận**
```sql
SELECT l.district, p.is_selling, COUNT(*) AS cnt, AVG(f.price_per_sqm) AS avg_ppsqm
FROM fact_listing f
JOIN dim_location l ON f.location_id = l.location_id
JOIN dim_property p ON f.property_id = p.property_id
GROUP BY l.district, p.is_selling
ORDER BY l.district, p.is_selling DESC;
```

**Lọc theo toạ độ (nếu có lat/long)**
```sql
SELECT l.district, AVG(f.price_per_sqm) AS avg_ppsqm
FROM fact_listing f
JOIN dim_location l ON f.location_id = l.location_id
WHERE l.latitude IS NOT NULL AND l.longitude IS NOT NULL
GROUP BY l.district;
```

**Theo dõi theo ngày đăng đầy đủ**
```sql
SELECT d.full_date, COUNT(*) AS listings, AVG(f.price_per_sqm) AS avg_ppsqm
FROM fact_listing f
JOIN dim_date d ON f.date_id = d.date_id
WHERE d.full_date IS NOT NULL
GROUP BY d.full_date
ORDER BY d.full_date;
```

---

## Gợi ý sử dụng
- Trong ứng dụng/BI, **query từ `fact_listing`** và **JOIN** các bảng `dim_` để phân tích theo **thời gian / địa điểm / thuộc tính**.
- Tạo & chạy DW:
  1. Thêm `warehouse/create_dw.sql`
  2. Tạo các bảng `dim_` và `fact_listing`
  3. Nạp dữ liệu & xác thực bằng row counts: `1282 / 5029 / 15526 / 15526`.

**Chạy lại (ví dụ với SQLite):**
```bash
sqlite3 cleaned_danang_real_estate.db < FinalReport/dam501_finalproject/warehouse/create_dw.sql
```
