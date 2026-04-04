# ShuttleKit Web

Next.js frontend for the ShuttleKit campus shuttle planning system.

## Quick Start

```bash
# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# Edit .env.local with your Google Maps API key and backend URL

# Run development server
npm run dev
```

App will be available at `http://localhost:3000`

## Routes

- **`/`** — Trip planner (map, search, itinerary)
- **`/schedule`** — Timetable view
- **`/chat`** — Shuttle assistant (shown in navigation when **`GET /api/features`** returns `chatbot: true`; backend **`FEATURE_FLAGS_CHATBOT`**)

## Environment Variables

- `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` - Google Maps JavaScript API key (required)
- `NEXT_PUBLIC_API_URL` - Backend API URL (defaults to `http://localhost:8000`; used for config, features, and API calls)
- `NEXT_PUBLIC_CAMPUS_NAME` - Campus name for page title and metadata (optional, defaults to "Campus")

The root layout fetches **`GET /api/features`** (via `lib/feature-flags-server.ts`) so the chat tab and related UI can stay in sync with backend toggles.

## Building for Production

```bash
npm run build
npm start
```

## Deployment

See [SETUP.md](../SETUP.md) in the root directory for deployment guides.
