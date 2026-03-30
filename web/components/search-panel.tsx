"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { MapPin, Navigation, Search, Loader2, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { getStops, type Stop } from "@/lib/shuttle-api"

export type CombinedSuggestion =
  | { kind: "stop"; stop: Stop }
  | { kind: "address"; prediction: google.maps.places.AutocompletePrediction }

export function filterStops(query: string, stops: Stop[]): Stop[] {
  if (!query) return []
  const lower = query.toLowerCase()
  return stops.filter((s) => s.name.toLowerCase().includes(lower)).slice(0, 6)
}

interface SearchPanelProps {
  onSearch: (
    from: { lat: number; lng: number; name: string },
    to: { lat: number; lng: number; name: string }
  ) => void
  isLoading: boolean
  isLoaded: boolean
  loadError: Error | undefined
}

export function SearchPanel({ onSearch, isLoading, isLoaded, loadError: _loadError }: SearchPanelProps) {
  const [stops, setStops] = useState<Stop[]>([])
  const [fromText, setFromText] = useState("")
  const [toText, setToText] = useState("")
  const [fromCoords, setFromCoords] = useState<{ lat: number; lng: number } | null>(null)
  const [toCoords, setToCoords] = useState<{ lat: number; lng: number } | null>(null)
  const [gettingLocation, setGettingLocation] = useState(false)
  const [fromSuggestions, setFromSuggestions] = useState<CombinedSuggestion[]>([])
  const [toSuggestions, setToSuggestions] = useState<CombinedSuggestion[]>([])
  const [showFromDropdown, setShowFromDropdown] = useState(false)
  const [showToDropdown, setShowToDropdown] = useState(false)

  // 5.1 — service refs
  const acServiceRef = useRef<google.maps.places.AutocompleteService | null>(null)
  const placesServiceRef = useRef<google.maps.places.PlacesService | null>(null)
  const sessionTokenRef = useRef<google.maps.places.AutocompleteSessionToken | null>(null)
  const mapDivRef = useRef<HTMLDivElement | null>(null)

  // debounce timer ref
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    getStops().then((stopsMap) => setStops(Object.values(stopsMap)))
  }, [])

  // 5.2 — initialize services when Maps API is ready
  useEffect(() => {
    if (!isLoaded || !mapDivRef.current) return
    acServiceRef.current = new google.maps.places.AutocompleteService()
    placesServiceRef.current = new google.maps.places.PlacesService(mapDivRef.current)
    sessionTokenRef.current = new google.maps.places.AutocompleteSessionToken()
  }, [isLoaded])

  // 5.3 — debounced query handler (300 ms)
  const handleQueryChange = useCallback(
    (query: string, field: "from" | "to") => {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current)

      debounceTimerRef.current = setTimeout(() => {
        const stopMatches = filterStops(query, stops)
        const stopSuggestions: CombinedSuggestion[] = stopMatches.map((stop) => ({ kind: "stop", stop }))

        if (acServiceRef.current && query.trim()) {
          acServiceRef.current.getPlacePredictions(
            { input: query, sessionToken: sessionTokenRef.current ?? undefined },
            (predictions, status) => {
              const addressSuggestions: CombinedSuggestion[] =
                status === google.maps.places.PlacesServiceStatus.OK && predictions
                  ? predictions.slice(0, 6).map((prediction) => ({ kind: "address", prediction }))
                  : []

              const combined = [...stopSuggestions, ...addressSuggestions]
              if (field === "from") {
                setFromSuggestions(combined)
                setShowFromDropdown(combined.length > 0)
              } else {
                setToSuggestions(combined)
                setShowToDropdown(combined.length > 0)
              }
            }
          )
        } else {
          if (field === "from") {
            setFromSuggestions(stopSuggestions)
            setShowFromDropdown(stopSuggestions.length > 0)
          } else {
            setToSuggestions(stopSuggestions)
            setShowToDropdown(stopSuggestions.length > 0)
          }
        }
      }, 300)
    },
    [stops]
  )

  // 5.4 — handle address prediction selection
  const handleAddressSelect = useCallback(
    (prediction: google.maps.places.AutocompletePrediction, field: "from" | "to") => {
      if (!placesServiceRef.current) return

      placesServiceRef.current.getDetails(
        {
          placeId: prediction.place_id,
          fields: ["geometry", "formatted_address", "name"],
          sessionToken: sessionTokenRef.current ?? undefined,
        },
        (result, status) => {
          if (status !== google.maps.places.PlacesServiceStatus.OK || !result?.geometry?.location) {
            return
          }

          const text = result.formatted_address ?? result.name ?? ""
          const coords = {
            lat: result.geometry.location.lat(),
            lng: result.geometry.location.lng(),
          }

          // reset session token for next billing session
          sessionTokenRef.current = new google.maps.places.AutocompleteSessionToken()

          if (field === "from") {
            setFromText(text)
            setFromCoords(coords)
            setShowFromDropdown(false)
          } else {
            setToText(text)
            setToCoords(coords)
            setShowToDropdown(false)
          }
        }
      )
    },
    []
  )

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
    setFromSuggestions([])
    setToSuggestions([])
    setShowFromDropdown(false)
    setShowToDropdown(false)
  }

  const canSubmit = Boolean(fromCoords && toCoords)

  return (
    <>
      {/* Invisible div required to construct PlacesService */}
      <div ref={mapDivRef} style={{ display: "none" }} />

      <Card className="fixed top-18 left-4 right-4 z-40 p-4 shadow-lg md:left-4 md:right-auto md:w-96">
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="space-y-2">
            {/* Origin */}
            <div className="relative">
              <div className="relative">
                <Navigation className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-emerald-600 pointer-events-none z-10" />
                <input
                  type="text"
                  placeholder="Starting point"
                  value={fromText}
                  onChange={(e) => {
                    setFromText(e.target.value)
                    setFromCoords(null)
                    handleQueryChange(e.target.value, "from")
                  }}
                  onBlur={() => setShowFromDropdown(false)}
                  className="w-full pl-10 pr-10 h-10 rounded-md border border-input bg-background text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                />
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
              {showFromDropdown && fromSuggestions.length > 0 && (
                <ul className="absolute top-full left-0 right-0 z-50 mt-1 max-h-60 overflow-y-auto rounded-md border bg-white shadow-md">
                  {fromSuggestions.some((s) => s.kind === "stop") && (
                    <li className="px-3 py-1 text-xs text-muted-foreground uppercase tracking-wide">Stops</li>
                  )}
                  {fromSuggestions.filter((s) => s.kind === "stop").map((s, i) => (
                    <li
                      key={`from-stop-${i}`}
                      className="px-3 py-2 text-sm cursor-pointer hover:bg-accent"
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={() => {
                        const stop = (s as { kind: "stop"; stop: Stop }).stop
                        setFromText(stop.name)
                        setFromCoords({ lat: stop.coords[0], lng: stop.coords[1] })
                        setShowFromDropdown(false)
                        sessionTokenRef.current = new google.maps.places.AutocompleteSessionToken()
                      }}
                    >
                      {(s as { kind: "stop"; stop: Stop }).stop.name}
                    </li>
                  ))}
                  {fromSuggestions.some((s) => s.kind === "address") && (
                    <li className="px-3 py-1 text-xs text-muted-foreground uppercase tracking-wide">Addresses</li>
                  )}
                  {fromSuggestions.filter((s) => s.kind === "address").map((s, i) => (
                    <li
                      key={`from-addr-${i}`}
                      className="px-3 py-2 text-sm cursor-pointer hover:bg-accent"
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={() => {
                        handleAddressSelect(
                          (s as { kind: "address"; prediction: google.maps.places.AutocompletePrediction }).prediction,
                          "from"
                        )
                      }}
                    >
                      {(s as { kind: "address"; prediction: google.maps.places.AutocompletePrediction }).prediction.description}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Destination */}
            <div className="relative">
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-red-500 pointer-events-none z-10" />
                <input
                  type="text"
                  placeholder="Destination"
                  value={toText}
                  onChange={(e) => {
                    setToText(e.target.value)
                    setToCoords(null)
                    handleQueryChange(e.target.value, "to")
                  }}
                  onBlur={() => setShowToDropdown(false)}
                  className="w-full pl-10 h-10 rounded-md border border-input bg-background text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                />
              </div>
              {showToDropdown && toSuggestions.length > 0 && (
                <ul className="absolute top-full left-0 right-0 z-50 mt-1 max-h-60 overflow-y-auto rounded-md border bg-white shadow-md">
                  {toSuggestions.some((s) => s.kind === "stop") && (
                    <li className="px-3 py-1 text-xs text-muted-foreground uppercase tracking-wide">Stops</li>
                  )}
                  {toSuggestions.filter((s) => s.kind === "stop").map((s, i) => (
                    <li
                      key={`to-stop-${i}`}
                      className="px-3 py-2 text-sm cursor-pointer hover:bg-accent"
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={() => {
                        const stop = (s as { kind: "stop"; stop: Stop }).stop
                        setToText(stop.name)
                        setToCoords({ lat: stop.coords[0], lng: stop.coords[1] })
                        setShowToDropdown(false)
                        sessionTokenRef.current = new google.maps.places.AutocompleteSessionToken()
                      }}
                    >
                      {(s as { kind: "stop"; stop: Stop }).stop.name}
                    </li>
                  ))}
                  {toSuggestions.some((s) => s.kind === "address") && (
                    <li className="px-3 py-1 text-xs text-muted-foreground uppercase tracking-wide">Addresses</li>
                  )}
                  {toSuggestions.filter((s) => s.kind === "address").map((s, i) => (
                    <li
                      key={`to-addr-${i}`}
                      className="px-3 py-2 text-sm cursor-pointer hover:bg-accent"
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={() => {
                        handleAddressSelect(
                          (s as { kind: "address"; prediction: google.maps.places.AutocompletePrediction }).prediction,
                          "to"
                        )
                      }}
                    >
                      {(s as { kind: "address"; prediction: google.maps.places.AutocompletePrediction }).prediction.description}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          <div className="flex gap-2">
            <Button type="submit" className="flex-1 cursor-pointer" disabled={!canSubmit || isLoading || gettingLocation}>
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
    </>
  )
}
