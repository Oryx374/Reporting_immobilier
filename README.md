# 🏠 Agent IA — Reporting Immobilier Hebdomadaire

Envoie automatiquement chaque **lundi matin** un rapport sur l'actualité immobilière française, compilé depuis **CFNews Immo** et **Business Immo**, synthétisé par **Claude Opus 4.6**.

---

## Architecture

```
agent.py              ← Point d'entrée principal (orchestre tout)
scraper.py            ← Scraping via Playwright (anti-bot)
report_generator.py   ← Synthèse avec Claude Opus 4.6
email_sender.py       ← Envoi SMTP
scheduler.py          ← Planification (lundi 08:00) ou cron
rapports/             ← Rapports HTML sauvegardés localement
```

---

## Installation

### 1. Dépendances Python

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Configuration

```bash
cp .env.example .env
# Éditez .env avec vos clés
```

Variables requises dans `.env` :

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Clé API Anthropic |
| `SMTP_HOST` | Serveur SMTP (ex: `smtp.gmail.com`) |
| `SMTP_PORT` | Port SMTP (ex: `587`) |
| `SMTP_USER` | Email expéditeur |
| `SMTP_PASSWORD` | Mot de passe ou [App Password Gmail](https://myaccount.google.com/apppasswords) |
| `REPORT_RECIPIENTS` | Destinataires séparés par des virgules |

---

## Utilisation

### Test immédiat (recommandé pour commencer)

```bash
python scheduler.py --now
```

### Scheduler continu (tourne en arrière-plan)

```bash
python scheduler.py
```

### Via cron (alternative recommandée en production)

```bash
crontab -e
```

Ajouter la ligne suivante (lundi à 8h00) :

```cron
0 8 * * 1 cd /chemin/vers/Reporting_immobilier && /usr/bin/python3 agent.py >> rapports/cron.log 2>&1
```

---

## Configuration Gmail

Pour envoyer depuis Gmail, créez un **App Password** :
1. Activez la validation en 2 étapes sur votre compte Google
2. Allez sur : [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Créez un App Password pour "Mail"
4. Utilisez ce mot de passe dans `SMTP_PASSWORD`

---

## Ce que fait l'agent

1. **Scraping** (Playwright headless) : visite CFNews Immo et Business Immo, extrait titres, résumés et liens des articles de la semaine
2. **Analyse** (Claude Opus 4.6 avec adaptive thinking) : synthétise les actualités en rapport structuré par segment (bureaux, logement, retail, logistique...)
3. **Email** : envoie le rapport HTML aux destinataires configurés
4. **Sauvegarde** : archive chaque rapport dans `rapports/rapport_YYYY-MM-DD.html`
