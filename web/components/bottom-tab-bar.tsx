"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Map, CalendarDays, MessageSquare } from "lucide-react"
import { cn } from "@/lib/utils"

const tabs = [
  { href: "/", label: "Map", icon: Map },
  { href: "/schedule", label: "Schedule", icon: CalendarDays },
  { href: "/chat", label: "Chat", icon: MessageSquare },
] as const

export function BottomTabBar() {
  const pathname = usePathname()
  if (pathname === "/admin" || pathname.startsWith("/admin/")) {
    return null
  }

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 pb-[max(0.35rem,env(safe-area-inset-bottom))]"
      aria-label="Primary"
    >
      <div className="mx-auto flex h-14 max-w-lg items-stretch justify-around px-2">
        {tabs.map(({ href, label, icon: Icon }) => {
          const active =
            href === "/"
              ? pathname === "/" || pathname === ""
              : pathname === href || pathname.startsWith(`${href}/`)
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex flex-1 flex-col items-center justify-center gap-0.5 rounded-lg text-xs font-medium transition-colors",
                active
                  ? "text-primary"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              <Icon className={cn("h-5 w-5", active && "stroke-[2.5]")} aria-hidden />
              <span>{label}</span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
