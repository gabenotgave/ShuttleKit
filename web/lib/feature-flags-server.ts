import { cache } from "react"

import { getFeatures, type FeatureFlags } from "@/lib/shuttle-api"

/** Server-only: one memoized GET /api/features per RSC request (shared by root + /chat layouts). */
export const getCachedFeatureFlags = cache(async (): Promise<FeatureFlags> => {
  try {
    return await getFeatures({ next: { revalidate: false } })
  } catch {
    // Build-time prerender and offline dev: backend may be unavailable.
    return { chatbot: true }
  }
})
