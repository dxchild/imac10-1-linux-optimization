#!/usr/bin/env bash
# Start the dashboard and status icon at login, without duplicate processes.
set -u
BIN="$HOME/.local/bin"
LOG="$HOME/.cache/imac-fan-suite"
mkdir -p "$LOG"

# Allows the MATE panel and Indicator Applet to initialize.
sleep 3

if ! pgrep -u "$(id -u)" -f '[/]imac-fan-control[.]py' >/dev/null; then
  nohup /usr/bin/python3 "$BIN/imac-fan-control.py" \
    >>"$LOG/dashboard.log" 2>&1 </dev/null &
fi

if ! pgrep -u "$(id -u)" -f '[/]imac-panel-monitor[.]py' >/dev/null; then
  nohup /usr/bin/python3 "$BIN/imac-panel-monitor.py" \
    >>"$LOG/indicator.log" 2>&1 </dev/null &
fi
