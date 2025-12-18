import { useState, useEffect } from "react";

export default function OTPControlPanel() {
  const API = "https://otp-api-kf7h.onrender.com/api";

  const [tab, setTab] = useState("registro");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [users, setUsers] = useState([]);
  const [devices, setDevices] = useState([]);
  const [logs, setLogs] = useState([]);
  const [qrImage, setQrImage] = useState(null);
  const [loadingQR, setLoadingQR] = useState(false);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [cedula, setCedula] = useState("");
  const [userID, setUserID] = useState("");

  useEffect(() => {
    setError("");
    if (tab === "usuarios") fetchUsers();
    if (tab === "dispositivos") fetchDevices();
    if (tab === "logs") fetchLogs();
  }, [tab]);

  async function fetchUsers() {
    try {
      setLoading(true);
      const res = await fetch(`${API}/users`);
      const data = await res.json();
      setUsers(data.users || []);
    } catch (e) {
      setError("Error cargando usuarios");
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  // ✅ CORREGIDO: Usar PATCH /api/devices/{name} con enabled
  async function toggleDeviceStatus(deviceName, currentEnabled) {
    try {
      setLoading(true);
      const newEnabled = !currentEnabled;
      
      console.log(`📤 Dispositivo: ${deviceName} -> enabled: ${newEnabled}`);
      
      const res = await fetch(`${API}/devices/${encodeURIComponent(deviceName)}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: newEnabled })
      });
      
      if (res.ok) {
        alert(`Dispositivo ${newEnabled ? 'habilitado' : 'deshabilitado'}`);
        fetchDevices();
      } else {
        const data = await res.json();
        alert(`Error: ${data.error || data.message}`);
      }
    } catch (e) {
      console.error('❌ Error:', e);
      alert("No se pudo cambiar el estado");
    } finally {
      setLoading(false);
    }
  }

  // ✅ NUEVO: Bloquear/Activar usuarios
  async function toggleUserStatus(userId, currentStatus) {
    try {
      setLoading(true);
      const newStatus = !currentStatus;
      
      console.log(`📤 Usuario: ${userId} -> status_user: ${newStatus}`);
      
      const res = await fetch(`${API}/users/${encodeURIComponent(userId)}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status_user: newStatus })
      });
      
      if (res.ok) {
        alert(`Usuario ${newStatus ? 'activado' : 'bloqueado'}`);
        fetchUsers();
      } else {
        const data = await res.json();
        alert(`Error: ${data.error || data.message}`);
      }
    } catch (e) {
      console.error('❌ Error:', e);
      alert("No se pudo cambiar el estado");
    } finally {
      setLoading(false);
    }
  }

  async function fetchDevices() {
    try {
      setLoading(true);
      const res = await fetch(`${API}/devices`);
      const data = await res.json();
      setDevices(data.devices || []);
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
      const res = await fetch(`${API}/logs`);
      const data = await res.json();
      setLogs(data.logs || []);
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
      const res = await fetch(`${API}/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userID,
          full_name: fullName,
          email,
          cedula
        })
      });

      if (res.ok) {
        alert("Usuario registrado correctamente");
        setFullName("");
        setEmail("");
        setCedula("");
        setUserID("");
        if (tab === "usuarios") fetchUsers();
      } else {
        alert("Error registrando usuario");
      }
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
      const res = await fetch(`${API}/users/${user_id}/qr`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setQrImage(url);
    } catch (e) {
      console.error("Error generando QR", e);
      alert("No se pudo generar el QR");
    } finally {
      setLoadingQR(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 to-indigo-900 p-6 text-white">
      <div className="max-w-5xl mx-auto bg-white/10 p-8 rounded-3xl shadow-xl backdrop-blur">

        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2">🔐 Panel de Control OTP</h1>
          <p className="text-purple-200">Sistema de autenticación de doble factor</p>
        </div>

        <div className="flex gap-4 mb-8 justify-center flex-wrap">
          {["registro", "usuarios", "dispositivos", "logs"].map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-6 py-3 rounded-lg font-bold transition-all ${
                tab === t 
                  ? "bg-indigo-600 shadow-lg scale-105" 
                  : "bg-white/20 hover:bg-white/30"
              }`}
            >
              {t.toUpperCase()}
            </button>
          ))}
        </div>

        {error && (
          <div className="bg-red-500/30 p-3 rounded mb-4 text-center border border-red-500">
            ⚠️ {error}
          </div>
        )}

        {loading && (
          <div className="text-center mb-4">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
            <p className="mt-2">Cargando datos...</p>
          </div>
        )}

        {/* REGISTRO */}
        {tab === "registro" && (
          <div>
            <h2 className="text-3xl font-bold mb-6">📝 Registrar Nuevo Usuario</h2>
            <div className="grid gap-4 max-w-xl mx-auto">
              <input 
                className="p-4 rounded-lg bg-white/20 backdrop-blur border border-white/30 placeholder-white/60" 
                placeholder="Nombre completo"
                value={fullName} 
                onChange={e => setFullName(e.target.value)} 
              />
              <input 
                className="p-4 rounded-lg bg-white/20 backdrop-blur border border-white/30 placeholder-white/60" 
                placeholder="Correo electrónico"
                type="email"
                value={email} 
                onChange={e => setEmail(e.target.value)} 
              />
              <input 
                className="p-4 rounded-lg bg-white/20 backdrop-blur border border-white/30 placeholder-white/60" 
                placeholder="Cédula"
                value={cedula} 
                onChange={e => setCedula(e.target.value)} 
              />
              <input 
                className="p-4 rounded-lg bg-white/20 backdrop-blur border border-white/30 placeholder-white/60" 
                placeholder="User ID"
                value={userID} 
                onChange={e => setUserID(e.target.value)} 
              />
              <button
                onClick={registrarUsuario}
                className="bg-green-600 p-4 rounded-lg font-bold hover:bg-green-700"
                disabled={loading || !fullName || !email || !cedula || !userID}
              >
                ✅ Registrar Usuario
              </button>
            </div>
          </div>
        )}

        {/* USUARIOS */}
        {tab === "usuarios" && (
          <div>
            <h2 className="text-3xl font-bold mb-6">👥 Gestión de Usuarios</h2>
            {users.length === 0 && <p className="text-center py-12 text-xl">No hay usuarios.</p>}
            <div className="grid gap-4">
              {users.map(u => (
                <div key={u.id} className="bg-white/10 p-6 rounded-xl border border-white/20">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-2xl font-bold mb-2">{u.full_name}</h3>
                      <p><strong>ID:</strong> {u.user_id}</p>
                      <p><strong>Email:</strong> {u.email}</p>
                      <p>
                        <strong>Estado:</strong>{" "}
                        <span className={u.status_user ? "text-green-400" : "text-red-400"}>
                          {u.status_user ? "✅ Activo" : "🚫 Inactivo"}
                        </span>
                      </p>
                    </div>
                    <button
                      className={`px-4 py-2 rounded-lg font-bold ${
                        u.status_user ? "bg-red-600" : "bg-green-600"
                      }`}
                      onClick={() => toggleUserStatus(u.user_id, u.status_user)}
                    >
                      {u.status_user ? "🔒 Bloquear" : "🔓 Activar"}
                    </button>
                  </div>
                  <button
                    className="mt-4 bg-indigo-600 px-6 py-3 rounded-lg font-bold w-full"
                    onClick={() => generarNuevoQR(u.user_id)}
                  >
                    📱 Generar QR
                  </button>
                </div>
              ))}
            </div>
            {loadingQR && <p className="text-center mt-4">Generando QR…</p>}
            {qrImage && (
              <div className="mt-6 text-center bg-white p-6 rounded-xl">
                <img src={qrImage} alt="QR" className="w-64 h-64 mx-auto" />
                <button
                  className="mt-4 bg-purple-600 px-6 py-3 rounded-lg font-bold"
                  onClick={() => setQrImage(null)}
                >
                  Cerrar
                </button>
              </div>
            )}
          </div>
        )}

        {/* DISPOSITIVOS */}
        {tab === "dispositivos" && (
          <div>
            <h2 className="text-3xl font-bold mb-6">🖥️ Gestión de Dispositivos</h2>
            {devices.length === 0 && <p className="text-center py-12 text-xl">No hay dispositivos.</p>}
            <div className="grid gap-4">
              {devices.map((d, i) => (
                <div key={i} className="bg-white/10 p-6 rounded-xl border border-white/20">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-2xl font-bold mb-2">{d.name}</h3>
                      <p>
                        <strong>Estado:</strong>{" "}
                        <span className={d.enabled ? "text-green-400" : "text-red-400"}>
                          {d.enabled ? "✅ Habilitado" : "🚫 Deshabilitado"}
                        </span>
                      </p>
                      <p><strong>IP:</strong> {d.ip_address || "—"}</p>
                      <p><strong>Último uso:</strong> {d.last_used ? new Date(d.last_used).toLocaleString() : "Nunca"}</p>
                    </div>
                    <button
                      className={`px-6 py-3 rounded-lg font-bold ${
                        d.enabled ? "bg-red-600" : "bg-green-600"
                      }`}
                      onClick={() => toggleDeviceStatus(d.name, d.enabled)}
                    >
                      {d.enabled ? "🔒 Deshabilitar" : "🔓 Habilitar"}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* LOGS */}
        {tab === "logs" && (
          <div>
            <h2 className="text-3xl font-bold mb-6">📋 Logs</h2>
            {logs.length === 0 && <p className="text-center py-12 text-xl">No hay logs.</p>}
            {logs.length > 0 && (
              <table className="w-full bg-white/10 rounded-xl overflow-hidden">
                <thead className="bg-black/30">
                  <tr>
                    <th className="p-3 text-left">Fecha</th>
                    <th className="p-3 text-left">Usuario</th>
                    <th className="p-3 text-left">Dispositivo</th>
                    <th className="p-3 text-left">Acción</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map(log => (
                    <tr key={log.id} className="border-t border-white/10">
                      <td className="p-3">{new Date(log.timestamp).toLocaleString()}</td>
                      <td className="p-3">{log.user_id || "—"}</td>
                      <td className="p-3">{log.device_name || "—"}</td>
                      <td className="p-3">
                        <span className={`px-3 py-1 rounded-full text-xs ${
                          log.action.includes("Exitoso") ? "bg-green-600" : "bg-red-600"
                        }`}>
                          {log.action}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

      </div>
    </div>
  );
}

