from __future__ import annotations

import re
from pathlib import Path

from footprint_api.models import HardwareConstraints


CPU_PATTERNS = [
    (r"cortex[-\s]m(0\+?|3|4|7|23|33|55|85)", "Arm Cortex-M{match}"),
    (r"risc[-\s]?v", "RISC-V"),
    (r"xtensa", "Xtensa"),
    (r"avr", "AVR"),
]

INTERFACE_TERMS = [
    "adc",
    "ble",
    "can",
    "ethernet",
    "gpio",
    "i2c",
    "i2s",
    "pdm",
    "spi",
    "uart",
    "usb",
    "wifi",
]

SENSOR_TERMS = [
    "accelerometer",
    "camera",
    "gyroscope",
    "humidity",
    "imu",
    "microphone",
    "pressure",
    "temperature",
]


def parse_datasheet_text(text: str) -> HardwareConstraints:
    normalized = _normalize(text)
    evidence: list[str] = []

    hardware = HardwareConstraints()
    hardware.device_name = _extract_device_name(text)
    hardware.cpu = _extract_cpu(normalized)
    hardware.mcu_family = _extract_family(text)
    hardware.clock_mhz = _extract_clock_mhz(normalized, evidence)
    hardware.flash_kb = _extract_memory_kb(normalized, ["flash", "rom", "program memory"], evidence)
    hardware.ram_kb = _extract_memory_kb(normalized, ["sram", "ram", "memory"], evidence)
    hardware.has_fpu = bool(re.search(r"\bfpu\b|floating[-\s]point", normalized))
    hardware.has_dsp = bool(re.search(r"\bdsp\b|simd|cmsis[-\s]?dsp", normalized))
    hardware.accelerators = _extract_accelerators(normalized)
    hardware.interfaces = _collect_terms(normalized, INTERFACE_TERMS)
    hardware.sensors = _collect_terms(normalized, SENSOR_TERMS)
    hardware.power_notes = _extract_power_notes(text)
    hardware.source_evidence = evidence[:12]
    return hardware


def extract_text_from_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".csv", ".json", ".c", ".h"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("Install footprint-api[pdf] to parse PDF datasheets.") from exc

        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    raise ValueError(f"Unsupported datasheet format: {suffix or 'unknown'}")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def _extract_device_name(text: str) -> str | None:
    candidates = re.findall(r"\b([A-Z]{2,}[A-Z0-9-]{3,})\b", text)
    ignored = {"GPIO", "UART", "I2C", "SPI", "ADC", "USB", "BLE", "RAM", "ROM", "CPU"}
    for candidate in candidates:
        if candidate not in ignored:
            return candidate
    return None


def _extract_family(text: str) -> str | None:
    match = re.search(r"\b(stm32[a-z0-9]*|nrf52|nrf53|esp32|rp2040|samd\d+|efm32)\b", text.lower())
    return match.group(1).upper() if match else None


def _extract_cpu(text: str) -> str | None:
    for pattern, label in CPU_PATTERNS:
        match = re.search(pattern, text)
        if match:
            token = match.group(1).upper() if match.groups() else ""
            return label.format(match=token)
    return None


def _extract_clock_mhz(text: str, evidence: list[str]) -> float | None:
    matches = re.finditer(r"(\d+(?:\.\d+)?)\s*(mhz|ghz)", text)
    values = []
    for match in matches:
        value = float(match.group(1)) * (1000 if match.group(2) == "ghz" else 1)
        values.append(value)
        evidence.append(_evidence_window(text, match.start(), match.end()))
    return max(values) if values else None


def _extract_memory_kb(text: str, labels: list[str], evidence: list[str]) -> int | None:
    values: list[int] = []
    label_pattern = "|".join(re.escape(label) for label in labels)
    patterns = [
        rf"(\d+(?:\.\d+)?)\s*(kb|kbytes?|mb|mbytes?)\s+(?:of\s+)?({label_pattern})",
        rf"({label_pattern})\D{{0,24}}(\d+(?:\.\d+)?)\s*(kb|kbytes?|mb|mbytes?)",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            groups = match.groups()
            number = next(group for group in groups if re.fullmatch(r"\d+(?:\.\d+)?", group))
            unit = next(group for group in groups if group in {"kb", "kbyte", "kbytes", "mb", "mbyte", "mbytes"})
            multiplier = 1024 if unit.startswith("mb") else 1
            values.append(round(float(number) * multiplier))
            evidence.append(_evidence_window(text, match.start(), match.end()))
    return max(values) if values else None


def _extract_accelerators(text: str) -> list[str]:
    accelerators = []
    for term in ["npu", "ethos-u", "dma", "crypto accelerator", "jpeg accelerator"]:
        if term in text:
            accelerators.append(term.upper() if term in {"npu", "dma"} else term)
    return sorted(set(accelerators))


def _collect_terms(text: str, terms: list[str]) -> list[str]:
    found = {term.upper() if len(term) <= 4 else term for term in terms if re.search(rf"\b{re.escape(term)}\b", text)}
    return sorted(found)


def _extract_power_notes(text: str) -> list[str]:
    notes = []
    for line in text.splitlines():
        lower = line.lower()
        if any(token in lower for token in ["ua", "ma", "mw", "sleep", "low power", "active mode"]):
            cleaned = " ".join(line.split())
            if 12 <= len(cleaned) <= 180:
                notes.append(cleaned)
    return notes[:8]


def _evidence_window(text: str, start: int, end: int) -> str:
    return text[max(0, start - 80) : min(len(text), end + 80)].strip()
