from __future__ import annotations

import re
from pathlib import Path

from footprint_api.models import FirmwareSignals


LANGUAGE_EXTENSIONS = {
    ".c": "C",
    ".cc": "C++",
    ".cpp": "C++",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".ino": "Arduino",
    ".rs": "Rust",
    ".py": "Python tooling",
}

PATTERNS = {
    "frameworks": {
        "Arduino": r"\bArduino\.h\b|setup\s*\(|loop\s*\(",
        "CMSIS": r"\bcmsis\b|arm_math\.h|core_cm\d+\.h",
        "ESP-IDF": r"esp_log|freertos/FreeRTOS\.h|sdkconfig",
        "HAL": r"\bHAL_[A-Z0-9_]+\(",
        "Zephyr": r"\bzephyr/kernel\.h\b|DEVICE_DT_GET",
    },
    "rtos": {
        "FreeRTOS": r"FreeRTOS|xTaskCreate|vTaskDelay|QueueHandle_t",
        "Zephyr": r"k_thread|k_sleep|K_THREAD_STACK_DEFINE",
        "CMSIS-RTOS": r"osThreadNew|osDelay|cmsis_os",
    },
    "io_interfaces": {
        "ADC": r"\bADC\b|analogRead|HAL_ADC",
        "BLE": r"\bBLE\b|bluetooth|nimble|bt_gatt",
        "CAN": r"\bCAN\b|HAL_CAN",
        "I2C": r"\bI2C\b|Wire\.|HAL_I2C|i2c_",
        "I2S": r"\bI2S\b|HAL_I2S|i2s_",
        "PDM": r"\bPDM\b|pdm_",
        "SPI": r"\bSPI\b|HAL_SPI|spi_",
        "UART": r"\bUART\b|Serial\.|HAL_UART|uart_",
        "USB": r"\bUSB\b|tinyusb|HAL_PCD",
    },
    "sensor_drivers": {
        "Accelerometer": r"lis3dh|adxl|bma\d+|accelerometer",
        "Camera": r"camera|ov2640|hm01b0|dcmi",
        "IMU": r"bno055|bmi\d+|icm20948|mpu6050|imu",
        "Microphone": r"microphone|mic_|pdm|i2s_read",
        "Temperature": r"tmp\d+|ds18b20|temperature",
    },
    "timing_signals": {
        "interrupt-driven": r"IRQHandler|attachInterrupt|NVIC|ISR\(",
        "periodic sampling": r"timer|Ticker|vTaskDelay|k_timer|millis\(",
        "DMA": r"\bDMA\b|HAL_DMA|dma_",
    },
    "memory_signals": {
        "static buffers": r"static\s+\w+.*\[[^\]]+\]",
        "heap allocation": r"\bmalloc\b|\bnew\b|pvPortMalloc",
        "ring buffers": r"ring[_\s]?buffer|circular[_\s]?buffer",
    },
    "ml_signals": {
        "TensorFlow Lite Micro": r"tflite|tensorflow/lite/micro|MicroInterpreter",
        "CMSIS-NN": r"arm_nn|cmsis_nn",
        "Edge Impulse": r"edge-impulse|run_classifier|ei_impulse",
        "custom DSP": r"fft|mfcc|filterbank|spectrogram",
    },
    "build_systems": {
        "CMake": r"cmake_minimum_required|CMakeLists\.txt",
        "Make": r"(^|\n)\s*all\s*:|Makefile",
        "PlatformIO": r"platformio\.ini",
        "West": r"west\.yml|prj\.conf",
    },
}


def analyze_firmware_files(files: dict[str, str]) -> FirmwareSignals:
    signals = FirmwareSignals(analyzed_files=len(files))
    corpus = "\n".join(f"// FILE: {name}\n{content}" for name, content in files.items())

    signals.languages = _detect_languages(files)
    for field, patterns in PATTERNS.items():
        setattr(signals, field, _collect_matches(corpus, patterns))

    signals.source_evidence = _collect_evidence(corpus)
    return signals


def load_firmware_directory(path: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    allowed = set(LANGUAGE_EXTENSIONS) | {".cmake", ".txt", ".ini", ".conf", ".yml", ".yaml"}
    for file_path in path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in allowed:
            try:
                files[str(file_path.relative_to(path))] = file_path.read_text(
                    encoding="utf-8", errors="ignore"
                )
            except OSError:
                continue
    return files


def _detect_languages(files: dict[str, str]) -> list[str]:
    languages = {
        LANGUAGE_EXTENSIONS[path.suffix.lower()]
        for name in files
        if (path := Path(name)).suffix.lower() in LANGUAGE_EXTENSIONS
    }
    return sorted(languages)


def _collect_matches(corpus: str, patterns: dict[str, str]) -> list[str]:
    found = [label for label, pattern in patterns.items() if re.search(pattern, corpus, re.I | re.M)]
    return sorted(found)


def _collect_evidence(corpus: str) -> list[str]:
    evidence = []
    interesting = [
        "MicroInterpreter",
        "run_classifier",
        "arm_math",
        "xTaskCreate",
        "HAL_ADC",
        "i2s_read",
        "attachInterrupt",
        "static",
    ]
    for token in interesting:
        match = re.search(re.escape(token), corpus, re.I)
        if match:
            evidence.append(corpus[max(0, match.start() - 90) : match.end() + 120].strip())
    return evidence[:12]
