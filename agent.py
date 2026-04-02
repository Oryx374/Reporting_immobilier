#!/usr/bin/env python3
"""
Agent Conseiller Investissement Quotidien
Génère chaque matin un briefing complet sur les marchés financiers globaux.
Usage : python3 agent.py [--save] [--output OUTPUT_DIR]
"""

import anyio
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage, AssistantMessage, TextBlock

# ─── Prompt système (persona + règles) ────────────────────────────────────────

SYSTEM_PROMPT = """Tu es un conseiller financier quantitatif senior spécialisé dans les marchés financiers globaux.
Tu maîtrises l'analyse technique, l'analyse fondamentale, la macroéconomie, les marchés on-chain et les marchés de prédiction.
Tu t'adresses à un investisseur avancé qui comprend le jargon financier et qui n'a pas besoin d'explications basiques.

RÈGLES ABSOLUES :
- Ne produis jamais de conseil financier au sens réglementaire (MIF II / AMF)
- Si les données sont insuffisantes sur un actif, dis-le plutôt qu'inventer
- Signale explicitement si un setup va à contre-courant du sentiment dominant
- Priorise la qualité des signaux sur la quantité
- Réponds TOUJOURS en français
- Utilise des tableaux Markdown pour les setups
- Sois direct et actionnable — pas de hedging inutile
- Si un signal est contradictoire, dis-le explicitement
"""

# ─── Prompt de tâche quotidien ─────────────────────────────────────────────────

def build_task_prompt(date_str: str) -> str:
    return f"""Date du jour : {date_str}

Effectue les recherches suivantes AVANT de produire ton analyse :
1. Actualité macro du jour (Fed, BCE, données éco, géopolitique)
2. Mouvements overnight des marchés US/Asie/Europe (indices, clôtures)
3. Flux on-chain crypto : exchange inflows/outflows, open interest, funding rates BTC/ETH
4. Sentiment de marché : Crypto Fear & Greed Index, VIX, DXY
5. Probabilités Polymarket sur événements à impact marché (volume élevé)
6. Altcoin avec setup technique ou narratif fort

Puis produis un briefing structuré EN FRANÇAIS avec ces 5 sections :

## 1. MACRO DU JOUR (5 lignes max)
Résumé des catalyseurs macro actifs : décisions de politique monétaire, publications économiques clés, tensions géopolitiques.
Indique le biais directionnel global : risk-on / risk-off / neutre.

## 2. NARRATIVE DE MARCHÉ
Identifie le thème dominant du moment.
Explique comment ce thème structure les flux entre classes d'actifs.

## 3. SETUPS & OPPORTUNITÉS
Pour chaque classe d'actifs pertinente, 1 à 3 setups actionnables sous forme de tableau :
| Actif | Direction | Entrée | Stop (invalidation) | Objectif | Horizon | Conviction |

Horizons : Intraday / Swing (2-7j) / Moyen terme (2-6 sem)
Conviction : FORTE / MODÉRÉE / FAIBLE

## 4. SIGNAUX POLYMARKET
2 à 3 marchés de prédiction actifs :
| Marché | Probabilité actuelle | Delta vs consensus | Impact actifs couverts |

## 5. ON-CHAIN & CRYPTO WATCH
- Flux exchange nets BTC/ETH (accumulation / distribution)
- Funding rates et open interest sur BTC/ETH
- Signal dominant : bullish / bearish / indécis
- 1 altcoin avec setup technique ou narratif fort

Termine par une **"PHRASE DU JOUR"** (1 ligne) résumant le biais général de la session.

---
*Disclaimer : Ce briefing est produit à des fins d'analyse quantitative et ne constitue pas un conseil en investissement au sens de la directive MIF II / AMF.*
"""


# ─── Collecte et affichage du résultat ────────────────────────────────────────

async def run_agent(save: bool = False, output_dir: str = "briefings") -> str:
    date_str = datetime.now().strftime("%d %B %Y")
    date_file = datetime.now().strftime("%Y-%m-%d")

    print(f"\n{'='*60}")
    print(f"  AGENT CONSEILLER INVESTISSEMENT — {date_str}")
    print(f"{'='*60}\n")
    print("Collecte des données de marché en cours...\n")

    task_prompt = build_task_prompt(date_str)
    full_briefing = []

    async for message in query(
        prompt=task_prompt,
        options=ClaudeAgentOptions(
            model="claude-opus-4-6",
            system_prompt=SYSTEM_PROMPT,
            allowed_tools=["WebSearch", "WebFetch"],
            max_turns=25,
        ),
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock) and block.text.strip():
                    print(block.text, end="", flush=True)
                    full_briefing.append(block.text)
        elif isinstance(message, ResultMessage):
            if message.result and message.result.strip():
                # Résultat final propre (parfois identique au dernier AssistantMessage)
                if not full_briefing or message.result not in full_briefing[-1]:
                    print(message.result)
                    full_briefing.append(message.result)

    briefing_text = "\n".join(full_briefing)

    if save and briefing_text.strip():
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        filename = output_path / f"briefing_{date_file}.md"
        header = f"# Briefing Investissement — {date_str}\n\n"
        filename.write_text(header + briefing_text, encoding="utf-8")
        print(f"\n\n✓ Briefing sauvegardé : {filename}")

    return briefing_text


# ─── Point d'entrée ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Agent conseiller investissement quotidien"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Sauvegarder le briefing dans un fichier Markdown daté",
    )
    parser.add_argument(
        "--output",
        default="briefings",
        metavar="DIR",
        help="Dossier de sauvegarde (défaut : briefings/)",
    )
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Erreur : la variable ANTHROPIC_API_KEY n'est pas définie.")
        print("Exécute : export ANTHROPIC_API_KEY='ta_clé_api'")
        sys.exit(1)

    anyio.run(run_agent, args.save, args.output)


if __name__ == "__main__":
    main()
