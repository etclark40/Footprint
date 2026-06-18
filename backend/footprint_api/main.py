from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from footprint_api.models import AnalysisRequest, AnalysisResult, ImplementationSeedRequest
from footprint_api.services.datasheet_parser import extract_text_from_file, parse_datasheet_text
from footprint_api.services.firmware_analyzer import analyze_firmware_files
from footprint_api.services.pipeline_recommender import recommend_pipelines
from footprint_api.services.prompt_builder import build_llm_prompt_json
from footprint_api.services.rag_store import RagStore, build_query_text


PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_DIR / "data"
STORE = RagStore(DATA_DIR / "footprint_rag.sqlite3")
_SEEDED = False

app = FastAPI(
    title="Footprint API",
    version="0.1.0",
    description="Parse datasheets, analyze firmware, retrieve implementation examples, and build LLM-ready JSON.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def seed_store() -> None:
    global _SEEDED
    if _SEEDED:
        return
    seed_path = DATA_DIR / "implementations.json"
    if seed_path.exists():
        STORE.seed_from_json(seed_path)
    _SEEDED = True


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalysisResult)
def analyze(request: AnalysisRequest) -> AnalysisResult:
    seed_store()
    hardware = parse_datasheet_text(request.datasheet_text)
    firmware = analyze_firmware_files(request.firmware_files)
    candidates = recommend_pipelines(hardware, firmware)
    rag_matches = STORE.search(build_query_text(hardware.model_dump(), firmware.model_dump(), request.user_goal))
    prompt_json = build_llm_prompt_json(
        user_goal=request.user_goal,
        priorities=request.priorities,
        hardware=hardware,
        firmware=firmware,
        rag_matches=rag_matches,
        candidates=candidates,
    )
    return AnalysisResult(
        hardware=hardware,
        firmware=firmware,
        rag_matches=rag_matches,
        pipeline_candidates=candidates,
        llm_prompt_json=prompt_json,
    )


@app.post("/analyze/upload", response_model=AnalysisResult)
async def analyze_upload(
    datasheet: UploadFile | None = File(default=None),
    firmware_files: list[UploadFile] | None = File(default=None),
    user_goal: str = Form("Suggest practical edge ML pipelines for this embedded system."),
) -> AnalysisResult:
    request_files: dict[str, str] = {}
    datasheet_text = ""

    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        if datasheet:
            datasheet_path = tmp_path / datasheet.filename
            datasheet_path.write_bytes(await datasheet.read())
            try:
                datasheet_text = extract_text_from_file(datasheet_path)
            except (RuntimeError, ValueError) as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

        for firmware_file in firmware_files or []:
            content = await firmware_file.read()
            request_files[firmware_file.filename] = content.decode("utf-8", errors="ignore")

    return analyze(
        AnalysisRequest(
            datasheet_text=datasheet_text,
            firmware_files=request_files,
            user_goal=user_goal,
        )
    )


@app.post("/implementations/seed")
def seed_implementations(request: ImplementationSeedRequest) -> dict[str, int]:
    STORE.upsert_examples(request.examples)
    return {"upserted": len(request.examples)}
