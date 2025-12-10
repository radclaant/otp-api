import sqlite3
from datetime import datetime

DB_FILE = 'otp_data.db'

# --- Inicialización de la base de datos ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Tabla de dispositivos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            otp TEXT NOT NULL,
            enabled INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            last_used TEXT
        )
    ''')

    # Tabla de logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_name TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            type TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# --- Funciones de dispositivos ---
def add_device_db(name, otp, enabled=True):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    device_id = str(int(datetime.now().timestamp() * 1000))
    created_at = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO devices (id, name, otp, enabled, created_at, last_used)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (device_id, name, otp, int(enabled), created_at, None))
    conn.commit()
    conn.close()
    return device_id

def get_devices_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, otp, enabled, created_at, last_used FROM devices')
    rows = cursor.fetchall()
    conn.close()
    devices = []
    for row in rows:
        devices.append({
            'id': row[0],
            'name': row[1],
            'otp': row[2],
            'enabled': bool(row[3]),
            'createdAt': row[4],
            'lastUsed': row[5]
        })
    return devices

def update_device_db(device_id, updates):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    fields = []
    values = []
    for k, v in updates.items():
        if k == 'enabled':
            v = int(v)
        fields.append(f"{k} = ?")
        values.append(v)
    values.append(device_id)
    cursor.execute(f'''
        UPDATE devices
        SET {', '.join(fields)}
        WHERE id = ?
    ''', values)
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success

def delete_device_db(device_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM devices WHERE id = ?', (device_id,))
    conn.commit()
    conn.close()

# --- Funciones de logs ---
def add_log_db(device_name, action, type_):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO logs (device_name, timestamp, action, type)
        VALUES (?, ?, ?, ?)
    ''', (device_name, timestamp, action, type_))
    # Mantener solo últimos 50 logs
    cursor.execute('''
        DELETE FROM logs
        WHERE id NOT IN (
            SELECT id FROM logs ORDER BY id DESC LIMIT 50
        )
    ''')
    conn.commit()
    conn.close()

def get_logs_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT device_name, timestamp, action, type FROM logs ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    logs = []
    for row in rows:
        logs.append({
            'device': row[0],
            'timestamp': row[1],
            'action': row[2],
            'type': row[3]
        })
    return logs
