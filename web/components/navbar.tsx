"use client"

import { Bus } from "lucide-react"
import { ShuttleStatus } from "../lib/shuttle-api"

interface NavbarProps {
  schoolName?: string
  status?: ShuttleStatus | null
}

export function Navbar({ schoolName = "", status }: NavbarProps) {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-border">
      <div className="flex items-center gap-3 px-4 h-14">
        <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-primary">
          <Bus className="w-5 h-5 text-primary-foreground" />
        </div>
        <div className="flex items-baseline gap-1.5">
          <span className="font-semibold text-lg text-foreground">{schoolName}</span>
          <span className="text-muted-foreground text-sm font-medium">ShuttleKit</span>
        </div>
        {status != null && (
          <div className="flex items-center gap-1.5 ml-2">
            <span
              className="inline-block w-2 h-2 rounded-full"
              style={{ backgroundColor: status.active ? "#22c55e" : "#ef4444" }}
            />
            <span className="text-sm text-muted-foreground">
              {status.active ? "Running" : status.message}
            </span>
          </div>
        )}
      </div>
    </nav>
  )
}
