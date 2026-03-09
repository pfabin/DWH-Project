import psycopg
import pandas as pd

# ==============================
# Connect
# ==============================
conn = psycopg.connect(
    host="localhost",
    port=5432,
    dbname="db_dwh",
    user="postgres",
    password="JamesRoot4697!",
    autocommit=True
)

cur = conn.cursor()

# ==============================
# Read raw table from ingestion
# ==============================
df = pd.read_sql_query(
    "SELECT * FROM ingestion.cust_info",
    conn
)

# ==============================
# Cleaning
# ==============================
# Dropping nulls and also getting 
df = df.dropna(subset=["cst_id"])
df = df.drop_duplicates(subset=["cst_id"], keep="first")
# df["cst_id"] = df["cst_id"].astype(int)

# First and Last Name
df["cst_firstname"] = df["cst_firstname"].str.strip()
df["cst_lastname"] = df["cst_lastname"].str.strip()

# Gender + marital status
df["cst_marital_status"] = df["cst_marital_status"].fillna("NA")
df["cst_marital_status"] = df["cst_marital_status"].replace({
    "M": "Married",
    "S": "Single"
})

df["cst_gndr"] = df["cst_gndr"].fillna("NA")
df["cst_gndr"] = df["cst_gndr"].replace({
    "M": "Male",
    "F": "Female"
})

# ==============================
# Save cleaned CSV
# ==============================
csv_file = "cust_info_clean.csv"
df.to_csv(csv_file, index=False)

print(f"✅ Cleaned CSV saved as: {csv_file}")

# ==============================
# Create schema if not exists
# ==============================
cur.execute("""
    CREATE SCHEMA IF NOT EXISTS transformation;
""")

# ==============================
# Drop table if exists
# ==============================
cur.execute("""
    DROP TABLE IF EXISTS transformation.cust_info;
""")

# ==============================
# Create table
# ==============================
cur.execute("""
    CREATE TABLE transformation.cust_info (
        cst_id FLOAT,
        cst_key VARCHAR(20),
        cst_firstname VARCHAR(100),
        cst_lastname VARCHAR(100),
        cst_marital_status VARCHAR(20),
        cst_gndr VARCHAR(10),
        cst_create_date DATE
    );
""")

print("✅ Table transformation.cust_info created")

# ==============================
# Load cleaned CSV into PostgreSQL
# ==============================
with open(csv_file, "r", encoding="utf-8") as f:
    with cur.copy("""
        COPY transformation.cust_info
        (cst_id, cst_key, cst_firstname, cst_lastname,
         cst_marital_status, cst_gndr, cst_create_date)
        FROM STDIN WITH CSV HEADER
    """) as copy:
        copy.write(f.read())

print("✅ Cleaned data loaded into transformation.cust_info")

# ==============================
# Close
# ==============================
cur.close()
conn.close()

print("✅ Pipeline completed successfully")