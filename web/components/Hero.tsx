"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

const COMMANDS = [
  "Search flights to Tokyo next week",
  "Move all PDFs from Downloads to Documents",
  "Reply to my last unread email",
  "Find all screenshots taken today and zip them",
  "Open Spotify and play my Discover Weekly",
  "Rename every file in this folder to snake_case",
];

export default function Hero() {
  const [commandIndex, setCommandIndex] = useState(0);
  const [displayText, setDisplayText] = useState("");
  const [phase, setPhase] = useState<"typing" | "holding" | "erasing">(
    "typing"
  );
  const [charIndex, setCharIndex] = useState(0);

  useEffect(() => {
    const current = COMMANDS[commandIndex];

    if (phase === "typing") {
      if (charIndex < current.length) {
        const t = setTimeout(() => {
          setDisplayText(current.slice(0, charIndex + 1));
          setCharIndex((c) => c + 1);
        }, 38);
        return () => clearTimeout(t);
      } else {
        const t = setTimeout(() => setPhase("holding"), 1800);
        return () => clearTimeout(t);
      }
    }

    if (phase === "holding") {
      const t = setTimeout(() => setPhase("erasing"), 600);
      return () => clearTimeout(t);
    }

    if (phase === "erasing") {
      if (charIndex > 0) {
        const t = setTimeout(() => {
          setDisplayText(current.slice(0, charIndex - 1));
          setCharIndex((c) => c - 1);
        }, 18);
        return () => clearTimeout(t);
      } else {
        setCommandIndex((i) => (i + 1) % COMMANDS.length);
        setPhase("typing");
      }
    }
  }, [phase, charIndex, commandIndex]);

  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center px-6 pt-14 overflow-hidden">
      {/* Subtle radial glow behind content */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 70% 50% at 50% 40%, rgba(6,182,212,0.06) 0%, transparent 70%)",
        }}
      />

      <div className="relative z-10 max-w-3xl mx-auto text-center">
        <div className="inline-block mb-8 px-3 py-1 rounded-full border border-cyan-500/30 bg-cyan-500/5 text-cyan-400 text-xs tracking-widest uppercase">
          Pre-launch — join the waitlist
        </div>

        <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight leading-tight mb-6 text-white">
          Automate your Mac
          <br />
          <span className="text-cyan-400">with plain English.</span>
        </h1>

        <p className="text-lg sm:text-xl text-gray-400 leading-relaxed mb-12 max-w-2xl mx-auto">
          NEXUS watches your screen, understands your intent, and acts — using
          local AI that never leaves your machine.
        </p>

        {/* Terminal block */}
        <div className="mx-auto max-w-xl mb-12">
          <div className="rounded-xl border border-gray-800 bg-gray-950/80 overflow-hidden shadow-2xl">
            <div className="flex items-center gap-1.5 px-4 py-3 border-b border-gray-800">
              <div className="w-3 h-3 rounded-full bg-red-500/60" />
              <div className="w-3 h-3 rounded-full bg-yellow-500/60" />
              <div className="w-3 h-3 rounded-full bg-green-500/60" />
              <span className="ml-3 text-xs text-gray-600">
                NEXUS — Cmd+Ctrl+Space
              </span>
            </div>
            <div className="px-5 py-5 min-h-[60px] flex items-center">
              <span className="text-cyan-400 text-sm mr-2 select-none">
                &gt;
              </span>
              <span className="text-gray-200 text-sm font-mono">
                {displayText}
              </span>
              <span className="ml-0.5 inline-block w-[2px] h-4 bg-cyan-400 align-middle animate-[blink_1s_step-end_infinite]" />
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/download/"
            className="px-7 py-3 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-black font-semibold text-sm transition-colors"
          >
            Get early access
          </Link>
          <a
            href="#features"
            className="px-7 py-3 rounded-lg border border-gray-700 hover:border-gray-500 text-gray-300 hover:text-white font-medium text-sm transition-colors"
          >
            See how it works
          </a>
        </div>
      </div>

      {/* Fade to next section */}
      <div className="absolute bottom-0 left-0 right-0 h-24 pointer-events-none bg-gradient-to-t from-[#0a0a0a] to-transparent" />

      <style>{`
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
      `}</style>
    </section>
  );
}
