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
    icon: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🏈</text></svg>",
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
