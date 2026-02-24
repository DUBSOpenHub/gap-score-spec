# Gap Score Specification

**Version:** 1.0.0  
**Status:** Draft  
**Date:** 2026-02-24  
**Authors:** DUBSOpenHub  
**License:** MIT  

---

## 1. Abstract

**Gap Score** is a framework-agnostic metric for measuring the quality of AI-generated code. It quantifies the difference between what an AI implementation agent *tested for itself* and what an independent, specification-derived test suite *actually requires*. A Gap Score of 0% means the implementation's own tests fully anticipated the acceptance criteria. A high Gap Score reveals blind spots — requirements the AI "thought" it covered but didn't.

Gap Score is computed using the **Sealed-Envelope Protocol**, a testing methodology where acceptance tests are generated from the specification *before code is written* and hidden from the implementation agent throughout the build process.

---

## 2. Motivation

### The Teach-to-Test Problem

Most AI coding tools write code and tests together. The AI generates an implementation, then writes tests that validate *what it built* — not *what was required*. These tests almost always pass, creating a false sense of quality.

This is analogous to a student writing both the exam and the answer key. A 100% score is guaranteed but meaningless.

### What's Missing

The industry lacks a standardized, quantitative metric for answering: **"How well did the AI understand and implement the specification, independent of its own self-assessment?"**

Existing metrics fall short:

| Metric | Limitation |
|--------|-----------|
| Test pass rate | AI writes tests to match its own code — circular |
| Code coverage | Measures lines executed, not requirements fulfilled |
| Human code review | Subjective, expensive, doesn't scale |
| LLM-as-judge | Another AI evaluating AI — same blindness risk |

### Gap Score Solves This

Gap Score introduces an **independent, adversarial quality signal** by separating test authorship from code authorship and measuring the delta. It answers a specific question: *"What percentage of specification requirements did the implementation fail to satisfy, as measured by tests the implementer never saw?"*

---

## 3. Definitions

### 3.1 Roles

| Role | Responsibility | Information Access |
|------|---------------|-------------------|
| **Specifier** | Produces the specification (requirements, acceptance criteria) | Full project context |
| **Seal Author** | Generates specification tests (sealed tests) from the spec | Specification ONLY — never code, never architecture |
| **Implementer** | Writes code and implementation tests (open tests) | Specification + architecture — NEVER sealed tests |
| **Validator** | Runs all tests and computes Gap Score | Full access: code + sealed tests + open tests |

In an AI agent pipeline, each role is typically a separate agent invocation with isolated context. In a human workflow, roles may be assigned to different team members.

### 3.2 Test Suites

- **Sealed Tests** (`S`): Tests generated from the specification before any implementation exists. These tests are hidden from the Implementer. They validate *requirements*, not *implementation details*.

- **Open Tests** (`O`): Tests written by the Implementer alongside the code. These validate the Implementer's own understanding of the requirements.

### 3.3 Gap Score Formula

```
Gap Score = (Sf / St) × 100
```

Where:
- `Sf` = Number of sealed tests that **failed**
- `St` = Total number of sealed tests
- Result is expressed as a percentage (0–100)

### 3.4 Interpretation Scale

| Score | Level | Indicator | Meaning |
|-------|-------|-----------|---------|
| 0% | Perfect | ✅ | Implementer's tests covered everything the sealed tests checked |
| 1–15% | Minor | 🟢 | Small blind spots — likely edge cases or boundary conditions |
| 16–30% | Moderate | 🟡 | Meaningful gaps — Implementer missed some scenarios |
| 31–50% | Significant | 🟠 | Major gaps — review the Implementer's testing approach |
| >50% | Critical | 🔴 | Fundamental quality issues — consider re-implementation |

### 3.5 Supplementary Metrics

These optional metrics provide additional context alongside the primary Gap Score:

- **Coverage Delta**: `|sealed_categories_tested - open_categories_tested|` — measures how many *types* of scenarios (happy path, edge case, error handling, security) differ between suites.
- **Overlap Ratio**: `matching_scenarios / St` — measures how many sealed test scenarios the Implementer independently anticipated.
- **Hardening Velocity**: `gap_reduction_per_cycle` — measures how quickly the Gap Score decreases during iterative fixing.

