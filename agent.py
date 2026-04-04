"""
Agent principal : orchestre le scraping, la génération du rapport et l'envoi email.
Peut être lancé manuellement ou via le scheduler.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv(Path(__file__).parent / ".env")

from scraper import scrape
from report_generator import generate_report, wrap_in_email_template
from email_sender import send_report


def run_agent() -> None:
    """Exécute le pipeline complet de l'agent."""
    print("=" * 60)
    print(f"🏠 Agent Reporting Immobilier — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 60)

    # 1. Scraping
    print("\n[1/3] Scraping des actualités...")
    articles = scrape()

    if not articles:
        print("⚠️  Aucun article collecté. Vérifiez la connexion ou les sélecteurs CSS.")
        # On génère quand même un rapport vide pour signaler le problème
        articles = []

    print(f"✓ {len(articles)} articles collectés au total")

    # 2. Génération du rapport
    print("\n[2/3] Génération du rapport avec Claude Opus 4.6...")
    report_content = generate_report(articles)

    today = datetime.now().strftime("%d %B %Y")
    full_html = wrap_in_email_template(report_content, today)

    # Sauvegarde locale du rapport
    reports_dir = Path(__file__).parent / "rapports"
    reports_dir.mkdir(exist_ok=True)
    report_path = reports_dir / f"rapport_{datetime.now().strftime('%Y-%m-%d')}.html"
    report_path.write_text(full_html, encoding="utf-8")
    print(f"✓ Rapport sauvegardé localement : {report_path}")

    # 3. Envoi email
    print("\n[3/3] Envoi du rapport par email...")
    try:
        send_report(full_html)
        print("✓ Rapport envoyé avec succès !")
    except KeyError as e:
        print(f"⚠️  Variable d'environnement manquante : {e}")
        print("   Le rapport a été sauvegardé localement mais n'a pas été envoyé.")
        print(f"   Consultez : {report_path}")
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi email : {e}")
        print(f"   Le rapport est disponible localement : {report_path}")
        raise

    print("\n" + "=" * 60)
    print("✅ Agent terminé avec succès.")
    print("=" * 60)


if __name__ == "__main__":
    run_agent()
