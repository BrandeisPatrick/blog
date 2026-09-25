#!/bin/sh
# Run the v2 tool arms to completion. Liveness is a PID file, never a `pgrep -f` pattern:
# helper loops whose own command lines contain the pattern keep each other "alive"
# (that deadlock cost three hours of wall-clock on 2026-09-18).
cd "$(dirname "$0")" || exit 1
PIDFILE=results/runs/v2/runner.pid
echo $$ > "$PIDFILE"
trap 'rm -f "$PIDFILE"' EXIT
caffeinate -i -w $$ &
for ph in "${@:-v2 v2-high}"; do python3 gym.py run --phase "$ph" --jobs "${JOBS:-4}" || exit 1; done
