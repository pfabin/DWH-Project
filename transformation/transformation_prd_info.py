import psycopg
import pandas as pd

table_name = "prd_info"

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
    f"SELECT * FROM ingestion.{table_name}",
    conn
)

# ==============================
# Cleaning
# ==============================

df["sales_key"] = df["prd_key"].astype(str).str[6:]
df["prd_key"] = df["prd_key"].str[:5].str.replace("-", "_")

df["prd_cost"] = df["prd_cost"].fillna(0)

df["prd_line"] = df["prd_line"].str.strip().fillna("Other")
df["prd_line"] = df["prd_line"].str.strip().replace({
   "M": "Mountain",
   "S": "Sport",
   "R": "Road"})

df["prd_start_dt"] = pd.to_datetime(df["prd_start_dt"], errors="coerce")
df["prd_end_dt"] = pd.to_datetime(df["prd_end_dt"], errors="coerce")
next_start = df["prd_start_dt"].shift(-1)
mask = next_start.notna()
df.loc[mask, "prd_end_dt"] = next_start[mask] - pd.Timedelta(days=1)

# ==============================
# Save cleaned CSV
# ==============================
csv_file = f"clean/{table_name}_clean.csv"
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
cur.execute(f"""
    DROP TABLE IF EXISTS transformation.{table_name};
""")

# ==============================
# Create table
# ==============================
cur.execute(f"""
    CREATE TABLE transformation.{table_name} (
        prd_id INT,
        prd_key VARCHAR(10),
        sales_key VARCHAR(10),
        prd_nm VARCHAR(50),
        prd_line VARCHAR(10),
        prd_cost FLOAT,
        prd_start_dt DATE,
        prd_end_dt DATE
    );
""")

print(f"✅ Table transformation.{table_name} created")

# ==============================
# Load cleaned CSV into PostgreSQL
# ==============================
with open(csv_file, "r", encoding="utf-8") as f:
    with cur.copy(f"""
        COPY transformation.{table_name}
        (prd_id, prd_key, prd_nm, prd_cost, prd_line,
         prd_start_dt, prd_end_dt, sales_key)
        FROM STDIN WITH CSV HEADER
    """) as copy:
        copy.write(f.read())

print(f"✅ Cleaned data loaded into transformation.{table_name}")

# ==============================
# Close
# ==============================
cur.close()
conn.close()

print("✅ Pipeline completed successfully")