#!/usr/bin/env bash
# Runner for OpenMath ten-stage pipeline (order S1..S10: ①②③④⑤⑥⑦⑩⑧⑨)
set -u
PY="C:/Users/mo/.workbuddy/binaries/python/versions/3.13.12/python.exe"
WD="D:/a10/aikjx/code/my_lib/openmath"
WF="$WD/06-AI自动化/01-工作流"
LOG="$WF/PIPELINE_RUN_20261031_2207.log"
REJ="$WD/09-数据/openmath_4d_analysis.json.rejected"
rm -f "$REJ"
: > "$LOG"

run_stage() {
  local name="$1"; shift
  local t0=$(date +%s)
  echo "===== [$(date +%H:%M:%S)] START $name =====" | tee -a "$LOG"
  "$PY" "$@" >> "$LOG" 2>&1
  local rc=$?
  local t1=$(date +%s)
  echo "===== [$(date +%H:%M:%S)] END   $name rc=$rc elapsed=$((t1-t0))s =====" | tee -a "$LOG"
  return $rc
}

cd "$WD" || { echo "cannot cd $WD"; exit 99; }

run_stage S1_ingest   "$WF/openmath_ingest.py"
rc1=$?
if [ $rc1 -ne 0 ]; then
  echo "!! S1 ingest rc=$rc1 non-zero" | tee -a "$LOG"
  if [ -f "$REJ" ]; then
    echo "!! GATE TRIGGERED: .rejected present. STOPPING. Do NOT force-push." | tee -a "$LOG"
    echo "PIPELINE_RESULT=ABORT_GATE" >> "$LOG"
    exit 0
  fi
fi

run_stage S2_analyze      "$WF/openmath_analyze.py";      rc2=$?
run_stage S3_experiments  "$WF/openmath_experiments.py";   rc3=$?
run_stage S4_coalition    "$WF/openmath_coalition.py";     rc4=$?
run_stage S5_synthesis    "$WF/openmath_synthesis.py";     rc5=$?
run_stage S6_meta         "$WF/openmath_meta.py";          rc6=$?
run_stage S7_theory       "$WF/openmath_theory.py";        rc7=$?
run_stage S10_millennium  "$WF/openmath_millennium.py";    rc10=$?
run_stage S8_audit        "$WF/openmath_audit.py";         rc8=$?
run_stage S9_sequences    "$WF/openmath_sequences.py";     rc9=$?

echo "=========== SUMMARY rc ===========" | tee -a "$LOG"
echo "S1=$rc1 S2=$rc2 S3=$rc3 S4=$rc4 S5=$rc5 S6=$rc6 S7=$rc7 S10=$rc10 S8=$rc8 S9=$rc9" | tee -a "$LOG"
fail=0
for v in $rc1 $rc2 $rc3 $rc4 $rc5 $rc6 $rc7 $rc10 $rc8 $rc9; do [ $v -ne 0 ] && fail=1; done
[ $fail -eq 0 ] && echo "PIPELINE_RESULT=ALL_OK" >> "$LOG" || echo "PIPELINE_RESULT=SOME_FAILED" >> "$LOG"
echo "done" | tee -a "$LOG"
