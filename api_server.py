"""
Servidor API para Sistema OTP - Version Render con Supabase
Desplegado en: https://otp-api-kf7h.onrender.com
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from supabase import create_client, Client
import os

app = Flask(__name__, static_folder='static')
CORS(app)

# Configurar Supabase
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def home():
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
    return jsonify({'status': 'ok', 'message': 'Servidor OTP activo'})

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Obtener todos los dispositivos desde Supabase"""
    response = supabase.table('devices').select('*').execute()
    return jsonify({'devices': response.data})

@app.route('/api/devices', methods=['POST'])
def add_device():
    """Agregar nuevo dispositivo"""
    device = request.json
    device_data = {
        'name': device.get('name'),
        'otp': device.get('otp'),
        'enabled': device.get('enabled', True),
        'created_at': datetime.now().isoformat()
    }
    response = supabase.table('devices').insert(device_data).execute()
    return jsonify(response.data[0]), 201

@app.route('/api/devices/<device_id>', methods=['PUT'])
def update_device(device_id):
    """Actualizar dispositivo"""
    updates = request.json
    response = supabase.table('devices').update(updates).eq('id', device_id).execute()
    if response.data:
        return jsonify(response.data[0])
    return jsonify({'error': 'Dispositivo no encontrado'}), 404

@app.route('/api/devices/<device_id>', methods=['DELETE'])
def delete_device(device_id):
    """Eliminar dispositivo"""
    supabase.table('devices').delete().eq('id', device_id).execute()
    return jsonify({'success': True})

@app.route('/api/validate', methods=['POST'])
def validate_otp():
    """Validar OTP"""
    req_data = request.json
    pc_name = req_data.get('pc_name')
    otp = req_data.get('otp')
    
    response = supabase.table('devices').select('*').eq('name', pc_name).execute()
    devices = response.data or []

    for device in devices:
        if device['otp'] == otp and device['enabled']:
            # Registrar log
            supabase.table('logs').insert({
                'device': pc_name,
                'action': 'Acceso Exitoso',
                'type': 'login',
                'timestamp': datetime.now().isoformat()
            }).execute()
            return jsonify({
                'valid': True,
                'device_id': device['id'],
                'message': 'Autenticacion exitosa'
            })

    # Log de intento fallido
    supabase.table('logs').insert({
        'device': pc_name,
        'action': 'Intento Fallido',
        'type': 'failed_login',
        'timestamp': datetime.now().isoformat()
    }).execute()

    return jsonify({
        'valid': False,
        'message': 'OTP invalido o dispositivo no autorizado'
    }), 401

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Obtener logs desde Supabase"""
    response = supabase.table('logs').select('*').order('timestamp', desc=True).limit(50).execute()
    return jsonify({'logs': response.data})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
