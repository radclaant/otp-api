import json
import os
from datetime import datetime

DB_FILE = "otp_storage.json"

def load_data():
    if not os.path.exists(DB_FILE):
        data = {"devices": [], "logs": []}
        save_data(data)
    else:
        with open(DB_FILE, "r") as f:
            data = json.load(f)
    return data

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def add_device(name, otp):
    data = load_data()
    device_id = len(data["devices"]) + 1
    data["devices"].append({
        "id": device_id,
        "name": name,
        "otp": otp
    })
    save_data(data)
    return device_id

def add_log(device_name, app_name):
    data = load_data()
    log_id = len(data["logs"]) + 1
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data["logs"].append({
        "id": log_id,
        "device_name": device_name,
        "timestamp": now,
        "app_name": app_name
    })
    save_data(data)
    return log_id
