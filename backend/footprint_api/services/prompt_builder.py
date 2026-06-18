from __future__ import annotations

from footprint_api.models import (
    ConstraintPriority,
    FirmwareSignals,
    HardwareConstraints,
    PipelineCandidate,
    RagMatch,
)


def build_llm_prompt_json(
    *,
    user_goal: str,
    priorities: list[ConstraintPriority],
    hardware: HardwareConstraints,
    firmware: FirmwareSignals,
    rag_matches: list[RagMatch],
    candidates: list[PipelineCandidate],
) -> dict[str, object]:
    return {
        "role": "edge_ml_system_architect",
        "task": user_goal,
        "output_requirements": {
            "format": "json",
            "include": [
                "recommended_pipeline",
                "model_family",
                "preprocessing_plan",
                "memory_and_latency_budget",
                "firmware_integration_steps",
                "risks_and_validation_plan",
            ],
            "do_not_call_external_tools": True,
        },
        "optimization_priorities": [priority.value for priority in priorities],
        "system_context": {
            "hardware_constraints": hardware.model_dump(),
            "firmware_signals": firmware.model_dump(),
        },
        "retrieved_implementations": [
            {
                "score": match.score,
                "matched_terms": match.matched_terms,
                "implementation": match.example.model_dump(),
            }
            for match in rag_matches
        ],
        "deterministic_pipeline_candidates": [
            candidate.model_dump() for candidate in candidates
        ],
        "llm_instruction": (
            "Choose or adapt one candidate pipeline. Ground every recommendation in the hardware, "
            "firmware, and retrieved implementation evidence. If constraints are missing, state the "
            "assumption and propose the smallest experiment to resolve it."
        ),
    }
