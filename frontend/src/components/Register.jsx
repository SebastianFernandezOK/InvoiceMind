import React, { useState } from "react";

export default function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  const handleRegister = async (e) => {
    e.preventDefault();
    setError("");
    setMsg("");
    try {
      const res = await fetch("http://localhost:8000/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
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
    <form onSubmit={handleRegister} style={{
      width: "100vw",
      minHeight: "100vh",
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
      alignItems: "center",
      background: "linear-gradient(120deg, #e3f2fd 0%, #fff 100%)",
      margin: 0,
      padding: 0,
    }}>
      <div style={{
        width: 400,
        background: "#fff",
        padding: 40,
        borderRadius: 18,
        boxShadow: "0 8px 32px #1a237e22",
        display: "flex",
        flexDirection: "column",
        gap: 18,
        alignItems: "center"
      }}>
        <h2 style={{ textAlign: "center", color: "#1a237e", marginBottom: 18, fontWeight: 700, letterSpacing: 1 }}>Registro</h2>
        <input 
          placeholder="Email" 
          value={email} 
          onChange={e => setEmail(e.target.value)} 
          style={{ 
            width: "100%", 
            marginBottom: 14, 
            padding: 14, 
            borderRadius: 8, 
            border: "1px solid #bdbdbd", 
            fontSize: 18, 
            outline: "none", 
            transition: "border 0.2s", 
            boxSizing: "border-box" 
          }} 
        />
        <input 
          placeholder="Password" 
          type="password" 
          value={password} 
          onChange={e => setPassword(e.target.value)} 
          style={{ 
            width: "100%", 
            marginBottom: 14, 
            padding: 14, 
            borderRadius: 8, 
            border: "1px solid #bdbdbd", 
            fontSize: 18, 
            outline: "none", 
            transition: "border 0.2s", 
            boxSizing: "border-box" 
          }} 
        />
        <button 
          type="submit" 
          style={{ 
            width: "100%", 
            background: "linear-gradient(90deg, #1a237e 60%, #3949ab 100%)", 
            color: "#fff", 
            padding: 14, 
            border: 0, 
            borderRadius: 8, 
            fontWeight: 600, 
            fontSize: 18, 
            letterSpacing: 1, 
            boxShadow: "0 2px 8px #1a237e22", 
            cursor: "pointer", 
            marginTop: 6
          }}
        >Registrarse</button>
        {msg && <div style={{color:"#388e3c", marginTop: 12, fontWeight: 500, fontSize: 16}}>{msg}</div>}
        {error && <div style={{color:"#d32f2f", marginTop: 12, fontWeight: 500, fontSize: 16}}>{error}</div>}
        <div style={{ marginTop: 18, textAlign: "center", fontSize: 16 }}>
          ¿Ya tienes cuenta? <a href="/login" style={{ color: "#3949ab", textDecoration: "underline" }}>Inicia sesión</a>
        </div>
      </div>
    </form>
  );
}
