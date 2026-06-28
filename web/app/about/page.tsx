import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "About — NEXUS",
  description:
    "What NEXUS is, why it was built, how the hybrid architecture works, and what it can honestly do.",
};

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <Nav />
      <main className="pt-14">
        <div className="max-w-2xl mx-auto px-6 py-20">
          <div className="mb-12">
            <h1 className="text-4xl font-bold text-white mb-4">About NEXUS</h1>
            <p className="text-gray-400 leading-relaxed">
              A local macOS automation agent built by one developer, for
              developers and power users who want AI to work with their tools
              without handing their screen over to a cloud.
            </p>
          </div>

          <div className="space-y-14 text-sm text-gray-400 leading-relaxed">
            <section>
              <h2 className="text-base font-semibold text-white mb-4">
                What it is
              </h2>
              <p className="mb-4">
                NEXUS is a macOS daemon that sits in your menu bar and responds
                to a global hotkey (Cmd+Ctrl+Space). You type a task in plain
                English. NEXUS breaks it into steps, locates the relevant UI
                elements, executes them in sequence, and reports back.
              </p>
              <p>
                It is not a chatbot. It is not a productivity app. It is a
                system-level agent that drives your Mac the way a human would —
                clicking, typing, reading, and navigating — based on instructions
                you give it in natural language.
              </p>
            </section>

            <section>
              <h2 className="text-base font-semibold text-white mb-4">
                Why it was built
              </h2>
              <p className="mb-4">
                Cloud-based computer-use agents (Operator, Claude Computer Use,
                etc.) work by taking screenshots and sending them to a remote
                server. That means your screen — your files, your emails, your
                banking — gets transmitted to a third party on every action.
              </p>
              <p className="mb-4">
                NEXUS takes the opposite approach. Screen reading happens via the
                macOS Accessibility API, which returns structured element data
                directly in-process. No screenshot leaves your machine. The only
                thing that goes to an external API is your text instruction and
                the action plan — not pixel data.
              </p>
              <p>
                When the Accessibility tree is insufficient (web canvases, native
                Qt apps, games), NEXUS falls back to a local vision model —
                Qwen3-VL-8B running in Ollama — which also runs entirely on your
                machine.
              </p>
            </section>

            <section>
              <h2 className="text-base font-semibold text-white mb-4">
                Architecture
              </h2>
              <p className="mb-4">
                The pipeline has three layers:
              </p>
              <ul className="space-y-3 list-none">
                <li className="flex gap-3">
                  <span className="text-cyan-400 font-mono text-xs mt-0.5 select-none">
                    01
                  </span>
                  <span>
                    <span className="text-white">Planning:</span> Claude Sonnet
                    4.6 takes your instruction and produces a structured action
                    list — each step has a target element, an action type, and
                    optional parameters.
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className="text-cyan-400 font-mono text-xs mt-0.5 select-none">
                    02
                  </span>
                  <span>
                    <span className="text-white">Execution:</span> The AX bridge
                    locates each element by role, label, or position in 30–80ms.
                    If that fails, Qwen3-VL-8B provides a bounding box via
                    vision inference.
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className="text-cyan-400 font-mono text-xs mt-0.5 select-none">
                    03
                  </span>
                  <span>
                    <span className="text-white">Verification:</span> Claude
                    Haiku 4.5 checks the screen state after each step. If the
                    expected outcome did not occur, the step is retried with
                    modified parameters before moving forward.
                  </span>
                </li>
              </ul>
              <p className="mt-4">
                Completed task sequences are cached in a local SQLite database.
                On repeat tasks, NEXUS replays cached steps without re-planning —
                typically 10x faster.
              </p>
            </section>

            <section>
              <h2 className="text-base font-semibold text-white mb-4">
                Honest expectations
              </h2>
              <p className="mb-4">
                NEXUS handles 3–5 step tasks on standard macOS apps with roughly
                70–80% reliability. Failures happen most often when:
              </p>
              <ul className="space-y-2 ml-4 list-disc list-outside marker:text-gray-600">
                <li>
                  An element is in a web canvas or custom renderer that exposes
                  no AX attributes and vision inference produces an imprecise
                  bounding box.
                </li>
                <li>
                  A multi-step task requires the app to change state in ways that
                  are hard to predict from the initial instruction.
                </li>
                <li>
                  A modal or OS-level dialog appears unexpectedly and interrupts
                  the action sequence.
                </li>
              </ul>
              <p className="mt-4">
                NEXUS does not take actions it is uncertain about without
                verification. When it cannot proceed, it stops and reports the
                last confirmed state, the step that failed, and what it tried.
              </p>
            </section>

            <section>
              <h2 className="text-base font-semibold text-white mb-4">
                Open source
              </h2>
              <p>
                NEXUS is MIT licensed. The source will be published on GitHub
                before the first release. Contributions, bug reports, and
                capability expansions are welcome. The project has no funding and
                no business model — it exists because computer-use should be
                private by default.
              </p>
            </section>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
