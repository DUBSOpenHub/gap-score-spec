#!/usr/bin/env bash
# Gap Score Reference Validator (Shell)
# Conforms to Gap Score Spec v1.0.0
#
# Usage:
#   ./gap-score.sh <sealed_total> <sealed_failed> [threshold]
#
# Examples:
#   ./gap-score.sh 18 2           # Compute gap score: 11.1%
#   ./gap-score.sh 18 2 15        # Compute + exit 1 if > 15%
#   ./gap-score.sh 15 9 30        # Compute + exit 1 if > 30%

set -euo pipefail

SPEC_VERSION="1.0.0"

if [ $# -lt 2 ]; then
    echo "Usage: $0 <sealed_total> <sealed_failed> [threshold]"
    echo ""
    echo "Gap Score Reference Validator (Spec v${SPEC_VERSION})"
    echo "Computes: (sealed_failed / sealed_total) × 100"
    exit 2
fi

SEALED_TOTAL=$1
SEALED_FAILED=$2
THRESHOLD=${3:-}

if [ "$SEALED_TOTAL" -eq 0 ]; then
    echo "Gap Score: 0% ✅ (perfect -- no sealed tests)"
    exit 0
fi

# Compute gap score (bash integer math → multiply first to preserve precision)
GAP_SCORE_X10=$(( (SEALED_FAILED * 1000) / SEALED_TOTAL ))
GAP_WHOLE=$(( GAP_SCORE_X10 / 10 ))
GAP_DECIMAL=$(( GAP_SCORE_X10 % 10 ))
GAP_SCORE="${GAP_WHOLE}.${GAP_DECIMAL}"

# Classify level
if [ "$GAP_SCORE_X10" -eq 0 ]; then
    LEVEL="perfect"
    INDICATOR="✅"
elif [ "$GAP_SCORE_X10" -le 150 ]; then
    LEVEL="minor"
    INDICATOR="🟢"
elif [ "$GAP_SCORE_X10" -le 300 ]; then
    LEVEL="moderate"
    INDICATOR="🟡"
elif [ "$GAP_SCORE_X10" -le 500 ]; then
    LEVEL="significant"
    INDICATOR="🟠"
else
    LEVEL="critical"
    INDICATOR="🔴"
fi

SEALED_PASSED=$(( SEALED_TOTAL - SEALED_FAILED ))

echo "Gap Score: ${GAP_SCORE}% ${INDICATOR} (${LEVEL})"
echo "Sealed: ${SEALED_PASSED}/${SEALED_TOTAL} passed, ${SEALED_FAILED} failed"

# Threshold check
if [ -n "$THRESHOLD" ]; then
    THRESHOLD_X10=$(( THRESHOLD * 10 ))
    if [ "$GAP_SCORE_X10" -gt "$THRESHOLD_X10" ]; then
        echo "FAIL: Gap Score ${GAP_SCORE}% exceeds threshold ${THRESHOLD}%"
        exit 1
    else
        echo "PASS: Gap Score ${GAP_SCORE}% within threshold ${THRESHOLD}%"
        exit 0
    fi
fi
