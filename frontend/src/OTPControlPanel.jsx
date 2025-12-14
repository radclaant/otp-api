import { useState, useEffect } from "react";
import axios from "axios";

export default function OtpControlPanel() {
  const API = "https://otp-api-kf7h.onrender.com/api";

  const [tab, setTab] = useState("registro");

  // Estados generales
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Usuarios
  const [users, setUsers] = useState([]);

  // Dispositivos
  const [devices, setDevices] = useState([]);

  // Logs
  const [logs, setLogs] = useState([]);

  // QR
  const [qrImage, setQrImage] = useState(null);
  const [loadingQR, setLoadingQR] = useState(false);

  // Registro usuario
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [cedula, setCedula] = useState("");
  const [userID, setUserID] = useState("");

  /* ----------------------------------------------------
     EFECTOS SEGÚN PESTAÑA
  ---------------------------------------------------- */
  useEffect(() => {
    setError("");

    if (tab === "usuarios") fetchUsers();
    if (tab === "dispositivos") fetchDevices();
    if (tab === "logs") fetchLogs();
  }, [tab]);

  /* ----------------------------------------------------
     API CALLS
  ---------------------------------------------------- */
  async function fetchUsers() {
    try {
      setLoading(true);
      const res = await axios.get(`${API}/users`);
      setUsers(res.data.users || []);
    } catch (e) {
      setError("Error cargando usuarios");
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function fetchDevices() {
    try {
      setLoading(true);
      const res = await axios.get(`${API}/devices`);
      setDevices(res.data.devices || []);
    } catch (e) {
      setError("Error cargando dispositivos");
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function fetchLogs() {
    try {
      setLoading(true);
      const res = await axios.get(`${API}/logs`);
      setLogs(res.data.logs || []);
    } catch (e) {
      setError("Error cargando logs");
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function registrarUsuario() {
    try {
      setLoading(true);

      await axios.post(`${API}/users`, {
        user_id: userID,
        full_name: fullName,
        email,
        cedula
      });

      alert("Usuario registrado correctamente");

      setFullName("");
      setEmail("");
      setCedula("");
      setUserID("");

      if (tab === "usuarios") fetchUsers();
    } catch (e) {
      alert("Error registrando usuario");
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function generarNuevoQR(user_id) {
    try {
      setLoadingQR(true);
      setQrImage(null);

      const res = await axios.get(`${API}/users/${user_id}/qr`, {
        responseType: "arraybuffer"
      });

      const base64 = btoa(
        new Uint8Array(res.data).reduce(
          (data, byte) => data + String.fromCharCode(byte),
          ""
        )
      );

      setQrImage(`data:image/png;base64,${base64}`);
    } catch (e) {
      console.error("Error generando QR", e);
      alert("No se pudo generar el QR");
    } finally {
      setLoadingQR(false);
    }
  }

  /* ----------------------------------------------------
     UI
  ---------------------------------------------------- */
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 to-indigo-900 p-6 text-white">
      <div className="max-w-5xl mx-auto bg-white/10 p-8 rounded-3xl shadow-xl backdrop-blur">

        {/* NAV */}
        <div className="flex gap-4 mb-8 justify-center">
          {["registro", "usuarios", "dispositivos", "logs"].map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-5 py-2 rounded-lg font-bold ${
                tab === t ? "bg-indigo-600" : "bg-white/20"
              }`}
            >
              {t.toUpperCase()}
            </button>
          ))}
        </div>

        {error && (
          <div className="bg-red-500/30 p-3 rounded mb-4 text-center">
            {error}
          </div>
        )}

        {loading && <p className="mb-4">Cargando datos...</p>}

        {/* REGISTRO */}
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

              <button
                onClick={registrarUsuario}
                className="bg-green-600 p-3 rounded font-bold hover:bg-green-700"
                disabled={loading}
              >
                Registrar
              </button>
            </div>
          </div>
        )}

        {/* USUARIOS */}
        {tab === "usuarios" && (
          <div>
            <h2 className="text-2xl font-bold mb-4">Usuarios</h2>

            {users.length === 0 && <p>No hay usuarios registrados.</p>}

            <div className="grid gap-4">
              {users.map(u => (
                <div key={u.id} className="bg-white/10 p-4 rounded-xl border border-white/20">
                  <h3 className="text-xl font-bold">{u.full_name}</h3>
                  <p>ID: {u.user_id}</p>
                  <p>Cédula: {u.cedula}</p>
                  <p>Email: {u.email}</p>

                  <button
                    className="mt-3 bg-indigo-600 px-4 py-2 rounded font-bold"
                    onClick={() => generarNuevoQR(u.user_id)}
                  >
                    Generar QR
                  </button>
                </div>
              ))}
            </div>

            {loadingQR && <p className="mt-4">Generando QR…</p>}

            {qrImage && (
              <div className="mt-6 text-center">
                <img src={qrImage} alt="QR" className="w-64 mx-auto" />
              </div>
            )}
          </div>
        )}

        {/* DISPOSITIVOS */}
        {tab === "dispositivos" && (
          <div>
            <h2 className="text-2xl font-bold mb-4">Dispositivos</h2>
            {devices.length === 0 && <p>No hay dispositivos registrados.X</p>}
            {devices.map((d, i) => (
              <pre key={i} className="bg-white/10 p-3 rounded text-sm">
                {JSON.stringify(d, null, 2)}
              </pre>
            ))}
          </div>
        )}

        {/* LOGS */}
        {tab === "logs" && (
          <div>
            <h2 className="text-2xl font-bold mb-4">Logs</h2>
            {logs.length === 0 && <p>No hay logs.</p>}
            {logs.map((l, i) => (
              <div key={i} className="bg-white/10 p-3 rounded text-sm mb-2">
                {l.created_at} | {l.user_id} | {l.action}
              </div>
            ))}
          </div>
        )}

      </div>
    </div>
  );
}
