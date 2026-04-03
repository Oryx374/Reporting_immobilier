"""
Scheduler hebdomadaire.
Lance automatiquement le rapport chaque semaine au jour/heure définis dans .env.

Variables :
  REPORT_DAY  = monday (par défaut)
  REPORT_TIME = 08:00  (par défaut)

Jours valides : monday, tuesday, wednesday, thursday, friday, saturday, sunday
"""

from __future__ import annotations

import logging
import time

import schedule

from config import REPORT_DAY, REPORT_TIME

logger = logging.getLogger(__name__)

DAY_MAP = {
    "monday": schedule.every().monday,
    "tuesday": schedule.every().tuesday,
    "wednesday": schedule.every().wednesday,
    "thursday": schedule.every().thursday,
    "friday": schedule.every().friday,
    "saturday": schedule.every().saturday,
    "sunday": schedule.every().sunday,
}


def run_scheduler():
    from main import run_report

    day = REPORT_DAY.lower().strip()
    if day not in DAY_MAP:
        logger.error(
            f"REPORT_DAY invalide : '{REPORT_DAY}'. "
            f"Valeurs acceptées : {', '.join(DAY_MAP.keys())}"
        )
        return

    DAY_MAP[day].at(REPORT_TIME).do(run_report, send_email=True)

    logger.info(
        f"Scheduler démarré — rapport programmé chaque {day} à {REPORT_TIME}"
    )
    logger.info("Appuyez sur Ctrl+C pour arrêter.")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Scheduler arrêté.")
