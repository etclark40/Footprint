export type AnalysisRequest = {
  datasheet_text: string;
  firmware_files: Record<string, string>;
  user_goal: string;
  priorities: string[];
};

export type HardwareConstraints = {
  device_name?: string | null;
  mcu_family?: string | null;
  cpu?: string | null;
  clock_mhz?: number | null;
  flash_kb?: number | null;
  ram_kb?: number | null;
  has_fpu?: boolean | null;
  has_dsp?: boolean | null;
  accelerators: string[];
  sensors: string[];
  interfaces: string[];
  power_notes: string[];
  source_evidence: string[];
};

export type FirmwareSignals = {
  languages: string[];
  frameworks: string[];
  rtos: string[];
  build_systems: string[];
  io_interfaces: string[];
  sensor_drivers: string[];
  timing_signals: string[];
  memory_signals: string[];
  ml_signals: string[];
  analyzed_files: number;
  source_evidence: string[];
};

export type PipelineCandidate = {
  name: string;
  fit_reason: string;
  model_family: string;
  input_signals: string[];
  preprocessing: string[];
  deployment_notes: string[];
  risks: string[];
};

export type RagMatch = {
  score: number;
  matched_terms: string[];
  example: {
    id: string;
    title: string;
    summary: string;
    tags: string[];
    hardware: string[];
    pipeline: string[];
    constraints: Record<string, unknown>;
    source_url?: string | null;
  };
};

export type AnalysisResult = {
  hardware: HardwareConstraints;
  firmware: FirmwareSignals;
  rag_matches: RagMatch[];
  pipeline_candidates: PipelineCandidate[];
};
