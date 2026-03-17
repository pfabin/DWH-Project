import psycopg
import pandas as pd

table_name = "cust_az12"

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

df["CID"] = df["CID"].astype(str).str[-5:]
df["CID"] = pd.to_numeric(df["CID"], errors="coerce")

today = pd.Timestamp.today().normalize()
df["BDATE"] = pd.to_datetime(df["BDATE"], errors="coerce")
df.loc[df["BDATE"] > today, "BDATE"] = pd.NaT

df["GEN"] = (df["GEN"].astype(str).str.strip().str.lower())
df["GEN"] = df["GEN"].replace({"m": "Male","f": "Female"})
df.loc[~df["GEN"].isin(["male", "female"]), "GEN"] = "NA"


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
        "CID" INTEGER,
        "BDATE" DATE,
        "GEN" VARCHAR(10)
    );
""")

print(f"✅ Table transformation.{table_name} created")

# ==============================
# Load cleaned CSV into PostgreSQL
# ==============================
with open(csv_file, "r", encoding="utf-8") as f:
    with cur.copy(f"""
        COPY transformation.{table_name}
        ("CID", "BDATE", "GEN")
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

### sils order dt has to be fixed formating, check multiple orders in item and they must have same order dt, if only one item set ship date -1
### fix sales price, qt, price
# Best replace with nulls if someone born after today