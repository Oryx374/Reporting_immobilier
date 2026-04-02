#!/bin/bash
# Script de lancement quotidien de l'agent investissement
# Ajouter au cron : 0 7 * * 1-5 /home/user/Reporting_immobilier/run_daily.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/briefings/agent.log"

mkdir -p "$SCRIPT_DIR/briefings"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Démarrage de l'agent..." >> "$LOG_FILE"

python3 "$SCRIPT_DIR/agent.py" --save --output "$SCRIPT_DIR/briefings" >> "$LOG_FILE" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Agent terminé." >> "$LOG_FILE"
