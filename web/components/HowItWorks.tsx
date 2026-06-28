const steps = [
  {
    number: "01",
    title: "You type a command",
    description:
      "Press Cmd+Ctrl+Space to open the NEXUS Spotlight bar. Type any instruction in plain English — no special syntax required.",
  },
  {
    number: "02",
    title: "Claude Sonnet 4.6 plans the steps",
    description:
      "Your command is sent to Claude Sonnet 4.6, which breaks it into a concrete sequence of UI actions: clicks, keystrokes, waits, and reads.",
  },
  {
    number: "03",
    title: "NEXUS reads the screen via Accessibility API",
    description:
      "Each element is located using the macOS Accessibility tree — 30 to 80ms per element. No screenshots, no GPU, no network. Just the AX tree.",
  },
  {
    number: "04",
    title: "Falls back to local Qwen3-VL-8B when needed",
    description:
      "If an element isn't reachable via AX (a web canvas, a Qt app, a game), NEXUS switches to the local vision model running in Ollama — fully offline.",
  },
  {
    number: "05",
    title: "Each step verified by Claude Haiku 4.5",
    description:
      "Before moving on, Claude Haiku 4.5 checks the screen state to confirm the action succeeded. If it failed, NEXUS retries with adjusted parameters.",
  },
  {
    number: "06",
    title: "Done, or retried automatically",
    description:
      "On success, the result is reported and the sequence is saved to SQLite for faster replay. On persistent failure, NEXUS explains what it tried and where it stopped.",
  },
];

export default function HowItWorks() {
  return (
    <section
      id="how-it-works"
      className="py-28 px-6 border-t border-gray-900"
    >
      <div className="max-w-6xl mx-auto">
        <div className="mb-16 max-w-xl">
          <h2 className="text-3xl font-bold text-white mb-4">How it works</h2>
          <p className="text-gray-400 leading-relaxed">
            Every task runs through the same pipeline: plan, locate, act,
            verify. The loop repeats until the task is done or NEXUS determines
            it cannot proceed safely.
          </p>
        </div>

        <div className="space-y-0">
          {steps.map(({ number, title, description }, i) => (
            <div key={number} className="flex gap-8 group">
              {/* Step number + connector line */}
              <div className="flex flex-col items-center">
                <div className="w-10 h-10 rounded-full border border-gray-700 group-hover:border-cyan-500/50 flex items-center justify-center flex-shrink-0 transition-colors">
                  <span className="text-xs font-mono text-gray-500 group-hover:text-cyan-400 transition-colors">
                    {number}
                  </span>
                </div>
                {i < steps.length - 1 && (
                  <div className="w-px flex-1 bg-gray-800 my-1" />
                )}
              </div>

              {/* Content */}
              <div className="pb-10 pt-1.5">
                <h3 className="text-base font-semibold text-white mb-2">
                  {title}
                </h3>
                <p className="text-sm text-gray-400 leading-relaxed max-w-lg">
                  {description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
