import Link from "next/link";
import { Github } from "lucide-react";

export default function Footer() {
  return (
    <footer className="border-t border-gray-900 py-10 px-6">
      <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
        <div>
          <div className="text-sm font-semibold tracking-widest text-cyan-400 uppercase mb-1">
            NEXUS
          </div>
          <p className="text-xs text-gray-600">
            Local AI automation for macOS. MIT license.
          </p>
        </div>

        <nav className="flex flex-wrap gap-x-6 gap-y-2">
          {[
            { href: "/", label: "Home" },
            { href: "/about/", label: "About" },
            { href: "/docs/", label: "Docs" },
            { href: "/download/", label: "Download" },
          ].map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
            >
              {label}
            </Link>
          ))}
          <a
            href="https://github.com/nexus-ai/nexus"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-gray-500 hover:text-gray-300 transition-colors flex items-center gap-1"
          >
            <Github className="w-3.5 h-3.5" strokeWidth={1.5} />
            GitHub
          </a>
        </nav>
      </div>
    </footer>
  );
}
