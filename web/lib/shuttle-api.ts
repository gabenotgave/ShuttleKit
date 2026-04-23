// ShuttleKit API Service

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

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

/** GET /api/features — boolean flags by name (whatever the backend returns). */
export type FeatureFlags = Record<string, boolean>

/**
 * Pass `init` from a Server Component for Next.js Data Cache hints, e.g. `{ next: { revalidate: false } }` or `{ next: { revalidate: 3600 } }`.
 * Throws if the request fails or the response is not OK.
 */
export async function getFeatures(
  init?: RequestInit & { next?: { revalidate?: number | false } },
): Promise<FeatureFlags> {
  const response = await fetch(`${API_BASE_URL}/api/features`, init)
  if (!response.ok) {
    throw new Error(`GET /api/features failed: ${response.status}`)
  }
  return (await response.json()) as FeatureFlags
}

export interface ScheduleStop {
  id: string
  name: string
  arrivals: string[]
  /** US 12-hour strings aligned with `arrivals` (server-generated) */
  arrivals_12?: string[]
}

/** One full loop of the route; same index as parallel `arrivals` entries per stop */
export interface ScheduleRun {
  index: number
  stops: { id: string; name: string; arrival: string; arrival_12?: string }[]
}

export interface ScheduleRoute {
  id: string
  name: string
  color: string | null
  stops: ScheduleStop[]
  /** Present when API returns pre-grouped loops (preferred for trip reasoning) */
  runs?: ScheduleRun[]
}

/** Day key -> { start, end } as HH:MM strings; optional US 12h from API */
export type ServiceHoursMap = Record<
  string,
  { start: string; end: string; start_12?: string; end_12?: string }
>

export interface ScheduleStopIndex {
  id: string
  name: string
  coords: [number, number]
  routes: string[]
}

/** Lean hint: first upcoming arrival at each stop (≥ server reference time) */
export interface ScheduleQuickNextStop {
  stop_name: string
  next_arrival_24: string | null
  next_arrival_12: string | null
  run_index_for_next: number | null
}

export interface ScheduleQuickNext {
  as_of_local: string
  as_of_hhmm_24: string
  per_route: {
    route_id: string
    route_name: string
    by_stop_id: Record<string, ScheduleQuickNextStop>
  }[]
}

export interface ScheduleResponse {
  campus: string
  timezone: string
  hours: ServiceHoursMap
  status: { active: boolean; message: string }
  stops: Record<string, ScheduleStopIndex>
  routes: ScheduleRoute[]
  quick_next?: ScheduleQuickNext
}

export async function getSchedule(): Promise<ScheduleResponse | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/schedule`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

/** Persisted client thread id for POST /api/chat (also used when history is loaded server-side). */
export const CHAT_SESSION_STORAGE_KEY = "shuttlekit_chat_session_id"

/** One row from GET /api/chat/history (matches API `get_chat_history_for_session`). */
export interface ChatHistoryApiMessage {
  role: string
  content?: string
  name?: string
  tool_calls?: unknown[]
}

export interface ChatHistoryResponse {
  session_id: string
  messages: ChatHistoryApiMessage[]
}

export type GetChatHistoryResult =
  | { ok: true; data: ChatHistoryResponse }
  | { ok: false; error: string }

export async function getChatHistory(sessionId: string): Promise<GetChatHistoryResult> {
  try {
    const params = new URLSearchParams({ session_id: sessionId })
    const response = await fetch(`${API_BASE_URL}/api/chat/history?${params}`)
    const data: unknown = await response.json().catch(() => ({}))
    if (!response.ok) {
      let detail = response.statusText || "Request failed"
      if (data && typeof data === "object" && "detail" in data) {
        const d = (data as { detail: unknown }).detail
        if (typeof d === "string") detail = d
      }
      return { ok: false, error: detail }
    }
    if (!data || typeof data !== "object" || !("session_id" in data) || !("messages" in data)) {
      return { ok: false, error: "Invalid history response" }
    }
    const session_id = String((data as { session_id: unknown }).session_id)
    const raw = (data as { messages: unknown }).messages
    const messages: ChatHistoryApiMessage[] = Array.isArray(raw)
      ? raw.filter(
          (m): m is ChatHistoryApiMessage =>
            m != null && typeof m === "object" && "role" in m && typeof (m as { role: unknown }).role === "string",
        )
      : []
    return { ok: true, data: { session_id, messages } }
  } catch (e) {
    return {
      ok: false,
      error: e instanceof Error ? e.message : "Network error",
    }
  }
}

export interface ChatApiResponse {
  session_id: string
  reply: string
  model_display: string
}

export async function getChatModelDisplay(): Promise<string | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat/model`)
    if (!response.ok) return null
    const data: unknown = await response.json()
    if (data && typeof data === "object" && "model_display" in data) {
      const v = (data as { model_display: unknown }).model_display
      return typeof v === "string" ? v : null
    }
    return null
  } catch {
    return null
  }
}

