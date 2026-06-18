import { ChangeEvent, FormEvent, useState } from "react";
import { analyzeSystem } from "./api";
import type { AnalysisResult } from "./types";

function App() {
  const [activeTab, setActiveTab] = useState<"analyze" | "about">("analyze");

  return (
    <main className="shell">
      <header className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Edge ML feasibility Advisor</p>
          <h1>Footprint AI</h1>
          <p>
            Turn datasheets and firmware into practical edge ML pipeline suggestions, memory budgets,
            and deployment tradeoffs for constrained hardware.
          </p>
        </div>
        <nav className="tabs" aria-label="Primary navigation">
          <button
            className={activeTab === "analyze" ? "active" : ""}
            onClick={() => setActiveTab("analyze")}
          >
            Analyze
          </button>
          <button
            className={activeTab === "about" ? "active" : ""}
            onClick={() => setActiveTab("about")}
          >
            Project
          </button>
        </nav>
      </header>

      {activeTab === "analyze" ? <AnalyzeTab /> : <AboutTab />}
    </main>
  );
}

function AnalyzeTab() {
  const [datasheetText, setDatasheetText] = useState("");
  const [datasheetFileName, setDatasheetFileName] = useState("");
  const [firmwareFiles, setFirmwareFiles] = useState<Record<string, string>>({});
  const [projectDescription, setProjectDescription] = useState(
    "I want to evaluate edge ML pipelines for this device and understand memory, latency, and firmware integration constraints.",
  );
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleDatasheetFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setDatasheetFileName(file.name);
    setDatasheetText(await file.text());
  }

  async function handleFirmwareDirectory(event: ChangeEvent<HTMLInputElement>) {
    const selectedFiles = Array.from(event.target.files ?? []);
    const readableFiles = selectedFiles.filter(isReadableFirmwareFile);
    const entries = await Promise.all(
      readableFiles.map(async (file) => [
        file.webkitRelativePath || file.name,
        await file.text(),
      ] as const),
    );

    setFirmwareFiles(Object.fromEntries(entries));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const response = await analyzeSystem({
        datasheet_text: datasheetText,
        firmware_files: firmwareFiles,
        user_goal: projectDescription,
        priorities: ["memory", "latency"],
      });
      setResult(response);
    } catch (unknownError) {
      setError(unknownError instanceof Error ? unknownError.message : "Analysis failed.");
    } finally {
      setLoading(false);
    }
  }

  const firmwareFileNames = Object.keys(firmwareFiles);

  return (
    <section className="workspace">
      <form className="panel form-panel" onSubmit={handleSubmit}>
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Inputs</p>
            <h2>Upload System Context</h2>
          </div>
          <span className="pill">{firmwareFileNames.length} code file(s)</span>
        </div>

        <label>
          Datasheet text or extracted notes
          <textarea
            value={datasheetText}
            onChange={(event) => setDatasheetText(event.target.value)}
            placeholder="Paste datasheet text, or upload a text-based datasheet below."
            rows={7}
          />
        </label>

        <div className="upload-grid">
          <label className="upload-card">
            <span>Upload datasheet file</span>
            <small>{datasheetFileName || "Text files work in the browser MVP."}</small>
            <span className="upload-action">Choose datasheet</span>
            <input
              type="file"
              accept=".txt,.md,.csv,.json,.c,.h"
              onChange={handleDatasheetFile}
            />
          </label>

          <label className="upload-card">
            <span>Upload firmware/code directory</span>
            <small>
              {firmwareFileNames.length > 0
                ? `${firmwareFileNames.length} readable code file(s) selected.`
                : "Select your source folder; readable code files will be analyzed."}
            </small>
            <span className="upload-action">Choose folder</span>
            <input
              type="file"
              multiple
              onChange={handleFirmwareDirectory}
              {...directoryInputProps}
            />
          </label>
        </div>

        {firmwareFileNames.length > 0 ? (
          <div className="file-summary">
            <strong>Selected code files</strong>
            <p>{firmwareFileNames.slice(0, 5).join(", ")}</p>
            {firmwareFileNames.length > 5 ? <p>and {firmwareFileNames.length - 5} more...</p> : null}
          </div>
        ) : null}

        <label>
          Project description
          <textarea
            value={projectDescription}
            onChange={(event) => setProjectDescription(event.target.value)}
            placeholder="Describe what the device does, what signal you care about, and any constraints you already know."
            rows={4}
          />
        </label>

        <button className="primary" type="submit" disabled={loading}>
          {loading ? "Analyzing..." : "Analyze system"}
        </button>
        {error ? <p className="error">{error}</p> : null}
      </form>

      <section className="results">
        {result ? <AnalysisResults result={result} /> : <EmptyState />}
      </section>
    </section>
  );
}

