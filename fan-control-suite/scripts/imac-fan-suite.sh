#!/bin/bash

BIN="$HOME/.local/bin"
LOG="$HOME/.cache/imac-fan-suite"

mkdir -p "$LOG"

# Allow the MATE panel to initialize.
sleep 3

# Launch the main application once.
if ! pgrep -u "$(id -u)" -f '[/]imac-fan-control[.]py' >/dev/null; then
    nohup /usr/bin/python3 \
        "$BIN/imac-fan-control.py" \
        >> "$LOG/main.log" 2>&1 < /dev/null &
fi

# Use the previously working panel monitor.
if [ -f "$BIN/imac-panel-monitor.py" ]; then
    if ! pgrep -u "$(id -u)" -f '[/]imac-panel-monitor[.]py' >/dev/null; then
        nohup /usr/bin/python3 \
            "$BIN/imac-panel-monitor.py" \
            >> "$LOG/panel.log" 2>&1 < /dev/null &
    fi
else
    echo "Panel monitor not found" >> "$LOG/panel.log"
fi
