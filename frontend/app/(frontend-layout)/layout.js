import ClientSessionProvider from '@/components/providers/SessionProvider'
import { Geist, Geist_Mono } from 'next/font/google'
import '../globals.css'
import MainLayout from './MainLayout'
import { metadata } from '../metadata'

// 字體設定
const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
})

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
})

export { metadata }
// Root Layout
export default function RootLayout({ children }) {
  return (
    <html lang="zh-TW">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Kanit:wght@400;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <ClientSessionProvider>
          <MainLayout>
            {children}
          </MainLayout>
        </ClientSessionProvider>
      </body>
    </html>
  )
}
