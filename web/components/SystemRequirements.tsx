import { CheckCircle, AlertCircle } from "lucide-react";

const requirements = [
  {
    label: "macOS version",
    value: "macOS 14 Sonoma or later",
    required: true,
  },
  {
    label: "Architecture",
    value: "Apple Silicon (M1 or later)",
    required: true,
  },
  {
    label: "RAM",
    value: "16 GB minimum — 32 GB recommended",
    required: true,
  },
  {
    label: "Disk space",
    value: "~4 GB for Qwen3-VL-8B model weights",
    required: true,
  },
  {
    label: "Ollama",
    value: "Free local model runner — ollama.ai",
    required: true,
  },
  {
    label: "Anthropic API key",
    value: "Claude Sonnet 4.6 + Haiku 4.5, ~$0.01–0.05 per task",
    required: true,
  },
];

export default function SystemRequirements() {
  return (
    <section
      id="requirements"
      className="py-28 px-6 border-t border-gray-900"
    >
      <div className="max-w-6xl mx-auto">
        <div className="mb-16 max-w-xl">
          <h2 className="text-3xl font-bold text-white mb-4">
            System requirements
          </h2>
          <p className="text-gray-400 leading-relaxed">
            NEXUS runs a local vision model, so hardware matters. Intel Macs and
            iOS/iPadOS are not supported.
          </p>
        </div>

        <div className="max-w-2xl">
          <div className="rounded-xl border border-gray-800 overflow-hidden">
            {requirements.map(({ label, value }, i) => (
              <div
                key={label}
                className={`flex items-start gap-4 px-6 py-4 ${
                  i < requirements.length - 1 ? "border-b border-gray-800" : ""
                } hover:bg-gray-900/50 transition-colors`}
              >
                <CheckCircle
                  className="w-4 h-4 text-cyan-500 mt-0.5 flex-shrink-0"
                  strokeWidth={2}
                />
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-0.5">
                    {label}
                  </div>
                  <div className="text-sm text-gray-200">{value}</div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-5 flex items-start gap-3 px-5 py-4 rounded-lg border border-yellow-500/20 bg-yellow-500/5">
            <AlertCircle
              className="w-4 h-4 text-yellow-500/80 mt-0.5 flex-shrink-0"
              strokeWidth={2}
            />
            <p className="text-xs text-gray-400 leading-relaxed">
              The Anthropic API key is required for planning and verification.
              All screen reading and vision inference run entirely on your
              machine. No screen data is ever sent to Anthropic.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
