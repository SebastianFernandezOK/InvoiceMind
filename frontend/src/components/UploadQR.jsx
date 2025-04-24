import { useState } from "react";

function UploadQR() {
  const [files, setFiles] = useState([]);
  const [jsonQR, setJsonQR] = useState(null);
  const [cargando, setCargando] = useState(false);

  const handleFileChange = (e) => {
    setFiles(e.target.files);
  };

  const handleUpload = async () => {
    setCargando(true);
    const formData = new FormData();
    Array.from(files).forEach(file => formData.append("pdfs", file));

    try {
      const response = await fetch("http://localhost:8000/procesar-etapa-qr", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      setJsonQR(data);
    } catch (error) {
      console.error("Error al procesar QR:", error);
    } finally {
      setCargando(false);
    }
  };

  const copiarAlPortapapeles = () => {
    navigator.clipboard.writeText(JSON.stringify(jsonQR, null, 2));
    alert("JSON copiado al portapapeles");
  };

  return (
    <div>
      <h2>Procesar QR de Facturas</h2>
      <input type="file" multiple accept="application/pdf" onChange={handleFileChange} />
      <button onClick={handleUpload} disabled={cargando} style={{ marginLeft: "10px" }}>
        {cargando ? "Procesando..." : "Procesar QR"}
      </button>

      {jsonQR && (
        <div style={{
          marginTop: "20px",
          backgroundColor: "#1e1e1e",
          color: "#ffffff",
          padding: "20px",
          borderRadius: "8px",
          fontFamily: "monospace",
          fontSize: "14px",
          overflowX: "auto",
          maxHeight: "500px"
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ color: "#00ffaa" }}>JSON con datos del QR:</h3>
            <button onClick={copiarAlPortapapeles} style={{
              background: "#00ffaa",
              color: "#000",
              border: "none",
              borderRadius: "4px",
              padding: "5px 10px",
              cursor: "pointer"
            }}>
              Copiar JSON
            </button>
          </div>
          <pre>{JSON.stringify(jsonQR, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default UploadQR;
