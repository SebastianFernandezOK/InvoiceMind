import { useState, useEffect } from "react";

function ProcesadorFacturas() {
  const [files, setFiles] = useState([]);
  const [excelBlob, setExcelBlob] = useState(null);
  const [estadoProceso, setEstadoProceso] = useState("idle");
  const [historial, setHistorial] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [pdfUrl, setPdfUrl] = useState(null);

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
        body: formData,
        headers: {
          Authorization: "Bearer " + localStorage.getItem("token")
        }
      });

      if (res.status === 401) {
        localStorage.removeItem("token");
        window.location.href = "/login";
        return;
      }

      if (!res.ok) throw new Error("Error al procesar facturas");
      const blob = await res.blob();

      if (blob && blob.size > 0) {
        setExcelBlob(blob);
        setEstadoProceso("completado");
      } else {
        setEstadoProceso("idle");
      }
    } catch (err) {
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

    setFiles([]);
    setExcelBlob(null);
    setEstadoProceso("idle");
  };

  const cargarHistorial = async () => {
    try {
      const res = await fetch("http://localhost:8000/historial", {
        headers: {
          Authorization: "Bearer " + localStorage.getItem("token")
        }
      });
      if (res.status === 401) {
        localStorage.removeItem("token");
        window.location.href = "/login";
        return;
      }
      const data = await res.json();
      setHistorial(data);
    } catch (err) {
      // Error manejado
    }
  };

  const handleVerPdf = (item) => {
    setPdfUrl(`http://localhost:8000/archivos/${encodeURIComponent(item.nombre_pdf)}`);
    setModalOpen(true);
  };

  const cerrarModal = () => {
    setModalOpen(false);
    setPdfUrl(null);
  };

  useEffect(() => {
    cargarHistorial();
  }, []);

  return (
    <div style={{
      height: "100vh",
      width: "100vw",
      backgroundColor: "#f0f4f8",
      fontFamily: "'Segoe UI', sans-serif",
      padding: "40px"
    }}>
      <h1 style={{
        textAlign: "center",
        fontSize: "48px",
        color: "#1a237e",
        marginBottom: "40px"
      }}>
        InvoiceMind
      </h1>

      <div style={{
        display: "flex",
        gap: "40px",
        justifyContent: "center",
        alignItems: "flex-start"
      }}>
        {/* Panel izquierdo */}
        <div style={{
          backgroundColor: "#ffffff",
          padding: "30px",
          borderRadius: "16px",
          boxShadow: "0 8px 20px rgba(0,0,0,0.1)",
          minWidth: "400px",
          display: "flex",
          flexDirection: "column"
        }}>
          <h2 style={{ fontSize: "24px", color: "#37474f", marginBottom: "10px" }}>Procesador de Facturas</h2>
          <p style={{ fontWeight: "bold", marginBottom: "6px", color: "#546e7a" }}>Centraliza información de facturas digitales</p>
          <p style={{ color: "#607d8b", marginBottom: "20px" }}>
            Procesa múltiples facturas PDF y obtené un Excel con los datos estructurados.
          </p>

          <label style={{
            backgroundColor: "#d32f2f",
            color: "white",
            padding: "12px 20px",
            borderRadius: "10px",
            fontWeight: "bold",
            cursor: "pointer",
            textAlign: "center",
            marginBottom: "16px"
          }}>
            Seleccionar archivos PDF
            <input type="file" multiple accept="application/pdf" onChange={handleFileChange} style={{ display: "none" }} />
          </label>

          {files.length > 0 && (
            <div style={{
              border: "2px dashed #90caf9",
              backgroundColor: "#e3f2fd",
              borderRadius: "10px",
              padding: "12px",
              marginBottom: "20px"
            }}>
              <p style={{ fontWeight: "bold", color: "#1565c0" }}>📄 Archivos seleccionados:</p>
              <ul style={{ listStyle: "none", paddingLeft: "10px", color: "#0d47a1", marginTop: "8px" }}>
                {files.map((f, i) => (
                  <li key={i}>• {f.name}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Botones y estados */}
          <div style={{ display: "flex", flexDirection: "column", gap: "14px", alignItems: "center" }}>
            {estadoProceso === "idle" && (
              <button
                onClick={procesarFacturas}
                disabled={files.length === 0}
                style={{
                  backgroundColor: "#43a047",
                  color: "#fff",
                  border: "none",
                  padding: "12px 20px",
                  borderRadius: "10px",
                  fontWeight: "bold",
                  cursor: "pointer",
                  width: "100%"
                }}>
                Procesar y Generar Excel
              </button>
            )}

            {estadoProceso === "procesando" && (
              <div className="circle-loader"></div>
            )}

            {estadoProceso === "completado" && excelBlob && (
              <button
                onClick={descargarExcel}
                style={{
                  backgroundColor: "#00796b",
                  color: "#fff",
                  border: "none",
                  padding: "12px 20px",
                  borderRadius: "10px",
                  fontWeight: "bold",
                  cursor: "pointer",
                  width: "100%"
                }}>
                Descargar Excel
              </button>
            )}
          </div>
        </div>

        {/* Historial */}
        <div style={{
          backgroundColor: "#ffffff",
          padding: "24px",
          borderRadius: "16px",
          boxShadow: "0 8px 20px rgba(0,0,0,0.1)",
          minWidth: "400px"
        }}>
          <h3 style={{ marginBottom: "16px", color: "#1a237e", fontSize: "20px" }}>📚 Historial de Archivos</h3>
          <ul style={{ paddingLeft: "20px", color: "#37474f" }}>
            {historial.length === 0 && (
              <li>No hay archivos en el historial.</li>
            )}
            {historial.map((item, idx) => (
              <li
                key={idx}
                style={{ marginBottom: "10px", cursor: "pointer", textDecoration: "underline" }}
                onClick={() => handleVerPdf(item)}
                title="Ver PDF"
              >
                <strong>{item.nombre_pdf}</strong>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Modal para mostrar el PDF */}
      {modalOpen && (
        <div style={{
          position: "fixed",
          top: 0,
          left: 0,
          width: "100vw",
          height: "100vh",
          background: "rgba(0,0,0,0.5)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 1000
        }}>
          <div style={{
            background: "#fff",
            borderRadius: "12px",
            padding: "24px",
            maxWidth: "90vw",
            maxHeight: "90vh",
            boxShadow: "0 8px 32px #1a237e33",
            display: "flex",
            flexDirection: "column",
            alignItems: "center"
          }}>
            <button
              onClick={cerrarModal}
              style={{
                alignSelf: "flex-end",
                background: "#d32f2f",
                color: "#fff",
                border: "none",
                borderRadius: "6px",
                padding: "6px 14px",
                marginBottom: "12px",
                fontWeight: 500,
                cursor: "pointer"
              }}
            >
              Cerrar
            </button>
            <iframe
              src={pdfUrl}
              title="Factura PDF"
              style={{ width: "70vw", height: "70vh", border: "none", borderRadius: "8px" }}
            />
          </div>
        </div>
      )}

      {/* Spinner CSS circular */}
      <style>{`
        .circle-loader {
          width: 42px;
          height: 42px;
          border: 5px solid #cfd8dc;
          border-top: 5px solid #42a5f5;
          border-radius: 50%;
          animation: girar 0.8s linear infinite;
        }
        @keyframes girar {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default ProcesadorFacturas;