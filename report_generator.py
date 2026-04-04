"""
Génération du rapport immobilier hebdomadaire via Claude Opus 4.6.
"""

import os
from datetime import datetime

import anthropic

from scraper import Article


def _format_articles_for_prompt(articles: list[Article]) -> str:
    """Formate les articles en texte structuré pour le prompt."""
    if not articles:
        return "Aucun article disponible cette semaine."

    lines = []
    for i, a in enumerate(articles, 1):
        lines.append(f"{i}. [{a.source}] {a.titre}")
        if a.date:
            lines.append(f"   Date : {a.date}")
        if a.resume:
            lines.append(f"   Résumé : {a.resume}")
        if a.lien:
            lines.append(f"   Lien : {a.lien}")
        lines.append("")

    return "\n".join(lines)


def generate_report(articles: list[Article]) -> str:
    """
    Génère un rapport immobilier hebdomadaire en HTML
    à partir des articles scrapés.
    """
    client = anthropic.Anthropic()

    articles_text = _format_articles_for_prompt(articles)
    today = datetime.now().strftime("%d %B %Y")

    system_prompt = """Tu es un analyste spécialisé dans l'immobilier commercial et résidentiel français.
Tu rédiges des rapports hebdomadaires professionnels, clairs et synthétiques pour des professionnels du secteur.
Tu dois toujours structurer ton rapport en sections thématiques pertinentes.
Tu rédiges en français impeccable, avec un ton professionnel mais accessible."""

    user_prompt = f"""Voici les actualités immobilières de la semaine (semaine du {today}) collectées depuis CFNews Immo et Business Immo :

{articles_text}

Rédige un rapport hebdomadaire complet en HTML (sans balises <html>, <head>, <body> — uniquement le contenu interne).

Structure obligatoire du rapport :
1. **En-tête** : titre du rapport + date
2. **Synthèse executive** (3-4 phrases) : les tendances clés de la semaine
3. **Faits marquants** : les 3-5 actualités les plus importantes, avec analyse
4. **Par segment de marché** : bureaux, logements, commerces/retail, logistique (uniquement les segments couverts par les articles)
5. **Transactions & investissements notables** (si mentionnés)
6. **Tendances & perspectives** : ce que ces actualités révèlent pour le marché
7. **Sources** : liste des articles avec leurs liens cliquables

Utilise des balises HTML sémantiques (<h1>, <h2>, <h3>, <p>, <ul>, <li>, <strong>, <a>).
Ajoute du style inline pour que le rapport soit visuellement propre dans un email.
Les liens vers les articles originaux doivent être cliquables."""

    print("[Rapport] Génération avec Claude Opus 4.6...")

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        html_content = ""
        for text in stream.text_stream:
            html_content += text
            print(text, end="", flush=True)

    print("\n[Rapport] Génération terminée.")
    return html_content


def wrap_in_email_template(content: str, date_str: str) -> str:
    """Encapsule le contenu dans un template email HTML complet."""
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Rapport Immobilier Hebdomadaire — {date_str}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
      line-height: 1.6;
      color: #2d3748;
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
      background-color: #f7fafc;
    }}
    .container {{
      background: #ffffff;
      border-radius: 8px;
      padding: 40px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }}
    .header {{
      border-bottom: 3px solid #2b6cb0;
      padding-bottom: 20px;
      margin-bottom: 30px;
    }}
    h1 {{ color: #1a365d; font-size: 1.8em; margin: 0 0 8px 0; }}
    h2 {{ color: #2b6cb0; font-size: 1.3em; margin-top: 30px; border-left: 4px solid #2b6cb0; padding-left: 12px; }}
    h3 {{ color: #2d3748; font-size: 1.1em; }}
    a {{ color: #2b6cb0; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    ul {{ padding-left: 20px; }}
    li {{ margin-bottom: 6px; }}
    .footer {{
      margin-top: 40px;
      padding-top: 20px;
      border-top: 1px solid #e2e8f0;
      font-size: 0.85em;
      color: #718096;
      text-align: center;
    }}
  </style>
</head>
<body>
  <div class="container">
    {content}
    <div class="footer">
      <p>Rapport généré automatiquement le {date_str} par l'agent IA Reporting Immobilier.</p>
      <p>Sources : <a href="https://www.cfnews-immo.com">CFNews Immo</a> · <a href="https://www.businessimmo.com">Business Immo</a></p>
    </div>
  </div>
</body>
</html>"""
