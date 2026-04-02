"use client"

import { useCallback, useEffect, useState, type FormEvent } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  deleteDisruption,
  getDisruptionsAdmin,
  getRoutes,
  postDisruption,
  type DisruptionStored,
  type Route,
} from "@/lib/shuttle-api"
import { Trash2 } from "lucide-react"

const STORAGE_KEY = "shuttlekit_admin_token"

function localToIsoNaive(value: string): string {
  if (!value) return ""
  if (value.length >= 16) return `${value.slice(0, 10)}T${value.slice(11, 16)}:00`
  return value
}

export default function AdminPage() {
  const [token, setToken] = useState("")
  const [saved, setSaved] = useState(false)
  const [rows, setRows] = useState<DisruptionStored[]>([])
  const [routes, setRoutes] = useState<Route[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const [routeId, setRouteId] = useState("")
  const [startLocal, setStartLocal] = useState("")
  const [endLocal, setEndLocal] = useState("")
  const [message, setMessage] = useState("")

  useEffect(() => {
    try {
      const t = sessionStorage.getItem(STORAGE_KEY) ?? ""
      setToken(t)
      setSaved(!!t)
    } catch {
      /* ignore */
    }
  }, [])

  useEffect(() => {
    getRoutes().then(setRoutes).catch(() => setRoutes([]))
  }, [])

  const refresh = useCallback(async (t: string) => {
    if (!t.trim()) {
      setRows([])
      return
    }
    setLoading(true)
    setError(null)
    const res = await getDisruptionsAdmin(t.trim())
    setLoading(false)
    if (!res) {
      setError("Unauthorized or network error")
      setRows([])
      return
    }
    setRows(res.disruptions)
  }, [])

  useEffect(() => {
    if (saved && token) void refresh(token)
  }, [saved, token, refresh])

  const persistToken = () => {
    const t = token.trim()
    try {
      if (t) sessionStorage.setItem(STORAGE_KEY, t)
      else sessionStorage.removeItem(STORAGE_KEY)
    } catch {
      /* ignore */
    }
    setSaved(!!t)
    void refresh(t)
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    const t = token.trim()
    if (!t) {
      setError("Enter admin passphrase")
      return
    }
    setError(null)
    const body = {
      route_id: routeId.trim() || null,
      start_local: localToIsoNaive(startLocal),
      end_local: localToIsoNaive(endLocal),
      message: message.trim(),
    }
    const res = await postDisruption(t, body)
    if (!res.ok) {
      setError(res.error)
      return
    }
    setStartLocal("")
    setEndLocal("")
    setMessage("")
    void refresh(t)
  }

  const handleDelete = async (id: string) => {
    const t = token.trim()
    if (!t) return
    const ok = await deleteDisruption(t, id)
    if (!ok) setError("Delete failed")
    else void refresh(t)
  }

  return (
    <main className="min-h-screen bg-background px-4 pb-12 pt-[calc(1.5rem+var(--sk-disruption-banner,0px))]">
      <div className="mx-auto w-full max-w-lg space-y-8">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Shuttle disruptions</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Passphrase matches <code className="text-xs">SHUTTLE_ADMIN_PASSPHRASE</code> on the API.
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="token">Admin token</Label>
          <div className="flex gap-2">
            <Input
              id="token"
              type="password"
              autoComplete="off"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Passphrase"
            />
            <Button type="button" variant="secondary" onClick={persistToken}>
              Save
            </Button>
          </div>
        </div>

        {error && (
          <p className="text-sm text-destructive" role="alert">
            {error}
          </p>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-border p-4">
          <h2 className="text-sm font-medium">Add cancellation window</h2>
          <div className="space-y-2">
            <Label htmlFor="route">Route (optional)</Label>
            <select
              id="route"
              className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm"
              value={routeId}
              onChange={(e) => setRouteId(e.target.value)}
            >
              <option value="">All routes</option>
              {routes.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name} ({r.id})
                </option>
              ))}
            </select>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="start">Start (local)</Label>
              <Input
                id="start"
                type="datetime-local"
                value={startLocal}
                onChange={(e) => setStartLocal(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="end">End (local)</Label>
              <Input
                id="end"
                type="datetime-local"
                value={endLocal}
                onChange={(e) => setEndLocal(e.target.value)}
                required
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="msg">Message</Label>
            <Input
              id="msg"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Shown in banner / assistant context"
            />
          </div>
          <Button type="submit" disabled={loading}>
            Add disruption
          </Button>
        </form>

        <div className="space-y-2">
          <h2 className="text-sm font-medium">Stored ({rows.length})</h2>
          {loading && <p className="text-sm text-muted-foreground">Loading…</p>}
          <ul className="space-y-2">
            {rows.map((r) => (
              <li
                key={r.id}
                className="flex items-start justify-between gap-2 rounded-md border border-border px-3 py-2 text-sm"
              >
                <div className="min-w-0">
                  <p className="font-medium">{r.message || "Cancellation"}</p>
                  <p className="text-muted-foreground">
                    {r.route_id ?? "all routes"} · {r.start_local} → {r.end_local}
                  </p>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="shrink-0 text-destructive"
                  onClick={() => void handleDelete(r.id)}
                  aria-label="Delete"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </main>
  )
}
