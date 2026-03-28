"use client"

import { useCallback, useState, useEffect } from "react"
import { GoogleMap, useJsApiLoader, Marker, OverlayView } from "@react-google-maps/api"
import { type PlanResponse } from "@/lib/shuttle-api"

const containerStyle = {
  width: "100%",
  height: "100%",
}

const mapOptions: google.maps.MapOptions = {
  disableDefaultUI: true,
  zoomControl: true,
  mapTypeControl: false,
  streetViewControl: false,
  fullscreenControl: false,
  styles: [
    {
      featureType: "poi",
      elementType: "labels",
      stylers: [{ visibility: "off" }],
    },
  ],
}

interface MapDisplayProps {
  plan: PlanResponse | null
  userLocation: { lat: number; lng: number } | null
  mapCenter: { lat: number; lng: number } | null
}

export function MapDisplay({ plan, userLocation, mapCenter }: MapDisplayProps) {
  const [map, setMap] = useState<google.maps.Map | null>(null)

  const { isLoaded, loadError } = useJsApiLoader({
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || "",
    libraries: ["places"],
  })

  const onLoad = useCallback((map: google.maps.Map) => {
    setMap(map)
  }, [])

  const onUnmount = useCallback(() => {
    setMap(null)
  }, [])

  // Fit bounds when plan changes
  useEffect(() => {
    if (map && plan && plan.legs.length > 0) {
      const bounds = new google.maps.LatLngBounds()
      plan.legs.forEach((leg) => {
        bounds.extend({ lat: leg.from.coords[0], lng: leg.from.coords[1] })
        bounds.extend({ lat: leg.to.coords[0], lng: leg.to.coords[1] })
      })
      map.fitBounds(bounds, 80)
    }
  }, [map, plan])

  if (loadError) {
    return (
      <div className="flex items-center justify-center h-full bg-muted">
        <p className="text-muted-foreground">Error loading maps</p>
      </div>
    )
  }

  if (!isLoaded) {
    return (
      <div className="flex items-center justify-center h-full bg-muted">
        <p className="text-muted-foreground">Loading map...</p>
      </div>
    )
  }

  // Get unique stop points for custom markers
  const stops = plan
    ? plan.legs.reduce<Array<{ lat: number; lng: number; name: string; type: string }>>((acc, leg, index) => {
        if (index === 0) {
          acc.push({
            lat: leg.from.coords[0],
            lng: leg.from.coords[1],
            name: leg.from.name,
            type: "start",
          })
        }
        acc.push({
          lat: leg.to.coords[0],
          lng: leg.to.coords[1],
          name: leg.to.name,
          type: index === plan.legs.length - 1 ? "end" : "stop",
        })
        return acc
      }, [])
    : []

  return (
    <GoogleMap
      mapContainerStyle={containerStyle}
      center={userLocation ?? mapCenter ?? { lat: 0, lng: 0 }}
      zoom={15}
      onLoad={onLoad}
      onUnmount={onUnmount}
      options={mapOptions}
    >
      {/* Stop markers */}
      {stops.map((stop, index) => (
        <Marker
          key={index}
          position={{ lat: stop.lat, lng: stop.lng }}
          icon={{
            path: google.maps.SymbolPath.CIRCLE,
            scale: stop.type === "start" || stop.type === "end" ? 10 : 7,
            fillColor:
              stop.type === "start"
                ? "#22c55e"
                : stop.type === "end"
                ? "#ef4444"
                : "#3b82f6",
            fillOpacity: 1,
            strokeColor: "#ffffff",
            strokeWeight: 2,
          }}
        />
      ))}

      {/* Stop labels via OverlayView — no chrome, no whitespace */}
      {stops.map((stop, index) => (
        <OverlayView
          key={`label-${index}`}
          position={{ lat: stop.lat, lng: stop.lng }}
          mapPaneName={OverlayView.OVERLAY_MOUSE_TARGET}
          getPixelPositionOffset={(_w, h) => ({ x: 14, y: -(h / 2) - 12 })}
        >
          <div style={{
            display: "inline-block",
            background: "white",
            borderRadius: "6px",
            padding: "3px 8px",
            fontSize: "12px",
            fontWeight: 600,
            color: "#111",
            whiteSpace: "nowrap",
            boxShadow: "0 1px 4px rgba(0,0,0,0.25)",
            pointerEvents: "none",
          }}>
            {stop.type === "start" ? "📍 " : stop.type === "end" ? "🏁 " : "🚌 "}
            {stop.name}
          </div>
        </OverlayView>
      ))}

      {/* User location marker with label */}
      {userLocation && !plan && (
        <>
          <Marker
            position={userLocation}
            icon={{
              path: google.maps.SymbolPath.CIRCLE,
              scale: 8,
              fillColor: "#3b82f6",
              fillOpacity: 1,
              strokeColor: "#ffffff",
              strokeWeight: 2,
            }}
          />
          <OverlayView
            position={userLocation}
            mapPaneName={OverlayView.OVERLAY_MOUSE_TARGET}
            getPixelPositionOffset={(_w, h) => ({ x: 14, y: -(h / 2) - 12 })}
          >
            <div style={{
              display: "inline-block",
              background: "white",
              borderRadius: "6px",
              padding: "3px 8px",
              fontSize: "12px",
              fontWeight: 600,
              color: "#111",
              whiteSpace: "nowrap",
              boxShadow: "0 1px 4px rgba(0,0,0,0.25)",
              pointerEvents: "none",
            }}>
              📍 Your location
            </div>
          </OverlayView>
        </>
      )}

    </GoogleMap>
  )
}
