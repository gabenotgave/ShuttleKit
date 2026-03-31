import type { Metadata } from 'next'
import type { ReactNode } from 'react'
import { Geist, Geist_Mono } from 'next/font/google'
import { Analytics } from '@vercel/analytics/next'
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
    return response.json()
  } catch {
    return null
  }
}

export async function generateMetadata(): Promise<Metadata> {
  const config = await getConfig()

  const campus = config?.campus || 'Campus'
  const title = `${campus} ShuttleKit`
  const description = `Plan your shuttle trips around ${campus}. Find routes, schedules, and real-time shuttle information.`

  return {
    title,
    description,
    generator: 'ShuttleKit',
    keywords: [campus, 'shuttle', 'bus', 'transit', 'transportation', 'campus shuttle', 'college shuttle'],
    icons: {
      icon: [
        {
          url: '/icon-light-32x32.png',
          media: '(prefers-color-scheme: light)',
        },
        {
          url: '/icon-dark-32x32.png',
          media: '(prefers-color-scheme: dark)',
        },
        {
          url: '/icon.svg',
          type: 'image/svg+xml',
        },
      ],
      apple: '/apple-icon.png',
    },
    openGraph: {
      title,
      description,
      type: 'website',
      siteName: 'ShuttleKit',
    },
    twitter: {
      card: 'summary',
      title,
      description,
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

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode
}>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable} font-sans antialiased`}>
        {children}
        <Analytics />
      </body>
    </html>
  )
}
