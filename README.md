# InvoiceMind

**InvoiceMind** es una plataforma para procesar facturas electrónicas en PDF, extraer sus datos relevantes (incluyendo QR AFIP/ARCA), y generar reportes estructurados en Excel. Permite a los usuarios autenticados subir facturas, consultar un historial y visualizar los PDFs procesados.

---

## Tabla de Contenidos

1. [Arquitectura General](#arquitectura-general)
2. [Estructura del Proyecto](#estructura-del-proyecto)
3. [Backend (FastAPI)](#backend-fastapi)
   - Instalación y dependencias
   - Endpoints principales
   - Procesamiento de facturas
   - Seguridad y autenticación
4. [Frontend (React + Vite)](#frontend-react--vite)
   - Instalación y dependencias
   - Componentes principales
   - Flujo de usuario
5. [Base de datos y modelos](#base-de-datos-y-modelos)
6. [Historial y visualización de PDFs](#historial-y-visualización-de-pdfs)
7. [Configuración y variables de entorno](#configuración-y-variables-de-entorno)
8. [Notas y troubleshooting](#notas-y-troubleshooting)

---

## Arquitectura General

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, SQLite, PyMuPDF, OpenCV, pyzbar, LLM (Gemini API), manejo de mails y archivos Excel.
- **Frontend:** React (Vite), autenticación JWT, consumo de API REST, visualización de PDFs en modal.
- **Base de datos:** SQLite (historial de archivos procesados y usuarios).

---

## Estructura del Proyecto

```
InvoiceMind/
│
├── backend/
│   ├── app/
│   │   ├── core/           # Configuración de base de datos
│   │   ├── crud/           # Lógica de acceso a datos (historial)
│   │   ├── models/         # Modelos ORM (usuarios, historial)
│   │   ├── routes/         # Endpoints FastAPI (auth, historial, mail)
│   │   ├── utils/          # Utilidades: QR, PDF, LLM, watcher, etc.
│   │   └── __init__.py
│   ├── main.py             # Entrypoint FastAPI
│   ├── requirements.txt    # Dependencias backend
│   └── ...                 # Otros archivos (db, exports, etc.)
│
├── frontend/
│   ├── src/
│   │   ├── components/     # Componentes React (Login, Register, Procesador, etc.)
│   │   ├── App.jsx         # Rutas y navegación
│   │   └── ...             # Estilos, index, etc.
│   ├── package.json        # Dependencias frontend
│   └── ...                 # Configuración Vite, public, etc.
│
├── facturas/               # PDFs de ejemplo
├── README.md               # (Este archivo)
└── ...
```

---

## Backend (FastAPI)

### Instalación y dependencias

1. Ve a la carpeta `backend`:
   ```sh
   cd backend
   ```
2. Instala las dependencias:
   ```sh
   pip install -r requirements.txt
   ```
   - Asegúrate de tener Python 3.11+ y el paquete `pymupdf` (no `fitz`).
   - Si usas entorno virtual, actívalo antes.

### Principales dependencias

- `fastapi`, `uvicorn`, `sqlalchemy`, `python-multipart`, `python-dotenv`
- `pymupdf` (PyMuPDF), `opencv-python`, `pyzbar`, `numpy`
- `beautifulsoup4`, `google-generativeai`
- `python-jose`, `passlib[bcrypt]` (JWT y hash)
- `aiosqlite`, `openpyxl`

### Endpoints principales

- `POST /procesar-excel`: Sube PDFs, procesa y devuelve un Excel con los datos extraídos.
- `GET /historial`: Devuelve el historial de archivos procesados (protegido, requiere login).
- `GET /archivos/{nombre_pdf}`: Devuelve el PDF binario para visualizarlo.
- `POST /login` y `POST /register`: Autenticación de usuarios.
- Watcher de mails: Procesa facturas recibidas por correo automáticamente.

### Procesamiento de facturas

- Extrae texto y QR de PDFs usando PyMuPDF, OpenCV y pyzbar.
- Si el QR es válido (AFIP/ARCA), se parsea y se extraen los datos fiscales.
- Si no hay QR, se usa OCR y LLM (Gemini) para completar los campos.
- Los datos se almacenan en la base y se pueden descargar en Excel.

### Seguridad y autenticación

- Autenticación JWT (login/register).
- Endpoints protegidos requieren token válido.
- Contraseñas hasheadas con bcrypt.

---

## Frontend (React + Vite)

### Instalación y dependencias

1. Ve a la carpeta `frontend`:
   ```sh
   cd frontend
   ```
2. Instala dependencias:
   ```sh
   npm install
   ```
3. Inicia el servidor de desarrollo:
   ```sh
   npm run dev
   ```

### Componentes principales

- `Login.jsx` y `Register.jsx`: Formularios de autenticación.
- `ProcesadorFacturas.jsx`: Subida de PDFs, descarga de Excel, historial y visualización de PDFs en modal.
- `RequireAuth.jsx`: Protege rutas, verifica token JWT.
- `App.jsx`: Ruteo principal.

### Flujo de usuario

1. El usuario se registra o inicia sesión.
2. Puede subir uno o varios PDFs y procesarlos.
3. Descarga el Excel generado.
4. Consulta el historial y visualiza PDFs anteriores en un modal.

---

## Base de datos y modelos

- **Usuarios:** email, password (hasheada).
- **HistorialArchivo:** nombre_pdf, nombre_excel, fecha_procesado, estado, pdf_data (binario).
- Se usa SQLite por defecto (`historial.db`).

---

## Historial y visualización de PDFs

- El historial muestra los archivos procesados, fecha y estado.
- Al hacer clic en un PDF del historial, se abre un modal con el PDF embebido (iframe).
- El backend sirve el PDF binario bajo demanda.

---

## Configuración y variables de entorno

- Variables como `GEMINI_API_KEY` se definen en `.env` en `backend`.
- El frontend espera que el backend corra en `localhost:8000` (ajustable en fetch si es necesario).

---

## Notas y troubleshooting

- Si tienes errores con `fitz`, asegúrate de usar `pymupdf` y no el paquete obsoleto.
- Si falta alguna dependencia, instálala y agrégala a `requirements.txt`.
- Si el watcher de mails no funciona, revisa la configuración de correo y permisos.
- El frontend requiere que el backend esté corriendo y accesible.

---