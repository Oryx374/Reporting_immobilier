"""
Envoi du rapport par email via SMTP.
Compatible Gmail (avec mot de passe d'application) et tout serveur SMTP.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime


def send_report(html_content: str, subject: str = None) -> None:
    """
    Envoie le rapport HTML par email aux destinataires configurés.

    Variables d'environnement requises :
    - SMTP_HOST       : ex. smtp.gmail.com
    - SMTP_PORT       : ex. 587
    - SMTP_USER       : adresse email expéditeur
    - SMTP_PASSWORD   : mot de passe ou mot de passe d'application
    - REPORT_RECIPIENTS : emails séparés par des virgules
    """
    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ["SMTP_USER"]
    smtp_password = os.environ["SMTP_PASSWORD"]
    recipients_raw = os.environ["REPORT_RECIPIENTS"]

    recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]
    if not recipients:
        raise ValueError("REPORT_RECIPIENTS est vide.")

    today = datetime.now().strftime("%d/%m/%Y")
    if subject is None:
        subject = f"📊 Rapport Immobilier Hebdomadaire — {today}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = ", ".join(recipients)

    # Version texte de repli (simplifiée)
    text_part = MIMEText(
        "Rapport immobilier hebdomadaire disponible. "
        "Veuillez consulter la version HTML de cet email.",
        "plain",
        "utf-8"
    )
    html_part = MIMEText(html_content, "html", "utf-8")

    msg.attach(text_part)
    msg.attach(html_part)

    print(f"[Email] Envoi à : {', '.join(recipients)}")

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, recipients, msg.as_string())

    print(f"[Email] ✓ Rapport envoyé avec succès à {len(recipients)} destinataire(s).")
