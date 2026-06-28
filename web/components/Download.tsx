import { Github, Star } from "lucide-react";
import Link from "next/link";

export default function Download() {
  return (
    <section
      id="download"
      className="py-28 px-6 border-t border-gray-900"
    >
      <div className="max-w-6xl mx-auto">
        <div className="max-w-2xl">
          <div className="inline-block mb-6 px-3 py-1 rounded-full border border-cyan-500/30 bg-cyan-500/5 text-cyan-400 text-xs tracking-widest uppercase">
            Coming soon
          </div>

          <h2 className="text-3xl font-bold text-white mb-4">
            NEXUS is not released yet
          </h2>
          <p className="text-gray-400 leading-relaxed mb-10">
            The core automation loop is working. The release is being prepared
            now. Star the repository on GitHub to get notified the moment it
            ships — or leave your email on the download page to join the
            waitlist.
          </p>

          <div className="flex flex-col sm:flex-row gap-4">
            <Link
              href="/download/"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-black font-semibold text-sm transition-colors"
            >
              Join the waitlist
            </Link>
            <a
              href="https://github.com/nexus-ai/nexus"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg border border-gray-700 hover:border-gray-500 text-gray-300 hover:text-white font-medium text-sm transition-colors"
            >
              <Github className="w-4 h-4" strokeWidth={1.5} />
              Star on GitHub
              <Star className="w-3.5 h-3.5 text-gray-500" strokeWidth={1.5} />
            </a>
          </div>

          <p className="mt-6 text-xs text-gray-600">
            MIT license. Build from source at any time — see the{" "}
            <Link
              href="/docs/"
              className="text-gray-400 hover:text-cyan-400 underline underline-offset-2 transition-colors"
            >
              setup docs
            </Link>
            .
          </p>
        </div>
      </div>
    </section>
  );
}