export type PostChatResult =
  | { ok: true; data: ChatApiResponse }
  | { ok: false; error: string }

export async function postChat(sessionId: string, message: string): Promise<PostChatResult> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message }),
    })
    const data: unknown = await response.json().catch(() => ({}))
    if (!response.ok) {
      let detail = response.statusText || "Request failed"
      if (data && typeof data === "object" && "detail" in data) {
        const d = (data as { detail: unknown }).detail
        if (typeof d === "string") {
          detail = d
        } else if (Array.isArray(d)) {
          detail = d
            .map((item) =>
              item && typeof item === "object" && "msg" in item
                ? String((item as { msg: unknown }).msg)
                : JSON.stringify(item),
            )
            .join("; ")
        }
      }
      return { ok: false, error: detail }
    }
    const session_id =
      data && typeof data === "object" && "session_id" in data
        ? String((data as { session_id: unknown }).session_id)
        : ""
    const reply =
      data && typeof data === "object" && "reply" in data
        ? String((data as { reply: unknown }).reply)
        : ""
    const model_display =
      data && typeof data === "object" && "model_display" in data
        ? String((data as { model_display: unknown }).model_display)
        : ""
    return { ok: true, data: { session_id, reply, model_display } }
  } catch (e) {
    return {
      ok: false,
      error: e instanceof Error ? e.message : "Network error",
    }
  }
}

// Helper to check if response is an error
export function isPlanError(response: PlanResponse | PlanError): response is PlanError {
  return "message" in response
}

/** Public GET /api/disruptions (banner) */
export interface DisruptionAlertRow {
  id: string
  route_id?: string | null
  message: string
  start_local: string
  end_local: string
}

export interface DisruptionsPublic {
  active: DisruptionAlertRow[]
  upcoming: DisruptionAlertRow[]
}

export async function getDisruptionsPublic(): Promise<DisruptionsPublic> {
  const response = await fetch(`${API_BASE_URL}/api/disruptions`)
  if (!response.ok) {
    return { active: [], upcoming: [] }
  }
  const data: unknown = await response.json()
  if (
    data &&
    typeof data === "object" &&
    "active" in data &&
    "upcoming" in data
  ) {
    const d = data as { active: unknown; upcoming: unknown }
    return {
      active: Array.isArray(d.active) ? (d.active as DisruptionAlertRow[]) : [],
      upcoming: Array.isArray(d.upcoming)
        ? (d.upcoming as DisruptionAlertRow[])
        : [],
    }
  }
  return { active: [], upcoming: [] }
}

export interface DisruptionStored {
  id: string
  route_id?: string | null
  kind?: string
  message: string
  start_local: string
  end_local: string
}

export async function getDisruptionsAdmin(
  token: string
): Promise<{ disruptions: DisruptionStored[] } | null> {
  const response = await fetch(`${API_BASE_URL}/api/disruptions`, {
    headers: { "X-Shuttle-Admin-Token": token },
  })
  if (!response.ok) return null
  const data: unknown = await response.json()
  if (data && typeof data === "object" && "disruptions" in data) {
    const raw = (data as { disruptions: unknown }).disruptions
    return {
      disruptions: Array.isArray(raw) ? (raw as DisruptionStored[]) : [],
    }
  }
  return null
}

export async function postDisruption(
  token: string,
  body: {
    route_id?: string | null
    start_local: string
    end_local: string
    message: string
  }
): Promise<{ ok: true } | { ok: false; error: string }> {
  const response = await fetch(`${API_BASE_URL}/api/disruptions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shuttle-Admin-Token": token,
    },
    body: JSON.stringify(body),
  })
  if (!response.ok) {
    const err: unknown = await response.json().catch(() => ({}))
    let detail = response.statusText
    if (err && typeof err === "object" && "detail" in err) {
      const d = (err as { detail: unknown }).detail
      if (typeof d === "string") detail = d
    }
    return { ok: false, error: detail }
  }
  return { ok: true }
}

export async function deleteDisruption(
  token: string,
  id: string
): Promise<boolean> {
  const response = await fetch(`${API_BASE_URL}/api/disruptions/${encodeURIComponent(id)}`, {
    method: "DELETE",
    headers: { "X-Shuttle-Admin-Token": token },
  })
  return response.ok
}
