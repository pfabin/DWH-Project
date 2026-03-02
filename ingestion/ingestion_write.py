import psycopg

# Database create
conn = psycopg.connect(
    dbname="postgres", 
    user="postgres",
    password="***",
    host="localhost",
    port=5432
)

conn.autocommit = True
cursor = conn.cursor()

# Check if db exists
cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'db_dwh'")
exists = cursor.fetchone()

if not exists:
    cursor.execute("CREATE DATABASE db_dwh")
    print("✅ Database created")
else:
    print("⚠ Database already exists")

cursor.close()
conn.close()

# schmea ingestion
conn = psycopg.connect(
    dbname= "db_dwh",
    user="postgres",
    password="JamesRoot4697!",
    host="localhost",
    port=5432
)

conn.autocommit = True
cursor = conn.cursor()

# Create schema
cursor.execute("CREATE SCHEMA IF NOT EXISTS ingestion")

# Set default schema so tables go there automatically
cursor.execute("SET search_path TO ingestion")

print("✅ Schema 'ingestion' ready for tables")

cursor.close()
conn.close()
