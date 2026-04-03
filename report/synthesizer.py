"""
Synthétise les articles scrapés en un rapport structuré pour un professionnel
de la structuration de club deals immobiliers.

Ordre de priorité des moteurs IA :
  1. Google Gemini Flash (gratuit, quota généreux) — si GEMINI_API_KEY définie
  2. Claude Opus (Anthropic, payant) — si ANTHROPIC_API_KEY définie
  3. Fallback sans IA — liste brute des articles
"""

from __future__ import annotations

import logging

from config import ANTHROPIC_API_KEY, GEMINI_API_KEY
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
    """
    Synthétise les articles via Gemini (gratuit) ou Claude (payant).
    Détection automatique de la clé disponible.
    """

    def synthesize(self, articles: list[Article]) -> dict:
        if not articles:
            return {
                "ai_report": "Aucun article collecté cette semaine.",
                "articles": [],
                "article_count": 0,
            }

        articles_text = self._format_articles_for_prompt(articles)
        prompt = ANALYSIS_PROMPT_TEMPLATE.format(
            count=len(articles),
            articles_text=articles_text,
        )

        if GEMINI_API_KEY:
            logger.info("Moteur IA : Google Gemini Flash (gratuit)")
            ai_report = self._call_gemini(prompt)
        elif ANTHROPIC_API_KEY:
            logger.info("Moteur IA : Claude Opus (Anthropic)")
            ai_report = self._call_claude(prompt)
        else:
            logger.warning("Aucune clé IA configurée — rapport sans synthèse.")
            ai_report = self._fallback_report(articles_text)

        return {
            "ai_report": ai_report,
            "articles": [a.to_dict() for a in articles],
            "article_count": len(articles),
        }

    # ------------------------------------------------------------------
    # Moteur 1 : Google Gemini Flash (gratuit)
    # ------------------------------------------------------------------

    def _call_gemini(self, prompt: str) -> str:
        try:
            import google.generativeai as genai

            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=SYSTEM_PROMPT,
            )
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Erreur Gemini : {e}")
            # Bascule sur Claude si disponible
            if ANTHROPIC_API_KEY:
                logger.info("Bascule sur Claude suite à erreur Gemini.")
                return self._call_claude(prompt)
            return self._fallback_report("")

    # ------------------------------------------------------------------
    # Moteur 2 : Claude Opus (Anthropic)
    # ------------------------------------------------------------------

    def _call_claude(self, prompt: str) -> str:
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            message = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Erreur Claude : {e}")
            return self._fallback_report("")

    # ------------------------------------------------------------------
    # Fallback : aucune IA
    # ------------------------------------------------------------------

    def _fallback_report(self, articles_text: str) -> str:
        return (
            "Synthèse IA indisponible (aucune clé API configurée).\n\n"
            "**Articles collectés cette semaine :**\n\n"
            + articles_text
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

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
