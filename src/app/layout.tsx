import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Show Me Your TDs",
  description: "Where Sports N Shit becomes a battlefield",
  icons: {
    icon: [
      { url: "/favicon.svg", type: "image/svg+xml" },
      { url: "/favicon-32x32.png", type: "image/png", sizes: "32x32" },
      { url: "/favicon-16x16.png", type: "image/png", sizes: "16x16" }
    ],
    apple: "/apple-touch-icon.png"
  },
  openGraph: {
    title: "Show Me Your TDs",
    description: "Where Sports N Shit becomes a battlefield",
    type: "website",
    url: "https://ffleague-fc3c9309ff7b.herokuapp.com",
    siteName: "Show Me Your TDs",
  },
  twitter: {
    card: "summary",
    title: "Show Me Your TDs",
    description: "Where Sports N Shit becomes a battlefield",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
