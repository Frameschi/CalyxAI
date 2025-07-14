import sqlite3

import os
DB_PATH = os.path.join(os.path.dirname(__file__), "datainfo.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Imprimir solo los nombres de los alimentos
try:
    cursor.execute("SELECT alimento FROM alimentos;")
    rows = cursor.fetchall()
    print("Alimentos en la base de datos:")
    for row in rows:
        print(row[0])
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
