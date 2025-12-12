import { useState, useEffect } from "react";
import axios from "axios";

export default function App() {
  const API = "https://otp-api-kf7h.onrender.com";
  const [tab, setTab] = useState("registro");
  const [users, setUsers] = useState([]);
  const [qrImage, setQrImage] = useState(null);
  const [loadingQR, setLoadingQR] = useState(false);

  // Datos registro usuario
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [cedula, setCedula] = useState("");
  const [userID, setUserID] = useState("");

  // Cargar usuarios al entrar en pestaña
  useEffect(() => {
    if (tab === "usuarios") {
      fetchUsers();
    }
  }, [tab]);

  async function fetchUsers() {
    try {
      const res = await axios.get(`${API}/get-users`);
      setUsers(res.data.users || []);
    } catch (e) {
      console.error("Error cargando usuarios", e);
    }
  }

  async function registrarUsuario() {
    try {
      const body = {
        full_name: fullName,
        email,
        cedula,
        user_id: userID
      };

      const res = await axios.post(`${API}/register-user`, body);

      alert("Usuario registrado correctamente.");
      setFullName("");
      setEmail("");
      setCedula("");
      setUserID("");

    } catch (e) {
      alert("Error registrando usuario");
      console.error(e);
    }
  }

  async function generarNuevoQR(user_id) {
    try {
      setLoadingQR(true);
      setQrImage(null);

      const res = await axios.post(`${API}/generate-qr`, { user_id });

      setQrImage(res.data.qr_image);
      setLoadingQR(false);

    } catch (e) {
      console.error("Error generando QR", e);
      setLoadingQR(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 to-indigo-900 p-6 text-white">
      <div className="max-w-4xl mx-auto bg-white/10 p-8 rounded-3xl shadow-xl backdrop-blur">

        {/* NAV */}
        <div className="flex gap-4 mb-8 justify-center">
          <button onClick={() => setTab("registro")} className={`px-5 py-2 rounded-lg font-bold ${tab === "registro" ? "bg-indigo-600" : "bg-white/20"}`}>Registro</button>
          <button onClick={() => setTab("dispositivos")} className={`px-5 py-2 rounded-lg font-bold ${tab === "dispositivos" ? "bg-indigo-600" : "bg-white/20"}`}>Dispositivos</button>
          <button onClick={() => setTab("logs")} className={`px-5 py-2 rounded-lg font-bold ${tab === "logs" ? "bg-indigo-600" : "bg-white/20"}`}>Logs</button>
          <button onClick={() => setTab("usuarios")} className={`px-5 py-2 rounded-lg font-bold ${tab === "usuarios" ? "bg-indigo-600" : "bg-white/20"}`}>Usuarios</button>
        </div>

        {/* TAB REGISTRO */}
        {tab === "registro" && (
          <div>
            <h2 className="text-2xl font-bold mb-4">Registrar Usuario</h2>

            <div className="grid gap-4">
              <input className="p-3 rounded bg-white/20" placeholder="Nombre completo"
                value={fullName} onChange={e => setFullName(e.target.value)} />

              <input className="p-3 rounded bg-white/20" placeholder="Correo"
                value={email} onChange={e => setEmail(e.target.value)} />

              <input className="p-3 rounded bg-white/20" placeholder="Cédula"
                value={cedula} onChange={e => setCedula(e.target.value)} />

              <input className="p-3 rounded bg-white/20" placeholder="User ID"
                value={userID} onChange={e => setUserID(e.target.value)} />

              <button onClick={registrarUsuario}
                className="bg-green-600 p-3 rounded font-bold hover:bg-green-700">
                Registrar
              </button>
            </div>

            {qrImage && (
              <div className="mt-6">
                <h3 className="text-xl font-bold mb-2">QR generado</h3>
                <img src={qrImage} alt="QR" className="w-56 mx-auto" />
              </div>
            )}
          </div>
        )}

        {/* TAB USUARIOS */}
        {tab === "usuarios" && (
          <div>
            <h2 className="text-2xl font-bold mb-4">Usuarios</h2>

            {users.length === 0 && (
              <p>No hay usuarios registrados.</p>
            )}

            <div className="grid gap-4">
              {users.map(u => (
                <div key={u.id} className="bg-white/10 p-4 rounded-xl border border-white/20">
                  <h3 className="text-xl font-bold">{u.full_name}</h3>
                  <p className="text-purple-200">Usuario: {u.user_id}</p>
                  <p className="text-purple-200">Cédula: {u.cedula}</p>
                  <p className="text-purple-200">Correo: {u.email}</p>

                  <button
                    className="mt-3 bg-indigo-600 px-4 py-2 rounded-lg font-bold hover:bg-indigo-700"
                    onClick={() => generarNuevoQR(u.user_id)}
                  >
                    Generar nuevo QR
                  </button>
                </div>
              ))}
            </div>

            {loadingQR && <p className="mt-4">Generando QR...</p>}

            {qrImage && (
              <div className="mt-6 text-center">
                <h3 className="text-xl font-bold mb-2">Nuevo QR</h3>
                <img src={qrImage} alt="QR" className="w-64 mx-auto" />
              </div>
            )}
          </div>
        )}

        {/* DEMÁS TABS (vacíos por ahora) */}
        {tab === "dispositivos" && <p>En construcción...</p>}
        {tab === "logs" && <p>En construcción...</p>}

      </div>
    </div>
  );
}
