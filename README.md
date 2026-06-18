# Footprint

Footprint is an embedded systems AI tool for analyzing hardware datasheets and firmware codebases, retrieving similar edge ML implementations, and suggesting edge ML pipelines that fit system constraints.

This repository currently implements:

- Datasheet parsing into hardware constraints.
- Firmware static analysis for embedded and TinyML signals.
- Local RAG-style retrieval over known implementation examples.
- Edge ML pipeline candidates.
- Memory, firmware integration, and deployment tradeoff notes.
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

## Public Website

The public GitHub Pages site is available at:

```text
https://etclark40.github.io/Footprint/
```

GitHub Pages hosts the static React website only. The analysis features require the FastAPI backend to be running locally during development, or deployed to a public backend host and configured with `VITE_API_BASE_URL`.

## Run The Backend Locally

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .
uvicorn footprint_api.main:app --reload
```

For local development, the API runs on `http://localhost:8000`.

Useful endpoints:

- `GET /health`
- `POST /analyze`
- `POST /analyze/upload`
- `POST /implementations/seed`

Install optional PDF support with:

```bash
pip install -e ".[pdf]"
```

## Run The Website Locally

```bash
cd frontend
npm install
npm run dev
```

For local development, the website runs on `http://localhost:5173` and calls the backend at `http://localhost:8000` by default. Set `VITE_API_BASE_URL` if the API runs elsewhere.

## Analysis Flow

1. Paste datasheet text or upload a text-based datasheet file.
2. Upload a firmware/code directory through the website, or call the API with files keyed by path.
3. Footprint parses hardware constraints and firmware signals.
4. The local RAG store retrieves similar implementation examples.
5. Pipeline candidates are generated with deployment notes for memory, latency, preprocessing, and firmware integration.

## Example API Request

```json
{
  "datasheet_text": "STM32F407 Cortex-M4 MCU, 168 MHz, 1 MB Flash, 192 KB SRAM, FPU, DSP, ADC, I2S.",
  "firmware_files": {
    "src/main.c": "#include \"arm_math.h\"\nstatic int16_t pdm_buffer[2048];\nvoid app_main(void) {}"
  },
  "user_goal": "Audio event recognition on a battery-powered sensor node.",
  "priorities": ["memory", "latency"]
}
```
