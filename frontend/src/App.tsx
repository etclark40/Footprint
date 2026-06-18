import { FormEvent, useMemo, useState } from "react";
import { analyzeSystem } from "./api";
import type { AnalysisResult } from "./types";

const SAMPLE_FIRMWARE = {
  "src/main.c": `#include "arm_math.h"
#include "tensorflow/lite/micro/micro_interpreter.h"

static int16_t pdm_buffer[2048];

void HAL_ADC_ConvCpltCallback(void) {
  // sensor sampling interrupt
}

void app_main(void) {
  MicroInterpreter interpreter;
}`,
};

const PRIORITIES = ["memory", "latency", "energy", "accuracy", "cost"];

function App() {
  const [activeTab, setActiveTab] = useState<"analyze" | "about">("analyze");

  return (
    <main className="shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Embedded AI feasibility</p>
          <h1>Footprint</h1>
          <p>
            Parse hardware constraints, inspect firmware signals, retrieve similar TinyML
            implementations, and prepare LLM-ready JSON for edge ML pipeline design.
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
  const [datasheetText, setDatasheetText] = useState(
    "STM32F407 Cortex-M4 MCU, 168 MHz, 1 MB Flash, 192 KB SRAM, FPU, DSP, ADC, I2S, SPI, UART. Low power sleep modes. Microphone input over I2S.",
  );
  const [firmwareJson, setFirmwareJson] = useState(JSON.stringify(SAMPLE_FIRMWARE, null, 2));
  const [goal, setGoal] = useState(
    "Suggest practical edge ML pipelines for recognizing audio events on this embedded system.",
  );
  const [priorities, setPriorities] = useState(["memory", "latency"]);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const firmwareFileCount = useMemo(() => {
    try {
      return Object.keys(JSON.parse(firmwareJson)).length;
    } catch {
      return 0;
    }
  }, [firmwareJson]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const firmwareFiles = JSON.parse(firmwareJson) as Record<string, string>;
      const response = await analyzeSystem({
        datasheet_text: datasheetText,
        firmware_files: firmwareFiles,
        user_goal: goal,
        priorities,
      });
      setResult(response);
    } catch (unknownError) {
      setError(unknownError instanceof Error ? unknownError.message : "Analysis failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="workspace">
      <form className="panel form-panel" onSubmit={handleSubmit}>
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Inputs</p>
            <h2>System Context</h2>
          </div>
          <span className="pill">{firmwareFileCount} firmware file(s)</span>
        </div>

        <label>
          Datasheet text
          <textarea
            value={datasheetText}
            onChange={(event) => setDatasheetText(event.target.value)}
            rows={8}
          />
        </label>

        <label>
          Firmware files JSON
          <textarea
            value={firmwareJson}
            onChange={(event) => setFirmwareJson(event.target.value)}
            rows={12}
            spellCheck={false}
          />
        </label>

        <label>
          Goal
          <input value={goal} onChange={(event) => setGoal(event.target.value)} />
        </label>

        <fieldset>
          <legend>Optimization priorities</legend>
          <div className="chips">
            {PRIORITIES.map((priority) => (
              <label className="chip" key={priority}>
                <input
                  type="checkbox"
                  checked={priorities.includes(priority)}
                  onChange={(event) => {
                    setPriorities((current) =>
                      event.target.checked
                        ? [...current, priority]
                        : current.filter((item) => item !== priority),
                    );
                  }}
                />
                {priority}
              </label>
            ))}
          </div>
        </fieldset>

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
        <JsonPanel title="Hardware JSON" value={result.hardware} />
        <JsonPanel title="Firmware JSON" value={result.firmware} />
      </div>

      <div className="panel">
        <p className="eyebrow">RAG</p>
        <h2>Retrieved Implementations</h2>
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

      <JsonPanel title="LLM Prompt JSON" value={result.llm_prompt_json} tall />
    </>
  );
}

function AboutTab() {
  return (
    <section className="panel about">
      <p className="eyebrow">Project</p>
      <h2>What Footprint Is Building</h2>
      <p>
        Footprint is an embedded systems AI tool for turning hardware datasheets and firmware
        codebases into practical edge ML pipeline recommendations. This repository currently stops
        at deterministic analysis and LLM prompt assembly.
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
          <h3>RAG Implementations</h3>
          <p>Retrieves similar TinyML examples from a local SQLite-backed implementation store.</p>
        </article>
        <article>
          <h3>LLM Handoff</h3>
          <p>Produces a structured JSON prompt for a future LLM API integration.</p>
        </article>
      </div>
    </section>
  );
}

function EmptyState() {
  return (
    <div className="panel empty">
      <p className="eyebrow">Ready</p>
      <h2>Run an analysis to see pipeline candidates.</h2>
      <p>
        The output will include parsed constraints, firmware signals, retrieved examples, and the
        exact JSON payload intended for the future LLM step.
      </p>
    </div>
  );
}

function JsonPanel({
  title,
  value,
  tall = false,
}: {
  title: string;
  value: unknown;
  tall?: boolean;
}) {
  return (
    <div className={`panel json-panel ${tall ? "tall" : ""}`}>
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

export default App;
