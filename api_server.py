"""
API OTP con doble validación: Usuario + Dispositivo
Versión completa con todos los endpoints
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from supabase import create_client, Client
import os
import traceback
import pyotp
import qrcode
from datetime import datetime, timedelta

app = Flask(__name__, static_folder='static')
CORS(app)

# Configuración Supabase
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL y SUPABASE_KEY deben estar configuradas")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ============================================
# HOME
# ============================================
@app.route('/')
def home():
    return jsonify({
        'service': 'OTP Authentication API',
        'version': '2.0',
        'security': 'Dual Layer (User + Device)',
        'status': 'online',
        'endpoints': {
            'auth': '/api/validate_totp',
            'users': '/api/users',
            'devices': '/api/devices',
            'logs': '/api/logs'
        }
    })


# ============================================
# AUTENTICACIÓN OTP
# ============================================
@app.route('/api/validate_totp', methods=['POST'])
def validate_totp():
    """
    Valida OTP con doble capa de seguridad:
    1. Usuario activo (users.status_user)
    2. Dispositivo activo (devices.enabled)
    3. OTP válido (users.totp_secret)
    """
    try:
        req = request.json or {}
        
        user_id = req.get("user_id")
        otp = req.get("otp")
        device_name = req.get("device_name")
        
        print(f"\n{'='*60}")
        print(f"📨 AUTENTICACIÓN")
        print(f"{'='*60}")
        print(f"Usuario: {user_id}, Dispositivo: {device_name}, OTP: {otp}")
        
        # Validar campos
        if not user_id or not otp or not device_name:
            missing = []
            if not user_id: missing.append("user_id")
            if not otp: missing.append("otp")
            if not device_name: missing.append("device_name")
            return jsonify({'valid': False, 'message': f'Faltan: {", ".join(missing)}'}), 400

        # Validar usuario
        user_response = supabase.table("users").select("*").eq("user_id", user_id).limit(1).execute()
        users = user_response.data or []
        
        if not users:
            _log_attempt(user_id, device_name, "Usuario no encontrado", "user_not_found")
            return jsonify({'valid': False, 'message': 'Usuario no encontrado'}), 404
        
        user = users[0]
        
        if not user.get("status_user", False):
            _log_attempt(user_id, device_name, "Usuario inactivo", "user_inactive")
            return jsonify({'valid': False, 'message': 'Usuario inactivo'}), 403
        
        totp_secret = user.get("totp_secret")
        if not totp_secret:
            return jsonify({'valid': False, 'message': 'Usuario sin TOTP'}), 400

        # Validar dispositivo
        device_response = supabase.table("devices").select("*").eq("name", device_name).limit(1).execute()
        devices = device_response.data or []
        
        if not devices:
            _log_attempt(user_id, device_name, "Dispositivo no registrado", "device_not_found")
            return jsonify({'valid': False, 'message': 'Dispositivo no autorizado'}), 403
        
        device = devices[0]
        
        if not device.get("enabled", False):
            _log_attempt(user_id, device_name, "Dispositivo deshabilitado", "device_disabled")
            return jsonify({'valid': False, 'message': 'Dispositivo deshabilitado'}), 403

        # Validar OTP
        totp = pyotp.TOTP(totp_secret)
        
        if totp.verify(str(otp), valid_window=1):
            # Actualizar dispositivo
            supabase.table("devices").update({
                "last_used": datetime.now().isoformat(),
                "ip_address": request.remote_addr
            }).eq("name", device_name).execute()
            
            _log_attempt(user_id, device_name, "Acceso exitoso", "login_success")
            
            print(f"✅ ACCESO CONCEDIDO\n")
            
            return jsonify({
                'valid': True,
                'message': 'Autenticación exitosa',
                'user': {
                    'user_id': user_id,
                    'full_name': user.get('full_name'),
                    'email': user.get('email')
                }
            }), 200

        _log_attempt(user_id, device_name, "OTP incorrecto", "otp_invalid")
        print(f"❌ OTP INVÁLIDO\n")
        return jsonify({'valid': False, 'message': 'OTP inválido'}), 401

    except Exception as e:
        print(f"💥 ERROR: {str(e)}")
        traceback.print_exc()
        return jsonify({'valid': False, 'error': str(e)}), 500


def _log_attempt(user_id, device_name, action, log_type):
    """Registra intento de autenticación"""
    try:
        supabase.table("logs").insert({
            'user_id': user_id,
            'device_name': device_name,
            'action': action,
            'log_type': log_type,
            'timestamp': datetime.now().isoformat(),
            'ip_address': request.remote_addr
        }).execute()
    except Exception as e:
        print(f"⚠️  Error log: {e}")


# ============================================
# GESTIÓN DE USUARIOS
# ============================================
@app.route('/api/users', methods=['GET'])
def get_users():
    """Listar todos los usuarios"""
    try:
        response = supabase.table("users")\
            .select("user_id, full_name, email, cedula, status_user, created_at")\
            .execute()
        
        return jsonify({
            "users": response.data or [],
            "message": "Usuarios cargados"
        }), 200
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/users', methods=['POST'])
def create_user():
    """Crear nuevo usuario con TOTP"""
    try:
        data = request.json or {}

        user_id = data.get("user_id")
        full_name = data.get("full_name")
        email = data.get("email")
        cedula = data.get("cedula")

        if not user_id or not full_name or not email or not cedula:
            return jsonify({'error': 'Faltan datos'}), 400

        totp_secret = pyotp.random_base32()

        user_data = {
            "user_id": user_id,
            "full_name": full_name,
            "email": email,
            "cedula": cedula,
            "totp_secret": totp_secret,
            "created_at": datetime.now().isoformat(),
            "date_totp": datetime.now().isoformat(),
            "status_user": True
        }

        response = supabase.table('users').insert(user_data).execute()

        if not response.data:
            return jsonify({'error': 'No se pudo crear usuario'}), 500

        # Generar QR
        otpauth_url = pyotp.totp.TOTP(totp_secret).provisioning_uri(
            name=email,
            issuer_name="OTP Auth System"
        )

        qr_dir = "static/qrs"
        os.makedirs(qr_dir, exist_ok=True)

        qr_path = f"{qr_dir}/{user_id}.png"
        img = qrcode.make(otpauth_url)
        img.save(qr_path)

        return jsonify({
            'user': response.data[0],
            'qr_url': f"/api/users/{user_id}/qr",
            'otpauth_url': otpauth_url
        }), 201

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/users/<user_id>', methods=['PATCH'])
def update_user(user_id):
    """Activar/Bloquear usuario"""
    try:
        data = request.json or {}
        status_user = data.get('status_user')
        
        if status_user is None:
            return jsonify({'error': 'Campo status_user requerido'}), 400
        
        response = supabase.table('users')\
            .update({'status_user': status_user})\
            .eq('user_id', user_id)\
            .execute()
        
        if not response.data:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        action = 'activado' if status_user else 'bloqueado'
        print(f"✅ Usuario {user_id} {action}")
        
        return jsonify({
            'message': f'Usuario {action}',
            'user': response.data[0]
        }), 200
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route("/api/users/<user_id>/qr", methods=["GET"])
def get_user_qr(user_id):
    """Obtener QR del usuario"""
    try:
        response = supabase.table("users").select("*").eq("user_id", user_id).limit(1).execute()
        users = response.data or []
        
        if not users:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        user = users[0]
        totp_secret = user.get("totp_secret")
        email = user.get("email")
        
        if not totp_secret:
            return jsonify({'error': 'Sin TOTP'}), 400
        
        otpauth_url = pyotp.totp.TOTP(totp_secret).provisioning_uri(
            name=email,
            issuer_name="OTP Auth System"
        )
        
        qr_dir = "static/qrs"
        os.makedirs(qr_dir, exist_ok=True)
        
        qr_path = f"{qr_dir}/{user_id}.png"
        img = qrcode.make(otpauth_url)
        img.save(qr_path)
        
        return send_from_directory(qr_dir, f"{user_id}.png", mimetype='image/png')
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============================================
# GESTIÓN DE DISPOSITIVOS
# ============================================
@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Listar todos los dispositivos"""
    try:
        response = supabase.table('devices')\
            .select('*')\
            .order('created_at', desc=True)\
            .execute()
        
        return jsonify({
            'devices': response.data or [],
            'count': len(response.data or [])
        }), 200
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/devices/<device_name>/status', methods=['GET'])
def check_device_status(device_name):
    """Verificar estado de un dispositivo"""
    try:
        response = supabase.table("devices")\
            .select("name, enabled, last_used")\
            .eq("name", device_name)\
            .limit(1)\
            .execute()
        
        if not response.data:
            return jsonify({
                'authorized': False,
                'message': 'Dispositivo no registrado',
                'device_name': device_name
            }), 404
        
        device = response.data[0]
        
        return jsonify({
            'authorized': device.get('enabled', False),
            'device': device
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/devices/register', methods=['POST'])
def register_device():
    """Registrar nuevo dispositivo"""
    try:
        req = request.json or {}
        device_name = req.get("device_name")
        
        if not device_name:
            return jsonify({'error': 'Falta device_name'}), 400
        
        # Verificar si existe
        existing = supabase.table("devices").select("*").eq("name", device_name).execute()
        
        if existing.data:
            return jsonify({
                'message': 'Dispositivo ya existe',
                'device': existing.data[0]
            }), 200
        
        # Crear
        new_device = supabase.table("devices").insert({
            "name": device_name,
            "otp": "000000",
            "enabled": True,
            "created_at": datetime.now().isoformat(),
            "ip_address": request.remote_addr
        }).execute()
        
        print(f"✅ Dispositivo registrado: {device_name}")
        
        return jsonify({
            'message': 'Dispositivo registrado',
            'device': new_device.data[0] if new_device.data else None
        }), 201
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/devices/<device_name>', methods=['PATCH'])
def update_device(device_name):
    """Habilitar/Deshabilitar dispositivo"""
    try:
        data = request.json or {}
        enabled = data.get('enabled')
        
        if enabled is None:
            return jsonify({'error': 'Campo enabled requerido'}), 400
        
        response = supabase.table('devices')\
            .update({'enabled': enabled})\
            .eq('name', device_name)\
            .execute()
        
        if not response.data:
            return jsonify({'error': 'Dispositivo no encontrado'}), 404
        
        action = 'habilitado' if enabled else 'deshabilitado'
        print(f"✅ Dispositivo {device_name} {action}")
        
        return jsonify({
            'message': f'Dispositivo {action}',
            'device': response.data[0]
        }), 200
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============================================
# LOGS
# ============================================
@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Obtener logs de actividad"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        response = supabase.table('logs')\
            .select('*')\
            .order('timestamp', desc=True)\
            .limit(limit)\
            .execute()
        
        return jsonify({
            'logs': response.data or [],
            'count': len(response.data or [])
        }), 200
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============================================
# MANTENIMIENTO
# ============================================
def refresh_totp_secrets():
    """Refrescar secretos TOTP antiguos"""
    try:
        limite = datetime.now() - timedelta(days=30)
        response = supabase.table("users").select("*").neq("status_user", False).execute()
        users = response.data or []

        for user in users:
            date_totp = user.get("date_totp")
            if date_totp:
                date_totp_dt = datetime.fromisoformat(date_totp)
            else:
                date_totp_dt = datetime.min

            if date_totp_dt <= limite:
                new_secret = pyotp.random_base32()
                now_str = datetime.now().isoformat()

                supabase.table("users").update({
                    "totp_secret": new_secret,
                    "date_totp": now_str
                }).eq("user_id", user["user_id"]).execute()

                print(f"🔄 TOTP actualizado: {user['user_id']}")

        print("✅ Actualización completada")
    except Exception as e:
        print(f"❌ Error: {e}")


# ============================================
# RUN
# ============================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
