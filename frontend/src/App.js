import React, { useState } from 'react';
import OTPControlPanel from './OtpControlPanel';
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
      <div className="login-container">
        <form onSubmit={handleSubmit} className="login-form">
          <h2>Ingrese la contraseña</h2>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Contraseña"
          />
          <button type="submit">Entrar</button>
        </form>
      </div>
    );
  }

  return <OTPControlPanel />;
}

export default App;
