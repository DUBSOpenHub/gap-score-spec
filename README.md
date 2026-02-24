# 📊 Gap Score Spec

[![Spec Version](https://img.shields.io/badge/spec-v1.0.0-blue.svg)](SPEC.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Conformance Levels](https://img.shields.io/badge/conformance-L1%20%7C%20L2%20%7C%20L3-green.svg)](SPEC.md#6-conformance-levels)

**A framework-agnostic metric for measuring AI code generation quality.**

---

## The Problem

AI coding tools write code and tests together. The tests always pass -- but they only validate what the AI *thought* to check, not what the *specification actually requires*. There's no independent quality signal.

## The Solution

```
Gap Score = (sealed_failures / sealed_total) × 100
```

Generate acceptance tests from the spec **before code exists**. Hide them from the AI. Build the code. Then run both test suites. The delta is your **Gap Score** -- an adversarial, quantitative measure of implementation quality.

## Interpretation Scale

| Score | Level | Meaning |
|-------|-------|---------|
| 0% | ✅ Perfect | Implementation tests covered everything |
| 1–15% | 🟢 Minor | Small blind spots -- edge cases |
| 16–30% | 🟡 Moderate | Meaningful gaps in coverage |
| 31–50% | 🟠 Significant | Major gaps -- review approach |
| >50% | 🔴 Critical | Fundamental quality issues |

## Quick Start: Add Gap Score in 5 Minutes

### Option A: Use the reference validators

```bash
# Python
python validators/gap-score.py --sealed results-sealed.json --open results-open.json

# Go
cd validators && go build -o gap-score-go . && cd ..
./validators/gap-score-go --sealed results-sealed.json --open results-open.json

# Shell (minimal deps)
./validators/gap-score.sh results-sealed.txt results-open.txt
```

### Option B: Compute it yourself

1. **Write sealed tests** from your spec (requirements → test cases, before code exists)
2. **Build the code** -- the implementer never sees the sealed tests
3. **Run both suites** -- sealed tests and the implementer's own tests
4. **Compute**: `failed_sealed / total_sealed × 100`
5. **Report**: Use the [JSON schema](validators/gap-report-schema.json) or markdown format

That's it. Framework, language, and tooling don't matter -- Gap Score works anywhere.

## The Sealed-Envelope Protocol

Gap Score is computed using the **Sealed-Envelope Protocol** -- a 4-phase testing methodology:

```
 SPEC ──► SEAL GENERATION ──► IMPLEMENTATION ──► VALIDATION ──► HARDENING
           (tests from spec,     (code + own        (run both      (fix from
            hidden from          tests, never       suites,       failure msgs
            implementer)         sees sealed)       compute gap)   only -- no
                                                                  test code)
```

**The critical rule:** The implementer **never sees** the sealed tests. During hardening, they receive only failure messages (test name, expected, actual) -- never the test source code. This forces root-cause fixes, not test-targeting hacks.

Full protocol details: [**SPEC.md §4**](SPEC.md#4-sealed-envelope-protocol)

## Conformance Levels

| Level | What's Required | Use Case |
|-------|----------------|----------|
| **L1** -- Gap Score | Compute + report Gap Score | Retrofitting onto existing test suites |
| **L2** -- Sealed Envelope | L1 + test isolation + tamper hash | AI agent pipelines |
| **L3** -- Full Protocol | L2 + hardening loop + velocity tracking | Production autonomous builds |

## Reference Implementation

The reference Level 3 implementation is **[Dark Factory](https://github.com/DUBSOpenHub/dark-factory)** -- an autonomous agentic build system for the GitHub Copilot CLI with sealed-envelope testing.

## Worked Examples

| Example | Gap Score | What Happened |
|---------|-----------|---------------|
| [01 -- Perfect Score](examples/01-perfect-score/) | 0% ✅ | All sealed tests passed |
| [02 -- Minor Gaps](examples/02-minor-gaps/) | 11.1% 🟢 | 2 edge cases missed |
| [03 -- Critical Gaps](examples/03-critical-gaps/) | 60% 🔴 | Only happy path tested |

## Reporting Format

Gap Reports can be produced in JSON (machine-readable) or Markdown (human-readable).

**JSON schema:** [`validators/gap-report-schema.json`](validators/gap-report-schema.json)

```json
{
  "gap_score_spec_version": "1.0.0",
  "report": {
    "gap_score": 11.1,
    "level": "minor"
  },
  "sealed_tests": { "total": 18, "passed": 16, "failed": 2 },
  "failures": [
    {
      "test_name": "test_rejects_gpl_dependency",
      "category": "security",
      "expected": "exit code 2",
      "actual": "exit code 0",
      "message": "GPL dependency not blocked"
    }
  ]
}
```

Full schema: [**SPEC.md §5**](SPEC.md#5-reporting-format)

## Adopters

| Project | Conformance | Description |
|---------|-------------|-------------|
| [Dark Factory](https://github.com/DUBSOpenHub/dark-factory) | Level 3 | Reference implementation -- autonomous agentic build system |

*Using Gap Score? [Open a PR](https://github.com/DUBSOpenHub/gap-score-spec/pulls) to add your project.*

## Full Specification

📄 **[Read the full spec →](SPEC.md)**

Covers: definitions, formula, sealed-envelope protocol, reporting format, conformance levels, worked examples, and FAQ.

## Contributing

Gap Score is an open specification. Contributions welcome:

- **Spec changes**: Open an issue to discuss before submitting a PR
- **New validators**: PRs for additional language validators (Go, Rust, TypeScript) are welcome
- **Adopter listings**: Add your project to the Adopters table

## License

[MIT](LICENSE) © 2026 DUBSOpenHub
