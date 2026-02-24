#!/usr/bin/env python3
"""Unit tests for the Gap Score reference validator."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

# Import the validator module
sys.path.insert(0, os.path.dirname(__file__))
from importlib import import_module

# gap-score.py has a hyphen, so we need importlib
import importlib.util

spec = importlib.util.spec_from_file_location(
    "gap_score", os.path.join(os.path.dirname(__file__), "gap-score.py")
)
gap_score = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gap_score)


class TestClassifyGap(unittest.TestCase):
    """Test the classify_gap function."""

    def test_perfect_score(self):
        level, indicator = gap_score.classify_gap(0)
        self.assertEqual(level, "perfect")
        self.assertEqual(indicator, "✅")

    def test_minor_score(self):
        level, indicator = gap_score.classify_gap(10)
        self.assertEqual(level, "minor")
        self.assertEqual(indicator, "🟢")

    def test_minor_boundary(self):
        level, indicator = gap_score.classify_gap(15)
        self.assertEqual(level, "minor")

    def test_moderate_score(self):
        level, indicator = gap_score.classify_gap(20)
        self.assertEqual(level, "moderate")
        self.assertEqual(indicator, "🟡")

    def test_moderate_boundary(self):
        level, indicator = gap_score.classify_gap(30)
        self.assertEqual(level, "moderate")

    def test_significant_score(self):
        level, indicator = gap_score.classify_gap(40)
        self.assertEqual(level, "significant")
        self.assertEqual(indicator, "🟠")

    def test_significant_boundary(self):
        level, indicator = gap_score.classify_gap(50)
        self.assertEqual(level, "significant")

    def test_critical_score(self):
        level, indicator = gap_score.classify_gap(60)
        self.assertEqual(level, "critical")
        self.assertEqual(indicator, "🔴")

    def test_critical_100(self):
        level, indicator = gap_score.classify_gap(100)
        self.assertEqual(level, "critical")


class TestComputeGapScore(unittest.TestCase):
    """Test the compute_gap_score function."""

    def test_empty_tests(self):
        result = gap_score.compute_gap_score([])
        self.assertEqual(result["gap_score"], 0.0)
        self.assertEqual(result["level"], "perfect")
        self.assertEqual(result["total"], 0)

    def test_all_pass(self):
        tests = [
            {"name": "t1", "status": "passed"},
            {"name": "t2", "status": "passed"},
            {"name": "t3", "status": "passed"},
        ]
        result = gap_score.compute_gap_score(tests)
        self.assertEqual(result["gap_score"], 0.0)
        self.assertEqual(result["passed"], 3)
        self.assertEqual(result["failed"], 0)

    def test_all_fail(self):
        tests = [
            {"name": "t1", "status": "failed", "message": "fail1"},
            {"name": "t2", "status": "failed", "message": "fail2"},
        ]
        result = gap_score.compute_gap_score(tests)
        self.assertEqual(result["gap_score"], 100.0)
        self.assertEqual(result["level"], "critical")
        self.assertEqual(result["failed"], 2)

    def test_partial_failure(self):
        tests = [
            {"name": "t1", "status": "passed"},
            {"name": "t2", "status": "failed", "message": "oops"},
            {"name": "t3", "status": "passed"},
            {"name": "t4", "status": "passed"},
            {"name": "t5", "status": "passed"},
        ]
        result = gap_score.compute_gap_score(tests)
        self.assertEqual(result["gap_score"], 20.0)
        self.assertEqual(result["level"], "moderate")
        self.assertEqual(result["failures"], [tests[1]])

    def test_minor_gap(self):
        # 2 out of 18 failed = 11.1%
        tests = [{"name": f"t{i}", "status": "passed"} for i in range(16)]
        tests.append({"name": "f1", "status": "failed", "message": "a"})
        tests.append({"name": "f2", "status": "failed", "message": "b"})
        result = gap_score.compute_gap_score(tests)
        self.assertEqual(result["gap_score"], 11.1)
        self.assertEqual(result["level"], "minor")


class TestBuildReport(unittest.TestCase):
    """Test the build_report function."""

    def test_report_structure(self):
        sealed = [{"name": "t1", "status": "passed", "category": "happy_path"}]
        report = gap_score.build_report(sealed)
        self.assertIn("gap_score_spec_version", report)
        self.assertIn("report", report)
        self.assertIn("sealed_tests", report)
        self.assertIn("failures", report)
        self.assertEqual(report["gap_score_spec_version"], "1.0.0")

    def test_report_with_open_tests(self):
        sealed = [{"name": "s1", "status": "passed", "category": "happy_path"}]
        open_tests = [
            {"name": "o1", "status": "passed", "category": "happy_path"},
            {"name": "o2", "status": "failed", "category": "edge_case"},
        ]
        report = gap_score.build_report(sealed, open_tests)
        self.assertIn("open_tests", report)
        self.assertEqual(report["open_tests"]["total"], 2)
        self.assertEqual(report["open_tests"]["passed"], 1)
        self.assertEqual(report["open_tests"]["failed"], 1)
        self.assertIn("coverage_comparison", report)

    def test_report_without_open_tests(self):
        sealed = [{"name": "s1", "status": "passed", "category": "happy_path"}]
        report = gap_score.build_report(sealed)
        self.assertNotIn("open_tests", report)
        self.assertNotIn("coverage_comparison", report)

    def test_failure_details(self):
        sealed = [
            {
                "name": "t1",
                "status": "failed",
                "category": "security",
                "expected": "hashed",
                "actual": "plaintext",
                "message": "Not hashed",
            }
        ]
        report = gap_score.build_report(sealed)
        self.assertEqual(len(report["failures"]), 1)
        f = report["failures"][0]
        self.assertEqual(f["test_name"], "t1")
        self.assertEqual(f["category"], "security")
        self.assertEqual(f["expected"], "hashed")
        self.assertEqual(f["actual"], "plaintext")
        self.assertEqual(f["message"], "Not hashed")


class TestCoverageComparison(unittest.TestCase):
    """Test the build_coverage_comparison function."""

    def test_empty_suites(self):
        result = gap_score.build_coverage_comparison([], [])
        for cat in gap_score.CATEGORIES:
            self.assertEqual(result[cat]["sealed"], 0)
            self.assertEqual(result[cat]["open"], 0)
            self.assertEqual(result[cat]["delta"], 0)

    def test_category_counting(self):
        sealed = [
            {"name": "s1", "category": "security"},
            {"name": "s2", "category": "security"},
            {"name": "s3", "category": "happy_path"},
        ]
        open_tests = [
            {"name": "o1", "category": "happy_path"},
            {"name": "o2", "category": "happy_path"},
        ]
        result = gap_score.build_coverage_comparison(sealed, open_tests)
        self.assertEqual(result["security"]["sealed"], 2)
        self.assertEqual(result["security"]["open"], 0)
        self.assertEqual(result["security"]["delta"], 2)
        self.assertEqual(result["happy_path"]["sealed"], 1)
        self.assertEqual(result["happy_path"]["open"], 2)
        self.assertEqual(result["happy_path"]["delta"], -1)


class TestLoadResults(unittest.TestCase):
    """Test the load_results function."""

    def test_load_valid_json(self):
        data = {"tests": [{"name": "t1", "status": "passed"}]}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            f.flush()
            results = gap_score.load_results(f.name)
        os.unlink(f.name)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "t1")

    def test_load_missing_tests_key(self):
        data = {"other": "data"}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            f.flush()
            results = gap_score.load_results(f.name)
        os.unlink(f.name)
        self.assertEqual(results, [])


class TestExamples(unittest.TestCase):
    """Validate the reference examples produce expected Gap Scores."""

    EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")

    def _run_example(self, example_dir):
        sealed_path = os.path.join(self.EXAMPLES_DIR, example_dir, "sealed-results.json")
        open_path = os.path.join(self.EXAMPLES_DIR, example_dir, "open-results.json")
        sealed = gap_score.load_results(sealed_path)
        open_tests = gap_score.load_results(open_path)
        return gap_score.build_report(sealed, open_tests)

    def test_example_01_perfect_score(self):
        report = self._run_example("01-perfect-score")
        self.assertEqual(report["report"]["gap_score"], 0.0)
        self.assertEqual(report["report"]["level"], "perfect")

    def test_example_02_minor_gaps(self):
        report = self._run_example("02-minor-gaps")
        self.assertEqual(report["report"]["gap_score"], 11.1)
        self.assertEqual(report["report"]["level"], "minor")

    def test_example_03_critical_gaps(self):
        report = self._run_example("03-critical-gaps")
        self.assertEqual(report["report"]["gap_score"], 60.0)
        self.assertEqual(report["report"]["level"], "critical")


if __name__ == "__main__":
    unittest.main()
