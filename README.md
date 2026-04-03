# Agent Immobilier — Rapport Hebdomadaire

Agent IA qui scrape **CFNEWS Immo** et **Business Immo**, synthétise les actualités
avec **Claude (Anthropic)** et envoie un **rapport HTML professionnel** par email chaque semaine.

---

## Architecture

```
Reporting_immobilier/
├── scrapers/
│   ├── base_scraper.py          # Classe de base (RSS → HTML → Playwright)
│   ├── cfnews_scraper.py        # Scraper CFNEWS Immo
│   └── businessimmo_scraper.py  # Scraper Business Immo
├── report/
│   ├── synthesizer.py           # Synthèse IA via Claude API
│   ├── formatter.py             # Mise en forme HTML / texte
│   └── templates/
│       └── weekly_report.html   # Template email HTML
├── email_sender.py              # Envoi SMTP
├── scheduler.py                 # Planificateur hebdomadaire
├── main.py                      # Point d'entrée
├── config.py                    # Configuration (lit le .env)
├── requirements.txt
└── .env.example
```

### Stratégie de scraping (3 niveaux)

1. **RSS/Atom** — méthode prioritaire, propre et rapide
2. **HTML requests + BeautifulSoup** — si le RSS est indisponible
3. **Playwright (Chromium headless)** — si le site bloque les requêtes simples

---

## Installation

```bash
# 1. Cloner le dépôt
git clone <repo-url>
cd Reporting_immobilier

# 2. Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Installer le navigateur Playwright (Chromium)
playwright install chromium

# 5. Configurer les variables d'environnement
cp .env.example .env
# Editer .env avec vos clés API et paramètres email
```

---

## Configuration (`.env`)

| Variable | Description | Exemple |
|---|---|---|
| `ANTHROPIC_API_KEY` | Clé API Anthropic (Claude) | `sk-ant-...` |
| `SMTP_HOST` | Serveur SMTP | `smtp.gmail.com` |
| `SMTP_PORT` | Port SMTP | `587` |
| `SMTP_USER` | Email expéditeur | `mon.email@gmail.com` |
| `SMTP_PASSWORD` | Mot de passe SMTP | Mot de passe d'application Gmail |
| `EMAIL_FROM` | Adresse expéditeur | `mon.email@gmail.com` |
| `EMAIL_TO` | Destinataire du rapport | `moi@email.com` |
| `REPORT_DAY` | Jour d'envoi hebdomadaire | `monday` |
| `REPORT_TIME` | Heure d'envoi | `08:00` |

> **Gmail** : utilisez un **mot de passe d'application** (pas votre mot de passe principal).
> Activez la validation en 2 étapes puis générez un mot de passe sur
> myaccount.google.com/apppasswords

---

## Utilisation

```bash
# Générer et envoyer le rapport maintenant
python main.py

# Générer le rapport sans l'envoyer (affiche dans le terminal)
python main.py --no-email

# Tester la configuration email
python main.py --test-email

# Lancer le scheduler hebdomadaire (mode démon)
python main.py --schedule
```

### Automatisation avec cron

```cron
# Tous les lundis à 8h00
0 8 * * 1 cd /chemin/vers/Reporting_immobilier && /chemin/vers/.venv/bin/python main.py
```

---

## Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## Comment ça marche

1. **Scraping** : l'agent tente d'abord les flux RSS de chaque site. Si bloqué,
   il passe au scraping HTML, puis à Playwright (navigateur Chromium headless).

2. **Synthèse IA** : les articles collectés sont envoyés à **Claude Opus** avec
   un prompt orienté "analyste club deals immobiliers". Claude produit un rapport
   structuré : synthèse exécutive, transactions notables, tendances, opportunités.

3. **Email HTML** : le rapport est mis en forme dans un template email professionnel
   et envoyé via SMTP.

---

## Personnalisation

- **Ajouter une source** : créer une nouvelle classe dans `scrapers/` héritant de `BaseScraper`
  et l'importer dans `main.py`.
- **Modifier l'analyse IA** : éditer le prompt dans `report/synthesizer.py`.
- **Modifier le design de l'email** : éditer `report/templates/weekly_report.html`.
