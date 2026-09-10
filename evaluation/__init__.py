"""Offline evaluation primitives for the RAG pipeline."""

from evaluation.metrics import (
    CaseMetrics,
    EvaluationCase,
    EvaluationObservation,
    aggregate_metrics,
    evaluate_case,
    evaluate_dataset,
    load_cases,
)

__all__ = [
    "CaseMetrics",
    "EvaluationCase",
    "EvaluationObservation",
    "aggregate_metrics",
    "evaluate_case",
    "evaluate_dataset",
    "load_cases",
]
