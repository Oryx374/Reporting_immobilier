"""
Envoi du rapport par email via SMTP (Gmail, OVH, etc.) ou SendGrid.
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

from config import (
    EMAIL_FROM,
    EMAIL_TO,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USER,
)

logger = logging.getLogger(__name__)


class EmailSender:
    def send(self, html_body: str, text_body: str) -> bool:
        """Envoie le rapport hebdomadaire par SMTP. Retourne True si succès."""
        if not all([SMTP_USER, SMTP_PASSWORD, EMAIL_TO]):
            logger.error(
                "Configuration email incomplète. "
                "Vérifiez SMTP_USER, SMTP_PASSWORD et EMAIL_TO dans votre .env"
            )
            return False

        subject = f"Rapport Immobilier Hebdomadaire — {datetime.now().strftime('%d/%m/%Y')}"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM or SMTP_USER
        msg["To"] = EMAIL_TO

        # Partie texte brut (fallback)
        part_text = MIMEText(text_body, "plain", "utf-8")
        # Partie HTML (prioritaire)
        part_html = MIMEText(html_body, "html", "utf-8")

        msg.attach(part_text)
        msg.attach(part_html)

        try:
            logger.info(f"Connexion SMTP à {SMTP_HOST}:{SMTP_PORT}...")
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(EMAIL_FROM or SMTP_USER, EMAIL_TO, msg.as_string())
            logger.info(f"Email envoyé avec succès à {EMAIL_TO}")
            return True
        except smtplib.SMTPAuthenticationError:
            logger.error(
                "Erreur d'authentification SMTP. "
                "Pour Gmail : utilisez un mot de passe d'application "
                "(https://myaccount.google.com/apppasswords)"
            )
        except smtplib.SMTPException as e:
            logger.error(f"Erreur SMTP : {e}")
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'envoi : {e}")

        return False

    def send_test(self) -> bool:
        """Envoie un email de test pour valider la configuration."""
        html = """
        <html><body>
        <h2>Test de configuration réussi !</h2>
        <p>Votre agent immobilier est correctement configuré.
        Vous recevrez votre premier rapport le prochain lundi matin.</p>
        </body></html>
        """
        text = "Test de configuration réussi ! Votre agent immobilier est prêt."
        return self.send(html, text)
