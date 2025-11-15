# TimeTrack Web-UI

React + Vite Frontend für Tages-/Monatsreview, Event-Zuordnung und CSV-Export.

## Entwicklung

```powershell
cd frontend
npm install
npm run dev -- --host
```

Default-API: `http://localhost:8000`. Per `.env` kannst du `VITE_API_BASE` configurieren.

## Prod Build

```powershell
npm run build
npm run preview
```

Docker:

```bash
docker build -t timetrack-web ./frontend
docker run -p 3000:80 timetrack-web
```

Innerhalb des `docker compose` läuft der Container bereits (Port 3000).

