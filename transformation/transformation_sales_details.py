import psycopg
import pandas as pd

table_name = "sales_details"

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

# fix formatting on due, ship, and order
for col in ["sls_order_dt", "sls_ship_dt", "sls_due_dt"]:
    df[col] = pd.to_datetime(df[col], format="%Y%m%d", errors="coerce")

# order_dt has multiple items with same order num, set them all equal, if only one item, set to NA
def fix_order_dates(group):
    valid_dates = group["sls_order_dt"].dropna().unique()

    if len(group) > 1:
        if len(valid_dates) > 1:
            group["sls_order_dt"] = max(valid_dates)
        elif len(valid_dates) == 1:
            group["sls_order_dt"] = valid_dates[0]
        else:
            group["sls_order_dt"] = pd.NaT
    else:
        group["sls_order_dt"] = group["sls_order_dt"]

    return group
df = df.groupby("sls_ord_num", group_keys=False).apply(fix_order_dates)

# price, quantity, and sales must be fixed mathematically for negatives, zeros
df["sls_price"] = pd.to_numeric(df["sls_price"], errors="coerce").fillna(0)
df["sls_sales"] = pd.to_numeric(df["sls_sales"], errors="coerce").fillna(0)
df["sls_quantity"] = pd.to_numeric(df["sls_quantity"], errors="coerce").fillna(0)

df["sls_price"] = df["sls_price"].abs()
df["sls_sales"] = df["sls_quantity"] * df["sls_price"]

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
        sls_ord_num VARCHAR(10), 
        sls_prd_key VARCHAR(15), 
        sls_cust_id INTEGER, 
        sls_order_dt DATE, 
        sls_ship_dt DATE, 
        sls_due_dt DATE, 
        sls_sales DECIMAL(10,2), 
        sls_quantity INTEGER,
        sls_price DECIMAL(10,2)
    );
""")

print(f"✅ Table transformation.{table_name} created")

# ==============================
# Load cleaned CSV into PostgreSQL
# ==============================
with open(csv_file, "r", encoding="utf-8") as f:
    with cur.copy(f"""
        COPY transformation.{table_name}
        (sls_ord_num, sls_prd_key, sls_cust_id, sls_order_dt, 
        sls_ship_dt, sls_due_dt, sls_sales, sls_quantity,
        sls_price)
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