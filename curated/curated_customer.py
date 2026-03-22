import psycopg
import pandas as pd

conn = psycopg.connect(
    host="localhost",
    port=5432,
    dbname="db_dwh",
    user="postgres",
    password="password"
)

crm_cust = pd.read_sql("""SELECT * FROM transformation.cust_info""", conn)
erp_cust  = pd.read_sql("""SELECT * FROM transformation.cust_az12""", conn)
erp_loc = pd.read_sql("""SELECT * FROM transformation.loc_a101""", conn)

df = pd.merge(
    left = crm_cust,
    right = erp_cust,
    how = "left",
    left_on = "cst_id",
    right_on = "CID")

df = pd.merge(
    left = df,
    right = erp_loc,
    how = "left",
    left_on = "cst_id",
    right_on = "CID",
    suffixes= ("","_loc"))

dim_customer = pd.DataFrame({"customer_id" : df["cst_id"],
                            "customer_number" : df["cst_key"],
                            "first_name" : df["cst_firstname"],
                            "last_name" : df["cst_lastname"],
                            "birthday" : df["BDATE"],
                            "marital_status" : df["cst_marital_status"],
                            "gender" : df["cst_gndr"],
                            "country": df["CNTRY"],
                            "create_date" : df["cst_create_date"]
                            })

dim_customer.insert(0, "customer_key", dim_customer.index + 1)

cur = conn.cursor()

cur.execute("""
    CREATE SCHEMA IF NOT EXISTS curated;
""")
conn.commit()

cur.execute("""
    DROP TABLE IF EXISTS curated.dim_customer;
""")
conn.commit()

cur.execute("""
    CREATE TABLE IF NOT EXISTS curated.dim_customer (
        customer_key INT,
        customer_id INT,
        customer_number CHAR(10),
        first_name VARCHAR(50),
        last_name VARCHAR(50),
        birthdate DATE,
        marital_status VARCHAR(10),
        gender VARCHAR(10),
        country VARCHAR(50),
        create_date DATE
    );
""")
conn.commit()

csv_file = "star_schema/dim_customer.csv"
dim_customer.to_csv(csv_file, index=False)

with open(csv_file, "r", encoding="utf-8") as f:
    with cur.copy("""
        COPY curated.dim_customer
        FROM STDIN WITH CSV HEADER
    """) as copy:
        copy.write(f.read())
conn.commit()

print("✅ dim_customer loaded into curated.dim_customer")

cur.close()
conn.close()

