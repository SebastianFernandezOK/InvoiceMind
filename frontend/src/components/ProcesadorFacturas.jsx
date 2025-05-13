import { useState } from "react";

function ProcesadorFacturas() {
  const [files, setFiles] = useState([]);
  const [excelBlob, setExcelBlob] = useState(null);
  const [cargando, setCargando] = useState(false);

  const handleFileChange = (e) => {
    setFiles(e.target.files);
    setExcelBlob(null);
  };

  const procesarFacturas = async () => {
    setCargando(true);
    const formData = new FormData();
    Array.from(files).forEach(file => formData.append("pdfs", file));

    try {
      const res = await fetch("http://localhost:8000/procesar-excel", {
        method: "POST",
        body: formData
      });

      if (!res.ok) throw new Error("Error al procesar facturas");
      const blob = await res.blob();
      setExcelBlob(blob);
    } catch (err) {
      console.error("Error:", err);
    } finally {
      setCargando(false);
    }
  };

  const descargarExcel = () => {
    if (!excelBlob) return;
    const url = window.URL.createObjectURL(excelBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "facturas.xlsx";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={{
      height: "100vh",
      width: "100vw",
      backgroundColor: "#f9f9f9",
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      flexDirection: "column",
      fontFamily: "'Segoe UI', sans-serif",
      padding: "20px"
    }}>
      <h1 style={{
        fontSize: "40px",
        marginBottom: "30px",
        fontWeight: "700",
        color: "#2c3e50"
      }}>
        InvoiceMind
      </h1>

      <div style={{
        width: "100%",
        maxWidth: "500px",
        backgroundColor: "#ffffff",
        padding: "40px",
        borderRadius: "16px",
        boxShadow: "0px 20px 40px rgba(0, 0, 0, 0.1)",
        textAlign: "center"
      }}>
        <h2 style={{ fontSize: "24px", marginBottom: "10px" }}>Procesador de Facturas</h2>
        <p style={{ fontWeight: "bold", margin: 0 }}>Centraliza información de facturas en PDF</p>
        <p style={{ fontSize: "14px", color: "#666", marginBottom: "20px" }}>
          Procesa múltiples facturas PDF y obtené un Excel con los datos estructurados.
        </p>

        <label style={{
          backgroundColor: "#e53935",
          color: "white",
          padding: "12px 24px",
          borderRadius: "6px",
          fontWeight: "bold",
          cursor: "pointer",
          display: "inline-block",
          marginBottom: "20px"
        }}>
          Seleccionar archivo PDF
          <input type="file" multiple accept="application/pdf" onChange={handleFileChange} style={{ display: "none" }} />
        </label>

        {files.length > 0 && (
          <div style={{
            backgroundColor: "#f1f1f1",
            marginTop: "10px",
            padding: "15px",
            borderRadius: "8px",
            textAlign: "left",
            maxHeight: "150px",
            overflowY: "auto"
          }}>
            <p style={{ margin: 0, fontWeight: "bold", color: "#2e7d32" }}>PDFs cargados:</p>
            <ul style={{ margin: "10px 0", paddingLeft: "20px", fontSize: "14px" }}>
              {Array.from(files).map((file, index) => (
                <li key={index}>{file.name}</li>
              ))}
            </ul>
          </div>
        )}

        <div style={{ marginTop: "30px" }}>
          {cargando ? (
            <div style={{ marginTop: "10px" }}>
              <div style={{
                width: "36px",
                height: "36px",
                border: "5px solid #ddd",
                borderTop: "5px solid #0077ff",
                borderRadius: "50%",
                animation: "spin 1s linear infinite",
                margin: "0 auto"
              }} />
              <p style={{ marginTop: "10px", color: "#0077ff", fontWeight: "500" }}>Procesando...</p>
            </div>
          ) : (
            <button
              onClick={excelBlob ? descargarExcel : procesarFacturas}
              disabled={files.length === 0}
              style={{
                backgroundColor: excelBlob ? "#0077ff" : "#00c853",
                color: "#fff",
                border: "none",
                padding: "12px 24px",
                borderRadius: "6px",
                fontWeight: "bold",
                cursor: "pointer",
                fontSize: "14px"
              }}
            >
              {excelBlob ? "Descargar Excel" : "Procesar y Generar Excel"}
            </button>
          )}
        </div>
      </div>

      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
    </div>
  );
}

export default ProcesadorFacturas;
