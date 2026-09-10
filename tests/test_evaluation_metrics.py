from __future__ import annotations

import pytest

from evaluation.metrics import (
    EvaluationCase,
    EvaluationObservation,
    aggregate_metrics,
    evaluate_case,
    evaluate_dataset,
)


def test_evaluate_case_measures_retrieval_and_required_facts() -> None:
    case = EvaluationCase(
        case_id="python-author",
        question="Who created Python?",
        expected_answer="Guido van Rossum",
        relevant_chunk_ids=("chunk-1",),
        required_facts=("Guido van Rossum",),
        answerable=True,
    )

    result = evaluate_case(case, "Guido van Rossum", ["chunk-2", "chunk-1"])

    assert result.retrieval_recall == 1.0
    assert result.retrieval_precision == 0.5
    assert result.reciprocal_rank == 0.5
    assert result.answer_exact_match == 1.0
    assert result.required_fact_coverage == 1.0
    assert result.abstention_correct == 1.0


def test_unanswerable_case_requires_explicit_abstention() -> None:
    case = EvaluationCase(
        case_id="missing-fact",
        question="What is the launch date?",
        expected_answer="",
        relevant_chunk_ids=(),
        required_facts=(),
        answerable=False,
    )

    result = evaluate_case(case, "The answer cannot be found in the context.", [])

    assert result.retrieval_recall == 1.0
    assert result.abstention_correct == 1.0


def test_aggregate_metrics_rejects_empty_results() -> None:
    with pytest.raises(ValueError, match="At least one"):
        aggregate_metrics([])


def test_evaluate_dataset_aggregates_observations() -> None:
    case = EvaluationCase(
        case_id="case-1",
        question="What is the answer?",
        expected_answer="42",
        relevant_chunk_ids=("chunk-1",),
        required_facts=("42",),
        answerable=True,
    )

    results, aggregate = evaluate_dataset(
        [case],
        {"case-1": EvaluationObservation("42", ("chunk-1",))},
    )

    assert len(results) == 1
    assert aggregate["retrieval_recall"] == 1.0
    assert aggregate["required_fact_coverage"] == 1.0
