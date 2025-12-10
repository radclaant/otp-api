"""
Servidor API para Sistema OTP - Version Render con SQLite
Desplegado en: https://otp-api-kf7h.onrender.com
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from bd_nr import add_device_db, get_devices_db, add_log_db, get_logs_db, update_device_db, delete_device_db

app = Flask(__name__, static_folder='static')
CORS(app)

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
    devices = get_devices_db()
    return jsonify({'devices': devices})

@app.route('/api/devices', methods=['POST'])
def add_device():
    """Agregar nuevo dispositivo"""
    device = request.json
    device_id = add_device_db(device.get('name'), device.get('otp'), device.get('enabled', True))
    return jsonify({'id': device_id, **device}), 201

@app.route('/api/devices/<device_id>', methods=['PUT'])
def update_device(device_id):
    """Actualizar dispositivo"""
    updates = request.json
    success = update_device_db(device_id, updates)
    if success:
        return jsonify({'id': device_id, **updates})
    return jsonify({'error': 'Dispositivo no encontrado'}), 404

@app.route('/api/devices/<device_id>', methods=['DELETE'])
def delete_device(device_id):
    """Eliminar dispositivo"""
    delete_device_db(device_id)
    return jsonify({'success': True})

@app.route('/api/validate', methods=['POST'])
def validate_otp():
    """Validar OTP"""
    req_data = request.json
    pc_name = req_data.get('pc_name')
    otp = req_data.get('otp')

    devices = get_devices_db()
    for device in devices:
        if device['name'] == pc_name and device['otp'] == otp and device['enabled']:
            # Registrar uso
            add_log_db(pc_name, 'Acceso Exitoso', 'login')
            return jsonify({
                'valid': True,
                'device_id': device['id'],
                'message': 'Autenticacion exitosa'
            })

    add_log_db(pc_name, 'Intento Fallido', 'failed_login')
    return jsonify({
        'valid': False,
        'message': 'OTP invalido o dispositivo no autorizado'
    }), 401

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Obtener logs de acceso"""
    logs = get_logs_db()
    return jsonify({'logs': logs})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
