"use client"

import { useEffect, useMemo, useState } from "react"
import { Navbar } from "@/components/navbar"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Spinner } from "@/components/ui/spinner"
import {
  getConfig,
  getSchedule,
  getStatus,
  type AppConfig,
  type ScheduleResponse,
  type ScheduleRoute,
  type ScheduleStop,
  type ShuttleStatus,
} from "@/lib/shuttle-api"
import { formatHhmm12h } from "@/lib/time-format"
import { cn } from "@/lib/utils"
import { AlertCircle, Bus, Clock, MapPin } from "lucide-react"

const DAY_ORDER = [
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
  "sunday",
] as const

function weekdayKeyInTimezone(date: Date, timeZone: string): string | null {
  try {
    const long = new Intl.DateTimeFormat("en-US", {
      timeZone,
      weekday: "long",
    }).format(date)
    return long.toLowerCase()
  } catch {
    return null
  }
}

function formatDayLabel(key: string): string {
  return key.charAt(0).toUpperCase() + key.slice(1)
}

function maxTripCount(stops: ScheduleStop[]): number {
  if (stops.length === 0) return 0
  return Math.max(...stops.map((s) => s.arrivals.length))
}

function arrivalAt(stop: ScheduleStop, tripIndex: number): string | null {
  return stop.arrivals[tripIndex] ?? null
}

/** Prefer server `arrivals_12` when present so UI matches API / agent. */
function arrivalAt12(stop: ScheduleStop, tripIndex: number): string | null {
  const pre = stop.arrivals_12?.[tripIndex]
  if (pre != null) return pre
  const raw = arrivalAt(stop, tripIndex)
  return raw != null ? formatHhmm12h(raw) : null
}

