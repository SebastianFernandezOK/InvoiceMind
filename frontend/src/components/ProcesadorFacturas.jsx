import { useState } from "react";

function ProcesadorFacturas() {
  const [files, setFiles] = useState([]);
  const [facturas, setFacturas] = useState([]);
  const [textos, setTextos] = useState([]);
  const [csvContent, setCsvContent] = useState("");
  const [cargando, setCargando] = useState(false);

  const handleFileChange = (e) => {
    setFiles(e.target.files);
  };

  const procesarLocal = async () => {
    setCargando(true);
    const formData = new FormData();
    Array.from(files).forEach(file => formData.append("pdfs", file));

    try {
      const res = await fetch("http://localhost:8000/procesar-todo-local", {
        method: "POST",
        body: formData
      });

      if (!res.ok) throw new Error("Error en procesamiento local");

      const data = await res.json();

      if (data.facturas) {
        setFacturas(data.facturas);
        setTextos(data.textos || []);
      } else if (data.json) {
        setFacturas([data.json]);
        setTextos([data.texto || ""]);
      }

    } catch (err) {
      console.error("Error:", err);
    } finally {
      setCargando(false);
    }
  };

  const procesarYExportar = async () => {
    setCargando(true);
    const formData = new FormData();
    Array.from(files).forEach(file => formData.append("pdfs", file));

    try {
      const res = await fetch("http://localhost:8000/procesar-y-exportar-csv", {
        method: "POST",
        body: formData
      });

      if (!res.ok) throw new Error("Error al procesar y exportar");

      const data = await res.json();

      if (data.facturas) {
        setFacturas(data.facturas);
      }

      if (data.csv_text) {
        setCsvContent(data.csv_text);
      }

    } catch (err) {
      console.error("Error:", err);
    } finally {
      setCargando(false);
    }
  };

  const completarConGemini = async (factura, index) => {
    setCargando(true);
    try {
      const texto = textos[index] || JSON.stringify(factura);
      const res = await fetch("http://localhost:8000/completar-json-con-gemini", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ json: factura, texto })
      });
      const data = await res.json();
      if (data.json) {
        const nuevas = [...facturas];
        nuevas[index] = { ...data.json, _completada_por_gemini: true };
        setFacturas(nuevas);
      }
    } catch (err) {
      console.error("Error al completar con Gemini:", err);
    } finally {
      setCargando(false);
    }
  };

  const enviarTodasAGemini = async () => {
    setCargando(true);
    try {
      const nuevasFacturas = await Promise.all(
        facturas.map(async (factura, index) => {
          const bodyFactura = factura.factura || factura;
          const texto = textos[index] || JSON.stringify(bodyFactura);
          const res = await fetch("http://localhost:8000/completar-json-con-gemini", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ json: bodyFactura, texto })
          });
          const data = await res.json();
          return data.json ? { ...data.json, _completada_por_gemini: true } : factura;
        })
      );
      setFacturas(nuevasFacturas);
    } catch (err) {
      console.error("Error al completar todas con Gemini:", err);
    } finally {
      setCargando(false);
    }
  };

  const descargarCSV = () => {
    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "facturas.csv";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const descargarJSONIndividual = (factura, index) => {
    const blob = new Blob([JSON.stringify(factura, null, 2)], {
      type: "application/json"
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `factura_${index + 1}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div>
      <h2>Procesador de Facturas</h2>

      <input type="file" multiple accept="application/pdf" onChange={handleFileChange} />

      <button onClick={procesarLocal} disabled={cargando} style={{ marginLeft: "10px" }}>
        {cargando ? "Procesando..." : "Procesar localmente"}
      </button>

      <button
        onClick={enviarTodasAGemini}
        disabled={cargando || facturas.length === 0}
        style={{
          marginLeft: "10px",
          background: "#00ffaa",
          color: "#000",
          border: "none",
          borderRadius: "4px",
          padding: "6px 12px",
          cursor: "pointer"
        }}
      >
        Enviar a Gemini para completar
      </button>

      <button onClick={procesarYExportar} disabled={cargando} style={{
        marginLeft: "10px",
        background: "#ffaa00",
        border: "none",
        borderRadius: "4px",
        padding: "6px 12px",
        color: "#000",
        cursor: "pointer"
      }}>
        {cargando ? "Procesando..." : "Exportar todas a CSV"}
      </button>

      {csvContent && (
        <button onClick={descargarCSV} style={{
          marginLeft: "10px",
          background: "#0077ff",
          color: "#fff",
          border: "none",
          borderRadius: "4px",
          padding: "6px 12px",
          cursor: "pointer"
        }}>
          Descargar CSV
        </button>
      )}

      {facturas.length > 0 && (
        <div style={{ marginTop: "20px" }}>
          <h3>Facturas procesadas:</h3>
          {facturas.map((facturaObj, index) => (
            <div key={index} style={{
              backgroundColor: "#1e1e1e",
              color: "#ffffff",
              padding: "15px",
              marginBottom: "15px",
              borderRadius: "8px",
              fontFamily: "monospace",
              fontSize: "14px",
              overflowX: "auto"
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <h4 style={{ color: "#00ffaa", margin: 0 }}>
                  Factura #{index + 1}
                  {facturaObj._completada_por_gemini && (
                    <span style={{ marginLeft: "10px", color: "#00ff99", fontWeight: "normal" }}>
                      ✅ Completada con Gemini
                    </span>
                  )}
                </h4>
                <div>
                  <button onClick={() => completarConGemini(facturaObj.factura || facturaObj, index)} style={{
                    background: "#00ffaa",
                    marginRight: "6px",
                    color: "#000",
                    border: "none",
                    padding: "4px 8px",
                    borderRadius: "4px",
                    fontSize: "12px",
                    cursor: "pointer"
                  }}>
                    Completar con Gemini
                  </button>
                  <button onClick={() => descargarJSONIndividual(facturaObj, index)} style={{
                    background: "#00ccff",
                    color: "#000",
                    border: "none",
                    padding: "4px 8px",
                    borderRadius: "4px",
                    fontSize: "12px",
                    cursor: "pointer"
                  }}>
                    Descargar JSON
                  </button>
                </div>
              </div>
              <pre>{JSON.stringify(facturaObj, null, 2)}</pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ProcesadorFacturas;
