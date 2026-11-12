# InterviewIQ

InterviewIQ is an AI-powered interview preparation platform. Phase 1 establishes
the FastAPI backend and React/Vite dashboard shell.

## Phase 1

### Backend

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

The health endpoint is available at `http://localhost:8000/health`.
Swagger documentation is available at `http://localhost:8000/docs`.

### Frontend

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

The dashboard is available at `http://localhost:5173`.
During development, Vite proxies `/health` and `/api` requests to the backend.

## Phase 2: PostgreSQL and resumes

Start Docker Desktop, then start the PostgreSQL service from the project root.
The Compose file uses the `POSTGRES_PASSWORD` value in the root `.env` file,
stores data in the named `interviewiq-postgres-data` volume, and publishes
PostgreSQL on `localhost:5432`:

```powershell
cd C:\AI-Projects\InterviewIQ
docker compose up -d
docker compose ps
docker inspect --format '{{.State.Health.Status}}' interviewiq-postgres
```

The local `backend/.env` uses the same password and connects to the
`interviewiq` database. The application does not create tables automatically;
apply the Alembic migration:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

Resume endpoints:

- `POST /api/v1/resumes/upload` — multipart field `file`; accepts PDF and DOCX
  files up to 10 MiB.
- `GET /api/v1/resumes/{resume_id}` — returns metadata and extracted text
  without exposing the stored filesystem path.

Uploaded files are stored under `backend/uploads` by default. The directory and
size limit can be changed through `UPLOAD_DIR` and `MAX_UPLOAD_SIZE_BYTES`.
Swagger testing is available at `http://localhost:8000/docs`.

### Phase 3: AI analysis and matching

Set `GEMINI_API_KEY` in `backend/.env` (never commit that file). The model and
request timeout are configurable with `GEMINI_MODEL` and
`GEMINI_TIMEOUT_SECONDS`. Phase 3 adds:

- `POST /api/v1/resumes/{resume_id}/analyze`
- `POST /api/v1/jobs/analyze`
- `POST /api/v1/jobs/{job_id}/match/{resume_id}`

Apply the current migrations before using these endpoints:

```powershell
cd C:\AI-Projects\InterviewIQ\backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```

For example, analyze a job description:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/api/v1/jobs/analyze `
  -ContentType "application/json" `
  -Body '{"description":"Backend engineer needed with Python, FastAPI, and PostgreSQL experience."}'
```

Matching requires both a stored job analysis and a stored resume analysis. Match
scores are evidence-based guidance, not a hiring probability.

## Project structure

The backend is organized by responsibility:

- `app/config` — environment-backed settings
- `app/routers` — HTTP endpoints
- `app/services`, `app/agents`, and `app/rag` — application service boundaries
- `app/models`, `app/schemas`, and `app/database` — persistence and API data boundaries

The remaining directories are intentionally lightweight in Phase 1 and are ready
for later feature work.
