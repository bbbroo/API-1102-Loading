# API 1102 Loading Calculator — Run Instructions

Quick steps to run the backend (FastAPI) and frontend (Vite + React).

## Backend (FastAPI)

1. Create and activate a Python virtual environment (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run the backend (development):

```powershell
python -m uvicorn app.backend.main:app --reload --host 127.0.0.1 --port 8000
```

3. Health check:

Open http://127.0.0.1:8000/api/health

Notes: the backend mounts `app/backend/static` at `/static` and allows CORS from the Vite dev server (port 5173).

## Frontend (Vite + React)

1. From a separate terminal, install and run:

```powershell
cd frontend
npm install
npm run dev
```

2. Dev site will be available at http://127.0.0.1:5173 (package.json uses `--host 127.0.0.1`).

## Optional: Build frontend and serve from backend static

1. Build the frontend and copy the `dist` output into the backend static folder:

```powershell
cd frontend
npm run build
# remove existing static files (optional)
Remove-Item -Recurse -Force ..\app\backend\static\*
Copy-Item -Path .\dist\* -Destination ..\app\backend\static -Recurse
```

2. Then run the backend and navigate to http://127.0.0.1:8000/static/index.html

## Troubleshooting
- If you see CORS errors while using the dev frontend, ensure the frontend is served from `127.0.0.1:5173` or `localhost:5173`.
- On Windows, run PowerShell as Administrator only if you get permission errors creating the venv.

---
