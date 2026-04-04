import type { ReactNode } from "react"
import { redirect } from "next/navigation"
import { getCachedFeatureFlags } from "@/lib/feature-flags-server"

export default async function ChatLayout({
  children,
}: Readonly<{
  children: ReactNode
}>) {
  const features = await getCachedFeatureFlags()
  if (!features.chatbot) {
    redirect("/")
  }

  return <>{children}</>
}
