"use client"

import { useRef, useState } from "react"
import { Autocomplete, useJsApiLoader } from "@react-google-maps/api"
import { MapPin, Navigation, Search, Loader2, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"

const LIBRARIES: ["places"] = ["places"]

interface SearchPanelProps {
  onSearch: (
    from: { lat: number; lng: number; name: string },
    to: { lat: number; lng: number; name: string }
  ) => void
  isLoading: boolean
}

export function SearchPanel({ onSearch, isLoading }: SearchPanelProps) {
  const [fromText, setFromText] = useState("")
  const [toText, setToText] = useState("")
  const [fromCoords, setFromCoords] = useState<{ lat: number; lng: number } | null>(null)
  const [toCoords, setToCoords] = useState<{ lat: number; lng: number } | null>(null)
  const [gettingLocation, setGettingLocation] = useState(false)

  const fromAcRef = useRef<google.maps.places.Autocomplete | null>(null)
  const toAcRef = useRef<google.maps.places.Autocomplete | null>(null)

  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || "",
    libraries: LIBRARIES,
  })

  const handleFromPlaceChanged = () => {
    const place = fromAcRef.current?.getPlace()
    if (place?.geometry?.location) {
      setFromCoords({ lat: place.geometry.location.lat(), lng: place.geometry.location.lng() })
      setFromText(place.formatted_address ?? place.name ?? "")
    }
  }

  const handleToPlaceChanged = () => {
    const place = toAcRef.current?.getPlace()
    if (place?.geometry?.location) {
      setToCoords({ lat: place.geometry.location.lat(), lng: place.geometry.location.lng() })
      setToText(place.formatted_address ?? place.name ?? "")
    }
  }

  const handleUseCurrentLocation = () => {
    if (!navigator.geolocation) return
    setGettingLocation(true)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setFromCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude })
        setFromText("Current Location")
        setGettingLocation(false)
      },
      () => {
        alert("Unable to get your location. Please type an address instead.")
        setGettingLocation(false)
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    )
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!fromCoords || !toCoords) return
    onSearch({ ...fromCoords, name: fromText }, { ...toCoords, name: toText })
  }

  const handleClear = () => {
    setFromText("")
    setToText("")
    setFromCoords(null)
    setToCoords(null)
  }

  const canSubmit = !!fromCoords && !!toCoords

  return (
    <Card className="fixed top-18 left-4 right-4 z-40 p-4 shadow-lg md:left-4 md:right-auto md:w-96">
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="space-y-2">
          {/* Origin */}
          <div className="relative">
            <Navigation className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-emerald-600 pointer-events-none z-10" />
            {isLoaded ? (
              <Autocomplete
                onLoad={(ac) => { fromAcRef.current = ac }}
                onPlaceChanged={handleFromPlaceChanged}
              >
                <input
                  type="text"
                  placeholder="Starting point"
                  value={fromText}
                  onChange={(e) => { setFromText(e.target.value); setFromCoords(null) }}
                  className="w-full pl-10 pr-10 h-10 rounded-md border border-input bg-background text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                />
              </Autocomplete>
            ) : (
              <input
                type="text"
                placeholder="Starting point"
                value={fromText}
                onChange={(e) => setFromText(e.target.value)}
                className="w-full pl-10 pr-10 h-10 rounded-md border border-input bg-background text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              />
            )}
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
              onClick={handleUseCurrentLocation}
              disabled={gettingLocation}
              title="Use current location"
            >
              {gettingLocation ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <MapPin className="w-4 h-4 text-muted-foreground" />
              )}
            </Button>
          </div>

          {/* Destination */}
          <div className="relative">
            <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-red-500 pointer-events-none z-10" />
            {isLoaded ? (
              <Autocomplete
                onLoad={(ac) => { toAcRef.current = ac }}
                onPlaceChanged={handleToPlaceChanged}
              >
                <input
                  type="text"
                  placeholder="Destination"
                  value={toText}
                  onChange={(e) => { setToText(e.target.value); setToCoords(null) }}
                  className="w-full pl-10 h-10 rounded-md border border-input bg-background text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                />
              </Autocomplete>
            ) : (
              <input
                type="text"
                placeholder="Destination"
                value={toText}
                onChange={(e) => setToText(e.target.value)}
                className="w-full pl-10 h-10 rounded-md border border-input bg-background text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              />
            )}
          </div>
        </div>

        <div className="flex gap-2">
          <Button type="submit" className="flex-1 cursor-pointer" disabled={isLoading || gettingLocation || !canSubmit}>
            {isLoading || gettingLocation ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                {gettingLocation ? "Getting location..." : "Planning trip..."}
              </>
            ) : (
              <>
                <Search className="w-4 h-4 mr-2" />
                Plan Trip
              </>
            )}
          </Button>
          {(fromText || toText) && (
            <Button
              type="button"
              variant="outline"
              className="cursor-pointer"
              onClick={handleClear}
              disabled={isLoading || gettingLocation}
            >
              <X className="w-4 h-4" />
            </Button>
          )}
        </div>
      </form>
    </Card>
  )
}
