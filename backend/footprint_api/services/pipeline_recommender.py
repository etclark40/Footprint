from __future__ import annotations

from footprint_api.models import FirmwareSignals, HardwareConstraints, PipelineCandidate


def recommend_pipelines(
    hardware: HardwareConstraints, firmware: FirmwareSignals
) -> list[PipelineCandidate]:
    candidates: list[PipelineCandidate] = []

    if _has_signal(hardware.sensors + firmware.sensor_drivers, ["Microphone", "microphone", "PDM", "I2S"]):
        candidates.append(
            PipelineCandidate(
                name="Keyword spotting pipeline",
                fit_reason="Audio input is present and can run on constrained MCUs with quantized CNN or DS-CNN models.",
                model_family="int8 quantized CNN / DS-CNN",
                input_signals=["microphone", "PDM/I2S audio frames"],
                preprocessing=["windowed audio capture", "MFCC or log-mel spectrogram"],
                deployment_notes=["Use TFLite Micro or CMSIS-NN kernels", "Keep arena sizing below available SRAM"],
                risks=["Audio buffering can dominate RAM", "Latency depends on frame stride and sample rate"],
            )
        )

    if _has_signal(hardware.sensors + firmware.sensor_drivers, ["Accelerometer", "IMU", "accelerometer", "imu"]):
        candidates.append(
            PipelineCandidate(
                name="Motion classification pipeline",
                fit_reason="IMU-style signals map well to small temporal CNNs or feature-based classifiers.",
                model_family="1D CNN / random forest / tiny transformer",
                input_signals=["accelerometer", "gyroscope"],
                preprocessing=["sliding windows", "normalization", "optional FFT features"],
                deployment_notes=["Prefer int8 1D CNN when CMSIS-NN or DSP support is available"],
                risks=["Window length trades responsiveness for accuracy"],
            )
        )

    if _has_signal(hardware.sensors + firmware.sensor_drivers, ["Camera", "camera"]):
        candidates.append(
            PipelineCandidate(
                name="Vision anomaly or object detection pipeline",
                fit_reason="Camera support suggests an image pipeline, but memory must be checked carefully.",
                model_family="MobileNetV1/V2 tiny variant or FOMO-style detector",
                input_signals=["camera frames"],
                preprocessing=["resize", "grayscale or RGB565 conversion", "quantization"],
                deployment_notes=["Use tile-based processing if SRAM is below full-frame needs"],
                risks=["Frame buffers can exceed SRAM", "Inference may require accelerator support"],
            )
        )

    if not candidates:
        candidates.append(
            PipelineCandidate(
                name="Sensor anomaly detection pipeline",
                fit_reason="Default low-risk option when the input modality is unclear.",
                model_family="autoencoder / one-class classifier / thresholded features",
                input_signals=hardware.sensors or firmware.io_interfaces or ["application telemetry"],
                preprocessing=["feature extraction", "rolling statistics", "calibration baseline"],
                deployment_notes=["Start with a classical baseline before moving to a neural model"],
                risks=["Needs representative normal-operation data"],
            )
        )

    return _annotate_constraints(candidates, hardware)


def _annotate_constraints(
    candidates: list[PipelineCandidate], hardware: HardwareConstraints
) -> list[PipelineCandidate]:
    for candidate in candidates:
        if hardware.ram_kb and hardware.ram_kb < 128:
            candidate.deployment_notes.append("Prioritize feature-based or very small int8 models under 128 KB SRAM")
        if hardware.flash_kb and hardware.flash_kb < 512:
            candidate.deployment_notes.append("Budget model weights carefully because flash is below 512 KB")
        if hardware.has_fpu is False:
            candidate.deployment_notes.append("Avoid float inference; generate int8 or fixed-point kernels")
        if hardware.has_dsp:
            candidate.deployment_notes.append("DSP support can accelerate preprocessing and CMSIS-NN kernels")
    return candidates


def _has_signal(values: list[str], needles: list[str]) -> bool:
    haystack = " ".join(values).lower()
    return any(needle.lower() in haystack for needle in needles)