function AnalysisResults({ result }: { result: AnalysisResult }) {
  return (
    <>
      <div className="panel">
        <p className="eyebrow">Candidates</p>
        <h2>Suggested Pipeline Starts</h2>
        <div className="cards">
          {result.pipeline_candidates.map((candidate) => (
            <article className="card" key={candidate.name}>
              <h3>{candidate.name}</h3>
              <p>{candidate.fit_reason}</p>
              <p className="muted">Model: {candidate.model_family}</p>
              <TagList items={[...candidate.input_signals, ...candidate.preprocessing]} />
            </article>
          ))}
        </div>
      </div>

      <div className="grid-two">
        <JsonPanel title="Parsed Hardware Constraints" value={result.hardware} />
        <JsonPanel title="Firmware Signals" value={result.firmware} />
      </div>

      <div className="panel">
        <p className="eyebrow">Examples</p>
        <h2>Similar Implementations</h2>
        <div className="cards">
          {result.rag_matches.map((match) => (
            <article className="card" key={match.example.id}>
              <div className="score">{Math.round(match.score * 100)}% match</div>
              <h3>{match.example.title}</h3>
              <p>{match.example.summary}</p>
              <TagList items={match.example.tags} />
            </article>
          ))}
        </div>
      </div>
    </>
  );
}

function AboutTab() {
  return (
    <section className="panel about">
      <p className="eyebrow">Project</p>
      <h2>What Footprint Offers</h2>
      <p>
        Footprint helps embedded teams turn hardware constraints and firmware context into practical
        edge ML deployment decisions. It focuses on what will fit on-device before teams invest time
        wiring up models, buffers, and integration code.
      </p>
      <div className="feature-grid">
        <article>
          <h3>Datasheet Parsing</h3>
          <p>Extracts CPU, memory, clocks, interfaces, sensors, accelerators, and power hints.</p>
        </article>
        <article>
          <h3>Firmware Analysis</h3>
          <p>Finds language, framework, RTOS, interface, sensor, memory, timing, and ML signals.</p>
        </article>
        <article>
          <h3>Pipeline Decision Making</h3>
          <p>
            Compares the device profile against known TinyML patterns for audio, motion, vision, and
            anomaly detection.
          </p>
        </article>
        <article>
          <h3>Memory Optimization</h3>
          <p>
            Highlights RAM, flash, buffering, quantization, and preprocessing tradeoffs that shape
            deployment feasibility.
          </p>
        </article>
      </div>
    </section>
  );
}

function EmptyState() {
  return (
    <div className="panel empty">
      <p className="eyebrow">Ready</p>
      <h2>Upload a datasheet and firmware directory to see pipeline candidates.</h2>
      <p>
        The output will include parsed constraints, firmware signals, similar implementations, and
        deployment-focused recommendations.
      </p>
    </div>
  );
}

function JsonPanel({ title, value }: { title: string; value: unknown }) {
  return (
    <div className="panel json-panel">
      <h2>{title}</h2>
      <pre>{JSON.stringify(value, null, 2)}</pre>
    </div>
  );
}

function TagList({ items }: { items: string[] }) {
  return (
    <div className="tag-list">
      {items.map((item) => (
        <span key={item}>{item}</span>
      ))}
    </div>
  );
}

const directoryInputProps = {
  webkitdirectory: "",
  directory: "",
};

const READABLE_EXTENSIONS = new Set([
  ".c",
  ".cc",
  ".cpp",
  ".h",
  ".hpp",
  ".ino",
  ".rs",
  ".py",
  ".cmake",
  ".txt",
  ".ini",
  ".conf",
  ".yml",
  ".yaml",
]);

function isReadableFirmwareFile(file: File) {
  const lowerName = file.name.toLowerCase();
  return Array.from(READABLE_EXTENSIONS).some((extension) => lowerName.endsWith(extension));
}

export default App;
