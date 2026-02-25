# Example 01 — Perfect Score (0%)

**Scenario:** Fibonacci calculator CLI  
**Shadow Score:** 0% ✅ Perfect

## What Happened

The Implementer wrote 8 tests covering happy path, error handling, and edge cases.
The sealed suite had 5 tests — all passed. The Implementer independently anticipated
every scenario the sealed tests checked, plus 3 additional cases.

## Run the Validator

```bash
python ../../validators/shadow-score.py \
  --sealed sealed-results.json \
  --open open-results.json \
  --format summary
```

**Expected output:**
```
Shadow Score: 0.0% ✅ (perfect)
Sealed: 5/5 passed
Open:   8/8 passed
```
