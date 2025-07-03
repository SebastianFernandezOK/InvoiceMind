import React, { useState } from "react";

export default function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [plan, setPlan] = useState("basico");
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  const planes = {
    basico: { nombre: "Básico", procesamientos: 100, precio: "Gratis" },
    profesional: { nombre: "Profesional", procesamientos: 500, precio: "$29/mes" },
    empresarial: { nombre: "Empresarial", procesamientos: 1000, precio: "$59/mes" }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError("");
    setMsg("");
    try {
      const res = await fetch("http://localhost:8000/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, plan }),
      });
      if (res.status === 400) {
        setError("Email ya registrado");
        return;
      }
      setMsg("Registro exitoso. Ahora puedes iniciar sesión.");
    } catch {
      setError("Error de red");
    }
  };

  return (
    <div className="centered">
      <div className="card">
        <h1 style={{ fontSize: "2.5rem", marginBottom: "1rem", color: "#1d1d1f" }}>Crear Cuenta</h1>
        <p style={{ marginBottom: "2rem", color: "#86868b" }}>Únete a InvoiceMind y comienza a procesar facturas</p>
        
        <form onSubmit={handleRegister} style={{ width: "100%" }}>
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

          <div className="form-group">
            <label className="form-label">Selecciona tu Plan</label>
            <div style={{ display: "flex", gap: "1rem", flexDirection: "column" }}>
              {Object.entries(planes).map(([key, planInfo]) => (
                <div 
                  key={key}
                  onClick={() => setPlan(key)}
                  style={{
                    padding: "1rem",
                    border: plan === key ? "2px solid #007aff" : "1px solid rgba(0, 0, 0, 0.1)",
                    borderRadius: "12px",
                    cursor: "pointer",
                    backgroundColor: plan === key ? "rgba(0, 122, 255, 0.1)" : "rgba(255, 255, 255, 0.6)",
                    transition: "all 0.3s ease"
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                      <div style={{ fontWeight: "600", fontSize: "1.1rem", color: "#1d1d1f" }}>
                        {planInfo.nombre}
                      </div>
                      <div style={{ color: "#86868b", fontSize: "0.9rem" }}>
                        {planInfo.procesamientos} procesamientos/mes
                      </div>
                    </div>
                    <div style={{ fontWeight: "600", color: "#007aff" }}>
                      {planInfo.precio}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <button type="submit" className="btn-main" style={{ width: "100%", marginTop: "1rem" }}>
            Crear Cuenta
          </button>

          {msg && (
            <div className="success-message" style={{ marginTop: "1rem" }}>
              {msg}
            </div>
          )}

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
            ¿Ya tienes cuenta?{" "}
            <a 
              href="/login" 
              style={{ 
                color: "#007aff", 
                textDecoration: "none",
                fontWeight: "500"
              }}
            >
              Inicia sesión
            </a>
          </div>
        </form>
      </div>
    </div>
  );
}
