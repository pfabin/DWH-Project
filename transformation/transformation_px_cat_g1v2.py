import psycopg
import pandas as pd

table_name = "px_cat_g1v2"

# ==============================
# Connect
# ==============================
conn = psycopg.connect(
    host="localhost",
    port=5432,
    dbname="db_dwh",
    user="postgres",
    password="password",
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

# Not Needed

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
      "ID" VARCHAR(10), 
      "CAT" VARCHAR(20), 
      "SUBCAT" VARCHAR(20), 
      "MAINTENANCE" VARCHAR(5)
      );
""")

print(f"✅ Table transformation.{table_name} created")

# ==============================
# Load cleaned CSV into PostgreSQL
# ==============================
with open(csv_file, "r", encoding="utf-8") as f:
    with cur.copy(f"""
        COPY transformation.{table_name}
        ("ID", "CAT", "SUBCAT", "MAINTENANCE")
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