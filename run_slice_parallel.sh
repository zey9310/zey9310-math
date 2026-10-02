#!/bin/bash
# run_slice_parallel.sh [FROM] [TO] [JOBS]
# Runs diam3_sms.py for every size FROM..TO (default 28..53), one size per core, max degree 4,
# diameter <= 3, forbidding 4- and 8-cycles. "UNSAT" for every size from 24 to 53 proves:
#   every graph with minimum degree >= 3, maximum degree <= 4 and diameter <= 3
#   contains a 4-cycle or an 8-cycle.
# Resumable: sizes with a finished result are skipped. Set PROOFS=1 to also write LRAT proofs
# (checkable with drat-trim's lrat-check; they can be very large).
export PATH=$HOME/.local/bin:$PATH LD_LIBRARY_PATH=$HOME/.local/lib:/usr/local/lib
FROM=${1:-28}; TO=${2:-53}; JOBS=${3:-$(nproc)}
mkdir -p slice_results
seq "$TO" -1 "$FROM" | xargs -P "$JOBS" -I{} bash -c '
  f=slice_results/n{}.txt
  grep -qE "UNSAT|FOUND" "$f" 2>/dev/null && exit 0
  extra=""; [ "$PROOFS" = 1 ] && extra="--lrat slice_results/n{}.lrat"
  python3 diam3_sms.py {} --maxdeg 4 --diam 3 --forbid 4,8 $extra > "$f" 2>&1'
cat slice_results/n*.txt | sort -t= -k2 -n
if grep -l FOUND slice_results/n*.txt 2>/dev/null; then echo "!!! a graph was found: rerun that size with --count and verify it"; fi
exit 0