function RouteTripCards({ route }: { route: ScheduleRoute }) {
  const n = maxTripCount(route.stops)
  if (n === 0) {
    return (
      <p className="text-sm text-muted-foreground px-1">
        No scheduled arrivals are configured for this route.
      </p>
    )
  }

  return (
    <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1 snap-x snap-mandatory">
      {Array.from({ length: n }, (_, tripIndex) => {
        const anchor = route.stops[0]
        const startTime12 = anchor ? arrivalAt12(anchor, tripIndex) : null
        const title =
          startTime12 != null
            ? `${startTime12} · ${anchor.name}`
            : `Loop ${tripIndex + 1}`

        return (
          <Card
            key={tripIndex}
            className="min-w-[min(100%,20rem)] shrink-0 snap-start shadow-sm py-4 gap-3"
          >
            <CardHeader className="px-4 pb-0 space-y-1">
              <CardTitle className="text-base font-semibold flex items-center gap-2">
                <Clock className="h-4 w-4 text-muted-foreground shrink-0" />
                {title}
              </CardTitle>
              <CardDescription className="text-xs">
                Stop order follows the route; times are scheduled arrivals.
              </CardDescription>
            </CardHeader>
            <CardContent className="px-4 pt-0">
              <ol className="space-y-0">
                {route.stops.map((stop, si) => {
                  const t12 = arrivalAt12(stop, tripIndex)
                  return (
                    <li key={stop.id} className="flex gap-3">
                      <div className="flex flex-col items-center w-6 shrink-0">
                        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-muted text-xs font-medium text-muted-foreground">
                          {si + 1}
                        </span>
                        {si < route.stops.length - 1 && (
                          <span className="w-px flex-1 min-h-[0.75rem] bg-border my-0.5" aria-hidden />
                        )}
                      </div>
                      <div className="flex-1 min-w-0 pb-3">
                        <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
                          <span className="font-medium text-foreground">{stop.name}</span>
                          {t12 != null ? (
                            <span className="text-sm tabular-nums text-muted-foreground">
                              {t12}
                            </span>
                          ) : (
                            <span className="text-sm text-muted-foreground">—</span>
                          )}
                        </div>
                      </div>
                    </li>
                  )
                })}
              </ol>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}

function RouteStopList({ route }: { route: ScheduleRoute }) {
  if (route.stops.length === 0) {
    return (
      <p className="text-sm text-muted-foreground px-1">No stops on this route.</p>
    )
  }

  return (
    <ul className="space-y-3 px-1">
      {route.stops.map((stop) => (
        <li key={stop.id}>
          <div className="flex items-start gap-2">
            <MapPin className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />
            <div className="min-w-0 flex-1">
              <p className="font-medium text-foreground">{stop.name}</p>
              {stop.arrivals.length === 0 ? (
                <p className="text-sm text-muted-foreground mt-1">No times listed</p>
              ) : (
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {stop.arrivals.map((t, i) => (
                    <Badge key={`${t}-${i}`} variant="secondary" className="tabular-nums font-normal">
                      {stop.arrivals_12?.[i] ?? formatHhmm12h(t)}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </div>
        </li>
      ))}
    </ul>
  )
}

function ServiceHoursCard({
  hours,
  timeZone,
}: {
  hours: ScheduleResponse["hours"]
  timeZone: string
}) {
  const todayKey = useMemo(
    () => weekdayKeyInTimezone(new Date(), timeZone),
    [timeZone],
  )

  const orderedEntries = useMemo(() => {
    const fromWeek = DAY_ORDER.filter((d) => d in hours).map((d) => ({
      key: d,
      start: hours[d].start,
      end: hours[d].end,
    }))
    const weekSet = new Set<string>(DAY_ORDER)
    const extras = Object.keys(hours)
      .filter((k) => !weekSet.has(k))
      .sort()
      .map((k) => ({ key: k, start: hours[k].start, end: hours[k].end }))
    return [...fromWeek, ...extras]
  }, [hours])

  if (orderedEntries.length === 0) {
    return null
  }

  return (
    <Card className="shadow-sm">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Service hours</CardTitle>
        <CardDescription>
          Times use the schedule&apos;s timezone ({timeZone}).
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-0">
        <ul className="space-y-2 text-sm">
          {orderedEntries.map(({ key, start, end }) => {
            const isToday = todayKey != null && key === todayKey
            return (
              <li
                key={key}
                className={cn(
                  "flex justify-between gap-4 rounded-lg px-3 py-2",
                  isToday && "bg-muted/80",
                )}
              >
                <span className={cn("text-muted-foreground", isToday && "font-medium text-foreground")}>
                  {formatDayLabel(key)}
                  {isToday && (
                    <Badge variant="outline" className="ml-2 align-middle text-[10px] px-1.5 py-0">
                      Today
                    </Badge>
                  )}
                </span>
                <span className="tabular-nums text-foreground shrink-0">
                  {formatHhmm12h(start)} – {formatHhmm12h(end)}
                </span>
              </li>
            )
          })}
        </ul>
      </CardContent>
    </Card>
  )
}

export default function SchedulePage() {
  const [schedule, setSchedule] = useState<ScheduleResponse | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [status, setStatus] = useState<ShuttleStatus | null>(null)
  const [appConfig, setAppConfig] = useState<AppConfig | null>(null)

  useEffect(() => {
    getStatus().then(setStatus)
    getConfig().then((config) => {
      setAppConfig(config)
      if (config?.campus) {
        document.title = `${config.campus} ShuttleKit · Schedule`
      }
    })
  }, [])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setLoadError(null)
    getSchedule().then((data) => {
      if (cancelled) return
      if (!data) {
        setSchedule(null)
        setLoadError("Could not load the schedule. Check that the API is running.")
      } else {
        setSchedule(data)
      }
      setLoading(false)
    })
    return () => {
      cancelled = true
    }
  }, [])

  const defaultRouteId = schedule?.routes[0]?.id ?? ""

  return (
    <main className="min-h-screen flex flex-col bg-background">
      <Navbar schoolName={appConfig?.campus ?? ""} status={status} />

      <div className="flex-1 overflow-y-auto pt-14 pb-[calc(3.5rem+max(0.35rem,env(safe-area-inset-bottom)))]">
        <div className="mx-auto max-w-2xl px-4 py-6 space-y-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Bus className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-foreground tracking-tight">Schedule</h1>
              <p className="text-sm text-muted-foreground">
                Routes and stops come from the live API configuration.
              </p>
            </div>
          </div>

          {loadError && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{loadError}</AlertDescription>
            </Alert>
          )}

          {loading && (
            <div className="flex items-center justify-center gap-2 py-16 text-muted-foreground">
              <Spinner className="h-5 w-5" />
              <span className="text-sm">Loading schedule…</span>
            </div>
          )}

          {!loading && schedule && (
            <>
              <ServiceHoursCard hours={schedule.hours} timeZone={schedule.timezone} />

              {schedule.routes.length === 0 ? (
                <Card className="shadow-sm">
                  <CardContent className="py-8 text-center text-sm text-muted-foreground">
                    No routes are configured.
                  </CardContent>
                </Card>
              ) : (
                <Tabs defaultValue={defaultRouteId} className="w-full gap-4">
                  <TabsList
                    className={cn(
                      "w-full h-auto flex-wrap justify-start gap-1 bg-muted/80 p-1",
                      schedule.routes.length === 1 && "hidden",
                    )}
                  >
                    {schedule.routes.map((r) => (
                      <TabsTrigger key={r.id} value={r.id} className="shrink-0">
                        {r.name}
                      </TabsTrigger>
                    ))}
                  </TabsList>

                  {schedule.routes.map((route) => (
                    <TabsContent key={route.id} value={route.id} className="space-y-4 mt-0">
                      {schedule.routes.length === 1 && (
                        <h2 className="text-lg font-semibold text-foreground px-0.5">
                          {route.name}
                        </h2>
                      )}

                      <Tabs defaultValue="loops" key={`${route.id}-view`} className="w-full gap-3">
                        <TabsList className="w-full grid grid-cols-2 h-9">
                          <TabsTrigger value="loops">By loop</TabsTrigger>
                          <TabsTrigger value="stops">By stop</TabsTrigger>
                        </TabsList>
                        <TabsContent value="loops" className="mt-3">
                          <RouteTripCards route={route} />
                        </TabsContent>
                        <TabsContent value="stops" className="mt-3">
                          <Card className="shadow-sm py-4 gap-3">
                            <CardHeader className="px-4 pb-0">
                              <CardTitle className="text-sm font-medium text-muted-foreground">
                                All times at each stop
                              </CardTitle>
                            </CardHeader>
                            <CardContent className="px-4 pt-2">
                              <RouteStopList route={route} />
                            </CardContent>
                          </Card>
                        </TabsContent>
                      </Tabs>
                    </TabsContent>
                  ))}
                </Tabs>
              )}
            </>
          )}
        </div>
      </div>
    </main>
  )
}
