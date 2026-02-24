# Example 02 -- Minor Gaps (11.1%)

**Scenario:** License scanner CLI tool  
**Gap Score:** 11.1% 🟢 Minor

## What Happened

The Implementer built solid core functionality with 12 tests covering happy path,
edge cases, and error handling. However, the sealed suite caught two gaps:

1. **`test_rejects_gpl_dependency`** -- The scanner didn't block GPL-licensed
   dependencies when running in "compliance mode." The Implementer hadn't considered
   license policy enforcement as a feature.

2. **`test_csv_report_includes_risk`** -- The CSV export was missing a "risk" column
   that the specification required. The Implementer tested the CSV had the right
   license data but missed this metadata field.

Both were fixed in one hardening cycle after receiving the failure messages.

## Run the Validator

```bash
python ../../validators/gap-score.py \
  --sealed sealed-results.json \
  --open open-results.json \
  --format summary
```

**Expected output:**
```
Gap Score: 11.1% 🟢 (minor)
Sealed: 16/18 passed
Open:   12/12 passed

Failures (2):
  ❌ test_rejects_gpl_dependency: GPL dependency not blocked
  ❌ test_csv_report_includes_risk: Report missing risk metadata
```
