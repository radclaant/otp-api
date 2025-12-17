"""
Servidor API para Sistema OTP - Versión TOTP Google Authenticator
Desplegado en Render
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask import send_file
from supabase import create_client, Client
import os
import traceback
import pyotp
import qrcode
import qrcode.image.svg
import pyotp
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler


app = Flask(__name__, static_folder='static')
CORS(app)

# Cargar Supabase
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL y SUPABASE_KEY deben estar configuradas")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# -------------------------------------------------------------
# FUNCIONES INTERNAS
# -------------------------------------------------------------

def refresh_totp_secrets():
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

                print(f"Se actualizó TOTP para usuario {user['user_id']}")

        print("Proceso de actualización de TOTP completado.")
    except Exception as e:
        traceback.print_exc()
        print("Error en la actualización de TOTP:", e)

# -------------------------------------------------------------
# HOME
# -------------------------------------------------------------

@app.route('/')
def home():
    return jsonify({
        'message': 'API OTP Server con TOTP',
        'status': 'online',
        'endpoints': {
            'users': '/api/users',
            'validate_totp': '/api/validate_totp',
            'devices': '/api/devices',
            'logs': '/api/logs'
        }
    })


# -------------------------------------------------------------
# CREAR USUARIO TOTP
# -------------------------------------------------------------

@app.route('/api/users', methods=['POST'])
def create_user():
    """
    Crear nuevo usuario con TOTP.
    """
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
            "created_at": datetime.now().isoformat()
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


# -------------------------------------------------------------
# Obtener QR del usuario
# -------------------------------------------------------------

@app.route("/api/users", methods=["GET"])
def get_users():
    try:
        response = supabase.table("users").select("*").execute()

        return jsonify({
            "users": response.data,
            "message": "Usuarios cargados"
        }), 200

    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "Error consultando usuarios"
        }), 500

# -------------------------------------------------------------
# Obtener QR del usuario
# -------------------------------------------------------------

@app.route("/api/users/<user_id>/qr", methods=["GET"])
def get_user_qr(user_id):
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

# -------------------------------------------------------------
# VALIDAR TOTP
# -------------------------------------------------------------

@app.route('/api/validate_totp', methods=['POST'])
def validate_totp():
    """
    Valida un OTP generado desde Google Authenticator.
    """
    try:
        req = request.json or {}

        user_id = req.get("user_id")
        otp = req.get("otp")

        if not user_id or not otp:
            return jsonify({'valid': False, 'message': 'Faltan campos'}), 400

        # Buscar usuario
        response = supabase.table("users").select("*").eq("user_id", user_id).limit(1).execute()
        users = response.data or []

        if not users:
            return jsonify({'valid': False, 'message': 'Usuario no existe'}), 404

        user = users[0]
        totp_secret = user["totp_secret"]

        totp = pyotp.TOTP(totp_secret)

        if totp.verify(str(otp)):
            # Registrar login exitoso
            supabase.table("logs").insert({
                'user_id': user_id,
                'action': 'Acceso Exitoso',
                'log_type': 'totp_login',
                'timestamp': datetime.now().isoformat()
            }).execute()

            return jsonify({'valid': True, 'message': 'OTP válido'})

        # Registrar intento fallido
        
        supabase.table("logs").insert({
            'user_id': user_id,
            'action': 'Intento Fallido',
            'log_type': 'totp_failed',
            'timestamp': datetime.now().isoformat()
        }).execute()

        return jsonify({'valid': False, 'message': 'OTP inválido'}), 401

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Error al validar TOTP', 'details': str(e)}), 500




# -------------------------------------------------------------
# LOGS
# -------------------------------------------------------------

@app.route('/api/logs', methods=['GET'])
def get_logs():
    try:
        response = (
            supabase
            .table('logs')
            .select('*')
            .order('timestamp', desc=True)
            .limit(100)
            .execute()
        )

        return jsonify({
            'logs': response.data or []
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'error': 'Error al obtener logs',
            'details': str(e)
        }), 500



# -------------------------------------------------------------
# (Opcional) Devices antiguos mientras migras
# -------------------------------------------------------------

@app.route('/api/devices', methods=['GET'])
def get_devices():
    try:
        response = supabase.table('devices').select('*').execute()
        return jsonify({'devices': response.data})
    except:
        return jsonify({'devices': []})

# -------------------------------------------------------------
# Scheduler automático
# -------------------------------------------------------------
scheduler = BackgroundScheduler()
scheduler.add_job(refresh_totp_secrets, 'interval', hours=24, next_run_time=datetime.now())  # Ejecuta al iniciar y cada 24h
scheduler.start()

# -------------------------------------------------------------
# RUN
# -------------------------------------------------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

# -------------------------------------------------------------
# RUN
# -------------------------------------------------------------



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

