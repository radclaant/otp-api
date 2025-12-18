import React, { useState } from 'react';
import OTPControlPanel from './OTPControlPanel';
import './App.css';

function App() {
  const [password, setPassword] = useState('');
  const [authenticated, setAuthenticated] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (password === '123456789') { // Cambia la contraseña aquí
      setAuthenticated(true);
    } else {
      alert('Contraseña incorrecta');
    }
  };

if (!authenticated) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-indigo-950 p-6">
      <form onSubmit={handleSubmit} className="bg-white/10 backdrop-blur-md p-8 rounded-2xl shadow-2xl border border-white/20 w-full max-w-md">
        <h2 className="text-3xl font-bold text-white mb-6 text-center">Acceso Seguro</h2>
        <div className="flex flex-col gap-4">
          <input
            type="password"
            className="w-full p-4 rounded-lg bg-white/20 text-white placeholder-white/50 border border-white/10 focus:outline-none focus:ring-2 focus:ring-purple-500"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Contraseña del sistema"
          />
          <button 
            type="submit" 
            className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-4 rounded-lg transition-all active:scale-95"
          >
            Entrar al Panel
          </button>
        </div>
      </form>
    </div>
  );
}

  return <OTPControlPanel />;
}

export default App;
