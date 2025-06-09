import { Geist, Geist_Mono } from "next/font/google";
import "../globals.css";
import DashboardLayout from "../../src/components/dashboard-layout/DashboardLayout";
import { metadata } from "app/metadata";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export { metadata }
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body
        style={{
          overflow: "hidden",
          height: "100vh",
        }}
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <DashboardLayout>{children}</DashboardLayout>
      </body>
    </html>
  );
}