---

## 4. Sealed-Envelope Protocol

The Sealed-Envelope Protocol is the testing methodology that produces a valid Gap Score. Implementations MUST follow this protocol to claim Gap Score conformance.

### 4.1 Seal Generation

**Input:** Specification document (requirements, acceptance criteria, user stories).  
**Output:** Sealed test files written to an isolated location.

Requirements:
1. The Seal Author receives ONLY the specification — never code, architecture, or design documents.
2. Sealed tests MUST validate **behavior**, not implementation details (no testing internal functions, private APIs, or data structures).
3. Sealed tests MUST cover:
   - Happy path scenarios (expected inputs → expected outputs)
   - Edge cases and boundary conditions
   - Error handling and invalid inputs
   - Security scenarios (where applicable)
4. Sealed tests MUST be executable by a standard test runner for the target language/framework.
5. After generation, the sealed test directory SHOULD be hashed (SHA-256) as tamper evidence.

### 4.2 Information Isolation

This is the **critical invariant** of the protocol. Breaking isolation invalidates the Gap Score.

| Phase | Seal Author Sees | Implementer Sees | Validator Sees |
|-------|-----------------|------------------|---------------|
| Seal Generation | Specification | — | — |
| Implementation | — | Specification, Architecture | — |
| Validation | — | — | Code, Sealed Tests, Open Tests |
| Hardening | — | Failure messages ONLY | Code, All Tests |

**Isolation mechanisms** (in order of strength):
1. **Process isolation**: Separate OS processes with no shared filesystem access (strongest)
2. **Context isolation**: Separate AI agent invocations with no shared context (recommended for AI pipelines)
3. **Role isolation**: Different humans/teams with access controls (acceptable for human workflows)
4. **Honor system**: Trust-based separation (weakest — not recommended for conformance claims)

### 4.3 Validation

**Input:** Implementation code, sealed tests, open tests.  
**Output:** Gap Report (see §5).

Procedure:
1. Copy sealed tests into the implementation workspace
2. Install dependencies and build the project
3. Run sealed tests using the appropriate test runner
4. Run open tests using the appropriate test runner
5. Record: total sealed tests, passed, failed (with failure messages)
6. Record: total open tests, passed, failed
7. Compute Gap Score: `(sealed_failures / sealed_total) × 100`
8. Categorize failures by type (happy path, edge case, error handling, security)
9. Produce Gap Report

### 4.4 Hardening

When Gap Score > 0%, the Implementer may fix the code iteratively. The hardening loop preserves information isolation:

1. Extract from the Gap Report: test name, expected result, actual result, failure message
2. **Do NOT** share the sealed test source code with the Implementer
3. The Implementer fixes the implementation based on failure descriptions only
4. Re-run validation (§4.3)
5. Repeat up to a configured maximum number of cycles
6. If Gap Score remains > 0% after max cycles, escalate to human review

**Rationale:** Sharing only failure messages (not test code) forces the Implementer to fix the *root cause* rather than pattern-match against specific test assertions.

### 4.5 Tamper Evidence

To ensure sealed tests are not modified after generation:

1. After seal generation, compute: `hash = SHA-256(sorted_file_contents_of_sealed_directory)`
2. Store the hash in a tamper-evident log (e.g., state file, database, version control)
3. Before validation, recompute the hash and compare
4. If hashes differ, the Gap Score is **invalid** — sealed tests were tampered with

**Recommended implementation:**
```bash
find <sealed_dir> -type f | sort | xargs shasum -a 256 | shasum -a 256
```

---

## 5. Reporting Format

### 5.1 Gap Report Structure

Implementations SHOULD produce a Gap Report in at least one of these formats:

#### JSON Format (machine-readable)

