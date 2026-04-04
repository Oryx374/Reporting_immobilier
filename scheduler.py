"""
Scheduler : lance l'agent chaque lundi matin à 8h00.
Peut tourner en arrière-plan ou être géré via cron (voir README).

Usage :
    python scheduler.py              # Lance le scheduler en continu
    python scheduler.py --now        # Lance l'agent immédiatement (test)
"""

import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

import schedule
from agent import run_agent


def main() -> None:
    if "--now" in sys.argv:
        print("🚀 Lancement immédiat (mode test)...")
        run_agent()
        return

    # Planification : chaque lundi à 08:00
    schedule.every().monday.at("08:00").do(run_agent)

    print("⏰ Scheduler démarré — exécution chaque lundi à 08:00")
    print("   Appuyez sur Ctrl+C pour arrêter.")
    print()

    while True:
        schedule.run_pending()
        time.sleep(60)  # Vérifie toutes les minutes


if __name__ == "__main__":
    main()
