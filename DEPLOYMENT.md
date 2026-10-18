# Deployment & Operations Guide — Omega FundGuard

This guide outlines deployment options for Omega FundGuard across local, containerized, and cloud hosting environments (Fly.io, Railway, Render, Docker Compose, and Vercel).

---

## 1. Environment Configuration

Copy `.env.example` to `.env` in the project root:

```bash
cp .env.example .env
```

Key environment variables:
```ini
DATABASE_URL=sqlite:///./fundguard.db
# For PostgreSQL: postgresql+psycopg://user:password@localhost:5432/fundguard
STELLAR_HORIZON_URL=https://horizon-testnet.stellar.org
ENABLE_TESTNET=true
ENABLE_MAINNET=false
LOG_LEVEL=INFO
```

---

## 2. Option A: Local Development & Verification

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Docs: <http://127.0.0.1:8000/docs>

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Dashboard: <http://127.0.0.1:5173>

---

## 3. Option B: Docker Compose (Full Stack)

Run both the FastAPI backend and React frontend with one command:

```bash
docker compose up --build -d
```

- Frontend: <http://localhost:5173>
- Backend API & OpenAPI: <http://localhost:8000/docs>

To shut down and wipe ephemeral database volumes:
```bash
docker compose down -v
```

---

## 4. Option C: Fly.io Deployment

Fly.io configuration is defined in [`fly.toml`](file:///home/skywalker/Projects/prj/Metta/Fundguard/omega-fundguard/fly.toml).

```bash
# Launch app
fly launch

# Deploy updates
fly deploy
```

---

## 5. Option D: Railway Deployment

Railway configuration is defined in [`railway.json`](file:///home/skywalker/Projects/prj/Metta/Fundguard/omega-fundguard/railway.json):

```bash
railway up
```

Railway automatically detects the root `Procfile` or `Dockerfile.backend`.

---

## 6. Option E: Render Deployment

Render blueprint is provided in [`render.yaml`](file:///home/skywalker/Projects/prj/Metta/Fundguard/omega-fundguard/render.yaml):

1. Connect the GitHub repository to your Render account.
2. Select **New > Blueprint**.
3. Point to `render.yaml`.
4. Deploy the managed web service.

---

## 7. Option F: Vercel (Frontend Static Hosting)

Vercel configuration is defined in [`vercel.json`](file:///home/skywalker/Projects/prj/Metta/Fundguard/omega-fundguard/vercel.json):

```bash
cd frontend
vercel deploy
```
Set the environment variable `VITE_API_URL` to point to your live backend domain.

---

## 8. Option G: Linux Bare-Metal Systemd Service

Create `/etc/systemd/system/fundguard-backend.service`:

```ini
[Unit]
Description=Omega FundGuard FastAPI Backend
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/omega-fundguard/backend
ExecStart=/var/www/omega-fundguard/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
EnvironmentFile=/var/www/omega-fundguard/.env

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now fundguard-backend
```

---

## 9. Security & Release Invariants
- **Mainnet Disabled**: `ENABLE_MAINNET=false` is enforced. Any attempt to submit to a live public network is blocked.
- **Approval Hash Binding**: Payouts cannot execute without explicit human approval matching the exact canonical proposal hash.
- **Base-Unit Integrity**: Stroops ($10^{-7}\text{ XLM}$) are used exclusively for financial arithmetic.
