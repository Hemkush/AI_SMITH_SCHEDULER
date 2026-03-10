# Docker Deployment

## 1) Prepare environment

```bash
cp docker.env.example .env
```

Update `.env` values as needed.

## 2) (Optional) Google Calendar credentials

If you use calendar sync, place these files in `backend/google-auth/`:

- `credentials.json`
- `token.json` (optional; will be generated after auth)

Without credentials, calendar endpoints may fail, but the app still starts.

If `token.json` is missing, generate it once on your host:

```bash
cd backend
python google_calendar.py
```

Then move/copy the generated `token.json` into `backend/google-auth/`.

## 3) Build and run

```bash
docker compose up --build -d
```

## 4) Access

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:5000/api/health`
- MySQL: `localhost:${MYSQL_PORT}` (default `3307`)

## 5) Stop

```bash
docker compose down
```

To also remove DB data volume:

```bash
docker compose down -v
```
