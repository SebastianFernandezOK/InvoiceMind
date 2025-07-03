import React, { useState } from "react";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const res = await fetch("http://localhost:8000/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (res.status === 401) {
        setError("Credenciales incorrectas");
        return;
      }
      const data = await res.json();
      localStorage.setItem("token", data.access_token);
      
      // Guardar información del usuario
      if (data.user) {
        localStorage.setItem("user", JSON.stringify(data.user));
      }
      
      window.location.href = "/procesar-facturas"; // Redirige al procesador de facturas
    } catch {
      setError("Error de red");
    }
  };

  return (
    <div className="centered">
      <div className="card">
        <h1 style={{ fontSize: "2.5rem", marginBottom: "1rem", color: "#1d1d1f" }}>Iniciar Sesión</h1>
        <p style={{ marginBottom: "2rem", color: "#86868b" }}>Accede a tu cuenta de InvoiceMind</p>
        
        <form onSubmit={handleLogin} style={{ width: "100%" }}>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input 
              type="email"
              placeholder="tucorreo@ejemplo.com" 
              value={email} 
              onChange={e => setEmail(e.target.value)} 
              className="form-input"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Contraseña</label>
            <input 
              type="password"
              placeholder="••••••••" 
              value={password} 
              onChange={e => setPassword(e.target.value)} 
              className="form-input"
              required
            />
          </div>

          <button type="submit" className="btn-main" style={{ width: "100%", marginTop: "1rem" }}>
            Iniciar Sesión
          </button>

          {error && (
            <div className="error-message" style={{ marginTop: "1rem" }}>
              {error}
            </div>
          )}

          <div style={{ 
            marginTop: "2rem", 
            textAlign: "center", 
            fontSize: "1.1rem", 
            fontWeight: "500" 
          }}>
            ¿No tienes cuenta?{" "}
            <a 
              href="/register" 
              style={{ 
                color: "#007aff", 
                textDecoration: "none",
                fontWeight: "500"
              }}
            >
              Regístrate aquí
            </a>
          </div>
        </form>
      </div>
    </div>
  );
}