import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Setup Docs — NEXUS",
  description:
    "How to install Ollama, pull Qwen3-VL-8B, configure your API key, and run NEXUS on macOS.",
};

function CodeBlock({ children }: { children: string }) {
  return (
    <div className="rounded-lg border border-gray-800 bg-gray-950 overflow-x-auto my-4">
      <pre className="px-5 py-4 text-sm font-mono text-gray-200 leading-relaxed">
        <code>{children}</code>
      </pre>
    </div>
  );
}

function InlineCode({ children }: { children: string }) {
  return (
    <code className="px-1.5 py-0.5 rounded text-xs font-mono bg-gray-900 border border-gray-800 text-cyan-300">
      {children}
    </code>
  );
}

function Step({
  n,
  title,
  children,
}: {
  n: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mb-12">
      <div className="flex items-baseline gap-3 mb-4">
        <span className="text-xs font-mono text-cyan-400 select-none">{n}</span>
        <h2 className="text-base font-semibold text-white">{title}</h2>
      </div>
      <div className="text-sm text-gray-400 leading-relaxed space-y-3 ml-6">
        {children}
      </div>
    </section>
  );
}

export default function DocsPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <Nav />
      <main className="pt-14">
        <div className="max-w-2xl mx-auto px-6 py-20">
          <div className="mb-12">
            <h1 className="text-4xl font-bold text-white mb-4">
              Setup guide
            </h1>
            <p className="text-gray-400 leading-relaxed">
              NEXUS has a few moving parts. Follow these steps in order. The
              whole process takes about 15 minutes, mostly waiting for model
              download.
            </p>
          </div>

          <div className="mb-12 p-5 rounded-xl border border-gray-800 bg-gray-950/50">
            <h3 className="text-sm font-semibold text-white mb-3">
              Prerequisites at a glance
            </h3>
            <ul className="space-y-1.5 text-xs text-gray-400">
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 flex-shrink-0" />
                macOS 14 Sonoma or later, Apple Silicon
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 flex-shrink-0" />
                16 GB RAM (32 GB recommended)
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 flex-shrink-0" />
                Python 3.12
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 flex-shrink-0" />
                Ollama (free)
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 flex-shrink-0" />
                Anthropic API key (Claude Sonnet 4.6 + Haiku 4.5)
              </li>
            </ul>
          </div>

          <Step n="01" title="Install Ollama">
            <p>
              Download and install Ollama from{" "}
              <a
                href="https://ollama.ai"
                target="_blank"
                rel="noopener noreferrer"
                className="text-cyan-400 hover:text-cyan-300 underline underline-offset-2"
              >
                ollama.ai
              </a>
              . Ollama is a free, open source local model runner that handles
              GPU scheduling and model memory for you.
            </p>
            <p>
              After installing, verify it is running:
            </p>
            <CodeBlock>{"ollama list"}</CodeBlock>
          </Step>

          <Step n="02" title="Pull the vision model">
            <p>
              NEXUS uses Qwen3-VL-8B as its fallback vision model. The download
              is approximately 4 GB. This only runs on Apple Silicon.
            </p>
            <CodeBlock>{"ollama pull qwen3-vl:8b"}</CodeBlock>
            <p>
              Wait for the pull to complete before continuing. You can verify it
              is available by running <InlineCode>{"ollama list"}</InlineCode>{" "}
              and checking for <InlineCode>{"qwen3-vl:8b"}</InlineCode> in the
              output.
            </p>
          </Step>

          <Step n="03" title="Clone and install NEXUS">
            <p>
              Clone the repository and install it in editable mode. A virtual
              environment is recommended.
            </p>
            <CodeBlock>{`git clone https://github.com/nexus-ai/nexus.git
cd nexus
python3 -m venv .venv
source .venv/bin/activate
pip install -e .`}</CodeBlock>
          </Step>

          <Step n="04" title="Set your Anthropic API key">
            <p>
              Create a <InlineCode>{".env"}</InlineCode> file in the project
              root. NEXUS reads this on startup.
            </p>
            <CodeBlock>{`# .env
ANTHROPIC_API_KEY=sk-ant-...`}</CodeBlock>
            <p>
              Your API key is used for Claude Sonnet 4.6 (planning) and Claude
              Haiku 4.5 (verification). Typical cost is $0.01–$0.05 per
              multi-step task. Screen data is never included in API calls.
            </p>
          </Step>

          <Step n="05" title="Grant macOS permissions">
            <p>
              NEXUS requires two system permissions. Both must be granted before
              the first run.
            </p>
            <ul className="space-y-3 list-none">
              <li>
                <span className="text-white font-medium">
                  Screen Recording:
                </span>{" "}
                Go to System Settings &rarr; Privacy &amp; Security &rarr;
                Screen &amp; System Audio Recording and enable NEXUS (or
                Terminal, if running from source).
              </li>
              <li>
                <span className="text-white font-medium">Accessibility:</span>{" "}
                Go to System Settings &rarr; Privacy &amp; Security &rarr;
                Accessibility and enable NEXUS.
              </li>
            </ul>
            <p>
              NEXUS will not be able to read UI elements or capture fallback
              screenshots without these permissions.
            </p>
          </Step>

          <Step n="06" title="Launch NEXUS">
            <p>
              With your virtual environment active and{" "}
              <InlineCode>{".env"}</InlineCode> in place:
            </p>
            <CodeBlock>{"python -m nexus"}</CodeBlock>
            <p>
              If you are using the packaged app, open{" "}
              <InlineCode>{"Nexus.app"}</InlineCode> from your Applications
              folder. A menu bar icon will appear when NEXUS is running.
            </p>
          </Step>

          <Step n="07" title="Run your first command">
            <p>
              Press <InlineCode>{"Cmd+Ctrl+Space"}</InlineCode> to open the
              NEXUS input bar. Type a command and press Enter:
            </p>
            <CodeBlock>{"Open Safari and go to google.com"}</CodeBlock>
            <p>
              NEXUS will plan the steps, locate the Safari icon or open a new
              window, navigate to the address, and report completion. The whole
              sequence takes 2–5 seconds on M-series hardware.
            </p>
          </Step>

          <section className="mt-16 pt-10 border-t border-gray-900">
            <h2 className="text-base font-semibold text-white mb-6">
              Troubleshooting
            </h2>
            <div className="space-y-6">
              <div className="rounded-lg border border-gray-800 p-5">
                <h3 className="text-sm font-medium text-white mb-2">
                  Screen capture shows only the wallpaper
                </h3>
                <p className="text-sm text-gray-400">
                  Screen Recording permission has not been granted or was granted
                  after NEXUS started. Grant it in System Settings &rarr;
                  Privacy &amp; Security &rarr; Screen &amp; System Audio
                  Recording, then restart NEXUS.
                </p>
              </div>
              <div className="rounded-lg border border-gray-800 p-5">
                <h3 className="text-sm font-medium text-white mb-2">
                  Elements not found / NEXUS clicks the wrong place
                </h3>
                <p className="text-sm text-gray-400">
                  Accessibility permission has not been granted. Go to System
                  Settings &rarr; Privacy &amp; Security &rarr; Accessibility
                  and enable NEXUS. If it is already enabled, try removing and
                  re-adding it. You may need to restart the target application
                  after granting permission.
                </p>
              </div>
              <div className="rounded-lg border border-gray-800 p-5">
                <h3 className="text-sm font-medium text-white mb-2">
                  Ollama model not found
                </h3>
                <p className="text-sm text-gray-400">
                  Run <InlineCode>{"ollama list"}</InlineCode> and confirm{" "}
                  <InlineCode>{"qwen3-vl:8b"}</InlineCode> is present. If it is
                  not, run <InlineCode>{"ollama pull qwen3-vl:8b"}</InlineCode>{" "}
                  again. Confirm Ollama is running (the elephant icon in your
                  menu bar).
                </p>
              </div>
              <div className="rounded-lg border border-gray-800 p-5">
                <h3 className="text-sm font-medium text-white mb-2">
                  API key error on first run
                </h3>
                <p className="text-sm text-gray-400">
                  Confirm your <InlineCode>{".env"}</InlineCode> file is in the
                  project root and your API key starts with{" "}
                  <InlineCode>{"sk-ant-"}</InlineCode>. The key must have access
                  to Claude Sonnet 4.6 and Claude Haiku 4.5. Check your
                  Anthropic console to verify.
                </p>
              </div>
            </div>
          </section>
        </div>
      </main>
      <Footer />
    </div>
  );
}
