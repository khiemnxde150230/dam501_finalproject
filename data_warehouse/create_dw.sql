-- Data Warehouse star schema for cleaned_danang_real_estate.db
-- Source table: cleaned_danang_batdongsan

PRAGMA foreign_keys = ON;

-- Make the script idempotent
DROP TABLE IF EXISTS fact_listing;
DROP TABLE IF EXISTS dim_property;
DROP TABLE IF EXISTS dim_location;
DROP TABLE IF EXISTS dim_date;

BEGIN TRANSACTION;

-- ==========================
-- Dimension: Date
-- ==========================
CREATE TABLE IF NOT EXISTS dim_date (
  date_id INTEGER PRIMARY KEY,               -- surrogate key
  full_date TEXT,                            -- YYYY-MM-DD
  year INTEGER,
  quarter INTEGER,
  month INTEGER,
  day INTEGER,
  week_of_year INTEGER,
  day_of_week INTEGER,                       -- 0=Sunday..6=Saturday (SQLite strftime('%w'))
  day_name TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_dim_date_nk
  ON dim_date(year, month, day);

-- Populate dim_date from distinct date parts in source
INSERT OR IGNORE INTO dim_date (date_id, full_date, year, quarter, month, day, week_of_year, day_of_week, day_name)
SELECT
  -- Surrogate key generation: year*10000 + month*100 + day (safe for small ranges)
  (COALESCE(posted_year, 0) * 10000) + (COALESCE(posted_month, 0) * 100) + COALESCE(posted_day, 0) AS date_id,
  CASE
    WHEN posted_year IS NOT NULL AND posted_month IS NOT NULL AND posted_day IS NOT NULL
    THEN date(
      printf('%04d-%02d-%02d', posted_year, posted_month, posted_day)
    )
    ELSE NULL
  END AS full_date,
  posted_year AS year,
  CASE WHEN posted_month IS NOT NULL THEN ((posted_month - 1) / 3) + 1 ELSE NULL END AS quarter,
  posted_month AS month,
  posted_day AS day,
  CASE
    WHEN posted_year IS NOT NULL AND posted_month IS NOT NULL AND posted_day IS NOT NULL
    THEN CAST(strftime('%W', date(printf('%04d-%02d-%02d', posted_year, posted_month, posted_day))) AS INTEGER)
    ELSE NULL
  END AS week_of_year,
  CASE
    WHEN posted_year IS NOT NULL AND posted_month IS NOT NULL AND posted_day IS NOT NULL
    THEN CAST(strftime('%w', date(printf('%04d-%02d-%02d', posted_year, posted_month, posted_day))) AS INTEGER)
    ELSE NULL
  END AS day_of_week,
  CASE CAST(strftime('%w', date(printf('%04d-%02d-%02d', posted_year, posted_month, posted_day))) AS INTEGER)
    WHEN 0 THEN 'Sunday'
    WHEN 1 THEN 'Monday'
    WHEN 2 THEN 'Tuesday'
    WHEN 3 THEN 'Wednesday'
    WHEN 4 THEN 'Thursday'
    WHEN 5 THEN 'Friday'
    WHEN 6 THEN 'Saturday'
    ELSE NULL
  END AS day_name
FROM (
  SELECT DISTINCT posted_year, posted_month, posted_day
  FROM cleaned_danang_batdongsan
) d
WHERE posted_year IS NOT NULL OR posted_month IS NOT NULL OR posted_day IS NOT NULL;

-- ==========================
-- Dimension: Location
-- ==========================
CREATE TABLE IF NOT EXISTS dim_location (
  location_id INTEGER PRIMARY KEY,
  city TEXT,
  district TEXT,
  ward TEXT,
  street TEXT,
  latitude TEXT,
  longitude TEXT,
  coordinates TEXT,
  -- Note: SQLite does not allow expressions in UNIQUE constraints.
  -- Using direct columns; NULLs are not equal so multiple NULL combos may exist.
  UNIQUE (city, district, ward, street, latitude, longitude)
);

INSERT OR IGNORE INTO dim_location (city, district, ward, street, latitude, longitude, coordinates)
SELECT DISTINCT
  NULLIF(TRIM(city), ''),
  NULLIF(TRIM(district), ''),
  NULLIF(TRIM(ward), ''),
  NULLIF(TRIM(street), ''),
  NULLIF(TRIM(latitude), ''),
  NULLIF(TRIM(longitude), ''),
  NULLIF(TRIM(coordinates), '')
FROM cleaned_danang_batdongsan;

CREATE INDEX IF NOT EXISTS ix_dim_location_city_district_ward_street
  ON dim_location(city, district, ward, street);

-- ==========================
-- Dimension: Property (per listing characteristics)
-- ==========================
CREATE TABLE IF NOT EXISTS dim_property (
  property_id INTEGER PRIMARY KEY,
  property_code TEXT,            -- natural key when available
  title TEXT,
  bedrooms INTEGER,
  bathrooms INTEGER,
  area REAL,
  is_selling INTEGER,
  -- No expressions allowed in UNIQUE; use direct columns
  UNIQUE (property_code, title, bedrooms, bathrooms, area, is_selling)
);

INSERT OR IGNORE INTO dim_property (property_code, title, bedrooms, bathrooms, area, is_selling)
SELECT DISTINCT
  NULLIF(TRIM(property_code), ''),
  NULLIF(TRIM(title), ''),
  bedrooms,
  bathrooms,
  area,
  is_selling
FROM cleaned_danang_batdongsan;

CREATE INDEX IF NOT EXISTS ix_dim_property_nk
  ON dim_property(property_code, title);

-- ==========================
-- Fact: Listing (measures like price)
-- ==========================
CREATE TABLE IF NOT EXISTS fact_listing (
  fact_id INTEGER PRIMARY KEY,
  listing_id INTEGER,                   -- original source id
  property_code TEXT,
  date_id INTEGER REFERENCES dim_date(date_id),
  location_id INTEGER REFERENCES dim_location(location_id),
  property_id INTEGER REFERENCES dim_property(property_id),
  price REAL,
  price_per_sqm REAL,
  price_log REAL,
  area_log REAL,
  posted_time TEXT
);

CREATE INDEX IF NOT EXISTS ix_fact_listing_fks ON fact_listing(date_id, location_id, property_id);

-- Populate fact table by resolving surrogate keys from dimensions
INSERT INTO fact_listing (
  listing_id, property_code, date_id, location_id, property_id,
  price, price_per_sqm, price_log, area_log, posted_time
)
SELECT
  s.id AS listing_id,
  s.property_code,
  -- date sk
  (COALESCE(s.posted_year, 0) * 10000) + (COALESCE(s.posted_month, 0) * 100) + COALESCE(s.posted_day, 0) AS date_id,
  -- location sk
  (
    SELECT l.location_id
    FROM dim_location l
    WHERE COALESCE(l.city,'')     = COALESCE(NULLIF(TRIM(s.city), ''),'')
      AND COALESCE(l.district,'') = COALESCE(NULLIF(TRIM(s.district), ''),'')
      AND COALESCE(l.ward,'')     = COALESCE(NULLIF(TRIM(s.ward), ''),'')
      AND COALESCE(l.street,'')   = COALESCE(NULLIF(TRIM(s.street), ''),'')
      AND COALESCE(l.latitude,'') = COALESCE(NULLIF(TRIM(s.latitude), ''),'')
      AND COALESCE(l.longitude,'')= COALESCE(NULLIF(TRIM(s.longitude), ''),'')
    LIMIT 1
  ) AS location_id,
  -- property sk
  (
    SELECT p.property_id
    FROM dim_property p
    WHERE COALESCE(p.property_code,'') = COALESCE(NULLIF(TRIM(s.property_code), ''),'')
      AND COALESCE(p.title,'')         = COALESCE(NULLIF(TRIM(s.title), ''),'')
      AND COALESCE(p.bedrooms,-1)      = COALESCE(s.bedrooms,-1)
      AND COALESCE(p.bathrooms,-1)     = COALESCE(s.bathrooms,-1)
      AND COALESCE(p.area,-1)          = COALESCE(s.area,-1)
      AND COALESCE(p.is_selling,-1)    = COALESCE(s.is_selling,-1)
    LIMIT 1
  ) AS property_id,
  s.price,
  s.price_per_sqm,
  s.price_log,
  s.area_log,
  s.posted_time
FROM cleaned_danang_batdongsan s;

COMMIT;

-- Basic row counts for verification
SELECT
  (SELECT COUNT(*) FROM dim_date)      AS dim_date_rows,
  (SELECT COUNT(*) FROM dim_location)  AS dim_location_rows,
  (SELECT COUNT(*) FROM dim_property)  AS dim_property_rows,
  (SELECT COUNT(*) FROM fact_listing)  AS fact_listing_rows;


