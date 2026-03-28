# ShuttleKit

A campus shuttle planning system with a FastAPI backend and Next.js frontend. Given a user's coordinates and destination, ShuttleKit finds the nearest stops, computes walk times using the Haversine formula, and returns a full itinerary with walk and shuttle legs displayed on an interactive map.

---

## Features

- Real-time trip planning with walk + shuttle legs
- Interactive Google Maps display with labeled pins
- Shuttle status indicator (active/inactive based on schedule)
- Automated schedule ingestion from PDFs/images using LLM vision models
- Configurable campus, routes, stops, and hours
- RESTful API with FastAPI
- Modern Next.js frontend with TypeScript and Tailwind CSS
- Fully decoupled architecture for flexible deployment

---

## Quick Start

> **Existing users:** If you're upgrading from an older version, see [MIGRATION.md](MIGRATION.md) for migration instructions.

### Prerequisites

- Python 3.11+
- Node.js 18+
- Google Maps API key

### Installation

```bash
# Clone the repo
git clone https://github.com/gabenotgave/ShuttleKit.git
cd ShuttleKit

# Backend setup
cd api
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../web
npm install
```

### Configuration

1. **Backend environment** (optional, only needed for schedule ingestion):
   ```bash
   cd api
   cp .env.example .env
   # Edit .env with your LLM API key for schedule ingestion
   ```

2. **Frontend environment**:
   ```bash
   cd web
   cp .env.local.example .env.local
   # Edit .env.local with:
   #   - NEXT_PUBLIC_GOOGLE_MAPS_API_KEY (required)
   #   - NEXT_PUBLIC_API_URL (defaults to http://localhost:8000)
   #   - NEXT_PUBLIC_CAMPUS_NAME (optional, for page title/metadata)
   ```

3. **Campus configuration** — The `api/config.json` file contains your campus-specific routes, stops, and schedules. See [SETUP.md](SETUP.md) for:
   - Automated extraction from schedule PDFs/images
   - Manual configuration guide

### Running the Application

**Backend:**
```bash
cd api
uvicorn main:app --reload
```
API available at `http://localhost:8000` (docs at `/docs`)

**Frontend:**
```bash
cd web
npm run dev
```
Frontend available at `http://localhost:3000`

---

## Documentation

### For Campus Deployment

**[SETUP.md](SETUP.md)** - Complete guide for deploying ShuttleKit at your campus:
- Fork and customize the repository
- Extract schedules from PDFs/images using AI
- Configure routes, stops, and operating hours
- Deploy backend and frontend to various platforms
- Post-deployment configuration and troubleshooting

### For Developers

**[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture documentation:
- System design and communication flow
- Project structure and file organization
- API endpoints and data models
- Technology stack details
- Deployment considerations and scaling

**[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines:
- Development setup
- Code style and standards
- Pull request process
- Reporting issues and feature requests

---

## Project Structure

```
ShuttleKit/
├── api/                      # Backend (FastAPI)
│   ├── main.py              # API server and endpoints
│   ├── geo.py               # Geospatial calculations (Haversine)
│   ├── planning.py          # Route planning logic
│   ├── config.json          # Campus configuration (routes, stops, schedules)
│   ├── requirements.txt     # Python dependencies
│   ├── ingestion/           # AI-powered schedule extraction
│   └── tests/               # Unit tests
│
├── web/                     # Frontend (Next.js + TypeScript)
│   ├── app/                 # Next.js app router pages
│   ├── components/          # React components (map, search, itinerary)
│   ├── lib/                 # API client and utilities
│   └── package.json         # Node dependencies
│
├── SETUP.md                 # Campus deployment guide
├── ARCHITECTURE.md          # Technical documentation
├── CONTRIBUTING.md          # Contribution guidelines
├── MIGRATION.md             # Upgrade guide
└── LICENSE                  # MIT License
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed structure documentation.

---

## API Reference

Full API documentation is available at `http://localhost:8000/docs` when running the backend.

### Key Endpoints

- `GET /api/config` — Campus configuration and map center
- `GET /api/status` — Current shuttle operational status
- `GET /api/stops` — All stops with their routes
- `GET /api/routes` — All routes with paths for map display
- `GET /api/plan` — Trip planning with walk + shuttle itinerary

See the [interactive API docs](http://localhost:8000/docs) for detailed parameters and responses.

---

## Deployment

ShuttleKit's decoupled architecture allows independent deployment of backend and frontend:

### Backend Options
- **Railway** - One-click deployment from GitHub
- **Render** - Free tier available
- **Fly.io** - Global edge deployment
- **DigitalOcean App Platform** - Managed platform
- **Self-hosted VPS** - Full control (Ubuntu/Debian)

### Frontend Options
- **Vercel** - Recommended for Next.js (free tier)
- **Netlify** - Easy deployment with CDN
- **Railway** - Full-stack on one platform
- **Static hosting** - Any web server (nginx, S3, etc.)

See [SETUP.md](SETUP.md) for step-by-step deployment guides for each platform.

---

## Testing

```bash
cd api
pytest tests/ -v
```

Tests cover geospatial calculations, route planning logic, and API endpoints.

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to get started.

---

## AI Transparency

This project was developed with assistance from AI tools. See [AI_USAGE.md](AI_USAGE.md) for full transparency about which AI models and tools were used for different aspects of development.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
