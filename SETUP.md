# ShuttleKit Setup Guide

This guide walks you through forking ShuttleKit, customizing it for your campus shuttle system, and deploying both the backend and frontend.

## Table of Contents

1. [Fork and Clone](#fork-and-clone)
2. [Configure for Your Campus](#configure-for-your-campus)
3. [Local Development](#local-development)
4. [MCP server and chat assistant](#mcp-server-and-chat-assistant)
5. [Deployment](#deployment)

---

## Fork and Clone

### 1. Fork the Repository

1. Visit [github.com/gabenotgave/ShuttleKit](https://github.com/gabenotgave/ShuttleKit)
2. Click the "Fork" button in the top right
3. Choose your account as the destination

### 2. Clone Your Fork

```bash
git clone https://github.com/YOUR-USERNAME/ShuttleKit.git
cd ShuttleKit
```

---

## Configure for Your Campus

### Option A: Automated Schedule Ingestion (Recommended)

If you have a shuttle schedule as a PDF or image, use the automated ingestion tool:

#### 1. Set Up Ingestion Environment

```bash
cd api
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. Configure API Key

```bash
cp .env.example .env
```

Edit `api/.env` and set ingestion variables:

```env
INGESTION_MODEL=gemini/gemini-1.5-flash
INGESTION_API_KEY=your_api_key_here
```

`ingest.py` passes `INGESTION_MODEL` to [LiteLLM](https://docs.litellm.ai/docs/providers) and maps `INGESTION_API_KEY` to the right provider env var (`GEMINI_*`, `OPENAI_*`, etc.). Use a **vision- or document-capable** model; PDF/image behavior varies by provider. Defaults that work well: **`gemini/gemini-1.5-flash`**. The legacy **`MODEL`** env var is still read if `INGESTION_MODEL` is unset.

#### 3. Run Ingestion

Place your schedule file in `api/ingestion/` and run:

```bash
python ingestion/ingest.py ingestion/schedule.pdf \
  --campus "Your University Name" \
  --location "City, State" \
  --geocode
```

**Arguments:**
- `ingestion/schedule.pdf` - Path to your schedule file (PDF, PNG, JPG, WEBP)
- `--campus` - Full name of your campus
- `--location` - City/state for geocoding (helps locate stops accurately)
- `--geocode` - (Optional) Use OpenStreetMap to geocode stop locations

This generates `api/config.json` with your routes, stops, and schedules.

#### 4. Review and Adjust

**Important:** Always review the generated `config.json` for accuracy. The LLM may misinterpret schedules or geocoding may return incorrect coordinates.

Common adjustments:
- Verify stop coordinates on a map
- Check route colors and names
- Confirm operating hours
- Validate arrival times

### Option B: Manual Configuration

Edit `api/config.json` directly:

```json
{
  "campus": "Your University Name",
  "timezone": "America/New_York",
  "routes": [
    {
      "id": "route-1",
      "name": "Main Campus Loop",
      "color": "#3b82f6",
      "stops": [
        {
          "id": "library",
          "name": "LIBRARY",
          "coords": [40.7128, -74.0060],
          "arrivals": ["08:00", "08:30", "09:00", "09:30"]
        }
      ]
    }
  ],
  "hours": {
    "monday": { "start": "08:00", "end": "22:00" },
    "tuesday": { "start": "08:00", "end": "22:00" }
  }
}
```

**Configuration Tips:**

1. **Timezone**: Use IANA timezone names (e.g., `America/New_York`, `America/Los_Angeles`)
2. **Coordinates**: Get accurate lat/lng from Google Maps (right-click → "What's here?")
3. **Stop IDs**: Use lowercase with hyphens (e.g., `student-center`)
4. **Times**: Use 24-hour format `HH:MM`
5. **Arrivals**: List all arrival times for each stop in chronological order

### Get Google Maps API Key

The frontend requires a Google Maps JavaScript API key:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Maps JavaScript API"
4. Create credentials → API Key
5. Restrict the key to "Maps JavaScript API" and your domain

---

## Local Development

### Backend Setup

```bash
cd api
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run the API server
uvicorn main:app --reload
```

API available at `http://localhost:8000`

Interactive docs at `http://localhost:8000/docs`

### Frontend Setup

```bash
cd web
npm install

# Configure environment
cp .env.local.example .env.local
```

Edit `web/.env.local`:

```env
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your_google_maps_api_key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

```bash
# Run the development server
npm run dev
```

Frontend available at `http://localhost:3000`

### Testing

```bash
cd api
pytest tests/api/ -v
```

---

## MCP server and chat assistant

The map and trip planner use only the **FastAPI** process. The **shuttle assistant** (`POST /api/chat`) additionally needs an **[MCP](https://modelcontextprotocol.io/)** (Model Context Protocol) server: it exposes shuttle data and planning as **tools** the LLM can call. ShuttleKit runs that server with **[FastMCP](https://github.com/jlowin/fastmcp)** over **SSE** (Server-Sent Events) on a **separate port** from the HTTP API.

**What the MCP server provides:** three FastMCP tools in `api/shuttlekit/mcp_server.py`: **`get_schedule`** (aggregates campus name, live service status, hours, timezone, stops with coordinates, routes, full timetable, disruption hints), **`get_trip`** (plan between two lat/lng points), and **`get_coords_by_addresses`** (geocode free-text addresses). `api/mcp_server.py` is the CLI entry and is what uvicorn spawns when the chatbot feature is on.

### Run locally

Use the same virtualenv and `api/.env`.

With **`FEATURE_FLAGS_CHATBOT` enabled** (see `.env.example`), **`uvicorn` starts `mcp_server.py` for you** as a child process. One terminal is enough:

```bash
cd api
source .venv/bin/activate   # Windows: .venv\Scripts\activate
uvicorn main:app --reload
```

The API stays on **port 8000**; MCP listens on **`MCP_PORT`** (default **8001**). The chat agent connects to MCP at **`MCP_SSE_URL`** (default `http://127.0.0.1:8001/sse`). Stop uvicorn to stop both.

If the chatbot feature is **disabled**, MCP is not started automatically and **`/api/chat*`** routes return **404** (not **503**).

### Environment variables (`api/.env`)

| Variable | Purpose |
|----------|---------|
| `MCP_PORT` | Port the MCP process binds (default `8001`). Avoid clashing with uvicorn (`8000`). |
| `MCP_SSE_URL` | Full SSE URL the LangGraph agent uses; must point at your running MCP server (path is `/sse`). |

For chat, also set **`MODEL_NAME`**, **`PROVIDER`**, and the API key for your provider (see `api/.env.example`). If the chatbot is **on** but MCP failed to start or is unreachable, **`POST /api/chat`** can fail with **503** (transport error). If the chatbot is **off**, you get **404** instead.

### Production

With chatbot enabled, the API process starts MCP locally; ensure **`MCP_SSE_URL`** is reachable from the agent (same host/port as in production). If MCP is omitted, disable the chat feature (`FEATURE_FLAGS_CHATBOT=false`).

---

## Deployment

The backend and frontend are fully decoupled and can be deployed separately to different platforms.

### Backend Deployment Options

#### Option 1: Railway

1. Create account at [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your forked repository
4. Configure:
   - **Root Directory**: `api`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Railway will provide a public URL (e.g., `https://your-app.railway.app`)

#### Option 2: Render

1. Create account at [render.com](https://render.com)
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Root Directory**: `api`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Render will provide a public URL

#### Option 3: Fly.io

1. Install [flyctl](https://fly.io/docs/hands-on/install-flyctl/)
2. Login: `fly auth login`
3. Create `api/fly.toml`:

```toml
app = "your-shuttlekit-api"

[build]
  builder = "paketobuildpacks/builder:base"

[env]
  PORT = "8000"

[[services]]
  http_checks = []
  internal_port = 8000
  protocol = "tcp"

  [[services.ports]]
    port = 80
    handlers = ["http"]

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]
```

4. Deploy: `cd api && fly launch`

#### Option 4: DigitalOcean App Platform

1. Create account at [digitalocean.com](https://www.digitalocean.com/)
2. Go to App Platform → "Create App"
3. Connect GitHub repository
4. Configure:
   - **Source Directory**: `api`
   - **Build Command**: `pip install -r requirements.txt`
   - **Run Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

#### Option 5: Self-Hosted (VPS)

On any Ubuntu/Debian server:

```bash
# Install dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx

# Clone and setup
git clone https://github.com/YOUR-USERNAME/ShuttleKit.git
cd ShuttleKit/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Install and configure systemd service
sudo nano /etc/systemd/system/shuttlekit.service
```

```ini
[Unit]
Description=ShuttleKit API
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/ShuttleKit/api
Environment="PATH=/path/to/ShuttleKit/api/.venv/bin"
ExecStart=/path/to/ShuttleKit/api/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable shuttlekit
sudo systemctl start shuttlekit

# Configure nginx reverse proxy
sudo nano /etc/nginx/sites-available/shuttlekit
```

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/shuttlekit /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Frontend Deployment Options

#### Option 1: Vercel (Recommended for Next.js)

1. Create account at [vercel.com](https://vercel.com)
2. Click "New Project" → Import your GitHub repository
3. Configure:
   - **Root Directory**: `web`
   - **Framework Preset**: Next.js (auto-detected)
4. Add environment variables:
   - `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY`: Your Google Maps API key
   - `NEXT_PUBLIC_API_URL`: Your deployed backend URL
5. Click "Deploy"

Vercel automatically handles builds, SSL, and CDN.

#### Option 2: Netlify

1. Create account at [netlify.com](https://netlify.com)
2. Click "Add new site" → "Import an existing project"
3. Connect GitHub repository
4. Configure:
   - **Base directory**: `web`
   - **Build command**: `npm run build` (Netlify’s Next.js runtime handles the output; no manual “static export” folder)
5. Add environment variables in Site settings
6. Deploy

#### Option 3: Railway

1. Create account at [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Configure:
   - **Root Directory**: `web`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm start`
4. Add environment variables
5. Deploy

#### Option 4: Self-Hosted (Node server)

This repo’s frontend is a standard **Next.js** app (SSR + API routes to your backend). Build and run with Node, or put a reverse proxy in front of `npm start`:

```bash
cd web
npm install
npm run build
npm start   # serves on port 3000 by default
```

For process management (systemd, PM2, etc.), run `npm start` from `web/` with `NODE_ENV=production` and the same `NEXT_PUBLIC_*` variables as cloud deploys. Static export (`next export`) is **not** configured in this project; use Vercel/Netlify/Railway or a Node host unless you add an export pipeline yourself.

---

## Post-Deployment Configuration

### Update CORS Settings

After deploying the frontend, update the backend CORS settings in `api/shuttlekit/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://your-frontend-domain.com",  # Production
    ],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
```

### Update Frontend API URL

Ensure `web/.env.local` (or Vercel/Netlify environment variables) points to your deployed backend:

```env
NEXT_PUBLIC_API_URL=https://your-api-domain.com
```

### Test Your Deployment

1. Visit your frontend URL
2. Check that the map loads with your campus center
3. Try planning a trip between two locations
4. Verify shuttle status indicator shows correct state
5. Check browser console for any API errors

---

## Troubleshooting

### Backend Issues

**Config not found:**
- Ensure `api/config.json` exists
- Check file permissions

**CORS errors:**
- Add your frontend domain to `allow_origins` in `api/shuttlekit/main.py`
- Redeploy backend

**Timezone issues:**
- Verify timezone string in `config.json` matches IANA format
- Test with: `python -c "from zoneinfo import ZoneInfo; print(ZoneInfo('Your/Timezone'))"`

**Chat returns 404:**
- **`FEATURE_FLAGS_CHATBOT`** is off — enable it or omit it (default is on) if you want `/api/chat*`.

**Chat returns 503 / “MCP” or transport error:**
- Ensure **`FEATURE_FLAGS_CHATBOT`** is enabled and uvicorn started the MCP child (check logs), or run `python mcp_server.py` from `api/` only if you are not relying on the built-in spawn (avoid two listeners on the same `MCP_PORT`).
- Check `MCP_SSE_URL` matches where MCP is listening (default `http://127.0.0.1:8001/sse`)
- Confirm `MCP_PORT` matches the port in that URL
- Verify LLM env vars (`MODEL_NAME`, `PROVIDER`, provider API keys) in `api/.env`

### Frontend Issues

**Map not loading:**
- Verify `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` is set correctly
- Check API key restrictions in Google Cloud Console
- Ensure "Maps JavaScript API" is enabled

**API connection failed:**
- Verify `NEXT_PUBLIC_API_URL` points to deployed backend
- Check backend is running and accessible
- Test API directly: `curl https://your-api-url.com/api/status`

**Build errors:**
- Clear cache: `rm -rf .next node_modules && npm install`
- Check Node.js version (requires 18+)

### Ingestion Issues

**LLM extraction errors:**
- Try a different model (Gemini vs GPT-4)
- Ensure schedule image/PDF is clear and readable
- Manually review and correct `config.json`

**Geocoding failures:**
- Remove `--geocode` flag and use LLM coordinates
- Manually verify coordinates on Google Maps
- Check that `--location` is specific enough

---

## Maintenance

### Updating Schedules

When shuttle schedules change:

1. Run ingestion again with new schedule file, or
2. Manually edit `api/config.json`
3. Commit changes: `git add api/config.json && git commit -m "Update schedule"`
4. Push to trigger redeployment: `git push`

Most platforms (Vercel, Railway, Render) auto-deploy on git push.

### Monitoring

- Check backend logs in your hosting platform dashboard
- Monitor API response times
- Set up uptime monitoring (e.g., UptimeRobot, Pingdom)
- Review Google Maps API usage in Cloud Console

---

## Need Help?

- Check [README.md](README.md) for general documentation
- Review [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- Open an issue on GitHub for bugs or questions
- Join discussions for feature requests and community support

Happy shuttling! 🚌
