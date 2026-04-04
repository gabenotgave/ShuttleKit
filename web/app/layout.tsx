import type { Metadata } from 'next'
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

export const metadata: Metadata = {
  title: 'ShuttleKit',
  description: 'Campus shuttle planning system',
  generator: 'ShuttleKit',
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
  children: React.ReactNode
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
