"""
Servidor API para Sistema OTP - Version Render
Desplegado en: https://otp-api-kf7h.onrender.com
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

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

@app.route('/')
def home():
    """Ruta principal"""
    return jsonify({
        'message': 'API OTP Server',
        'status': 'online',
        'endpoints': {
            'health': '/api/health',
            'devices': '/api/devices',
            'validate': '/api/validate',
            'logs': '/api/logs'
        }
    })

@app.route('/api/health', methods=['GET'])
def health():
    """Verificar que el servidor esta funcionando"""
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
    
    for device in data['devices']:
        if (device.get('name') == pc_name and 
            device.get('otp') == otp and 
            device.get('enabled', False)):
            
            device['lastUsed'] = datetime.now().isoformat()
            
            log = {
                'timestamp': datetime.now().isoformat(),
                'action': 'Acceso Exitoso',
                'device': pc_name,
                'type': 'login'
            }
            data['logs'].insert(0, log)
            data['logs'] = data['logs'][:50]
            
            save_data(data)
            
            return jsonify({
                'valid': True,
                'device_id': device['id'],
                'message': 'Autenticacion exitosa'
            })
    
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
        'message': 'OTP invalido o dispositivo no autorizado'
    }), 401

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Obtener logs de acceso"""
    data = load_data()
    return jsonify({'logs': data.get('logs', [])})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
