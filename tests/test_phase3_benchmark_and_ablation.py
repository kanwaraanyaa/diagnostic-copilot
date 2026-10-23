"""
Tests for Benchmark Dataset and Ablation Study Engine — Phase 3.
"""

from __future__ import annotations

import pytest
from evaluation.benchmark_dataset import (
    load_benchmark_cases,
    get_benchmark_case_by_id,
    BENCHMARK_CASES_CATALOG,
)
from evaluation.benchmark_runner import (
    run_benchmark_suite,
    BenchmarkRunResult,
)
from evaluation.ablation import (
    run_ablation_study,
    AblationStudyResult,
)


def test_benchmark_dataset_integrity():
    cases = load_benchmark_cases()
    assert len(cases) == 50
    assert len(BENCHMARK_CASES_CATALOG) == 50

    categories = {c.category for c in cases}
    assert "Cardiovascular" in categories
    assert "Respiratory" in categories
    assert "Infectious" in categories
    assert "Renal/Metabolic" in categories
    assert "Gastrointestinal" in categories
    assert "Neurological" in categories

    for c in cases:
        assert c.case_id.startswith("BM-")
        assert len(c.symptoms) > 0
        assert len(c.gold_standard_primary) > 0
        assert len(c.critical_rule_outs) > 0


def test_get_benchmark_case_by_id():
    c = get_benchmark_case_by_id("BM-RESP-01")
    assert c is not None
    assert c.case_id == "BM-RESP-01"
    assert c.category == "Respiratory"
    assert "Pneumonia" in c.gold_standard_primary


def test_benchmark_runner_execution():
    # Test on small sample (2 cases) for speed
    res = run_benchmark_suite(max_cases=2)
    assert isinstance(res, BenchmarkRunResult)
    assert res.total_cases_evaluated == 2
    assert len(res.case_details) == 2
    assert res.mean_faithfulness_score > 0.0


def test_ablation_study_execution():
    # Test on small sample (2 cases) for speed
    res = run_ablation_study(max_cases=2)
    assert isinstance(res, AblationStudyResult)
    assert res.cases_evaluated == 2
    assert len(res.variants) == 5
    var_ids = [v.variant_id for v in res.variants]
    assert "proposed_system" in var_ids
    assert "no_debate" in var_ids
    assert "single_agent_rag" in var_ids
