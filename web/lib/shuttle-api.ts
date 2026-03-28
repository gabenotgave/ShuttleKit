// ShuttleKit API Service

const API_BASE_URL = "http://localhost:8000"

export interface Location {
  name: string
  coords: [number, number]
}

export interface WalkLeg {
  type: "walk"
  description: string
  duration_minutes: number
  from: Location
  to: Location
}

export interface ShuttleLeg {
  type: "shuttle"
  description: string
  departs: string
  arrives: string
  wait_minutes: number
  ride_minutes: number
  from: Location
  to: Location
}

export type Leg = WalkLeg | ShuttleLeg

export interface PlanResponse {
  legs: Leg[]
  total_minutes: number
  arrives_at: string
}

export interface PlanError {
  message: string
}

export interface Stop {
  id: string
  name: string
  coords: [number, number]
  routes: string[]
}

export interface Route {
  id: string
  name: string
  color: string | null
  path: [number, number][]
}

export interface ShuttleStatus {
  active: boolean
  message: string
}

export async function planTrip(
  fromLat: number,
  fromLng: number,
  toLat: number,
  toLng: number,
  time?: string
): Promise<PlanResponse | PlanError> {
  const params = new URLSearchParams({
    from_lat: fromLat.toString(),
    from_lng: fromLng.toString(),
    to_lat: toLat.toString(),
    to_lng: toLng.toString(),
  })

  if (time) {
    params.append("time", time)
  }

  const response = await fetch(`${API_BASE_URL}/api/plan?${params}`)
  return response.json()
}

export async function getStops(): Promise<Record<string, Stop>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/stops`)
    return response.json()
  } catch {
    return {}
  }
}

export async function getRoutes(): Promise<Route[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/routes`)
    return response.json()
  } catch {
    return []
  }
}

export async function getStatus(): Promise<ShuttleStatus> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/status`)
    return response.json()
  } catch {
    return { active: false, message: "Status unavailable" }
  }
}

export interface AppConfig {
  campus: string
  map_center: { lat: number; lng: number }
}

export async function getConfig(): Promise<AppConfig | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/config`)
    return response.json()
  } catch {
    return null
  }
}

// Helper to check if response is an error
export function isPlanError(response: PlanResponse | PlanError): response is PlanError {
  return "message" in response
}
