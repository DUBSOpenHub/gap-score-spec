# Example 03 -- Critical Gaps (60%)

**Scenario:** User registration REST API  
**Gap Score:** 60% 🔴 Critical

## What Happened

The Implementer wrote only 4 tests -- all happy path. The sealed suite had 15 tests
and 9 failed, revealing severe blind spots:

| # | Failure | Category |
|---|---------|----------|
| 1 | Passwords stored in plaintext | 🔴 Security |
| 2 | Duplicate email → HTTP 500 (unhandled) | Error handling |
| 3 | Invalid email format accepted | Error handling |
| 4 | Empty password accepted | Error handling |
| 5 | Short password (< 8 chars) accepted | Edge case |
| 6 | SQL injection via email field | 🔴 Security |
| 7 | No rate limiting | 🔴 Security |
| 8 | Password leaked in API response | 🔴 Security |
| 9 | Race condition on duplicate email | Edge case |

**Analysis:** The Implementer built the "golden path" -- register a user, get a
response, save to database. But it completely missed input validation, security
hardening, and error handling. 4 of the 9 failures are security vulnerabilities.

**Recommendation:** Re-implement with explicit attention to the security and error
handling requirements in the specification.

## Run the Validator

```bash
python ../../validators/gap-score.py \
  --sealed sealed-results.json \
  --open open-results.json \
  --format summary
```

**Expected output:**
```
Gap Score: 60.0% 🔴 (critical)
Sealed: 6/15 passed
Open:   4/4 passed

Failures (9):
  ❌ test_register_hashes_password: Passwords not hashed before storage
  ❌ test_duplicate_email_returns_409: Duplicate email causes unhandled database error
  ❌ test_invalid_email_rejected: Invalid email format accepted without validation
  ❌ test_empty_password_rejected: Empty password accepted
  ❌ test_password_min_length: Short password accepted
  ❌ test_sql_injection_in_email: SQL injection possible via email field
  ❌ test_rate_limiting: No rate limiting on registration endpoint
  ❌ test_response_excludes_password: Password leaked in API response
  ❌ test_concurrent_registration: Race condition allows duplicate registration
```
