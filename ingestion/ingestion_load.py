import pandas as pd
import psycopg
from psycopg import sql

DB = dict(
    dbname="db_dwh",
    user="postgres",
    password="***",
    host="localhost",
    port=5432
)

SCHEMA = "ingestion"

FILES = [
    ("source_crm/cust_info.csv", "cust_info"),
    ("source_crm/prd_info.csv", "prd_info"),
    ("source_crm/sales_details.csv", "sales_details"),
    ("source_erp/CUST_AZ12.csv", "cust_az12"),
    ("source_erp/LOC_A101.csv", "loc_a101"),
    ("source_erp/PX_CAT_G1V2.csv", "px_cat_g1v2"),
]


def import_csv(cur, csv_path: str, table_name: str):
    df = pd.read_csv(csv_path)

    # Ensure schema exists
    cur.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(SCHEMA)))

    # Create table (all TEXT = simplest/robust)
    cols = [str(c) for c in df.columns]
    col_defs = sql.SQL(", ").join(
        sql.SQL("{} TEXT").format(sql.Identifier(c)) for c in cols
    )

    cur.execute(
        sql.SQL("CREATE TABLE IF NOT EXISTS {}.{} ({})").format(
            sql.Identifier(SCHEMA),
            sql.Identifier(table_name),
            col_defs
        )
    )

    # Insert rows
    insert_stmt = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
        sql.Identifier(SCHEMA),
        sql.Identifier(table_name),
        sql.SQL(", ").join(sql.Identifier(c) for c in cols),
        sql.SQL(", ").join(sql.Placeholder() for _ in cols),
    )

    rows = []
    for row in df.itertuples(index=False, name=None):
        rows.append([None if pd.isna(x) else str(x) for x in row])

    if rows:
        cur.executemany(insert_stmt, rows)

    print(f"✅ {csv_path} -> {SCHEMA}.{table_name} ({len(rows)} rows)")


def main():
    conn = psycopg.connect(**DB)
    conn.autocommit = True

    with conn.cursor() as cur:
        # Optional: set default schema for this session
        cur.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(SCHEMA)))

        for path, table in FILES:
            import_csv(cur, path, table)

    conn.close()


if __name__ == "__main__":
    main()
