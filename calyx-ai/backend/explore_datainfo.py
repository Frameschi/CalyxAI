import sqlite3
import sys

DB_PATH = "datainfo.db"

def print_tables(conn):
    print("\nTablas en la base de datos:")
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    for t in tables:
        print(f"- {t}")
    return tables

def print_first_rows(conn, table, n=5):
    print(f"\nPrimeras {n} filas de '{table}':")
    try:
        cursor = conn.execute(f"SELECT * FROM {table} LIMIT {n}")
        columns = [desc[0] for desc in cursor.description]
        print(" | ".join(columns))
        for row in cursor.fetchall():
            print(" | ".join(str(x) for x in row))
    except Exception as e:
        print(f"  (No se pudo leer la tabla: {e})")

def buscar_alimento(conn, nombre):
    print(f"\nBuscando alimentos que contengan '{nombre}':")
    try:
        cursor = conn.execute("SELECT * FROM alimentos WHERE LOWER(alimento) LIKE ? LIMIT 10", (f"%{nombre.lower()}%",))
        rows = cursor.fetchall()
        if not rows:
            print("  No se encontraron coincidencias.")
            return
        columns = [desc[0] for desc in cursor.description]
        print(" | ".join(columns))
        for row in rows:
            print(" | ".join(str(x) for x in row))
    except Exception as e:
        print(f"  (Error en la búsqueda: {e})")

def main():
    try:
        conn = sqlite3.connect(DB_PATH)
    except Exception as e:
        print(f"No se pudo conectar a la base de datos: {e}")
        sys.exit(1)
    tables = print_tables(conn)
    if "alimentos" in tables:
        print_first_rows(conn, "alimentos", n=5)
        buscar_alimento(conn, "lechuga")
    else:
        print("La tabla 'alimentos' no existe en la base de datos.")
    conn.close()

if __name__ == "__main__":
    main()