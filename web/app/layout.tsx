import type { Metadata } from 'next'
import type { ReactNode } from 'react'
import { Geist, Geist_Mono } from 'next/font/google'
import { Analytics } from '@vercel/analytics/next'
import { BottomTabBar } from '@/components/bottom-tab-bar'
import { DisruptionBanner } from '@/components/disruption-banner'
import { getCachedFeatureFlags } from '@/lib/feature-flags-server'
import './globals.css'

const geistSans = Geist({
  subsets: ["latin"],
  variable: '--font-geist-sans',
});

const geistMono = Geist_Mono({
  subsets: ["latin"],
  variable: '--font-geist-mono',
});

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

async function getConfig(): Promise<{ campus: string; map_center: { lat: number; lng: number } } | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/config`, { next: { revalidate: 3600 } })
    if (!response.ok) return null
    return await response.json()
  } catch {
    return null
  }
}

export async function generateMetadata(): Promise<Metadata> {
  const config = await getConfig()

  const campus = config?.campus || 'Campus'
  const title = `${campus} ShuttleKit`
  const description = `Plan your shuttle trips around ${campus}. Find routes, schedules, and real-time shuttle information.`

  const metadataBase = new URL(
    process.env.NEXT_PUBLIC_SITE_URL ||
      (process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : 'http://localhost:3000'),
  )

  return {
    metadataBase,
    title,
    description,
    generator: 'ShuttleKit',
    keywords: [campus, 'shuttle', 'bus', 'transit', 'transportation', 'campus shuttle', 'college shuttle'],
    icons: {
      icon: '/ShuttleKit_Icon_Black.png',
      apple: '/ShuttleKit_Icon_Black.png',
    },
    openGraph: {
      title,
      description,
      type: 'website',
      siteName: 'ShuttleKit',
      images: [
        {
          url: '/ShuttleKit_Black.png',
          width: 2522,
          height: 1499,
          alt: 'ShuttleKit',
        },
      ],
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description,
      images: ['/ShuttleKit_Black.png'],
    },
    ...(config?.map_center && {
      other: {
        'geo.position': `${config.map_center.lat};${config.map_center.lng}`,
        'ICBM': `${config.map_center.lat}, ${config.map_center.lng}`,
        'geo.placename': campus,
      },
    }),
  }
}

async function chatbotFlagForShell(): Promise<boolean> {
  try {
    const features = await getCachedFeatureFlags()
    return features.chatbot
  } catch {
    return true
  }
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: ReactNode
}>) {
  const chatbotEnabled = await chatbotFlagForShell()

  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable} font-sans antialiased`}>
        <DisruptionBanner />
        {children}
        <BottomTabBar chatbotEnabled={chatbotEnabled} />
        <Analytics />
      </body>
    </html>
  )
}
