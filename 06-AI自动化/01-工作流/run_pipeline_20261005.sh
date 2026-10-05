#!/usr/bin/env bash
cd "D:/a10/aikjx/code/my_lib/openmath" || exit 1
PY="C:/Users/mo/.workbuddy/binaries/python/versions/3.13.12/python.exe"
W="06-AI自动化/01-工作流"
TS="20261005_100222"
LOG="$W/PIPELINE_${TS}.log"
echo "PIPELINE START $(date)" > "$LOG"

run_stage() {
  local n="$1" f="$2"
  echo "=== STAGE $n: $f ===" >> "$LOG"
  local start end rc
  start=$(date +%s)
  "$PY" "$W/$f.py" >> "$LOG" 2>&1
  rc=$?
  end=$(date +%s)
  echo "STAGE $n EXIT=$rc TIME=$((end-start))s" >> "$LOG"
  printf "STAGE %s: %s EXIT=%s TIME=%ss\n" "$n" "$f" "$rc" "$((end-start))"
  return $rc
}

overall=0
run_stage 1 openmath_ingest          || overall=1
run_stage 2 openmath_analyze         || overall=1
run_stage 3 openmath_experiments      || overall=1
run_stage 4 openmath_coalition       || overall=1
run_stage 5 openmath_synthesis       || overall=1
run_stage 6 openmath_meta            || overall=1
run_stage 7 openmath_theory          || overall=1
run_stage 10 openmath_millennium     || overall=1
run_stage 8 openmath_audit           || overall=1
run_stage 9 openmath_sequences       || overall=1

echo "=== PIPELINE OVERALL rc=$overall ===" >> "$LOG"
echo "PIPELINE DONE overall_rc=$overall"
exit $overall
