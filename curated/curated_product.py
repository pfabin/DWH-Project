import psycopg
import pandas as pd

conn = psycopg.connect(
    host="localhost",
    port=5432,
    dbname="db_dwh",
    user="postgres",
    password="password"
)
cur = conn.cursor()

erp_cat = pd.read_sql("""SELECT * FROM transformation.px_cat_g1v2""", conn)
crm_prd = pd.read_sql("""SELECT * FROM transformation.prd_info""", conn)

df = pd.merge(
    left=crm_prd,
    right=erp_cat,
    how="left",
    left_on="category_id",
    right_on="ID"
)

dim_product = pd.DataFrame({   
    "product_number": df["prd_key"],
    "product_name": df["prd_nm"],
    "category_id": df["category_id"],
    "category": df["CAT"],
    "subcategory": df["SUBCAT"],
    "maintenance": df["MAINTENANCE"],
    "cost": df["prd_cost"],
    "product_line": df["prd_line"],
    "start_date": df["prd_start_dt"],
    "end_date": df["prd_end_dt"]
})

dim_product.insert(0, "product_key", dim_product.index + 1)

cur.execute("""
    CREATE SCHEMA IF NOT EXISTS curated;
""")
conn.commit()

cur.execute("""
    DROP TABLE IF EXISTS curated.dim_product;
""")
conn.commit()

cur.execute("""
    CREATE TABLE IF NOT EXISTS curated.dim_product (
        product_key INT,
        product_number VARCHAR(50),
        product_name VARCHAR(50),
        category_id VARCHAR(10),
        category VARCHAR(100),
        subcategory VARCHAR(100),
        maintenance VARCHAR(10),
        cost DECIMAL(10,2),
        product_line VARCHAR(10),
        start_date DATE,
        end_date DATE
    );
""")
conn.commit()

csv_file = "star_schema/dim_product.csv"
dim_product.to_csv(csv_file, index=False)

with open(csv_file, "r", encoding="utf-8") as f:
    with cur.copy("""
        COPY curated.dim_product
        FROM STDIN WITH CSV HEADER
    """) as copy:
        copy.write(f.read())
conn.commit()

print("✅ dim_customer loaded into curated.dim_product")

cur.close()
conn.close()