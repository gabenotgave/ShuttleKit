"use client"

import { useState } from "react"
import { ChevronUp, ChevronDown, Footprints, Bus, Clock, MapPin } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import type { PlanResponse, Leg } from "@/lib/shuttle-api"
import { formatHhmm12h } from "@/lib/time-format"

interface ItineraryPanelProps {
  plan: PlanResponse
  onClose: () => void
}

/** Format a minute count as "Xh Ym" or "Y min" */
function fmtDuration(minutes: number): string {
  const abs = Math.abs(minutes)
  if (abs < 60) return `${abs} min`
  const h = Math.floor(abs / 60)
  const m = abs % 60
  return m === 0 ? `${h}h` : `${h}h ${m}m`
}

function LegIcon({ type }: { type: "walk" | "shuttle" }) {
  if (type === "walk") {
    return (
      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-amber-100 text-amber-600">
        <Footprints className="w-4 h-4" />
      </div>
    )
  }
  return (
    <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary">
      <Bus className="w-4 h-4" />
    </div>
  )
}

function LegDetails({ leg, index }: { leg: Leg; index: number }) {
  const isWalk = leg.type === "walk"
  
  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center">
        <LegIcon type={leg.type} />
        {index < 2 && <div className="w-0.5 h-full bg-border mt-2" />}
      </div>
      <div className="flex-1 pb-4">
        <div className="flex items-center justify-between">
          <p className="font-medium text-foreground">{leg.description}</p>
          <span className="text-sm text-muted-foreground">
            {isWalk ? (
              fmtDuration(leg.duration_minutes)
            ) : (
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {formatHhmm12h(leg.departs)} – {formatHhmm12h(leg.arrives)}
              </span>
            )}
          </span>
        </div>
        <div className="flex items-center gap-1 mt-1 text-sm text-muted-foreground">
          <MapPin className="w-3 h-3" />
          <span>{leg.from.name}</span>
          <span className="mx-1">→</span>
          <span>{leg.to.name}</span>
        </div>
        {!isWalk && (
          <div className="flex gap-3 mt-2 text-xs">
            <span className="px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
              Wait: {fmtDuration(leg.wait_minutes)}
            </span>
            <span className="px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
              Ride: {fmtDuration(leg.ride_minutes)}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

export function ItineraryPanel({ plan, onClose }: ItineraryPanelProps) {
  const [expanded, setExpanded] = useState(true)

  return (
    <Card className="fixed left-0 right-0 z-40 rounded-b-none shadow-lg border-b-0 bottom-[calc(3.5rem+max(0.35rem,env(safe-area-inset-bottom)))]">
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div
          role="button"
          tabIndex={0}
          onClick={() => setExpanded(!expanded)}
          onKeyDown={(e) => e.key === "Enter" && setExpanded(!expanded)}
          className="flex items-center gap-3 flex-1 text-left cursor-pointer"
        >
          <div className="flex items-center justify-center w-10 h-10 rounded-full bg-primary text-primary-foreground">
            <Bus className="w-5 h-5" />
          </div>
          <div>
            <p className="font-semibold text-foreground">
              {fmtDuration(plan.total_minutes)} total
            </p>
            <p className="text-sm text-muted-foreground">
              Arrives at {formatHhmm12h(plan.arrives_at)}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={onClose}>
            Clear
          </Button>
          <div
            role="button"
            tabIndex={0}
            onClick={() => setExpanded(!expanded)}
            onKeyDown={(e) => e.key === "Enter" && setExpanded(!expanded)}
            className="p-1 cursor-pointer"
          >
            {expanded ? (
              <ChevronDown className="w-5 h-5 text-muted-foreground" />
            ) : (
              <ChevronUp className="w-5 h-5 text-muted-foreground" />
            )}
          </div>
        </div>
      </div>
      
      {expanded && (
        <div className="p-4 max-h-64 overflow-y-auto">
          {plan.legs.map((leg, index) => (
            <LegDetails key={index} leg={leg} index={index} />
          ))}
        </div>
      )}
    </Card>
  )
}
