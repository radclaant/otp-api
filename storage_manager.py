from database import conn, cursor
from datetime import datetime

# Agregar dispositivo
def add_device(name, otp):
    cursor.execute("INSERT INTO devices (name, otp) VALUES (?, ?)", (name, otp))
    conn.commit()

# Obtener todos los dispositivos
def get_devices():
    cursor.execute("SELECT * FROM devices")
    return cursor.fetchall()

# Agregar log
def add_log(device_name, app_name):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO logs (device_name, event_time, app_name) VALUES (?, ?, ?)",
                   (device_name, now, app_name))
    conn.commit()

# Obtener logs
def get_logs():
    cursor.execute("SELECT * FROM logs")
    return cursor.fetchall()
