"""Deterministic metrics for offline RAG evaluation.

These metrics intentionally do not claim to measure semantic faithfulness. That
requires a reviewed evaluator or a model-based judge and is kept as a separate
evaluation stage.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

ABSTENTION_MARKERS = (
    "cannot be found",
    "not found in the context",
    "do not have enough information",
    "não encontrei",
    "não há informação",
    "não tenho informação suficiente",
)


@dataclass(frozen=True)
class EvaluationCase:
    """Ground-truth data for one RAG question."""

    case_id: str
    question: str
    expected_answer: str
    relevant_chunk_ids: tuple[str, ...]
    required_facts: tuple[str, ...]
    answerable: bool


@dataclass(frozen=True)
class CaseMetrics:
    """Deterministic results for one evaluated question."""

    case_id: str
    retrieval_recall: float
    retrieval_precision: float
    reciprocal_rank: float
    answer_exact_match: float
    required_fact_coverage: float
    abstention_correct: float


@dataclass(frozen=True)
class EvaluationObservation:
    """Observed output produced by the RAG pipeline for one case."""

    answer: str
    retrieved_chunk_ids: tuple[str, ...]


def evaluate_case(
    case: EvaluationCase,
    answer: str,
    retrieved_chunk_ids: Sequence[str],
) -> CaseMetrics:
    """Evaluate retrieval and answer properties for one case."""

    relevant = set(case.relevant_chunk_ids)
    retrieved = list(retrieved_chunk_ids)
    hits = relevant.intersection(retrieved)

    retrieval_recall = len(hits) / len(relevant) if relevant else float(not retrieved)
    retrieval_precision = len(hits) / len(retrieved) if retrieved else 0.0
    reciprocal_rank = next(
        (1.0 / (index + 1) for index, chunk_id in enumerate(retrieved) if chunk_id in relevant),
        0.0,
    )

    normalized_answer = _normalize(answer)
    exact_match = float(normalized_answer == _normalize(case.expected_answer))
    required_fact_coverage = _fact_coverage(normalized_answer, case.required_facts)
    abstention_correct = float(_is_abstention(answer) is (not case.answerable))

    return CaseMetrics(
        case_id=case.case_id,
        retrieval_recall=retrieval_recall,
        retrieval_precision=retrieval_precision,
        reciprocal_rank=reciprocal_rank,
        answer_exact_match=exact_match,
        required_fact_coverage=required_fact_coverage,
        abstention_correct=abstention_correct,
    )


def aggregate_metrics(results: Sequence[CaseMetrics]) -> dict[str, float]:
    """Return macro-averaged metrics for a dataset."""

    if not results:
        raise ValueError("At least one evaluation result is required")

    return {
        "retrieval_recall": mean(result.retrieval_recall for result in results),
        "retrieval_precision": mean(result.retrieval_precision for result in results),
        "mrr": mean(result.reciprocal_rank for result in results),
        "answer_exact_match": mean(result.answer_exact_match for result in results),
        "required_fact_coverage": mean(result.required_fact_coverage for result in results),
        "abstention_accuracy": mean(result.abstention_correct for result in results),
    }


def load_cases(path: str | Path) -> list[EvaluationCase]:
    """Load newline-delimited evaluation cases from a JSONL file."""

    cases: list[EvaluationCase] = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
            cases.append(
                EvaluationCase(
                    case_id=payload["case_id"],
                    question=payload["question"],
                    expected_answer=payload["expected_answer"],
                    relevant_chunk_ids=tuple(payload["relevant_chunk_ids"]),
                    required_facts=tuple(payload["required_facts"]),
                    answerable=payload["answerable"],
                )
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError(f"Invalid evaluation case at line {line_number}") from exc
    return cases


def evaluate_dataset(
    cases: Sequence[EvaluationCase],
    observations: dict[str, EvaluationObservation],
) -> tuple[list[CaseMetrics], dict[str, float]]:
    """Evaluate all cases and return per-case and aggregate metrics."""

    results: list[CaseMetrics] = []
    for case in cases:
        try:
            observation = observations[case.case_id]
        except KeyError as exc:
            raise ValueError(f"Missing observation for case {case.case_id}") from exc
        results.append(evaluate_case(case, observation.answer, observation.retrieved_chunk_ids))
    return results, aggregate_metrics(results)


def _fact_coverage(answer: str, required_facts: Sequence[str]) -> float:
    if not required_facts:
        return 1.0
    covered = sum(_normalize(fact) in answer for fact in required_facts)
    return covered / len(required_facts)


def _is_abstention(answer: str) -> bool:
    normalized = _normalize(answer)
    return any(marker in normalized for marker in ABSTENTION_MARKERS)


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()
