import { useState, useEffect } from "react";

function ProcesadorFacturas() {
  const [files, setFiles] = useState([]);
  const [excelBlob, setExcelBlob] = useState(null);
  const [estadoProceso, setEstadoProceso] = useState("idle");
  const [historial, setHistorial] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [pdfUrl, setPdfUrl] = useState(null);
  const [leftPanelHeight, setLeftPanelHeight] = useState(null);
  const [userInfo, setUserInfo] = useState(null);

  // Cargar información del usuario
  useEffect(() => {
    const userData = localStorage.getItem("user");
    if (userData) {
      setUserInfo(JSON.parse(userData));
    } else {
      // Si no hay datos del usuario, obtenerlos del servidor
      fetchUserInfo();
    }
  }, []);

  const fetchUserInfo = async () => {
    try {
      const res = await fetch("http://localhost:8000/me", {
        headers: {
          Authorization: "Bearer " + localStorage.getItem("token")
        }
      });
      if (res.ok) {
        const data = await res.json();
        setUserInfo(data);
        localStorage.setItem("user", JSON.stringify(data));
      }
    } catch (err) {
      console.error("Error fetching user info:", err);
    }
  };

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
        localStorage.removeItem("user");
        window.location.href = "/login";
        return;
      }

      if (res.status === 403) {
        const errorData = await res.json();
        alert(errorData.detail);
        setEstadoProceso("idle");
        return;
      }

      if (!res.ok) throw new Error("Error al procesar facturas");
      const blob = await res.blob();

      if (blob && blob.size > 0) {
        setExcelBlob(blob);
        setEstadoProceso("completado");
        
        // Actualizar información del usuario después del procesamiento
        await fetchUserInfo();
      } else {
        setEstadoProceso("idle");
      }
    } catch (err) {
      alert("Error al procesar facturas: " + err.message);
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

  const handleVerPdf = async (item) => {
    try {
      const response = await fetch(`http://localhost:8000/archivos/${encodeURIComponent(item.nombre_pdf)}`, {
        headers: {
          Authorization: "Bearer " + localStorage.getItem("token")
        }
      });
      
      if (response.status === 401) {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        window.location.href = "/login";
        return;
      }
      
      if (!response.ok) {
        alert("Error al cargar el PDF");
        return;
      }
      
      const blob = await response.blob();
      const pdfUrl = window.URL.createObjectURL(blob);
      setPdfUrl(pdfUrl);
      setModalOpen(true);
    } catch (error) {
      console.error("Error al cargar PDF:", error);
      alert("Error al cargar el PDF");
    }
  };

  const cerrarModal = () => {
    setModalOpen(false);
    if (pdfUrl) {
      // Liberar la URL del blob para evitar memory leaks
      window.URL.revokeObjectURL(pdfUrl);
      setPdfUrl(null);
    }
  };

  useEffect(() => {
    cargarHistorial();
  }, []);

  useEffect(() => {
    const updateHeight = () => {
      const leftPanel = document.getElementById('left-panel');
      if (leftPanel) {
        setLeftPanelHeight(leftPanel.offsetHeight);
      }
    };

    updateHeight();
    window.addEventListener('resize', updateHeight);
    
    // Observar cambios en el contenido del panel izquierdo
    const observer = new MutationObserver(updateHeight);
    const leftPanel = document.getElementById('left-panel');
    if (leftPanel) {
      observer.observe(leftPanel, { childList: true, subtree: true });
    }

    return () => {
      window.removeEventListener('resize', updateHeight);
      observer.disconnect();
    };
  }, [files, estadoProceso, excelBlob]);

  return (
    <div>
      {/* Navigation Bar */}
      <div className="nav-container">
        <div className="nav-brand">InvoiceMind</div>
        <div className="nav-menu">
          {userInfo && (
            <div style={{ 
              display: "flex", 
              alignItems: "center", 
              gap: "1rem",
              marginRight: "1rem"
            }}>
              <div style={{
                background: "rgba(0, 122, 255, 0.1)",
                padding: "0.5rem 1rem",
                borderRadius: "20px",
                border: "1px solid rgba(0, 122, 255, 0.3)"
              }}>
                <span style={{ fontSize: "0.9rem", fontWeight: "600", color: "#007aff" }}>
                  Plan {userInfo.plan.charAt(0).toUpperCase() + userInfo.plan.slice(1)}
                </span>
                <span style={{ margin: "0 0.5rem", color: "#86868b" }}>•</span>
                <span style={{ fontSize: "0.9rem", fontWeight: "500", color: "#1d1d1f" }}>
                  {userInfo.procesamientos_restantes} procesamientos restantes
                </span>
              </div>
            </div>
          )}
          <a href="/historial-excel" style={{ marginRight: "1rem", textDecoration: "none" }}>
            <button className="btn-secondary">Excel</button>
          </a>
          <button 
            onClick={() => {
              localStorage.removeItem("token");
              localStorage.removeItem("user");
              window.location.href = "/login";
            }}
            className="btn-secondary"
          >
            Cerrar Sesión
          </button>
        </div>
      </div>

      <div className="container">
        <div className="centered">
          <div style={{ 
            display: "flex", 
            gap: "2rem", 
            flexWrap: "wrap", 
            justifyContent: "center", 
            alignItems: "flex-start", 
            width: "100%", 
            maxWidth: "1400px"
          }}>
            {/* Panel principal de procesamiento */}
            <div 
              id="left-panel"
              className="card" 
              style={{ 
                flex: "1", 
                minWidth: "400px", 
                maxWidth: "600px",
                display: "flex",
                flexDirection: "column"
              }}
            >
              <h2>Procesar Facturas</h2>
              <p style={{ fontSize: "1.2rem", fontWeight: "500", marginBottom: "0.5rem", color: "#1d1d1f" }}>
                Digitaliza y estructura tus documentos
              </p>
              <p style={{ marginBottom: "2rem", color: "#86868b" }}>
                Sube múltiples facturas PDF y obtén un archivo Excel con toda la información organizada.
              </p>

              <label className="btn-main" style={{ display: "block", textAlign: "center", textDecoration: "none" }}>
                Seleccionar Archivos PDF
                <input type="file" multiple accept="application/pdf" onChange={handleFileChange} style={{ display: "none" }} />
              </label>

              {files.length > 0 && (
                <div className="upload-area" style={{ marginTop: "1.5rem" }}>
                  <p style={{ fontSize: "1.1rem", fontWeight: "600", marginBottom: "1rem", color: "#1d1d1f" }}>Archivos seleccionados:</p>
                  <ul style={{ listStyle: "none", padding: "0", textAlign: "left" }}>
                    {files.map((f, i) => (
                      <li key={i} style={{ 
                        padding: "0.5rem 0", 
                        fontSize: "1rem", 
                        fontWeight: "400",
                        borderBottom: "1px solid rgba(0, 0, 0, 0.1)",
                        color: "#1d1d1f"
                      }}>
                        • {f.name}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Botones de acción */}
              <div className="button-group" style={{ 
                display: "flex", 
                flexDirection: "column", 
                gap: "0", 
                alignItems: "stretch", 
                marginTop: "1rem",
                width: "100%"
              }}>
                {estadoProceso === "idle" && (
                  <button
                    onClick={procesarFacturas}
                    disabled={files.length === 0}
                    className="btn-main"
                    style={{ 
                      width: "100%", 
                      opacity: files.length === 0 ? 0.5 : 1,
                      cursor: files.length === 0 ? "not-allowed" : "pointer"
                    }}
                  >
                    Procesar Archivos
                  </button>
                )}

                {estadoProceso === "procesando" && (
                  <div style={{ textAlign: "center", padding: "2rem" }}>
                    <div className="circle-loader"></div>
                    <p style={{ marginTop: "1rem", fontSize: "1.2rem", fontWeight: "600" }}>
                      Procesando facturas...
                    </p>
                  </div>
                )}

                {estadoProceso === "completado" && excelBlob && (
                  <button onClick={descargarExcel} className="btn-main" style={{ width: "100%" }}>
                    Descargar Excel
                  </button>
                )}
              </div>
            </div>

            {/* Panel de historial - mismo tamaño exacto */}
            <div className="card" style={{ 
              flex: "1", 
              minWidth: "400px", 
              maxWidth: "600px",
              height: leftPanelHeight ? `${leftPanelHeight}px` : 'auto',
              display: "flex",
              flexDirection: "column"
            }}>
              <h3>Historial de Archivos</h3>
              <p style={{ marginBottom: "1.5rem", color: "#86868b" }}>
                Archivos procesados anteriormente
              </p>
              <div className="results-container" style={{ 
                flex: "1",
                overflowY: "auto"
              }}>
                {historial.length === 0 ? (
                  <div style={{ 
                    display: "flex", 
                    alignItems: "center", 
                    justifyContent: "center", 
                    height: "100%",
                    minHeight: "200px"
                  }}>
                    <p style={{ textAlign: "center", fontStyle: "italic", opacity: "0.8" }}>
                      No hay archivos en el historial.
                    </p>
                  </div>
                ) : (
                  <ul style={{ listStyle: "none", padding: "0" }}>
                    {historial.map((item, idx) => (
                      <li
                        key={idx}
                        onClick={() => handleVerPdf(item)}
                        style={{
                          padding: "1rem",
                          marginBottom: "0.5rem",
                          backgroundColor: "rgba(255, 255, 255, 0.6)",
                          borderRadius: "12px",
                          cursor: "pointer",
                          transition: "all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)",
                          border: "1px solid rgba(0, 0, 0, 0.05)"
                        }}
                        onMouseEnter={(e) => {
                          e.target.style.backgroundColor = "rgba(0, 122, 255, 0.1)";
                          e.target.style.transform = "translateY(-2px)";
                        }}
                        onMouseLeave={(e) => {
                          e.target.style.backgroundColor = "rgba(255, 255, 255, 0.6)";
                          e.target.style.transform = "translateY(0)";
                        }}
                        title="Clic para ver PDF"
                      >
                        <strong style={{ fontSize: "1rem", color: "#1d1d1f" }}>{item.nombre_pdf}</strong>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>
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
          background: "rgba(0, 0, 0, 0.4)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 1000,
          backdropFilter: "blur(10px)"
        }}>
          <div className="card" style={{
            maxWidth: "90vw",
            maxHeight: "90vh",
            padding: "2rem",
            display: "flex",
            flexDirection: "column",
            alignItems: "center"
          }}>
            <button
              onClick={cerrarModal}
              className="btn-secondary"
              style={{
                alignSelf: "flex-end",
                marginBottom: "1rem",
                padding: "0.5rem 1rem"
              }}              >
                Cerrar
              </button>
            <iframe
              src={pdfUrl}
              title="Factura PDF"
              style={{ 
                width: "70vw", 
                height: "70vh", 
                border: "none", 
                borderRadius: "12px",
                backgroundColor: "white"
              }}
            />
          </div>
        </div>
      )}

      {/* Spinner CSS circular */}
      <style>{`
        .circle-loader {
          width: 50px;
          height: 50px;
          border: 3px solid rgba(0, 122, 255, 0.2);
          border-top: 3px solid #007aff;
          border-radius: 50%;
          animation: girar 1s linear infinite;
          margin: 0 auto;
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