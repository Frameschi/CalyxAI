import sqlite3

DB_PATH = "datainfo.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Mostrar todas las tablas
print("Tablas en la base de datos:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]
for table in tables:
    print(f"\nTabla: {table}")
    # Mostrar columnas
    cursor.execute(f"PRAGMA table_info({table});")
    columns = [col[1] for col in cursor.fetchall()]
    print("Columnas:", columns)
    # Mostrar todas las filas
    cursor.execute(f"SELECT * FROM {table};")
    rows = cursor.fetchall()
    print(f"Total de filas: {len(rows)}")
    for row in rows:
        print(row)

conn.close()