```json
{
  "gap_score_spec_version": "1.0.0",
  "report": {
    "id": "run-20260224-1200",
    "timestamp": "2026-02-24T12:00:00Z",
    "specification": "PRD.md",
    "gap_score": 11.1,
    "level": "minor",
    "sealed_hash": "sha256:a1b2c3d4..."
  },
  "sealed_tests": {
    "total": 18,
    "passed": 16,
    "failed": 2
  },
  "open_tests": {
    "total": 12,
    "passed": 12,
    "failed": 0
  },
  "failures": [
    {
      "test_name": "test_rejects_gpl_dependency",
      "category": "security",
      "expected": "CLI exits with code 2",
      "actual": "CLI exits with code 0",
      "message": "GPL dependency not blocked"
    },
    {
      "test_name": "test_csv_report_includes_risk",
      "category": "edge_case",
      "expected": "CSV contains risk column",
      "actual": "Column missing",
      "message": "Report missing risk metadata"
    }
  ],
  "coverage_comparison": {
    "happy_path": { "open": 6, "sealed": 6, "delta": 0 },
    "edge_cases": { "open": 3, "sealed": 5, "delta": 2 },
    "error_handling": { "open": 3, "sealed": 4, "delta": 1 },
    "security": { "open": 0, "sealed": 3, "delta": 3 }
  },
  "hardening": {
    "cycles_completed": 1,
    "max_cycles": 3,
    "initial_gap_score": 22.2,
    "final_gap_score": 11.1
  }
}
```

#### Markdown Format (human-readable)

See `examples/` for complete rendered examples.

### 5.2 Required Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `gap_score_spec_version` | string | ✅ | Spec version this report conforms to |
| `gap_score` | number | ✅ | The computed Gap Score (0–100) |
| `level` | string | ✅ | One of: `perfect`, `minor`, `moderate`, `significant`, `critical` |
| `sealed_tests.total` | integer | ✅ | Total sealed tests run |
| `sealed_tests.passed` | integer | ✅ | Sealed tests that passed |
| `sealed_tests.failed` | integer | ✅ | Sealed tests that failed |
| `failures` | array | ✅ | List of failure objects (test_name, expected, actual, message) |
| `sealed_hash` | string | RECOMMENDED | SHA-256 hash of sealed test directory |
| `open_tests.*` | object | RECOMMENDED | Open test results for comparison |
| `coverage_comparison` | object | OPTIONAL | Category-level breakdown |
| `hardening` | object | OPTIONAL | Hardening loop metadata |

### 5.3 Failure Categories

Implementations SHOULD categorize each sealed test into one of:

| Category | Description |
|----------|-------------|
| `happy_path` | Standard expected-input → expected-output scenarios |
| `edge_case` | Boundary conditions, empty inputs, max values, unicode |
| `error_handling` | Invalid inputs, missing data, malformed requests |
| `security` | Injection, overflow, unauthorized access, data leakage |

---

## 6. Conformance Levels

Implementations may claim conformance at three levels:

### Level 1 — Gap Score Computation
**Requirements:**
- Computes Gap Score using the formula in §3.3
- Produces a Gap Report with all required fields (§5.2)
- Uses the interpretation scale in §3.4

**Does NOT require:** Sealed-envelope isolation (tests may be authored with knowledge of the implementation).

**Use case:** Retrofitting Gap Score onto existing test suites for comparative analysis.

### Level 2 — Sealed-Envelope Isolation
**Requirements:**
- All of Level 1
- Sealed tests are generated before implementation begins
- Information isolation (§4.2) is enforced at context-isolation level or stronger
- Tamper evidence hash is computed and stored (§4.5)

**Use case:** AI agent pipelines and multi-agent build systems.

### Level 3 — Full Protocol with Hardening
**Requirements:**
- All of Level 2
- Hardening loop (§4.4) is implemented
- Failure messages shared with Implementer do NOT include test source code
- Hardening velocity is tracked
- Gap Score is recomputed after each hardening cycle

**Use case:** Production-grade autonomous build systems.

---

## 7. Reference Implementation

