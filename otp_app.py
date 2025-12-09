import tkinter as tk
from tkinter import messagebox, ttk
import socket
import json
import requests
from datetime import datetime

class OTPAuthApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Autenticacion OTP")
        self.root.geometry("500x450")
        self.root.resizable(False, False)
        
        # API del servidor local
        self.api_url = "http://localhost:5000/api"
        
        # Obtener nombre del PC
        self.pc_name = socket.gethostname()
        
        # Variable de autenticacion
        self.authenticated = False
        
        # Configurar estilo
        self.setup_styles()
        
        # Crear interfaz de login
        self.create_login_interface()
    
    def setup_styles(self):
        """Configurar estilos visuales"""
        self.root.configure(bg='#1a1a2e')
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', background='#1a1a2e', foreground='#ffffff', font=('Arial', 10))
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
    
    def create_login_interface(self):
        """Crear interfaz de inicio de sesion"""
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#1a1a2e')
        main_frame.pack(expand=True, fill='both', padx=40, pady=40)
        
        # Titulo
        title_label = ttk.Label(
            main_frame,
            text="Autenticacion OTP",
            style='Title.TLabel'
        )
        title_label.pack(pady=(0, 10))
        
        # Subtitulo
        subtitle = ttk.Label(
            main_frame,
            text="Ingresa tu codigo de acceso",
            font=('Arial', 10)
        )
        subtitle.pack(pady=(0, 20))
        
        # Info del PC
        pc_frame = tk.Frame(main_frame, bg='#16213e', relief='solid', bd=1)
        pc_frame.pack(fill='x', pady=(0, 20))
        
        pc_label = ttk.Label(
            pc_frame,
            text=f"Dispositivo: {self.pc_name}",
            font=('Arial', 9)
        )
        pc_label.pack(pady=10, padx=10)
        
        # URL del panel
        url_frame = tk.Frame(main_frame, bg='#7b2cbf', relief='flat')
        url_frame.pack(fill='x', pady=(0, 20))
        
        url_label = ttk.Label(
            url_frame,
            text="Gestiona accesos en el Panel Web",
            font=('Arial', 9, 'bold'),
            background='#7b2cbf'
        )
        url_label.pack(pady=8, padx=10)
        
        # Campo OTP
        otp_label = ttk.Label(main_frame, text="Codigo OTP (6 digitos):")
        otp_label.pack(anchor='w', pady=(0, 5))
        
        self.otp_entry = tk.Entry(
            main_frame,
            font=('Arial', 14, 'bold'),
            justify='center',
            bg='#16213e',
            fg='#ffffff',
            insertbackground='#ffffff',
            relief='flat',
            bd=0
        )
        self.otp_entry.pack(fill='x', ipady=10)
        self.otp_entry.bind('<Return>', lambda e: self.authenticate())
        
        # Boton de autenticacion
        auth_button = tk.Button(
            main_frame,
            text="Autenticar",
            command=self.authenticate,
            bg='#7b2cbf',
            fg='#ffffff',
            font=('Arial', 12, 'bold'),
            relief='flat',
            cursor='hand2',
            activebackground='#9d4edd',
            activeforeground='#ffffff'
        )
        auth_button.pack(fill='x', pady=(20, 0), ipady=10)
        
        # Estado de conexion
        self.status_label = ttk.Label(
            main_frame,
            text="Listo para autenticar",
            font=('Arial', 8)
        )
        self.status_label.pack(pady=(10, 0))
        
        # Enfocar el campo OTP
        self.otp_entry.focus()
    
    def authenticate(self):
        """Autenticar usando OTP"""
        otp = self.otp_entry.get().strip()
        
        if not otp:
            messagebox.showerror("Error", "Por favor ingresa un codigo OTP")
            return
        
        if len(otp) != 6 or not otp.isdigit():
            messagebox.showerror("Error", "El OTP debe ser un codigo de 6 digitos")
            return
        
        self.status_label.config(text="Verificando...")
        self.root.update()
        
        # Validar OTP
        is_valid, device_id = self.validate_otp(otp)
        
        if is_valid:
            self.authenticated = True
            self.status_label.config(text="Autenticado correctamente")
            messagebox.showinfo("Exito", f"Bienvenido!\n\nDispositivo: {self.pc_name}\nAcceso autorizado")
            self.show_main_app()
        else:
            self.status_label.config(text="Autenticacion fallida")
            messagebox.showerror(
                "Acceso Denegado", 
                f"OTP invalido o dispositivo bloqueado.\n\n"
                f"Dispositivo: {self.pc_name}\n\n"
                f"Verifica:\n"
                f"- Que el codigo OTP sea correcto\n"
                f"- Que tu dispositivo este habilitado\n"
                f"- Que el nombre del PC coincida"
            )
            self.otp_entry.delete(0, tk.END)
    
    def validate_otp(self, otp):
        """
        Validar OTP contra el servidor API.
        
        Retorna: (is_valid: bool, device_id: str)
        """
        try:
            # Hacer peticion al servidor
            response = requests.post(
                f"{self.api_url}/validate",
                json={
                    "pc_name": self.pc_name,
                    "otp": otp
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('valid', False), data.get('device_id')
            else:
                return False, None
                
        except requests.exceptions.ConnectionError:
            messagebox.showerror(
                "Error de Conexion",
                "No se puede conectar con el servidor.\n\n"
                "Verifica que el servidor API este ejecutandose:\n"
                "python api_server.py"
            )
            return False, None
        except Exception as e:
            print(f"Error validando OTP: {e}")
            return False, None
    
    def show_main_app(self):
        """Mostrar aplicacion principal despues de autenticar"""
        # Limpiar ventana
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#1a1a2e')
        main_frame.pack(expand=True, fill='both', padx=40, pady=40)
        
        # Titulo
        title = ttk.Label(
            main_frame,
            text="Hola Mundo!",
            style='Title.TLabel'
        )
        title.pack(pady=(0, 20))
        
        # Mensaje de bienvenida
        welcome = ttk.Label(
            main_frame,
            text=f"Bienvenido desde: {self.pc_name}",
            font=('Arial', 12)
        )
        welcome.pack(pady=(0, 30))
        
        # Info
        info_frame = tk.Frame(main_frame, bg='#16213e', relief='solid', bd=1)
        info_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        info_text = tk.Text(
            info_frame,
            bg='#16213e',
            fg='#ffffff',
            font=('Arial', 10),
            relief='flat',
            wrap='word',
            height=10
        )
        info_text.pack(padx=20, pady=20, fill='both', expand=True)
        
        info_content = f"""Autenticacion exitosa!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Dispositivo: {self.pc_name}
Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tu aplicacion esta protegida con control remoto

Desde el Panel Web puedes:
  - Bloquear/desbloquear este dispositivo
  - Regenerar el codigo OTP
  - Ver el registro de accesos
  - Eliminar dispositivos

Sistema de seguridad activo!"""
        
        info_text.insert('1.0', info_content)
        info_text.config(state='disabled')
        
        # Boton de salir
        exit_button = tk.Button(
            main_frame,
            text="Cerrar Sesion",
            command=self.root.quit,
            bg='#e63946',
            fg='#ffffff',
            font=('Arial', 11, 'bold'),
            relief='flat',
            cursor='hand2'
        )
        exit_button.pack(fill='x', ipady=8)


def main():
    """Funcion principal"""
    root = tk.Tk()
    app = OTPAuthApp(root)
    
    # Centrar ventana
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    main()