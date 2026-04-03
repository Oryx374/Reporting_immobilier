"""
Utilise l'API Claude pour synthétiser les articles scrapés en un rapport
structuré pour un professionnel de la structuration de club deals immobiliers.
"""

from __future__ import annotations

import logging
from typing import Optional

import anthropic

from config import ANTHROPIC_API_KEY
from scrapers.base_scraper import Article

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """Tu es un analyste immobilier senior spécialisé dans les club deals et
l'investissement immobilier institutionnel en France. Tu travailles pour un professionnel
qui structure des club deals immobiliers et qui a besoin d'un rapport hebdomadaire synthétique
et actionnable sur le marché.

Ton rôle est de :
1. Analyser les actualités immobilières de la semaine
2. Identifier les tendances de marché, les transactions significatives et les opportunités
3. Produire un rapport structuré, professionnel et concis
4. Mettre en avant ce qui est pertinent pour la structuration de club deals

Tu dois répondre en français, avec un ton professionnel et analytique."""

ANALYSIS_PROMPT_TEMPLATE = """Voici les {count} articles immobiliers collectés cette semaine
sur CFNEWS Immo et Business Immo :

{articles_text}

---

Produis un rapport hebdomadaire structuré comprenant :

1. **SYNTHÈSE EXÉCUTIVE** (3-5 phrases)
   - Vue d'ensemble de la semaine immobilière
   - Tendance générale du marché

2. **TRANSACTIONS & DEALS NOTABLES**
   - Liste des principales transactions mentionnées
   - Volumes, acteurs, typologies d'actifs

3. **TENDANCES DU MARCHÉ**
   - Évolutions de prix, taux, financement
   - Dynamiques par segment (bureaux, résidentiel, logistique, commerce...)
   - Contexte macro-économique pertinent

4. **ACTEURS & MOUVEMENTS**
   - Fonds d'investissement, promoteurs, family offices actifs
   - Levées de fonds, nouveaux véhicules d'investissement

5. **OPPORTUNITÉS POUR LES CLUB DEALS**
   - Actifs ou segments présentant des opportunités
   - Tendances favorables à la structuration de club deals
   - Points d'attention / risques à surveiller

6. **À SURVEILLER LA SEMAINE PROCHAINE**
   - Événements, publications, échéances importantes

Sois concis, factuel et orienté décision. Évite la reformulation des articles — apporte
une vraie valeur analytique."""


class ReportSynthesizer:
    """Synthétise les articles via Claude pour produire un rapport structuré."""

    def __init__(self):
        if not ANTHROPIC_API_KEY:
            logger.warning("ANTHROPIC_API_KEY non définie. La synthèse IA sera désactivée.")
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

    def synthesize(self, articles: list[Article]) -> dict:
        """
        Retourne un dict avec :
          - 'ai_report': le rapport rédigé par Claude (str)
          - 'articles': la liste des articles bruts
          - 'article_count': nombre d'articles
        """
        if not articles:
            return {
                "ai_report": "Aucun article collecté cette semaine.",
                "articles": [],
                "article_count": 0,
            }

        articles_text = self._format_articles_for_prompt(articles)
        ai_report = self._call_claude(articles_text, len(articles))

        return {
            "ai_report": ai_report,
            "articles": [a.to_dict() for a in articles],
            "article_count": len(articles),
        }

    def _format_articles_for_prompt(self, articles: list[Article]) -> str:
        lines = []
        for i, a in enumerate(articles, 1):
            lines.append(f"### Article {i} — {a.source}")
            lines.append(f"**Titre :** {a.title}")
            if a.published_at:
                lines.append(f"**Date :** {a.published_at.strftime('%d/%m/%Y')}")
            if a.category:
                lines.append(f"**Catégorie :** {a.category}")
            if a.summary:
                lines.append(f"**Résumé :** {a.summary}")
            lines.append(f"**Lien :** {a.url}")
            lines.append("")
        return "\n".join(lines)

    def _call_claude(self, articles_text: str, count: int) -> str:
        if not self.client:
            return self._fallback_report(articles_text)

        try:
            prompt = ANALYSIS_PROMPT_TEMPLATE.format(
                count=count,
                articles_text=articles_text,
            )
            message = self.client.messages.create(
                model="claude-opus-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except anthropic.APIError as e:
            logger.error(f"Erreur API Claude : {e}")
            return self._fallback_report(articles_text)

    def _fallback_report(self, articles_text: str) -> str:
        """Rapport de secours sans IA (liste brute des articles)."""
        return (
            "⚠️ Synthèse IA indisponible (clé API manquante ou erreur).\n\n"
            "**Articles collectés cette semaine :**\n\n"
            + articles_text
        )
