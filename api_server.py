"""
Servidor API para Sistema OTP - Version Render con Supabase
Desplegado en: https://otp-api-kf7h.onrender.com
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from supabase import create_client, Client
import os
import traceback

app = Flask(__name__, static_folder='static')
CORS(app)

# Configurar Supabase
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL y SUPABASE_KEY deben estar configuradas")

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
    try:
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
    
    except Exception as e:
        print(f"Error en get_devices: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Error al obtener dispositivos', 'details': str(e)}), 500


@app.route('/api/devices', methods=['POST'])
def add_device():
    """Agregar nuevo dispositivo"""
    try:
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
    
    except Exception as e:
        print(f"Error en add_device: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Error al agregar dispositivo', 'details': str(e)}), 500


@app.route('/api/devices/<device_id>', methods=['PUT'])
def update_device(device_id):
    """Actualizar dispositivo"""
    try:
        updates = request.json or {}

        # No convertir a int, dejar como string por si es UUID
        response = supabase.table('devices').update(updates).eq('id', device_id).execute()

        if response.data:
            return jsonify(response.data[0])

        return jsonify({'error': 'Dispositivo no encontrado'}), 404
    
    except Exception as e:
        print(f"Error en update_device: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Error al actualizar dispositivo', 'details': str(e)}), 500


@app.route('/api/devices/<device_id>', methods=['DELETE'])
def delete_device(device_id):
    """Eliminar dispositivo"""
    try:
        # No convertir a int, dejar como string por si es UUID
        supabase.table('devices').delete().eq('id', device_id).execute()
        return jsonify({'success': True})
    
    except Exception as e:
        print(f"Error en delete_device: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Error al eliminar dispositivo', 'details': str(e)}), 500


# -------------------------------------------------------------
# VALIDACIÓN OTP
# -------------------------------------------------------------

@app.route('/api/validate', methods=['POST'])
def validate_otp():
    """Validar OTP enviado por la app de escritorio"""
    # Obtener IP real del cliente
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    try:
        req = request.json or {}

        pc_name = req.get('pc_name')
        otp = req.get('otp')

        print(f"Validación recibida - PC: {pc_name}, OTP: {otp}")

        if not pc_name or not otp:
            return jsonify({'valid': False, 'message': 'Faltan campos'}), 400

        # Buscar dispositivo en Supabase por nombre
        response = supabase.table('devices').select('*').eq('name', pc_name).limit(1).execute()
        device_list = response.data or []

        print(f"Dispositivos encontrados: {len(device_list)}")

        if not device_list:
            print(f"Dispositivo no encontrado: {pc_name}")
            # Registrar intento fallido
            try:
                supabase.table('logs').insert({
                    'device_name': pc_name,
                    'ip_address': ip_address,
                    'action': 'Intento Fallido',
                    'log_type': 'failed_login'
                }).execute()
            except Exception as log_error:
                print(f"Error al registrar log: {log_error}")

            return jsonify({'valid': False, 'message': 'Dispositivo no registrado'}), 401

        device = device_list[0]
        print(f"Dispositivo encontrado: {device.get('name')}, OTP esperado: {device.get('otp')}, Habilitado: {device.get('enabled')}")

        # Validar OTP (convertir ambos a string para comparación)
        if str(device.get('otp')) == str(otp) and device.get('enabled'):
            print(f"✓ Autenticación exitosa para {pc_name}")
            
            # Registrar acceso exitoso
            try:
                supabase.table('logs').insert({
                    'device_name': pc_name,
                    'ip_address': ip_address,
                    'action': 'Intento Fallido',
                    'log_type': 'failed_login'
                }).execute()
            except Exception as log_error:
                print(f"Error al registrar log: {log_error}")

            return jsonify({
                'valid': True,
                'device_id': device.get('id'),
                'message': 'Autenticación exitosa'
            })

        print(f"✗ OTP inválido o dispositivo deshabilitado para {pc_name}")
        
        # Registrar intento fallido
        try:
            supabase.table('logs').insert({
                'device_name': pc_name,
                'ip_address': ip_address,
                'action': 'Intento Fallido',
                'log_type': 'failed_login'
            }).execute()
        except Exception as log_error:
            print(f"Error al registrar log: {log_error}")

        return jsonify({'valid': False, 'message': 'OTP inválido o dispositivo deshabilitado'}), 401

    except Exception as e:
        print(f"Error en validate_otp: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Error en validación', 'details': str(e)}), 500


# -------------------------------------------------------------
# LOGS
# -------------------------------------------------------------

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Obtener logs desde Supabase"""
    try:
        response = supabase.table('logs').select('*').order('created_at', desc=True).limit(100).execute()
        return jsonify({'logs': response.data})
    
    except Exception as e:
        print(f"Error en get_logs: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Error al obtener logs', 'details': str(e)}), 500


# -------------------------------------------------------------
# RUN
# -------------------------------------------------------------

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

