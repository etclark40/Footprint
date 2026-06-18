from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ConstraintPriority(str, Enum):
    latency = "latency"
    memory = "memory"
    energy = "energy"
    accuracy = "accuracy"
    cost = "cost"


class HardwareConstraints(BaseModel):
    device_name: str | None = None
    mcu_family: str | None = None
    cpu: str | None = None
    clock_mhz: float | None = None
    flash_kb: int | None = None
    ram_kb: int | None = None
    has_fpu: bool | None = None
    has_dsp: bool | None = None
    accelerators: list[str] = Field(default_factory=list)
    sensors: list[str] = Field(default_factory=list)
    interfaces: list[str] = Field(default_factory=list)
    power_notes: list[str] = Field(default_factory=list)
    source_evidence: list[str] = Field(default_factory=list)


class FirmwareSignals(BaseModel):
    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    rtos: list[str] = Field(default_factory=list)
    build_systems: list[str] = Field(default_factory=list)
    io_interfaces: list[str] = Field(default_factory=list)
    sensor_drivers: list[str] = Field(default_factory=list)
    timing_signals: list[str] = Field(default_factory=list)
    memory_signals: list[str] = Field(default_factory=list)
    ml_signals: list[str] = Field(default_factory=list)
    analyzed_files: int = 0
    source_evidence: list[str] = Field(default_factory=list)


class ImplementationExample(BaseModel):
    id: str
    title: str
    summary: str
    tags: list[str] = Field(default_factory=list)
    hardware: list[str] = Field(default_factory=list)
    pipeline: list[str] = Field(default_factory=list)
    constraints: dict[str, Any] = Field(default_factory=dict)
    source_url: str | None = None


class RagMatch(BaseModel):
    example: ImplementationExample
    score: float
    matched_terms: list[str] = Field(default_factory=list)


class AnalysisRequest(BaseModel):
    datasheet_text: str = ""
    firmware_files: dict[str, str] = Field(default_factory=dict)
    user_goal: str = "Suggest practical edge ML pipelines for this embedded system."
    priorities: list[ConstraintPriority] = Field(default_factory=lambda: [ConstraintPriority.memory])


class PipelineCandidate(BaseModel):
    name: str
    fit_reason: str
    model_family: str
    input_signals: list[str] = Field(default_factory=list)
    preprocessing: list[str] = Field(default_factory=list)
    deployment_notes: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    hardware: HardwareConstraints
    firmware: FirmwareSignals
    rag_matches: list[RagMatch]
    pipeline_candidates: list[PipelineCandidate]
    llm_prompt_json: dict[str, Any]


class ImplementationSeedRequest(BaseModel):
    examples: list[ImplementationExample]
