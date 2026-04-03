"""
Orchestrateur principal de l'agent immobilier.

Usage :
  python main.py              → Génère et envoie le rapport immédiatement
  python main.py --test-email → Envoie un email de test (vérifie la config SMTP)
  python main.py --no-email   → Génère le rapport mais ne l'envoie pas (affiche dans le terminal)
  python main.py --schedule   → Lance le scheduler hebdomadaire (mode démon)
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime

from config import MAX_ARTICLES_PER_SOURCE
from email_sender import EmailSender
from report import ReportFormatter, ReportSynthesizer
from scrapers import BusinessImmoScraper, CFNewsScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("main")


def run_report(send_email: bool = True) -> bool:
    """
    Pipeline complet :
    1. Scraping des deux sources
    2. Synthèse IA
    3. Formatage HTML
    4. Envoi email (si send_email=True)
    """
    logger.info("=" * 60)
    logger.info(f"RAPPORT IMMOBILIER — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    logger.info("=" * 60)

    # ------------------------------------------------------------------ #
    # 1. Scraping
    # ------------------------------------------------------------------ #
    all_articles = []

    scrapers = [
        CFNewsScraper(),
        BusinessImmoScraper(),
    ]

    for scraper in scrapers:
        logger.info(f"Scraping : {scraper.SOURCE_NAME}...")
        articles = scraper.fetch()
        logger.info(f"  → {len(articles)} articles récupérés")
        all_articles.extend(articles)

    logger.info(f"Total : {len(all_articles)} articles collectés")

    if not all_articles:
        logger.warning(
            "Aucun article collecté. "
            "Vérifiez votre connexion ou les URLs des scrapers."
        )

    # ------------------------------------------------------------------ #
    # 2. Synthèse IA
    # ------------------------------------------------------------------ #
    logger.info("Synthèse IA en cours (Claude)...")
    synthesizer = ReportSynthesizer()
    synthesis = synthesizer.synthesize(all_articles)
    logger.info("Synthèse IA terminée.")

    # ------------------------------------------------------------------ #
    # 3. Formatage
    # ------------------------------------------------------------------ #
    formatter = ReportFormatter()
    html_report = formatter.to_html(synthesis)
    text_report = formatter.to_text(synthesis)

    # Affichage terminal si pas d'email
    if not send_email:
        print("\n" + "=" * 60)
        print(text_report)
        print("=" * 60)
        return True

    # ------------------------------------------------------------------ #
    # 4. Envoi email
    # ------------------------------------------------------------------ #
    logger.info("Envoi de l'email...")
    sender = EmailSender()
    success = sender.send(html_report, text_report)

    if success:
        logger.info("Rapport envoyé avec succès.")
    else:
        logger.error("Échec de l'envoi du rapport.")

    return success


def main():
    parser = argparse.ArgumentParser(
        description="Agent immobilier — Rapport hebdomadaire CFNEWS Immo & Business Immo"
    )
    parser.add_argument(
        "--test-email",
        action="store_true",
        help="Envoie un email de test pour valider la configuration SMTP",
    )
    parser.add_argument(
        "--no-email",
        action="store_true",
        help="Génère le rapport sans l'envoyer par email (affiche dans le terminal)",
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Lance le scheduler hebdomadaire (mode démon)",
    )
    args = parser.parse_args()

    if args.test_email:
        logger.info("Envoi d'un email de test...")
        sender = EmailSender()
        success = sender.send_test()
        sys.exit(0 if success else 1)

    if args.schedule:
        from scheduler import run_scheduler
        run_scheduler()
        return

    success = run_report(send_email=not args.no_email)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
