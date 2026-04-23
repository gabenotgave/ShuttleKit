"use client"

import { useEffect, useLayoutEffect, useRef, useState } from "react"
import { AlertTriangle } from "lucide-react"
import { getDisruptionsPublic, type DisruptionsPublic } from "@/lib/shuttle-api"
import { cn } from "@/lib/utils"

function summarize(rows: DisruptionsPublic["active"], label: string) {
  if (rows.length === 0) return null
  return (
    <p className="text-sm leading-snug">
      <span className="font-medium">{label}: </span>
      {rows.map((r, i) => (
        <span key={r.id || `${i}`}>
          {i > 0 ? " · " : ""}
          {r.message?.trim() || "Service disruption"}
          {r.route_id != null && r.route_id !== "" ? ` (${r.route_id})` : ""}
        </span>
      ))}
    </p>
  )
}

export function DisruptionBanner() {
  const [data, setData] = useState<DisruptionsPublic | null>(null)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    getDisruptionsPublic()
      .then(setData)
      .catch(() => setData({ active: [], upcoming: [] }))
  }, [])

  useLayoutEffect(() => {
    const el = ref.current
    const h = el?.offsetHeight ?? 0
    document.documentElement.style.setProperty(
      "--sk-disruption-banner",
      h ? `${h}px` : "0px",
    )
    return () => {
      document.documentElement.style.setProperty("--sk-disruption-banner", "0px")
    }
  }, [data])

  const has =
    data != null && (data.active.length > 0 || data.upcoming.length > 0)
  if (!has || data == null) return null

  return (
    <div
      ref={ref}
      role="status"
      className={cn(
        "fixed top-0 left-0 right-0 z-[60] border-b border-amber-500/40",
        "bg-amber-50 text-amber-950 dark:bg-amber-950/90 dark:text-amber-50",
      )}
    >
      <div className="mx-auto flex max-w-lg gap-2 px-3 py-2 sm:px-4">
        <AlertTriangle
          className="mt-0.5 h-4 w-4 shrink-0 text-amber-700 dark:text-amber-300"
          aria-hidden
        />
        <div className="min-w-0 space-y-1">
          {summarize(data.active, "Active")}
          {summarize(data.upcoming, "Upcoming")}
        </div>
      </div>
    </div>
  )
}
