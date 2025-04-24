import { useState } from "react";

function ProcesadorFacturas() {
  const [files, setFiles] = useState([]);
  const [jsonFinal, setJsonFinal] = useState(null);
  const [textoExtraido, setTextoExtraido] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [etapaGemini, setEtapaGemini] = useState(false);

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
        body: formData,
      });
      const data = await res.json();
      setJsonFinal(data.json);
      setTextoExtraido(data.texto); // guardamos el texto plano también
      setEtapaGemini(false);
    } catch (err) {
      console.error("Error en procesamiento local:", err);
    } finally {
      setCargando(false);
    }
  };

  const completarConGemini = async () => {
    setCargando(true);
    try {
      const res = await fetch("http://localhost:8000/completar-con-gemini", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          json_parcial: jsonFinal,
          texto_origen: textoExtraido
        })
      });
      const data = await res.json();
      setJsonFinal(data.json_completo);
      setEtapaGemini(true);
    } catch (err) {
      console.error("Error al enviar a Gemini:", err);
    } finally {
      setCargando(false);
    }
  };

  return (
    <div>
      <h2>Procesar Factura PDF</h2>
      <input type="file" multiple accept="application/pdf" onChange={handleFileChange} />
      <button onClick={procesarLocal} disabled={cargando} style={{ marginLeft: "10px" }}>
        {cargando ? "Procesando..." : "Procesar localmente"}
      </button>

      {jsonFinal && (
        <button onClick={completarConGemini} disabled={cargando} style={{
          marginLeft: "10px",
          background: "#00ffaa",
          color: "#000",
          border: "none",
          borderRadius: "4px",
          padding: "5px 10px",
          cursor: "pointer"
        }}>
          Enviar a Gemini para completar
        </button>
      )}

      {jsonFinal && (
        <div style={{
          marginTop: "20px",
          backgroundColor: "#1e1e1e",
          color: "#ffffff",
          padding: "20px",
          borderRadius: "8px",
          fontFamily: "monospace",
          fontSize: "14px",
          overflowX: "auto",
          maxHeight: "600px"
        }}>
          <h3 style={{ color: etapaGemini ? "#66ff66" : "#00ffaa" }}>
            JSON {etapaGemini ? "completado con Gemini" : "procesado localmente"}:
          </h3>
          <pre>{JSON.stringify(jsonFinal, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default ProcesadorFacturas;
