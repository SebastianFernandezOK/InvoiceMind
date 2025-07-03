import { useState, useEffect } from "react";

function HistorialExcel() {
  const [historialExcel, setHistorialExcel] = useState([]);
  const [loading, setLoading] = useState(true);
  const [userInfo, setUserInfo] = useState(null);

  // Cargar información del usuario
  useEffect(() => {
    const userData = localStorage.getItem("user");
    if (userData) {
      setUserInfo(JSON.parse(userData));
    }
  }, []);

  const cargarHistorialExcel = async () => {
    try {
      setLoading(true);
      const res = await fetch("http://localhost:8000/excel/", {
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
      
      if (res.ok) {
        const data = await res.json();
        setHistorialExcel(data);
      }
    } catch (err) {
      console.error("Error cargando historial Excel:", err);
    } finally {
      setLoading(false);
    }
  };

  const descargarExcel = async (item) => {
    try {
      const res = await fetch(`http://localhost:8000/excel/descargar/${item.id}`, {
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
      
      if (!res.ok) {
        alert("Error al descargar el archivo Excel");
        return;
      }
      
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = item.nombre_archivo;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Error al descargar Excel:", error);
      alert("Error al descargar el archivo");
    }
  };

  const formatearFecha = (fechaString) => {
    const fecha = new Date(fechaString);
    return fecha.toLocaleDateString("es-ES", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  useEffect(() => {
    cargarHistorialExcel();
  }, []);

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
          <a href="/procesar-facturas" style={{ marginRight: "1rem", textDecoration: "none" }}>
            <button className="btn-secondary">Procesar Facturas</button>
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
            justifyContent: "center", 
            width: "100%", 
            maxWidth: "1200px"
          }}>
            <div className="card" style={{ 
              width: "100%",
              maxWidth: "800px",
              display: "flex",
              flexDirection: "column"
            }}>
              <h2 style={{ textAlign: "center", marginBottom: "1rem" }}>Historial de Archivos Excel</h2>
              <p style={{ 
                textAlign: "center", 
                marginBottom: "2rem", 
                color: "#86868b" 
              }}>
                Descarga todos los archivos Excel que has generado
              </p>
              
              {loading ? (
                <div style={{ 
                  display: "flex", 
                  justifyContent: "center", 
                  alignItems: "center", 
                  padding: "3rem" 
                }}>
                  <div className="circle-loader"></div>
                </div>
              ) : historialExcel.length === 0 ? (
                <div style={{ 
                  display: "flex", 
                  alignItems: "center", 
                  justifyContent: "center", 
                  padding: "3rem",
                  textAlign: "center"
                }}>
                  <div>
                    <p style={{ fontSize: "1.2rem", color: "#86868b", marginBottom: "1rem" }}>
                      No tienes archivos Excel generados aún
                    </p>
                    <a href="/procesar-facturas">
                      <button className="btn-main">Procesar Primera Factura</button>
                    </a>
                  </div>
                </div>
              ) : (
                <div style={{ overflowY: "auto", maxHeight: "600px" }}>
                  <div style={{ display: "grid", gap: "1rem" }}>
                    {historialExcel.map((item, idx) => (
                      <div
                        key={idx}
                        style={{
                          padding: "1.5rem",
                          backgroundColor: "rgba(255, 255, 255, 0.6)",
                          borderRadius: "12px",
                          border: "1px solid rgba(0, 0, 0, 0.05)",
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          transition: "all 0.3s ease"
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = "rgba(0, 122, 255, 0.1)";
                          e.currentTarget.style.transform = "translateY(-2px)";
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.6)";
                          e.currentTarget.style.transform = "translateY(0)";
                        }}
                      >
                        <div>
                          <h4 style={{ 
                            margin: "0 0 0.5rem 0", 
                            fontSize: "1.1rem", 
                            fontWeight: "600",
                            color: "#1d1d1f"
                          }}>
                            {item.nombre_archivo}
                          </h4>
                          <p style={{ 
                            margin: "0", 
                            fontSize: "0.9rem", 
                            color: "#86868b" 
                          }}>
                            {formatearFecha(item.fecha_generado)} • {item.cantidad_facturas} facturas procesadas
                          </p>
                        </div>
                        <button
                          onClick={() => descargarExcel(item)}
                          className="btn-main"
                          style={{ padding: "0.5rem 1rem", fontSize: "0.9rem" }}
                        >
                          Descargar
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default HistorialExcel;
