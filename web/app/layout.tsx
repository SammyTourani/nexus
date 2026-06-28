import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "NEXUS — AI automation for macOS",
  description:
    "NEXUS is a local macOS AI agent that automates your computer with plain English. Uses a hybrid accessibility tree + local vision model, with Claude Sonnet 4.6 for planning. Your data never leaves your machine.",
  openGraph: {
    title: "NEXUS — AI automation for macOS",
    description:
      "Automate your Mac with plain English. NEXUS watches your screen, understands your intent, and acts — using local AI that never leaves your machine.",
    type: "website",
    siteName: "NEXUS",
  },
  twitter: {
    card: "summary_large_image",
    title: "NEXUS — AI automation for macOS",
    description:
      "Automate your Mac with plain English. Local AI, no cloud, no data sharing.",
  },
  keywords: [
    "macOS automation",
    "AI agent",
    "local AI",
    "accessibility automation",
    "Ollama",
    "Claude",
    "open source",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`dark ${inter.variable}`}>
      <body className="min-h-screen bg-[#0a0a0a] text-gray-100 font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
