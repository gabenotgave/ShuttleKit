"use client"

import { useState, useEffect } from "react"
import { Navbar } from "@/components/navbar"
import { SearchPanel } from "@/components/search-panel"
import { ItineraryPanel } from "@/components/itinerary-panel"
import { MapDisplay } from "@/components/map-display"
import { planTrip, isPlanError, getStatus, getConfig, type PlanResponse, type ShuttleStatus, type AppConfig } from "@/lib/shuttle-api"
import { AlertCircle } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"

export default function Home() {
  const [plan, setPlan] = useState<PlanResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(null)
  const [status, setStatus] = useState<ShuttleStatus | null>(null)
  const [appConfig, setAppConfig] = useState<AppConfig | null>(null)

  // Fetch shuttle status and config on mount
  useEffect(() => {
    getStatus().then(setStatus)
    getConfig().then((config) => {
      setAppConfig(config)
      // Update document title with campus name
      if (config?.campus) {
        document.title = `${config.campus} ShuttleKit`
      }
    })
  }, [])

  // Get user location on mount
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude,
          })
        },
        () => {
          // Fall back to map center from config if available, otherwise null
          if (appConfig) setUserLocation(appConfig.map_center)
        }
      )
    }
  }, [appConfig])

  const handleSearch = async (
    from: { lat: number; lng: number; name: string },
    to: { lat: number; lng: number; name: string }
  ) => {
    setIsLoading(true)
    setError(null)

    try {
      const result = await planTrip(from.lat, from.lng, to.lat, to.lng)
      
      if (isPlanError(result)) {
        setError(result.message)
        setPlan(null)
      } else {
        setPlan(result)
      }
    } catch {
      setError("Failed to plan trip. Please try again.")
      setPlan(null)
    } finally {
      setIsLoading(false)
    }
  }

  const handleClearPlan = () => {
    setPlan(null)
    setError(null)
  }

  return (
    <main className="relative h-screen w-full">
      <Navbar schoolName={appConfig?.campus ?? ""} status={status} />
      
      {/* Map fills the screen; bottom inset leaves room for tab bar + safe area */}
      <div className="absolute inset-0 pt-14 pb-[calc(3.5rem+max(0.35rem,env(safe-area-inset-bottom)))]">
        <MapDisplay plan={plan} userLocation={userLocation} mapCenter={appConfig?.map_center ?? null} />
      </div>

      {/* Search panel overlays the map */}
      <SearchPanel onSearch={handleSearch} isLoading={isLoading} />

      {/* Error alert */}
      {error && (
        <Alert variant="destructive" className="fixed top-36 left-4 right-4 z-40 md:left-4 md:right-auto md:w-96">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Itinerary panel at bottom */}
      {plan && <ItineraryPanel plan={plan} onClose={handleClearPlan} />}
    </main>
  )
}
