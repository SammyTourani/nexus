"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Home" },
  { href: "/about/", label: "About" },
  { href: "/docs/", label: "Docs" },
  { href: "/download/", label: "Download" },
];

export default function Nav() {
  const pathname = usePathname();

  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-gray-800 bg-[#0a0a0a]/90 backdrop-blur-sm">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link
          href="/"
          className="text-sm font-semibold tracking-widest text-cyan-400 uppercase"
        >
          NEXUS
        </Link>

        <nav className="flex items-center gap-1">
          {links.map(({ href, label }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={`px-3 py-1.5 text-sm rounded transition-colors ${
                  active
                    ? "text-white bg-gray-800"
                    : "text-gray-400 hover:text-white hover:bg-gray-900"
                }`}
              >
                {label}
              </Link>
            );
          })}
          <a
            href="https://github.com/nexus-ai/nexus"
            target="_blank"
            rel="noopener noreferrer"
            className="ml-3 px-3 py-1.5 text-sm rounded border border-gray-700 text-gray-400 hover:text-white hover:border-gray-500 transition-colors"
          >
            GitHub
          </a>
        </nav>
      </div>
    </header>
  );
}
