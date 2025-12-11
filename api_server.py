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


# -------------------------------------------------------------
# RUTAS BÁSICAS
# -------------------------------------------------------------

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


# -------------------------------------------------------------
# DEVICES
# -------------------------------------------------------------

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Obtener todos los dispositivos o uno filtrado por name"""
    
    name = request.args.get("name")

    query = supabase.table('devices').select('*')

    if name:
        query = query.eq("name", name)

    response = query.order('created_at', desc=False).execute()

    # Si pidió un nombre específico, devolver solo 1 device
    if name:
        devices = response.data or []
        if len(devices) == 0:
            return jsonify({'error': 'Device not found'}), 404
        return jsonify(devices[0])

    # Si no pidió un nombre, devolver lista completa
    return jsonify({'devices': response.data})



@app.route('/api/devices', methods=['POST'])
def add_device():
    """Agregar nuevo dispositivo"""
    device = request.json or {}

    device_data = {
        'name': device.get('name'),
        'otp': device.get('otp'),
        'enabled': device.get('enabled', True),
        'created_at': datetime.now().isoformat()
    }

    response = supabase.table('devices').insert(device_data).execute()

    if not response.data:
        return jsonify({'error': 'No se pudo insertar en Supabase'}), 500

    return jsonify(response.data[0]), 201


@app.route('/api/devices/<device_id>', methods=['PUT'])
def update_device(device_id):
    """Actualizar dispositivo"""
    updates = request.json or {}

    response = supabase.table('devices').update(updates).eq('id', int(device_id)).execute()

    if response.data:
        return jsonify(response.data[0])

    return jsonify({'error': 'Dispositivo no encontrado'}), 404


@app.route('/api/devices/<device_id>', methods=['DELETE'])
def delete_device(device_id):
    """Eliminar dispositivo"""
    supabase.table('devices').delete().eq('id', int(device_id)).execute()
    return jsonify({'success': True})


# -------------------------------------------------------------
# VALIDACIÓN OTP
# -------------------------------------------------------------

@app.route('/api/validate', methods=['POST'])
def validate_otp():
    """Validar OTP enviado por la app de escritorio"""

    req = request.json or {}

    pc_name = req.get('pc_name')
    otp = req.get('otp')

    if not pc_name or not otp:
        return jsonify({'valid': False, 'message': 'Faltan campos'}), 400

    # Buscar dispositivo en Supabase por nombre
    response = supabase.table('devices').select('*').eq('name', pc_name).limit(1).execute()
    device_list = response.data or []

    if not device_list:
        # Registrar intento fallido
        supabase.table('logs').insert({
            'device': pc_name,
            'action': 'Intento Fallido',
            'type': 'failed_login',
            'timestamp': datetime.now().isoformat()
        }).execute()

        return jsonify({'valid': False, 'message': 'Dispositivo no registrado'}), 401

    device = device_list[0]

    # Validar OTP
    if device['otp'] == otp and device['enabled']:

        supabase.table('logs').insert({
            'device': pc_name,
            'action': 'Acceso Exitoso',
            'type': 'login',
            'timestamp': datetime.now().isoformat()
        }).execute()

        return jsonify({
            'valid': True,
            'device_id': device['id'],
            'message': 'Autenticación exitosa'
        })

    # Registrar intento fallido
    supabase.table('logs').insert({
        'device': pc_name,
        'action': 'Intento Fallido',
        'type': 'failed_login',
        'timestamp': datetime.now().isoformat()
    }).execute()

    return jsonify({'valid': False, 'message': 'OTP inválido o dispositivo deshabilitado'}), 401


# -------------------------------------------------------------
# LOGS
# -------------------------------------------------------------

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Obtener logs desde Supabase"""
    response = supabase.table('logs').select('*').order('timestamp', desc=True).limit(100).execute()
    return jsonify({'logs': response.data})


# -------------------------------------------------------------
# RUN
# -------------------------------------------------------------

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

