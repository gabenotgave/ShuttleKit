"use client"

import { ShuttleStatus } from "../lib/shuttle-api"

interface NavbarProps {
  schoolName?: string
  status?: ShuttleStatus | null
}

function statusShort(status: ShuttleStatus): string {
  if (status.active) return "Running"
  return "Not running"
}

export function Navbar({ schoolName = "", status }: NavbarProps) {
  return (
    <nav className="fixed top-[var(--sk-disruption-banner,0px)] left-0 right-0 z-50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-border">
      <div className="flex h-14 items-center gap-2 px-3 sm:gap-3 sm:px-4">
        <div className="flex min-w-0 flex-1 items-center gap-2 sm:gap-3">
          <img
            src="/ShuttleKit_Icon_Black.png"
            alt="ShuttleKit"
            width={40}
            height={40}
            className="h-10 w-10 shrink-0 rounded-lg object-contain"
            fetchPriority="high"
            decoding="async"
          />
          <div className="min-w-0 flex-1">
            <div className="flex items-baseline gap-x-1.5 gap-y-0">
              <span className="truncate text-base font-semibold text-foreground sm:text-lg">
                {schoolName}
              </span>
              <span className="shrink-0 text-xs font-medium text-muted-foreground sm:text-sm">
                ShuttleKit
              </span>
            </div>
          </div>
        </div>
        {status != null && (
          <div className="flex shrink-0 items-center gap-1.5">
            <span
              className="inline-block h-2 w-2 shrink-0 rounded-full"
              style={{ backgroundColor: status.active ? "#22c55e" : "#ef4444" }}
            />
            <span className="text-xs leading-tight text-muted-foreground sm:text-sm">
              <span className="sm:hidden">{statusShort(status)}</span>
              <span className="hidden sm:inline">
                {status.active ? "Running" : status.message}
              </span>
            </span>
          </div>
        )}
      </div>
    </nav>
  )
}
