# ShuttleKit Architecture

ShuttleKit is designed with a fully decoupled architecture, allowing the backend and frontend to be developed, deployed, and scaled independently.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│                      (Next.js / React)                      │
│                                                             │
│  • Interactive Google Maps                                  │
│  • Trip search interface                                    │
│  • Itinerary display                                        │
│  • Responsive UI components                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ HTTP/REST API
                       │ (CORS-enabled)
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                         Backend                             │
│                      (FastAPI / Python)                     │
│                                                             │
│  • RESTful API endpoints                                    │
│  • Route planning algorithm                                 │
│  • Geospatial calculations                                  │
│  • Schedule management                                      │
│  • Configuration loading                                    │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
ShuttleKit/
├── api/                          # Backend (FastAPI)
│   ├── main.py                   # Uvicorn entry (`uvicorn main:app`)
│   ├── mcp_server.py             # MCP SSE entry (`python mcp_server.py`)
│   ├── shuttlekit/               # Application package
│   │   ├── main.py               # FastAPI app and routes
│   │   ├── geo.py                # Haversine, nearest stops, geocoding
│   │   ├── planning.py           # Trip scheduling on loop routes
│   │   ├── services.py           # Config + HTTP service helpers
│   │   ├── mcp_server.py         # FastMCP tool definitions
│   │   └── agent/                # LangGraph agent + MCP client
│   ├── config.json               # Campus configuration
│   ├── requirements.txt          # Python dependencies
│   ├── .env.example              # Environment template
│   ├── .gitignore                # Backend-specific ignores
│   ├── pytest.ini                # Test configuration
│   ├── README.md                 # Backend documentation
│   ├── ingestion/                # Schedule extraction tools
│   │   ├── ingest.py            # LLM-based schedule parser
│   │   └── schedule.*           # Source schedule files
│   └── tests/                    # Unit tests
│       ├── api/
│       │   ├── test_geo.py
│       │   ├── test_planning.py
│       │   └── test_chat.py
│       └── postman/
│           └── *.postman_collection.json
│
├── web/                          # Frontend (Next.js)
│   ├── app/                      # Next.js app router
│   │   ├── page.tsx             # Main application page
│   │   ├── layout.tsx           # Root layout
│   │   └── globals.css          # Global styles
│   ├── components/               # React components
│   │   ├── map-display.tsx      # Google Maps integration
│   │   ├── search-panel.tsx     # Trip search form
│   │   ├── itinerary-panel.tsx  # Results display
│   │   ├── navbar.tsx           # Navigation bar
│   │   └── ui/                  # Reusable UI components
│   ├── lib/                      # Utilities
│   │   ├── shuttle-api.ts       # API client
│   │   └── utils.ts             # Helper functions
│   ├── hooks/                    # React hooks
│   ├── public/                   # Static assets
│   ├── package.json              # Node dependencies
│   ├── .env.local.example        # Environment template
│   ├── tsconfig.json             # TypeScript config
│   └── README.md                 # Frontend documentation
│
├── README.md                     # Main project documentation
├── SETUP.md                      # Deployment and setup guide
├── CONTRIBUTING.md               # Contribution guidelines
├── ARCHITECTURE.md               # This file
├── LICENSE                       # MIT License
└── .gitignore                    # Root-level ignores
```

## Communication Flow

### 1. Trip Planning Request

```
User Input (coordinates) 
  → Frontend (search-panel.tsx)
  → API Client (shuttle-api.ts)
  → Backend API (/api/plan)
  → Planning Logic (`shuttlekit/planning.py` + `shuttlekit/geo.py`)
  → Response (itinerary JSON)
  → Frontend Display (itinerary-panel.tsx + map-display.tsx)
```

### 2. Map Initialization

```
Page Load
  → Frontend (page.tsx)
  → API Client (shuttle-api.ts)
  → Backend API (/api/config, /api/routes, /api/stops)
  → Config Data (config.json)
  → Map Display (map-display.tsx with Google Maps)
```

### 3. Shuttle assistant (optional)

```
User message + session_id
  → POST /api/chat
  → shuttlekit.agent (LangGraph + LLM)
  → MCP tools over SSE (shuttlekit/mcp_server.py process)
  → JSON { session_id, reply }
