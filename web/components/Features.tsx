import { Eye, Brain, Database } from "lucide-react";

const features = [
  {
    icon: Eye,
    title: "Vision + Accessibility",
    description:
      "Reads your screen the fast way first: macOS Accessibility tree (30ms). Falls back to local Qwen3-VL-8B vision model only when needed — for web canvases, Qt apps, and anything the AX tree can't reach.",
  },
  {
    icon: Brain,
    title: "Thinks with Claude",
    description:
      "Task planning runs through Claude Sonnet 4.6 via Anthropic API. Every action is verified by Claude Haiku 4.5 before moving to the next step. One model plans, one model checks.",
  },
  {
    icon: Database,
    title: "Learns what works",
    description:
      "Successful task sequences are cached locally in SQLite. Repeat tasks run 10x faster — NEXUS remembers what worked and skips re-planning from scratch each time.",
  },
];

export default function Features() {
  return (
    <section id="features" className="py-28 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-16 max-w-xl">
          <h2 className="text-3xl font-bold text-white mb-4">
            Built around how macOS actually works
          </h2>
          <p className="text-gray-400 leading-relaxed">
            Most AI agents treat your screen as a pixel grid and fire off
            screenshots every second. NEXUS reads the accessibility tree
            directly — fast, deterministic, and private.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {features.map(({ icon: Icon, title, description }) => (
            <div
              key={title}
              className="rounded-xl border border-gray-800 bg-gray-950 p-7 hover:border-gray-700 transition-colors"
            >
              <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center mb-5">
                <Icon className="w-5 h-5 text-cyan-400" strokeWidth={1.5} />
              </div>
              <h3 className="text-base font-semibold text-white mb-3">
                {title}
              </h3>
              <p className="text-sm text-gray-400 leading-relaxed">
                {description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
