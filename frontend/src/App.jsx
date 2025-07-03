import { BrowserRouter, Routes, Route } from "react-router-dom";
import ProcesadorFacturas from "./components/ProcesadorFacturas";
import Login from "./components/Login";
import Register from "./components/Register";
import RequireAuth from "./components/RequireAuth";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/"
          element={
            <RequireAuth>
              <ProcesadorFacturas />
            </RequireAuth>
          }
        />
        <Route
          path="/procesar-facturas"
          element={
            <RequireAuth>
              <ProcesadorFacturas />
            </RequireAuth>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;