```

With chat enabled (`FEATURE_FLAGS_CHATBOT`), uvicorn starts `mcp_server.py` as a child process. Configure `MCP_SSE_URL` / `MCP_PORT` in `api/.env`.

## Key Design Principles

### 1. Decoupling

- Backend and frontend communicate exclusively through REST API
- No shared code or dependencies between layers
- Each can be deployed to different platforms
- Independent scaling and versioning

### 2. Configuration-Driven

- All campus-specific data in `api/config.json`
- No hardcoded routes, stops, or schedules
- Easy customization for different campuses
- Automated ingestion from schedule documents

### 3. REST layer and chat sessions

- Most endpoints are stateless: each request is independent and needs no cookie or server session.
- **`POST /api/chat`** uses a client-generated **`session_id`** so the LangGraph agent can continue a thread; checkpoint state is **in-process** (`MemorySaver`) unless you swap in a persistent checkpointer.
- No authentication (can be added).

### 4. Environment-Based Configuration

**Backend (`api/.env`):**
- **Ingestion:** `INGESTION_MODEL`, `INGESTION_API_KEY` (see `api/ingestion/ingest.py`, `api/.env.example`)
- **Chat agent:** `MODEL_NAME`, `PROVIDER`, provider API keys as needed; `MCP_PORT`, `MCP_SSE_URL` (MCP server must be running for chat)
- See `api/.env.example` for the full list

**Frontend (`web/.env.local`):**
- `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` - Google Maps API key
- `NEXT_PUBLIC_API_URL` - Backend API URL

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/config` | GET | Campus name and map center |
| `/api/status` | GET | Current shuttle operational status |
| `/api/stops` | GET | All stops with routes |
| `/api/routes` | GET | All routes with paths for map display |
| `/api/schedule` | GET | Full timetable per route, hours, timezone |
| `/api/plan` | GET | Trip planning with itinerary |
| `/api/chat` | POST | LLM + MCP shuttle assistant (`session_id`, `message`) |

See interactive docs at `http://localhost:8000/docs` when running the backend.

## Data Models

### Config Schema (`api/config.json`)

```typescript
{
  campus: string              // Campus name
  timezone: string            // IANA timezone (e.g., "America/New_York")
  routes: [
    {
      id: string              // Unique route identifier
      name: string            // Display name
      color: string | null    // Hex color for map display
      stops: [
        {
          id: string          // Unique stop identifier
          name: string        // Display name
          coords: [number, number]  // [latitude, longitude]
          arrivals: string[]  // Array of "HH:MM" times
        }
      ]
    }
  ]
  hours: {
    [day: string]: {          // "monday", "tuesday", etc.
      start: string           // "HH:MM"
      end: string             // "HH:MM"
    }
  }
}
```

### Trip Plan Response

```typescript
{
  legs: [
    {
      type: "walk" | "shuttle"
      description: string
      duration_minutes?: number      // For walk legs
      departs?: string               // For shuttle legs
      arrives?: string               // For shuttle legs
      wait_minutes?: number          // For shuttle legs
      ride_minutes?: number          // For shuttle legs
      from: {
        name: string
        coords: [number, number]
      }
      to: {
        name: string
        coords: [number, number]
      }
    }
  ]
  total_minutes: number
  arrives_at: string
}
```

## Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Geospatial**: Custom Haversine implementation
- **Schedule Parsing**: LiteLLM + Vision models
- **Geocoding**: Geopy + Nominatim (OpenStreetMap)
- **Shuttle assistant (`/api/chat`)**: LangChain + LangGraph agent; tools invoked via **[MCP](https://modelcontextprotocol.io/)** over **SSE** using [FastMCP](https://github.com/jlowin/fastmcp) (child process when chatbot feature is on; default port `8001`; see [SETUP.md](SETUP.md#mcp-server-and-chat-assistant))
- **Testing**: pytest

### Frontend
- **Framework**: Next.js 16 (React 19)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Maps**: Google Maps JavaScript API
- **UI Components**: Radix UI + shadcn/ui
- **State Management**: React hooks (useState, useEffect)

## Deployment Considerations

### Backend
- Stateless design allows horizontal scaling for read-only and planning endpoints
- No database required (config file-based)
- Can run on serverless platforms (with config in environment)
- CORS configuration needed for production frontend URL
- **Chat**: MCP over SSE (child of uvicorn when `FEATURE_FLAGS_CHATBOT` is on); the API must reach MCP at `MCP_SSE_URL`, or disable chat via feature flags

### Frontend
- Static generation possible for most pages
- Client-side API calls for dynamic data
- CDN-friendly architecture
- Environment variables for API URL configuration

### Security
- API key restrictions (Google Maps)
- CORS origin whitelisting
- HTTPS recommended for production
- Rate limiting can be added at API gateway level

## Future Enhancements

Potential architectural improvements:

1. **Real-time Updates**: WebSocket support for live shuttle tracking
2. **Database Layer**: PostgreSQL/PostGIS for dynamic schedule management
3. **Authentication**: User accounts and saved trips
4. **Caching**: Redis for frequently accessed routes/stops
5. **Analytics**: Usage tracking and optimization insights
6. **Mobile Apps**: React Native using same API
7. **Admin Panel**: Web interface for schedule management
8. **Multi-tenancy**: Support multiple campuses in one deployment

## Development Workflow

1. **Local Development**: Run backend and frontend separately
2. **Testing**: Unit tests for backend, manual testing for frontend
3. **Configuration**: Update `config.json` for campus-specific data
4. **Deployment**: Deploy backend and frontend independently
5. **Monitoring**: Check logs and API response times

See [SETUP.md](SETUP.md) for detailed deployment instructions.
