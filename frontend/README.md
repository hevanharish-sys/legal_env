# LegalEnv Frontend

This is a small React/Tailwind frontend for the `legal_env` FastAPI backend.

## Prerequisites

- Node.js 18+ (recommended)
- Backend running (`legal_env/api.py`)

## Run backend (API)

From `d:\scaler\legal_env`:

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn api:app --host 127.0.0.1 --port 8000
```

## Run frontend

From `d:\scaler\legal_env\frontend`:

```powershell
npm install
npm run dev
```

Open the dev URL printed by Vite (usually `http://localhost:5173`).

## Configure API base URL

By default the frontend calls `http://127.0.0.1:8000`.

To change it, set:

- `VITE_API_BASE_URL`

Example (PowerShell):

```powershell
$env:VITE_API_BASE_URL="http://127.0.0.1:8000"
npm run dev
```

