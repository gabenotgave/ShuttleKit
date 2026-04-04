import { cache } from "react"

import { getFeatures, type FeatureFlags } from "@/lib/shuttle-api"

/** Server-only: one memoized GET /api/features per RSC request (shared by root + /chat layouts). */
export const getCachedFeatureFlags = cache(
  async (): Promise<FeatureFlags> =>
    getFeatures({ next: { revalidate: false } }),
)
