import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import { Github, CheckCircle } from "lucide-react";
import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Download — NEXUS",
  description:
    "NEXUS is not yet released. Join the waitlist or build from source using the setup docs.",
};

const requirements = [
  "macOS 14 Sonoma or later",
  "Apple Silicon (M1 or later)",
  "16 GB RAM minimum, 32 GB recommended",
  "Ollama installed",
  "Anthropic API key",
  "~4 GB disk for Qwen3-VL-8B",
];

export default function DownloadPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <Nav />
      <main className="pt-14">
        <div className="max-w-2xl mx-auto px-6 py-20">
          {/* Coming soon header */}
          <div className="mb-12">
            <div className="inline-block mb-6 px-3 py-1 rounded-full border border-cyan-500/30 bg-cyan-500/5 text-cyan-400 text-xs tracking-widest uppercase">
              Not yet released
            </div>
            <h1 className="text-4xl font-bold text-white mb-4">
              NEXUS is coming soon
            </h1>
            <p className="text-gray-400 leading-relaxed">
              The core automation loop is functional and being tested. The first
              public release is being prepared now. Leave your email below to
              join the waitlist, or star the GitHub repo to get a notification
              when it ships.
            </p>
          </div>

          {/* Email waitlist */}
          <div className="mb-14 p-7 rounded-xl border border-gray-800 bg-gray-950">
            <h2 className="text-base font-semibold text-white mb-2">
              Join the waitlist
            </h2>
            <p className="text-sm text-gray-400 mb-5">
              You will get one email when NEXUS is publicly available. No
              newsletters, no marketing.
            </p>
            <div className="flex gap-3">
              <a
                href="mailto:nexus-waitlist@example.com?subject=NEXUS%20Waitlist&body=Please%20add%20me%20to%20the%20NEXUS%20waitlist."
                className="flex-1 inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-black font-semibold text-sm transition-colors"
              >
                Send waitlist request
              </a>
            </div>
            <p className="mt-3 text-xs text-gray-600">
              This opens your email client. Until a backend is wired up, email
              is the simplest approach.
            </p>
          </div>

          {/* GitHub */}
          <div className="mb-14 p-7 rounded-xl border border-gray-800 bg-gray-950">
            <h2 className="text-base font-semibold text-white mb-2">
              GitHub
            </h2>
            <p className="text-sm text-gray-400 mb-5">
              The repository is being prepared for public release. Starring it
              now will give you a GitHub notification the moment the first commit
              lands.
            </p>
            <a
              href="https://github.com/nexus-ai/nexus"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg border border-gray-700 hover:border-gray-500 text-gray-300 hover:text-white font-medium text-sm transition-colors"
            >
              <Github className="w-4 h-4" strokeWidth={1.5} />
              github.com/nexus-ai/nexus
            </a>
          </div>

          {/* Build from source */}
          <div className="mb-14 p-7 rounded-xl border border-gray-800 bg-gray-950">
            <h2 className="text-base font-semibold text-white mb-2">
              Build from source
            </h2>
            <p className="text-sm text-gray-400 mb-5">
              If you want to run NEXUS today and are comfortable with Python and
              the command line, the{" "}
              <Link
                href="/docs/"
                className="text-cyan-400 hover:text-cyan-300 underline underline-offset-2"
              >
                setup docs
              </Link>{" "}
              walk through every step: installing Ollama, pulling the model,
              cloning the repo, and granting macOS permissions.
            </p>
            <Link
              href="/docs/"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg border border-gray-700 hover:border-gray-500 text-gray-300 hover:text-white font-medium text-sm transition-colors"
            >
              Read the setup docs
            </Link>
          </div>

          {/* System requirements */}
          <div>
            <h2 className="text-base font-semibold text-white mb-5">
              System requirements
            </h2>
            <div className="rounded-xl border border-gray-800 overflow-hidden">
              {requirements.map((req, i) => (
                <div
                  key={req}
                  className={`flex items-center gap-3 px-5 py-3.5 ${
                    i < requirements.length - 1
                      ? "border-b border-gray-800"
                      : ""
                  }`}
                >
                  <CheckCircle
                    className="w-4 h-4 text-cyan-500 flex-shrink-0"
                    strokeWidth={2}
                  />
                  <span className="text-sm text-gray-300">{req}</span>
                </div>
              ))}
            </div>
            <p className="mt-4 text-xs text-gray-600">
              Intel Macs are not supported. iOS and iPadOS are not supported.
            </p>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