The reference implementation of the Gap Score Specification is **[Dark Factory](https://github.com/DUBSOpenHub/dark-factory)**, an autonomous agentic build system for the GitHub Copilot CLI.

Dark Factory implements **Level 3** conformance:
- Sealed tests generated by QA Sealed agent from PRD only (§4.1)
- Context-isolated agents via separate `task()` invocations (§4.2)
- QA Validator runs both suites and produces Gap Report (§4.3)
- Hardening loop with failure-message-only feedback (§4.4)
- SHA-256 hash computed and stored in state.json (§4.5)

Lightweight reference validators for computing Gap Score from test output are available in the [`validators/`](./validators/) directory.

---

## Appendix A: Worked Examples

### A.1 — Perfect Score (0%)

**Scenario:** Build a Fibonacci calculator CLI.

| Suite | Total | Passed | Failed |
|-------|-------|--------|--------|
| Sealed | 5 | 5 | 0 |
| Open | 8 | 8 | 0 |

**Gap Score:** `0 / 5 × 100 = 0%` ✅ Perfect

The Implementer's tests covered all scenarios the sealed tests checked, plus 3 additional cases. This indicates thorough understanding of the specification.

### A.2 — Minor Gaps (11.1%)

**Scenario:** Build a license scanner CLI tool.

| Suite | Total | Passed | Failed |
|-------|-------|--------|--------|
| Sealed | 18 | 16 | 2 |
| Open | 12 | 12 | 0 |

**Gap Score:** `2 / 18 × 100 = 11.1%` 🟢 Minor

**Failures:**
1. `test_rejects_gpl_dependency` — GPL dependency not blocked (security gap)
2. `test_csv_report_includes_risk` — Report missing risk column (edge case)

The Implementer built solid core functionality but missed a security edge case and a reporting detail. One hardening cycle resolved both.

### A.3 — Critical Gaps (60%)

**Scenario:** Build a user registration API.

| Suite | Total | Passed | Failed |
|-------|-------|--------|--------|
| Sealed | 15 | 6 | 9 |
| Open | 4 | 4 | 0 |

**Gap Score:** `9 / 15 × 100 = 60%` 🔴 Critical

The Implementer wrote only 4 tests — all happy path. Sealed tests caught: missing email validation, no password hashing, duplicate user returns 500 instead of 409, SQL injection vulnerability, missing rate limiting, and more. This indicates the Implementer built to the "golden path" without considering real-world edge cases.

**Recommendation:** Re-implement with explicit attention to error handling and security requirements.

---

## Appendix B: FAQ

**Q: Can I use Gap Score without AI agents?**  
A: Yes. Gap Score works with any workflow where one party writes specification-based tests and another party implements the code. Human teams can use it for code review, pair programming assessment, or contractor evaluation.

**Q: What if the sealed tests themselves are wrong?**  
A: Sealed tests should be reviewed by a human (or a separate validator) before being finalized. Buggy sealed tests inflate the Gap Score incorrectly. The tamper evidence hash (§4.5) ensures they aren't changed after the fact — but it doesn't guarantee correctness.

**Q: Does a 0% Gap Score mean the code is perfect?**  
A: No. It means the code passes all sealed tests. The sealed tests may not cover every possible scenario. Gap Score measures *specification compliance*, not *absolute correctness*.

**Q: How many sealed tests should I write?**  
A: Enough to cover every acceptance criterion in the specification, including happy path, edge cases, error handling, and security. As a guideline: 3–5 sealed tests per acceptance criterion.

**Q: Can the Implementer game the system?**  
A: If information isolation (§4.2) is properly enforced, no. The Implementer cannot see the sealed tests and therefore cannot write code that specifically targets them. If isolation is broken, the Gap Score is invalid.

**Q: How does Gap Score compare to code coverage?**  
A: Code coverage measures *lines of code executed by tests*. Gap Score measures *specification requirements satisfied by the implementation*. You can have 100% code coverage and a 50% Gap Score (the code runs but produces wrong results for half the requirements).

**Q: Is Gap Score useful for non-AI development?**  
A: Yes. Any team practicing independent verification and validation (IV&V) can benefit. The concept originates from quality engineering practices used in aerospace, medical devices, and safety-critical systems.

---

## Appendix C: Changelog

### 1.0.0 (2026-02-24)
- Initial specification release
- Gap Score formula and interpretation scale
- Sealed-Envelope Protocol (4 phases)
- Reporting format (JSON + Markdown)
- Three conformance levels
- Reference implementation: Dark Factory
