import React, { useState, useEffect } from 'react';
import { Shield, Check, X, Monitor, Key, Clock, AlertCircle } from 'lucide-react';

const OTPControlPanel = () => {
  const [devices, setDevices] = useState([]);
  const [newDevice, setNewDevice] = useState({ name: '', otp: '' });
  const [accessLogs, setAccessLogs] = useState([]);
  const [activeTab, setActiveTab] = useState('devices');
  const [loading, setLoading] = useState(false);

  const API_URL = 'https://otp-api-kf7h.onrender.com/api';
  
  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const res = await fetch(`${API_URL}/devices`);
      const data = await res.json();
      setDevices(data.devices || []);
      setAccessLogs(data.logs || []);
    } catch (e) {
      console.error(e);
    }
  };

  const generateOTP = () => Math.floor(100000 + Math.random() * 900000).toString();

  const addDevice = async () => {
    if (!newDevice.name.trim()) return alert('Ingresa nombre de dispositivo');
    setLoading(true);
    const otp = generateOTP();
    const device = { name: newDevice.name.trim(), otp, enabled: true };
    try {
      const res = await fetch(`${API_URL}/devices`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(device)
      });
      if (res.ok) {
        await loadData();
        setNewDevice({ name: '', otp: '' });
        alert(`✅ Dispositivo agregado: ${device.name}\nOTP: ${otp}`);
      }
    } catch (e) {
      console.error(e);
      alert('❌ Error agregando dispositivo');
    } finally {
      setLoading(false);
    }
  };

  const toggleDevice = async (id) => {
    const device = devices.find(d => d.id === id);
    try {
      const res = await fetch(`${API_URL}/devices/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: !device.enabled })
      });
      if (res.ok) await loadData();
    } catch (e) { console.error(e); }
  };

  const deleteDevice = async (id) => {
    if (!window.confirm('⚠️ Eliminar dispositivo?')) return;
    try {
      const res = await fetch(`${API_URL}/devices/${id}`, { method: 'DELETE' });
      if (res.ok) await loadData();
    } catch (e) { console.error(e); }
  };

  const formatDate = (iso) => iso ? new Date(iso).toLocaleString('es-ES') : 'Nunca';

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-indigo-900 to-slate-900 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 mb-6 border border-white/20 flex items-center gap-4">
          <div className="bg-gradient-to-br from-pink-500 to-purple-500 p-3 rounded-xl">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white">Sistema OTP - Control Remoto</h1>
            <p className="text-purple-200">Gestiona el acceso desde cualquier lugar</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-4 mb-6">
          {['devices', 'logs'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-3 rounded-xl font-semibold transition-all ${
                activeTab === tab
                  ? 'bg-white text-purple-900 shadow-lg'
                  : 'bg-white/10 text-white hover:bg-white/20'
              }`}
            >
              {tab === 'devices' ? <Monitor className="w-5 h-5 inline mr-2"/> : <Clock className="w-5 h-5 inline mr-2"/>}
              {tab === 'devices' ? 'Dispositivos' : 'Registro'}
            </button>
          ))}
        </div>

        {/* Content */}
        {activeTab === 'devices' && (
          <div className="space-y-6">
            {/* Nuevo Dispositivo */}
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
              <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2"><Key className="w-6 h-6"/> Agregar Dispositivo</h2>
              <div className="flex gap-4">
                <input
                  type="text"
                  placeholder="Nombre del PC"
                  value={newDevice.name}
                  onChange={e => setNewDevice({ ...newDevice, name: e.target.value })}
                  className="flex-1 px-4 py-3 rounded-xl bg-white/20 border border-white/30 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                <button
                  onClick={addDevice}
                  disabled={loading}
                  className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold rounded-xl hover:shadow-lg hover:scale-105 transition-all disabled:opacity-50"
                >
                  {loading ? '⏳ Generando...' : 'Generar OTP'}
                </button>
              </div>
            </div>

            {/* Lista de Dispositivos */}
            <div className="grid gap-4">
              {devices.length === 0 ? (
                <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-12 border border-white/10 text-center">
                  <AlertCircle className="w-16 h-16 text-white/30 mx-auto mb-4"/>
                  <p className="text-white/50 text-lg">No hay dispositivos</p>
                  <p className="text-white/30 text-sm mt-2">Agrega tu primer dispositivo para empezar</p>
                </div>
              ) : devices.map(device => (
                <div key={device.id} className={`bg-white/10 backdrop-blur-lg rounded-2xl p-6 border transition-all ${
                  device.enabled
                    ? 'border-green-400/50 shadow-lg shadow-green-500/20'
                    : 'border-red-400/50 opacity-75'
                }`}>
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-3 mb-2">
                        <Monitor className="w-6 h-6 text-white"/>
                        <h3 className="text-xl font-bold text-white">{device.name}</h3>
                        <span className={`px-3 py-1 rounded-full text-sm font-semibold flex items-center gap-1 ${
                          device.enabled ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'
                        }`}>
                          {device.enabled ? <Check className="w-4 h-4"/> : <X className="w-4 h-4"/>}
                          {device.enabled ? 'Activo' : 'Bloqueado'}
                        </span>
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-white/50 text-sm">OTP:</span>
                          <code className="px-4 py-2 bg-black/30 text-green-300 font-mono text-lg rounded-lg border border-white/10">{device.otp}</code>
                        </div>
                        <div className="text-white/50 text-sm">Creado: {formatDate(device.createdAt)}</div>
                        {device.lastUsed && <div className="text-white/50 text-sm">Último uso: {formatDate(device.lastUsed)}</div>}
                      </div>
                    </div>
                    <div className="flex flex-col gap-2 ml-4">
                      <button onClick={() => toggleDevice(device.id)} className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                        device.enabled ? 'bg-red-500/20 text-red-300 hover:bg-red-500/30' : 'bg-green-500/20 text-green-300 hover:bg-green-500/30'
                      }`}>{device.enabled ? 'Bloquear' : 'Activar'}</button>
                      <button onClick={() => deleteDevice(device.id)} className="px-4 py-2 bg-white/10 text-white/50 rounded-lg font-semibold hover:bg-white/20 transition-all">Eliminar</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'logs' && (
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 max-h-96 overflow-y-auto">
            <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2"><Clock className="w-6 h-6"/> Registro</h2>
            {accessLogs.length === 0 ? <p className="text-white/50 text-center py-8">No hay registros</p> :
              accessLogs.map((log, i) => (
                <div key={i} className="flex items-center justify-between p-4 bg-white/5 rounded-lg border border-white/10 mb-2">
                  <div>
                    <span className="text-white font-semibold">{log.device}</span>
                    <span className="text-white/50 mx-2">•</span>
                    <span className="text-white/70">{log.action}</span>
                  </div>
                  <span className="text-white/50 text-sm">{formatDate(log.timestamp)}</span>
                </div>
              ))
            }
          </div>
        )}
      </div>
    </div>
  );
};

export default OTPControlPanel;
