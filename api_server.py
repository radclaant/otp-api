"""
Servidor API Local para Sistema OTP
100% Gratuito - Corre en tu red local
No requiere servicios externos ni pagos

Instalación:
pip install flask flask-cors

Uso:
python api_server.py

El servidor correrá en http://localhost:5000
Para acceso remoto, usa tu IP local (ej: http://192.168.1.100:5000)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Permitir acceso desde cualquier origen

# Archivo de almacenamiento
STORAGE_FILE = 'otp_storage.json'

def load_data():
    """Cargar datos del archivo"""
    if not os.path.exists(STORAGE_FILE):
        return {'devices': [], 'logs': []}
    
    try:
        with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {'devices': [], 'logs': []}

def save_data(data):
    """Guardar datos al archivo"""
    with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@app.route('/api/health', methods=['GET'])
def health():
    """Verificar que el servidor está funcionando"""
    return jsonify({'status': 'ok', 'message': 'Servidor OTP activo'})

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Obtener todos los dispositivos"""
    data = load_data()
    return jsonify(data)

@app.route('/api/devices', methods=['POST'])
def add_device():
    """Agregar nuevo dispositivo"""
    device = request.json
    data = load_data()
    
    # Generar ID único
    device['id'] = str(int(datetime.now().timestamp() * 1000))
    device['createdAt'] = datetime.now().isoformat()
    device['lastUsed'] = None
    
    data['devices'].append(device)
    save_data(data)
    
    return jsonify(device), 201

@app.route('/api/devices/<device_id>', methods=['PUT'])
def update_device(device_id):
    """Actualizar dispositivo"""
    updates = request.json
    data = load_data()
    
    for device in data['devices']:
        if device['id'] == device_id:
            device.update(updates)
            save_data(data)
            return jsonify(device)
    
    return jsonify({'error': 'Dispositivo no encontrado'}), 404

@app.route('/api/devices/<device_id>', methods=['DELETE'])
def delete_device(device_id):
    """Eliminar dispositivo"""
    data = load_data()
    
    data['devices'] = [d for d in data['devices'] if d['id'] != device_id]
    save_data(data)
    
    return jsonify({'success': True})

@app.route('/api/validate', methods=['POST'])
def validate_otp():
    """Validar OTP"""
    req_data = request.json
    pc_name = req_data.get('pc_name')
    otp = req_data.get('otp')
    
    data = load_data()
    
    # Buscar dispositivo
    for device in data['devices']:
        if (device.get('name') == pc_name and 
            device.get('otp') == otp and 
            device.get('enabled', False)):
            
            # Actualizar último uso
            device['lastUsed'] = datetime.now().isoformat()
            
            # Agregar log
            log = {
                'timestamp': datetime.now().isoformat(),
                'action': 'Acceso Exitoso',
                'device': pc_name,
                'type': 'login'
            }
            data['logs'].insert(0, log)
            data['logs'] = data['logs'][:50]  # Mantener últimos 50
            
            save_data(data)
            
            return jsonify({
                'valid': True,
                'device_id': device['id'],
                'message': 'Autenticación exitosa'
            })
    
    # Registrar intento fallido
    log = {
        'timestamp': datetime.now().isoformat(),
        'action': 'Intento Fallido',
        'device': pc_name,
        'type': 'failed_login'
    }
    data['logs'].insert(0, log)
    data['logs'] = data['logs'][:50]
    save_data(data)
    
    return jsonify({
        'valid': False,
        'message': 'OTP inválido o dispositivo no autorizado'
    }), 401

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Obtener logs de acceso"""
    data = load_data()
    return jsonify({'logs': data.get('logs', [])})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🔐 SERVIDOR API OTP INICIADO")
    print("="*60)
    print("\n📍 Acceso Local:")
    print("   http://localhost:5000")
    print("\n🌐 Para acceso remoto en tu red:")
    print("   1. Encuentra tu IP: ipconfig (Windows) o ifconfig (Mac/Linux)")
    print("   2. Usa: http://TU_IP:5000")
    print("   Ejemplo: http://192.168.1.100:5000")
    print("\n💡 Panel Web: Actualiza la URL de la API en el código")
    print("💡 App Tkinter: Actualiza API_URL = 'http://TU_IP:5000'")
    print("\n" + "="*60 + "\n")
    
    # Iniciar servidor
    # Para acceso desde toda tu red local, usa host='0.0.0.0'
    app.run(host='0.0.0.0', port=5000, debug=True)