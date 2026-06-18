from __future__ import annotations

import json
import math
import re
import sqlite3
from collections import Counter
from pathlib import Path

from footprint_api.models import ImplementationExample, RagMatch


TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9_+-]{1,}", re.I)


class RagStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def upsert_examples(self, examples: list[ImplementationExample]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                """
                INSERT INTO implementations (id, payload, search_text)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    payload = excluded.payload,
                    search_text = excluded.search_text
                """,
                [
                    (
                        example.id,
                        example.model_dump_json(),
                        _example_search_text(example),
                    )
                    for example in examples
                ],
            )

    def seed_from_json(self, path: Path) -> None:
        payload = json.loads(path.read_text(encoding="utf-8"))
        examples = [ImplementationExample.model_validate(item) for item in payload]
        self.upsert_examples(examples)

    def search(self, query: str, limit: int = 5) -> list[RagMatch]:
        query_vector = _vectorize(query)
        if not query_vector:
            return []

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT payload, search_text FROM implementations").fetchall()

        scored: list[RagMatch] = []
        for payload, search_text in rows:
            score = _cosine(query_vector, _vectorize(search_text))
            if score <= 0:
                continue
            example = ImplementationExample.model_validate_json(payload)
            matched_terms = sorted(set(query_vector).intersection(_vectorize(search_text)))[:12]
            scored.append(RagMatch(example=example, score=round(score, 4), matched_terms=matched_terms))

        return sorted(scored, key=lambda item: item.score, reverse=True)[:limit]

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS implementations (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    search_text TEXT NOT NULL
                )
                """
            )


def build_query_text(*parts: object) -> str:
    return " ".join(_flatten(part) for part in parts if part)


def _example_search_text(example: ImplementationExample) -> str:
    return build_query_text(
        example.title,
        example.summary,
        example.tags,
        example.hardware,
        example.pipeline,
        example.constraints,
    )


def _flatten(value: object) -> str:
    if isinstance(value, dict):
        return " ".join(f"{key} {_flatten(child)}" for key, child in value.items())
    if isinstance(value, list):
        return " ".join(_flatten(child) for child in value)
    return str(value)


def _vectorize(text: str) -> Counter[str]:
    tokens = [token.lower() for token in TOKEN_PATTERN.findall(text)]
    stop_words = {"and", "for", "with", "the", "this", "that", "from", "into", "using"}
    return Counter(token for token in tokens if token not in stop_words)


def _cosine(left: Counter[str], right: Counter[str]) -> float:
    common = set(left).intersection(right)
    dot = sum(left[token] * right[token] for token in common)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)
