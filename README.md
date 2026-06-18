# Footprint

Footprint is an embedded systems AI tool for analyzing hardware datasheets and firmware codebases, retrieving similar edge ML implementations, and preparing structured JSON for a future LLM API call.

This repository currently implements everything up to the LLM call:

- Datasheet parsing into hardware constraints.
- Firmware static analysis for embedded and TinyML signals.
- Local RAG-style retrieval over known implementation examples.
- Deterministic edge ML pipeline candidates.
- LLM-ready JSON prompt generation.
- A React website with an analysis interface and project description tab.

## Repository Layout

```text
backend/
  footprint_api/
    data/implementations.json
    services/
      datasheet_parser.py
      firmware_analyzer.py
      pipeline_recommender.py
      prompt_builder.py
      rag_store.py
    main.py
    models.py
  pyproject.toml
frontend/
  src/
    App.tsx
    api.ts
    styles.css
    types.ts
  package.json
  vite.config.ts
```

## Run The Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .
uvicorn footprint_api.main:app --reload
```

The API will run on `http://localhost:8000`.

Useful endpoints:

- `GET /health`
- `POST /analyze`
- `POST /analyze/upload`
- `POST /implementations/seed`

Install optional PDF support with:

```bash
pip install -e ".[pdf]"
```

## Run The Website

```bash
cd frontend
npm install
npm run dev
```

The website will run on `http://localhost:5173` and calls the backend at `http://localhost:8000` by default. Set `VITE_API_BASE_URL` if the API runs elsewhere.

## Analysis Flow

1. Paste datasheet text into the UI or call the API directly.
2. Provide firmware files as a JSON object keyed by path.
3. Footprint parses hardware constraints and firmware signals.
4. The local RAG store retrieves similar implementation examples.
5. Pipeline candidates are generated deterministically.
6. The final `llm_prompt_json` is ready to send to an LLM API in a future integration.

## Example API Request

```json
{
  "datasheet_text": "STM32F407 Cortex-M4 MCU, 168 MHz, 1 MB Flash, 192 KB SRAM, FPU, DSP, ADC, I2S.",
  "firmware_files": {
    "src/main.c": "#include \"arm_math.h\"\nstatic int16_t pdm_buffer[2048];\nvoid app_main(void) {}"
  },
  "user_goal": "Suggest practical edge ML pipelines for recognizing audio events.",
  "priorities": ["memory", "latency"]
}
```

## Next LLM Integration Point

Add a provider module that accepts `llm_prompt_json` from the `/analyze` response and sends it to your chosen LLM API. The current code intentionally keeps that boundary explicit so API keys, model routing, logging, and prompt evaluation can be added cleanly.
