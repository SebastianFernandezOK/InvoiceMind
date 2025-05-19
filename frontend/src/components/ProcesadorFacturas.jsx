import { useState, useEffect } from "react";

function ProcesadorFacturas() {
  const [files, setFiles] = useState([]);
  const [excelBlob, setExcelBlob] = useState(null);
  const [estadoProceso, setEstadoProceso] = useState("idle"); // 'idle' | 'procesando' | 'completado'
  const [historial, setHistorial] = useState([]);

  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files));
    setExcelBlob(null);
    setEstadoProceso("idle");
  };

  const procesarFacturas = async () => {
    setEstadoProceso("procesando");
    const formData = new FormData();
    files.forEach(file => formData.append("pdfs", file));

    try {
      const res = await fetch("http://localhost:8000/procesar-excel", {
        method: "POST",
        body: formData
      });

      if (!res.ok) throw new Error("Error al procesar facturas");
      const blob = await res.blob();

      console.log("Blob recibido", blob);

      if (blob && blob.size > 0) {
        setExcelBlob(blob);
        setEstadoProceso("completado");
      } else {
        console.warn("El archivo recibido está vacío");
        setEstadoProceso("idle");
      }
    } catch (err) {
      console.error("Error:", err);
      setEstadoProceso("idle");
    } finally {
      cargarHistorial();
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

    // Limpiar después de descargar
    setFiles([]);
    setExcelBlob(null);
    setEstadoProceso("idle");
  };

  const cargarHistorial = async () => {
    try {
      const res = await fetch("http://localhost:8000/historial");
      const data = await res.json();
      setHistorial(data);
    } catch (err) {
      console.error("Error cargando historial:", err);
    }
  };

  useEffect(() => {
    cargarHistorial();
  }, []);

  return (
    <div style={{
      height: "100vh",
      width: "100vw",
      backgroundColor: "#f5f5f5",
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      fontFamily: "sans-serif"
    }}>
      <div style={{
        display: "flex",
        gap: "40px",
        alignItems: "flex-start"
      }}>
        {/* Panel izquierdo */}
        <div style={{
          backgroundColor: "#fff",
          padding: "30px",
          borderRadius: "12px",
          boxShadow: "0 4px 10px rgba(0,0,0,0.1)",
          minWidth: "350px"
        }}>
          <h2 style={{ fontSize: "22px", color: "#002244", marginBottom: "10px" }}>Procesador de Facturas</h2>
          <p style={{ fontWeight: "bold", marginBottom: "6px" }}>Centraliza información de facturas en PDF</p>
          <p style={{ color: "#555", marginBottom: "20px" }}>
            Procesa múltiples facturas PDF y obtené un Excel con los datos estructurados.
          </p>

          {/* Selector de archivos */}
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <label style={{
              backgroundColor: "#e53935",
              color: "white",
              padding: "10px 20px",
              borderRadius: "8px",
              fontWeight: "bold",
              cursor: "pointer",
              textAlign: "center"
            }}>
              Seleccionar archivo PDF
              <input type="file" multiple accept="application/pdf" onChange={handleFileChange} style={{ display: "none" }} />
            </label>

            {/* Caja de archivos seleccionados */}
            {files.length > 0 && (
              <div style={{
                border: "1px solid #ccc",
                borderRadius: "8px",
                padding: "10px",
                backgroundColor: "#fafafa"
              }}>
                <p style={{ fontWeight: "bold", color: "#444", marginBottom: "6px" }}>Archivos seleccionados:</p>
                <ul style={{ fontSize: "14px", paddingLeft: "18px", color: "#333", margin: 0 }}>
                  {files.map((f, i) => (
                    <li key={i}>{f.name}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Estados del botón principal */}
            {estadoProceso === "idle" && (
              <button
                onClick={procesarFacturas}
                disabled={files.length === 0}
                style={{
                  backgroundColor: "#00c853",
                  color: "#fff",
                  border: "none",
                  padding: "10px 20px",
                  borderRadius: "8px",
                  fontWeight: "bold",
                  cursor: "pointer"
                }}>
                Procesar y Generar Excel
              </button>
            )}

            {estadoProceso === "procesando" && (
              <div style={{ display: "flex", justifyContent: "center", marginTop: "10px" }}>
                <div className="spinner"></div>
              </div>
            )}

            {estadoProceso === "completado" && excelBlob && (
              <button
                onClick={descargarExcel}
                style={{
                  backgroundColor: "#007f00",
                  color: "#fff",
                  border: "none",
                  padding: "10px 20px",
                  borderRadius: "8px",
                  fontWeight: "bold",
                  cursor: "pointer"
                }}>
                Descargar Excel
              </button>
            )}
          </div>
        </div>

        {/* Historial */}
        <div style={{
          backgroundColor: "#fff",
          padding: "20px",
          borderRadius: "12px",
          boxShadow: "0 4px 10px rgba(0,0,0,0.1)",
          minWidth: "350px"
        }}>
          <h3 style={{ marginBottom: "10px", color: "#002244" }}>Historial de Archivos</h3>
          <ul>
            {historial.map((item, idx) => (
              <li key={idx} style={{ marginBottom: "10px" }}>
                <strong>{item.nombre_pdf}</strong><br />
                <a href={`http://localhost:8000/exports/${item.nombre_excel}`} target="_blank" rel="noreferrer">
                  Descargar Excel consolidado
                </a>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Spinner CSS */}
      <style>{`
        .spinner {
          width: 32px;
          height: 32px;
          border: 4px solid #0077cc;
          border-top: 4px solid transparent;
          border-radius: 50%;
          animation: spin 0.7s linear infinite;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default ProcesadorFacturas;
