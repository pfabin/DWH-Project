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

sales_details_df = pd.read_sql("SELECT * FROM transformation.sales_details;", conn)
dim_product_df = pd.read_sql("SELECT * FROM curated.dim_product;", conn)
dim_customer_df = pd.read_sql("SELECT * FROM curated.dim_customer;", conn)

df = pd.merge(
    left=sales_details_df,
    right=dim_product_df[["product_key", "product_number"]],
    how="left",
    left_on="sls_prd_key",
    right_on="product_number"
)

df = pd.merge(
    left=df,
    right=dim_customer_df[["customer_key", "customer_id"]],
    how="left",
    left_on="sls_cust_id",
    right_on="customer_id"
)

fact_sales = pd.DataFrame({
    "product_key": df["product_key"],
    "customer_key": df["customer_key"],
    "order_number": df["sls_ord_num"],
    "order_date": df["sls_order_dt"],
    "shipping_date": df["sls_ship_dt"],
    "due_date": df["sls_due_dt"],
    "sales": df["sls_sales"],
    "quantity": df["sls_quantity"],
    "price": df["sls_price"]
})

fact_sales.insert(0, "sales_key", fact_sales.index + 1)

cur.execute("""
DROP TABLE IF EXISTS curated.fact_sales;
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS curated.fact_sales (
    sales_key INT,
    product_key INT,
    customer_key INT,
    order_number VARCHAR(50),
    order_date DATE,
    shipping_date DATE,
    due_date DATE,
    sales DECIMAL(10,2),
    quantity INT,
    price DECIMAL(10,2)
);
""")
conn.commit()

csv_file = "star_schema/fact_sales.csv"
fact_sales.to_csv(csv_file, index=False)

with open(csv_file, "r", encoding="utf-8") as f:
    with cur.copy("""
        COPY curated.fact_sales
        (sales_key, product_key, customer_key, order_number,
         order_date, shipping_date, due_date,
         sales, quantity, price)
        FROM STDIN WITH CSV HEADER
    """) as copy:
        copy.write(f.read())
conn.commit()

print("✅ fact_sales loaded into curated.fact_sales")

cur.close()
conn.close()


