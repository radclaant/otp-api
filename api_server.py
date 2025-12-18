"""
API OTP con doble validación: Usuario + Dispositivo
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from supabase import create_client, Client
import os
import traceback
import pyotp
import qrcode
from datetime import datetime

app = Flask(__name__, static_folder='static')
CORS(app)

# Configuración Supabase
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL y SUPABASE_KEY deben estar configuradas")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


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
        print(f"📨 NUEVA PETICIÓN DE AUTENTICACIÓN")
        print(f"{'='*60}")
        print(f"👤 Usuario: {user_id}")
        print(f"🖥️  Dispositivo: {device_name}")
        print(f"🔐 OTP: {otp}")
        print(f"🌐 IP: {request.remote_addr}")
        
        # ============================================
        # VALIDACIÓN 1: Campos requeridos
        # ============================================
        if not user_id or not otp or not device_name:
            missing = []
            if not user_id: missing.append("user_id")
            if not otp: missing.append("otp")
            if not device_name: missing.append("device_name")
            
            error_msg = f"Faltan campos: {', '.join(missing)}"
            print(f"❌ {error_msg}")
            return jsonify({'valid': False, 'message': error_msg}), 400

        # ============================================
        # VALIDACIÓN 2: Usuario existe y está activo
        # ============================================
        print(f"\n🔍 Validando usuario...")
        user_response = supabase.table("users")\
            .select("*")\
            .eq("user_id", user_id)\
            .limit(1)\
            .execute()
        
        users = user_response.data or []
        
        if not users:
            print(f"❌ Usuario '{user_id}' no existe")
            
            # Log de intento fallido
            _log_attempt(user_id, device_name, "Usuario no encontrado", "user_not_found")
            
            return jsonify({
                'valid': False, 
                'message': 'Usuario no encontrado'
            }), 404
        
        user = users[0]
        
        # Verificar si el usuario está activo
        if not user.get("status_user", False):
            print(f"🚫 Usuario '{user_id}' está INACTIVO")
            
            # Log de intento con usuario inactivo
            _log_attempt(user_id, device_name, "Usuario inactivo", "user_inactive")
            
            return jsonify({
                'valid': False,
                'message': 'Usuario inactivo. Contacte al administrador.'
            }), 403
        
        print(f"✅ Usuario activo")
        
        # Verificar que tiene TOTP secret
        totp_secret = user.get("totp_secret")
        if not totp_secret:
            print(f"❌ Usuario sin TOTP secret configurado")
            
            _log_attempt(user_id, device_name, "Sin TOTP configurado", "no_totp")
            
            return jsonify({
                'valid': False,
                'message': 'Usuario sin TOTP configurado'
            }), 400

        # ============================================
        # VALIDACIÓN 3: Dispositivo existe y está activo
        # ============================================
        print(f"\n🔍 Validando dispositivo...")
        print(f"   Buscando: '{device_name}'")
        print(f"   Longitud: {len(device_name)} caracteres")
        print(f"   Tipo: {type(device_name)}")
        
        # Consulta con debugging
        try:
            device_response = supabase.table("devices")\
                .select("*")\
                .eq("name", device_name)\
                .execute()
            
            print(f"   Query ejecutada correctamente")
            print(f"   Response data: {device_response.data}")
        except Exception as query_error:
            print(f"   ❌ Error en query: {query_error}")
            traceback.print_exc()
            raise
        
        devices = device_response.data or []
        
        print(f"   Resultados: {len(devices)} dispositivo(s) encontrado(s)")
        
        if not devices:
            print(f"⚠️  Dispositivo '{device_name}' no encontrado en la consulta")
            
            # 🔍 DEBUG: Mostrar todos los dispositivos disponibles
            try:
                all_devices_response = supabase.table("devices").select("name, enabled").execute()
                print(f"\n   📋 Dispositivos en la base de datos ({len(all_devices_response.data or [])} total):")
                for d in (all_devices_response.data or []):
                    device_db_name = d.get('name', '')
                    match = "✅ MATCH" if device_db_name == device_name else "❌"
                    print(f"      {match} '{device_db_name}' (len: {len(device_db_name)}, enabled: {d.get('enabled')})")
                print()
            except Exception as list_error:
                print(f"   ❌ Error listando dispositivos: {list_error}")
            
            # Log de intento desde dispositivo no registrado
            try:
                _log_attempt(user_id, device_name, "Dispositivo no registrado", "device_not_found")
            except Exception as log_error:
                print(f"   ⚠️  Error al registrar log: {log_error}")
            
            return jsonify({
                'valid': False,
                'message': f'Dispositivo "{device_name}" no autorizado. Contacte al administrador.',
                'debug': {
                    'searched_name': device_name,
                    'name_length': len(device_name)
                }
            }), 403
        
        device = devices[0]
        
        print(f"   ✅ Dispositivo encontrado: '{device.get('name')}'")
        print(f"   ID: {device.get('id')}")
        print(f"   Enabled: {device.get('enabled')}")
        print(f"   Enabled type: {type(device.get('enabled'))}")
        
        # Verificar si el dispositivo está habilitado
        enabled_value = device.get("enabled")
        if enabled_value is None:
            print(f"   ⚠️  Campo 'enabled' es None, asumiendo False")
            enabled_value = False
        
        if not enabled_value:
            print(f"🚫 Dispositivo '{device_name}' está DESHABILITADO (enabled={enabled_value})")
            
            # Log de intento con dispositivo deshabilitado
            try:
                _log_attempt(user_id, device_name, "Dispositivo deshabilitado", "device_disabled")
            except Exception as log_error:
                print(f"   ⚠️  Error al registrar log: {log_error}")
            
            return jsonify({
                'valid': False,
                'message': 'Dispositivo deshabilitado. Contacte al administrador.',
                'debug': {
                    'device_name': device_name,
                    'enabled': enabled_value
                }
            }), 403
        
        print(f"✅ Dispositivo habilitado correctamente")

        # ============================================
        # VALIDACIÓN 4: OTP es válido
        # ============================================
        print(f"\n🔐 Validando OTP...")
        
        totp = pyotp.TOTP(totp_secret)
        current_otp = totp.now()
        
        print(f"   OTP recibido: {otp}")
        print(f"   OTP esperado: {current_otp}")
        
        # valid_window=1 permite ±30 segundos de tolerancia
        is_valid = totp.verify(str(otp), valid_window=1)
        
        if not is_valid:
            print(f"❌ OTP INVÁLIDO")
            
            # Log de intento fallido por OTP incorrecto
            _log_attempt(user_id, device_name, "OTP incorrecto", "otp_invalid")
            
            return jsonify({
                'valid': False,
                'message': 'Código OTP incorrecto'
            }), 401
        
        print(f"✅ OTP VÁLIDO")
        
        # ============================================
        # ✅ AUTENTICACIÓN EXITOSA
        # ============================================
        print(f"\n{'='*60}")
        print(f"✅ ACCESO CONCEDIDO")
        print(f"{'='*60}\n")
        
        # Actualizar último uso del dispositivo
        supabase.table("devices").update({
            "last_used": datetime.now().isoformat(),
            "ip_address": request.remote_addr
        }).eq("name", device_name).execute()
        
        # Log de acceso exitoso
        _log_attempt(user_id, device_name, "Acceso exitoso", "login_success")
        
        return jsonify({
            'valid': True,
            'message': 'Autenticación exitosa',
            'user': {
                'user_id': user_id,
                'full_name': user.get('full_name'),
                'email': user.get('email')
            }
        }), 200

    except Exception as e:
        print(f"\n💥 ERROR CRÍTICO:")
        traceback.print_exc()
        
        return jsonify({
            'valid': False,
            'error': 'Error interno del servidor',
            'details': str(e)
        }), 500


def _log_attempt(user_id, device_name, action, log_type):
    """Registra intento de autenticación en logs"""
    try:
        log_data = {
            'user_id': user_id,
            'device_name': device_name,
            'action': action,
            'log_type': log_type,
            'timestamp': datetime.now().isoformat(),
            'ip_address': request.remote_addr
        }
        
        print(f"   📝 Registrando log: {log_data}")
        
        result = supabase.table("logs").insert(log_data).execute()
        
        print(f"   ✅ Log registrado: {result.data}")
        
    except Exception as e:
        print(f"   ⚠️  Error al registrar log: {e}")
        traceback.print_exc()
        # No fallar la autenticación por un error de logging


# ============================================
# ENDPOINTS ADICIONALES
# ============================================

@app.route('/api/users', methods=['GET'])
def get_users():
    """Obtener lista de usuarios activos"""
    try:
        response = supabase.table("users")\
            .select("user_id, full_name, email, status_user")\
            .execute()
        
        print(f"📋 Usuarios consultados: {len(response.data or [])} encontrados")
        
        # Devolver todos los usuarios (el cliente filtrará los activos)
        users_list = []
        for user in (response.data or []):
            users_list.append({
                "user_id": user.get("user_id"),
                "full_name": user.get("full_name"),
                "email": user.get("email"),
                "status_user": user.get("status_user", False)
            })
        
        return jsonify({
            "users": users_list,
            "message": "Usuarios cargados correctamente"
        }), 200
    
    except Exception as e:
        print(f"❌ Error consultando usuarios: {e}")
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "message": "Error consultando usuarios"
        }), 500


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
            return jsonify({'error': 'Faltan datos obligatorios'}), 400

        # Generar secreto TOTP Base32
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
            return jsonify({'error': 'No se pudo insertar usuario'}), 500

        # Crear QR del otpauth:// URL
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
        return jsonify({'error': 'Error al crear usuario', 'details': str(e)}), 500


@app.route("/api/users/<user_id>/qr", methods=["GET"])
def get_user_qr(user_id):
    """Obtener código QR del usuario para Google Authenticator"""
    try:
        # Buscar usuario
        response = supabase.table("users").select("*").eq("user_id", user_id).limit(1).execute()
        users = response.data or []
        
        if not users:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        user = users[0]
        totp_secret = user.get("totp_secret")
        email = user.get("email")
        
        if not totp_secret:
            return jsonify({'error': 'Usuario no tiene secreto TOTP'}), 400
        
        # Generar QR desde el secreto existente
        otpauth_url = pyotp.totp.TOTP(totp_secret).provisioning_uri(
            name=email,
            issuer_name="OTP Auth System"
        )
        
        # Crear directorio si no existe
        qr_dir = "static/qrs"
        os.makedirs(qr_dir, exist_ok=True)
        
        # Generar QR
        qr_path = f"{qr_dir}/{user_id}.png"
        img = qrcode.make(otpauth_url)
        img.save(qr_path)
        
        # Enviar imagen
        return send_from_directory(qr_dir, f"{user_id}.png", mimetype='image/png')
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Error generando QR', 'details': str(e)}), 500


@app.route('/api/devices/<device_name>/status', methods=['GET'])
def check_device_status(device_name):
    """Verificar si un dispositivo está autorizado"""
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
    """Registrar un nuevo dispositivo (temporal para debugging)"""
    try:
        req = request.json or {}
        device_name = req.get("device_name")
        
        if not device_name:
            return jsonify({'error': 'Falta device_name'}), 400
        
        # Verificar si ya existe
        existing = supabase.table("devices")\
            .select("*")\
            .eq("name", device_name)\
            .execute()
        
        if existing.data:
            return jsonify({
                'message': 'Dispositivo ya existe',
                'device': existing.data[0]
            }), 200
        
        # Crear nuevo dispositivo
        new_device = supabase.table("devices").insert({
            "name": device_name,
            "otp": "000000",
            "enabled": True,
            "created_at": datetime.now().isoformat(),
            "ip_address": request.remote_addr
        }).execute()
        
        print(f"✅ Dispositivo registrado: {device_name}")
        
        return jsonify({
            'message': 'Dispositivo registrado exitosamente',
            'device': new_device.data[0] if new_device.data else None
        }), 201
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Obtener logs de autenticación"""
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
        return jsonify({'error': str(e)}), 500


@app.route('/')
def home():
    return jsonify({
        'service': 'OTP Authentication API',
        'version': '2.0',
        'security': 'Dual Layer (User + Device)',
        'status': 'online'
    })


# ============================================
# FUNCIONES DE MANTENIMIENTO
# ============================================

def refresh_totp_secrets():
    """Refrescar secretos TOTP que tengan más de 30 días"""
    try:
        from datetime import timedelta
        
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

                print(f"🔄 TOTP actualizado para usuario {user['user_id']}")

        print("✅ Proceso de actualización de TOTP completado")
    except Exception as e:
        traceback.print_exc()
        print(f"❌ Error en actualización de TOTP: {e}")


# ============================================
# SCHEDULER (opcional - comentado por defecto)
# ============================================
# from apscheduler.schedulers.background import BackgroundScheduler
# scheduler = BackgroundScheduler()
# scheduler.add_job(refresh_totp_secrets, 'interval', hours=24, next_run_time=datetime.now())
# scheduler.start()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
