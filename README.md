[README.md](https://github.com/user-attachments/files/26332689/README.md)
# ADS Parser — Full Stack

Chinese Word itinerary → ADS JSON pipeline.
**Stack**: Next.js 14 (frontend) + FastAPI (backend) + Anthropic Claude API.

---

## Repository structure

```
ads-parser/
├── render.yaml                  ← Render IaC (both services)
├── .gitignore
├── backend/
│   ├── main.py                  ← FastAPI app + CORS
│   ├── requirements.txt
│   ├── routers/
│   │   ├── parse.py             ← POST /api/parse
│   │   ├── suppliers.py         ← GET/POST/PATCH /api/suppliers
│   │   └── health.py            ← GET /api/health
│   ├── services/
│   │   ├── parser_service.py    ← docx extraction + LLM call
│   │   └── supplier_service.py  ← in-memory DB + fuzzy lookup
│   └── models/
│       └── schemas.py           ← Pydantic models
└── frontend/
    ├── package.json
    ├── next.config.js
    ├── tailwind.config.js
    ├── tsconfig.json
    └── src/
        ├── app/
        │   ├── layout.tsx
        │   ├── page.tsx          ← Main page (upload → parse → results)
        │   └── globals.css
        ├── components/
        │   ├── UploadZone.tsx    ← Drag & drop + API key input
        │   ├── ParseResults.tsx  ← Tabbed results (Overview/Itinerary/Flights/Suppliers)
        │   ├── SupplierRow.tsx   ← Inline edit with missing highlight
        │   └── WarningBanner.tsx ← Collapsible warnings
        ├── lib/
        │   └── api.ts            ← Typed fetch wrappers
        └── types/
            └── ads.ts            ← Full TypeScript domain types
```

---

## Local development

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
uvicorn main:app --reload --port 8000
# API docs: http://localhost:8000/docs
```

### Frontend
```bash
cd frontend
npm install
# Create .env.local:
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
# UI: http://localhost:3000
```

---

## Deploy to Render via GitHub

Follow these steps exactly — takes about 10 minutes.

### Step 1 — Push to GitHub

```bash
cd ads-parser
git init
git add .
git commit -m "initial commit"
# Create a new repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/ads-parser.git
git branch -M main
git push -u origin main
```

### Step 2 — Create Render account
Go to https://render.com and sign up (free tier works).

### Step 3 — Deploy the backend first

1. Dashboard → **New +** → **Web Service**
2. Connect your GitHub account and select the `ads-parser` repo
3. Fill in:
   | Field | Value |
   |---|---|
   | Name | `ads-parser-api` |
   | Root Directory | `backend` |
   | Runtime | `Python 3` |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
4. Under **Environment Variables**, click **Add** and set:
   - Key: `ANTHROPIC_API_KEY`  Value: your `sk-ant-...` key
5. Click **Create Web Service**
6. Wait ~2 min. Copy the deployed URL, e.g. `https://ads-parser-api.onrender.com`

### Step 4 — Deploy the frontend

1. Dashboard → **New +** → **Web Service**
2. Same repo, then fill in:
   | Field | Value |
   |---|---|
   | Name | `ads-parser-frontend` |
   | Root Directory | `frontend` |
   | Runtime | `Node` |
   | Build Command | `npm install && npm run build` |
   | Start Command | `npm start` |
3. Under **Environment Variables**, add:
   - Key: `NEXT_PUBLIC_API_URL`  Value: `https://ads-parser-api.onrender.com` (your backend URL)
4. Click **Create Web Service**
5. Wait ~3 min. Render gives you a URL like `https://ads-parser-frontend.onrender.com`

### Step 5 — Fix CORS (production)

In `backend/main.py`, replace `allow_origins=["*"]` with your actual frontend URL:

```python
allow_origins=["https://ads-parser-frontend.onrender.com"],
```

Commit and push — Render auto-redeploys.

### Step 6 — Verify

```bash
curl https://ads-parser-api.onrender.com/api/health
# Expected: {"status":"ok","supplier_count":7}
```

Open your frontend URL, upload a `.docx` file, enter your API key, and parse.

---

## Alternative: use render.yaml (Blueprint deploy)

If you prefer one-click deploy:

1. Make sure `render.yaml` is in the repo root (it is).
2. Render Dashboard → **New +** → **Blueprint**
3. Connect repo → Render reads `render.yaml` and creates both services automatically.
4. You will be prompted to enter `ANTHROPIC_API_KEY` as a secret during setup.
5. After deploy, update `NEXT_PUBLIC_API_URL` in the frontend service env vars with the actual backend URL.

---

## Upgrading the supplier database to PostgreSQL

Currently the supplier DB is an in-memory dict. To persist across restarts:

1. Add a Render **PostgreSQL** instance (free tier available)
2. `pip install sqlalchemy asyncpg`
3. Replace `SUPPLIER_DB` dict in `services/supplier_service.py` with SQLAlchemy queries
4. Set `DATABASE_URL` env var in Render to the connection string Render provides

---

## Environment variables reference

| Variable | Service | Required | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Backend | Yes | Claude API key |
| `NEXT_PUBLIC_API_URL` | Frontend | Yes | Backend base URL |
| `PORT` | Backend | Auto | Set by Render |
| `NODE_VERSION` | Frontend | Recommended | Pin to `20.11.0` |
| `PYTHON_VERSION` | Backend | Recommended | Pin to `3.11.0` |
