import { useState } from "react";

function UploadPDF() {
  const [files, setFiles] = useState([]);
  const [resultado, setResultado] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [seccion, setSeccion] = useState("completo");

  const handleFileChange = (e) => {
    setFiles(e.target.files);
  };

  const handleUpload = async () => {
    setCargando(true);
    const formData = new FormData();
    Array.from(files).forEach(file => formData.append("pdfs", file));

    try {
      const response = await fetch("http://localhost:8000/parse-and-send", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();

      // Intenta parsear JSON
      try {
        const json = JSON.parse(data.resultado);
        setResultado(json);
      } catch (err) {
        setResultado(data.resultado); // Si no es JSON válido
      }
    } catch (error) {
      console.error("Error al subir PDF:", error);
    } finally {
      setCargando(false);
    }
  };

  const copiarAlPortapapeles = () => {
    navigator.clipboard.writeText(JSON.stringify(resultado, null, 2));
    alert("JSON copiado al portapapeles");
  };

  const renderSeccion = (factura) => {
    switch (seccion) {
      case "general":
        return {
          razon_social: factura.razon_social,
          cuit: factura.cuit,
          fecha: factura.fecha,
          condicion_iva: factura.condicion_iva,
          domicilio: factura.domicilio,
        };
      case "iva":
        return factura.iva;
      case "detalle":
        return factura.detalle;
      case "totales":
        return {
          importe_neto_gravado: factura.importe_neto_gravado,
          importe_otros_tributos: factura.importe_otros_tributos,
          importe_total: factura.importe_total,
        };
      case "completo":
      default:
        return factura;
    }
  };

  return (
    <div>
      <h2>Subir facturas en PDF</h2>
      <input type="file" multiple accept="application/pdf" onChange={handleFileChange} />
      <button onClick={handleUpload} disabled={cargando} style={{ marginLeft: "10px" }}>
        {cargando ? "Procesando..." : "Enviar a Gemini"}
      </button>

      {resultado && Array.isArray(resultado) && (
        <>
          <div style={{ marginTop: "20px" }}>
            <label htmlFor="seccion">Mostrar sección: </label>
            <select
              id="seccion"
              value={seccion}
              onChange={(e) => setSeccion(e.target.value)}
              style={{ marginLeft: "10px", padding: "4px" }}
            >
              <option value="completo">JSON completo</option>
              <option value="general">Datos generales</option>
              <option value="iva">IVA</option>
              <option value="detalle">Detalle</option>
              <option value="totales">Totales</option>
            </select>
            <button onClick={copiarAlPortapapeles} style={{
              marginLeft: "10px",
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

          {resultado.map((factura, index) => (
            <div key={index} style={{
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
              <h3 style={{ color: "#00ffaa" }}>Factura #{index + 1}</h3>
              <pre>{JSON.stringify(renderSeccion(factura), null, 2)}</pre>
            </div>
          ))}
        </>
      )}

      {resultado && !Array.isArray(resultado) && (
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
          <h3 style={{ color: "#00ffaa" }}>Resultado (Texto crudo):</h3>
          <pre>{resultado}</pre>
        </div>
      )}
    </div>
  );
}

export default UploadPDF;
