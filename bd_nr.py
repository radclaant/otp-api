import sqlite3

# Conexión a la base de datos (archivo en el proyecto)
conn = sqlite3.connect("otp_data.db", check_same_thread=False)
cursor = conn.cursor()

# Crear tabla de dispositivos
cursor.execute("""
CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    otp TEXT NOT NULL
)
""")

# Crear tabla de logs
cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_name TEXT NOT NULL,
    event_time TEXT NOT NULL,
    app_name TEXT NOT NULL
)
""")

conn.commit()
