"""
Classe de base pour les scrapers. Fournit:
- Récupération RSS/Atom via xml.etree.ElementTree (stdlib) + feedparser en optionnel
- Scraping HTML via requests + BeautifulSoup
- Scraping JavaScript via Playwright (fallback)
"""

from __future__ import annotations

import time
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

try:
    import feedparser as _feedparser
    HAS_FEEDPARSER = True
except ImportError:
    _feedparser = None
    HAS_FEEDPARSER = False

import requests
from bs4 import BeautifulSoup

from config import BROWSER_HEADERS, COOKIES_FILE, MAX_ARTICLES_PER_SOURCE, PREMIUM_EMAIL, PREMIUM_PASSWORD, PROXIES, REQUEST_DELAY

logger = logging.getLogger(__name__)


@dataclass
class Article:
    title: str
    url: str
    source: str
    published_at: Optional[datetime] = None
    summary: str = ""
    category: str = ""
    author: str = ""

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "summary": self.summary,
            "category": self.category,
            "author": self.author,
        }


class BaseScraper:
    """Classe de base avec stratégies de scraping multiples."""

    SOURCE_NAME = "Base"
    RSS_URLS: list[str] = []
    BASE_URL = ""

    # URL de login à surcharger dans chaque scraper
    LOGIN_URL: Optional[str] = None
    LOGIN_CHECK_TEXT: str = ""  # texte présent sur la page si connecté

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(BROWSER_HEADERS)
        if PROXIES:
            self.session.proxies.update(PROXIES)
        self.articles: list[Article] = []
        self._logged_in = False

        # Priorité 1 : cookies exportés depuis le navigateur (méthode la plus fiable)
        if COOKIES_FILE:
            loaded = self._load_cookies_from_file(COOKIES_FILE)
            if loaded:
                self._logged_in = True
                return

        # Priorité 2 : login automatique avec identifiants
        if PREMIUM_EMAIL and PREMIUM_PASSWORD and self.LOGIN_URL:
            self._login()

    # ------------------------------------------------------------------
    # Chargement des cookies depuis le navigateur
    # ------------------------------------------------------------------

    def _load_cookies_from_file(self, filepath: str) -> bool:
        """
        Charge les cookies depuis un fichier JSON exporté par l'extension
        'Cookie-Editor' (Chrome/Firefox).

        Format attendu : liste de dicts avec les champs 'name', 'value', 'domain'.
        """
        import json, os
        if not os.path.exists(filepath):
            logger.warning(f"Fichier cookies introuvable : {filepath}")
            return False
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                cookies = json.load(f)

            # Supporte deux formats : liste directe ou dict avec clé 'cookies'
            if isinstance(cookies, dict) and "cookies" in cookies:
                cookies = cookies["cookies"]

            count = 0
            for c in cookies:
                name = c.get("name", "")
                value = c.get("value", "")
                domain = c.get("domain", "")
                if not name or not value:
                    continue
                # On ne charge que les cookies des domaines cibles
                if any(d in domain for d in ["cfnews", "cfnewsimmo", "businessimmo"]):
                    self.session.cookies.set(name, value, domain=domain)
                    count += 1

            if count > 0:
                logger.info(
                    f"[{self.SOURCE_NAME}] {count} cookies chargés depuis {filepath}"
                )
                return True
            else:
                logger.warning(
                    f"[{self.SOURCE_NAME}] Aucun cookie correspondant trouvé dans {filepath}"
                )
                return False
        except Exception as e:
            logger.warning(f"Erreur chargement cookies : {e}")
            return False

    # ------------------------------------------------------------------
    # Authentification premium
    # ------------------------------------------------------------------

    def _login(self) -> bool:
        """Tente de se connecter au site avec les identifiants premium."""
        try:
            logger.info(f"[{self.SOURCE_NAME}] Connexion premium ({PREMIUM_EMAIL})...")
            payload = self._login_payload()
            resp = self.session.post(self.LOGIN_URL, data=payload, timeout=20, allow_redirects=True)
            if resp.status_code in (200, 302):
                if self.LOGIN_CHECK_TEXT and self.LOGIN_CHECK_TEXT in resp.text:
                    self._logged_in = True
                    logger.info(f"[{self.SOURCE_NAME}] Connecté en premium.")
                    return True
                elif not self.LOGIN_CHECK_TEXT:
                    # Sans texte de vérification, on suppose succès si pas d'erreur
                    self._logged_in = True
                    logger.info(f"[{self.SOURCE_NAME}] Login envoyé (vérification manuelle recommandée).")
                    return True
            logger.warning(f"[{self.SOURCE_NAME}] Login échoué (status {resp.status_code}).")
        except Exception as e:
            logger.warning(f"[{self.SOURCE_NAME}] Erreur login : {e}")
        return False

    def _login_payload(self) -> dict:
        """Payload POST de login — à surcharger si le site a des champs spécifiques."""
        return {
            "email": PREMIUM_EMAIL,
            "password": PREMIUM_PASSWORD,
            "username": PREMIUM_EMAIL,
            "login": PREMIUM_EMAIL,
            "pass": PREMIUM_PASSWORD,
        }

    def _login_playwright(self, page) -> bool:
        """Login via Playwright pour les sites avec formulaire JS."""
        return False  # à surcharger dans chaque scraper si besoin

    # ------------------------------------------------------------------
    # Méthode principale
    # ------------------------------------------------------------------

    def fetch(self) -> list[Article]:
        """Tente RSS d'abord, puis scraping HTML, puis Playwright en dernier recours."""
        articles: list[Article] = []

        # 1. Essai RSS
        if self.RSS_URLS:
            logger.info(f"[{self.SOURCE_NAME}] Tentative de récupération RSS...")
            articles = self._fetch_rss()
            if articles:
                logger.info(f"[{self.SOURCE_NAME}] {len(articles)} articles via RSS")
                return articles[:MAX_ARTICLES_PER_SOURCE]

        # 2. Essai scraping HTML
        logger.info(f"[{self.SOURCE_NAME}] RSS échoué, tentative scraping HTML...")
        articles = self._fetch_html()
        if articles:
            logger.info(f"[{self.SOURCE_NAME}] {len(articles)} articles via HTML")
            return articles[:MAX_ARTICLES_PER_SOURCE]

        # 3. Essai Playwright (navigateur headless)
        logger.info(f"[{self.SOURCE_NAME}] HTML échoué, tentative Playwright...")
        articles = self._fetch_playwright()
        if articles:
            logger.info(f"[{self.SOURCE_NAME}] {len(articles)} articles via Playwright")
            return articles[:MAX_ARTICLES_PER_SOURCE]

        logger.warning(f"[{self.SOURCE_NAME}] Aucun article récupéré.")
        return []

    # ------------------------------------------------------------------
    # Stratégie 1 : RSS / Atom
    # ------------------------------------------------------------------

    def _fetch_rss(self) -> list[Article]:
        articles: list[Article] = []
        for rss_url in self.RSS_URLS:
            try:
                response = self.session.get(rss_url, timeout=15)
                if response.status_code != 200:
                    logger.debug(f"RSS {rss_url} → {response.status_code}")
                    continue

                # Essai feedparser en priorité si disponible
                if HAS_FEEDPARSER:
                    feed = _feedparser.parse(response.content)
                    for entry in feed.entries:
                        article = self._parse_feedparser_entry(entry)
                        if article:
                            articles.append(article)
                else:
                    # Fallback : parser XML natif (stdlib)
                    parsed = self._parse_rss_xml(response.content)
                    articles.extend(parsed)

                if articles:
                    break
                time.sleep(REQUEST_DELAY)
            except Exception as e:
                logger.debug(f"RSS {rss_url} erreur : {e}")
        return articles

    def _parse_feedparser_entry(self, entry) -> Optional[Article]:
        """Convertit une entrée feedparser en Article."""
        try:
            title = entry.get("title", "").strip()
            url = entry.get("link", "").strip()
            if not title or not url:
                return None

            published_at = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published_at = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

            summary = ""
            if hasattr(entry, "content") and entry.content:
                raw = entry.content[0].get("value", "")
                summary = BeautifulSoup(raw, "lxml").get_text(separator=" ", strip=True)[:1000]
            elif hasattr(entry, "summary"):
                raw = entry.get("summary", "")
                summary = BeautifulSoup(raw, "lxml").get_text(separator=" ", strip=True)[:1000]

            category = ""
            if hasattr(entry, "tags") and entry.tags:
                category = entry.tags[0].get("term", "")

            return Article(
                title=title,
                url=url,
                source=self.SOURCE_NAME,
                published_at=published_at,
                summary=summary,
                category=category,
                author=entry.get("author", ""),
            )
        except Exception as e:
            logger.debug(f"Erreur parsing entrée feedparser : {e}")
            return None

    def _parse_rss_xml(self, content: bytes) -> list[Article]:
        """Parse un flux RSS/Atom avec xml.etree.ElementTree (stdlib)."""
        articles: list[Article] = []
        NS_ATOM = "http://www.w3.org/2005/Atom"
        NS_CONTENT = "http://purl.org/rss/1.0/modules/content/"
        NS_DC = "http://purl.org/dc/elements/1.1/"
        try:
            root = ET.fromstring(content)
            tag = root.tag

            # Atom feed
            if "Atom" in tag or "atom" in tag or tag == f"{{{NS_ATOM}}}feed":
                entries = root.findall(f"{{{NS_ATOM}}}entry")
                for entry in entries:
                    title_el = entry.find(f"{{{NS_ATOM}}}title")
                    link_el = entry.find(f"{{{NS_ATOM}}}link")
                    summary_el = entry.find(f"{{{NS_ATOM}}}summary")
                    date_el = entry.find(f"{{{NS_ATOM}}}updated") or entry.find(f"{{{NS_ATOM}}}published")

                    title = title_el.text.strip() if title_el is not None and title_el.text else ""
                    url = link_el.get("href", "") if link_el is not None else ""
                    summary = summary_el.text.strip() if summary_el is not None and summary_el.text else ""
                    published_at = self._parse_date(date_el.text if date_el is not None else "")

                    if title and url:
                        articles.append(Article(
                            title=title, url=url, source=self.SOURCE_NAME,
                            published_at=published_at, summary=summary[:1000],
                        ))
            else:
                # RSS 2.0
                channel = root.find("channel")
                items = channel.findall("item") if channel is not None else root.findall(".//item")
                for item in items:
                    title_el = item.find("title")
                    link_el = item.find("link")
                    desc_el = item.find("description")
                    date_el = item.find("pubDate")
                    cat_el = item.find("category")
                    author_el = item.find(f"{{{NS_DC}}}creator") or item.find("author")

                    title = title_el.text.strip() if title_el is not None and title_el.text else ""
                    url = link_el.text.strip() if link_el is not None and link_el.text else ""
                    raw_summary = desc_el.text or "" if desc_el is not None else ""
                    summary = BeautifulSoup(raw_summary, "lxml").get_text(separator=" ", strip=True)[:1000]
                    published_at = self._parse_date(date_el.text if date_el is not None else "")
                    category = cat_el.text.strip() if cat_el is not None and cat_el.text else ""
                    author = author_el.text.strip() if author_el is not None and author_el.text else ""

                    if title and url:
                        articles.append(Article(
                            title=title, url=url, source=self.SOURCE_NAME,
                            published_at=published_at, summary=summary,
                            category=category, author=author,
                        ))
        except ET.ParseError as e:
            logger.debug(f"Erreur XML RSS : {e}")
        return articles

    @staticmethod
    def _parse_date(date_str: str) -> Optional[datetime]:
        """Parse une date RSS (RFC 2822) ou ISO 8601."""
        if not date_str:
            return None
        try:
            return parsedate_to_datetime(date_str)
        except Exception:
            pass
        for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
            except ValueError:
                continue
        return None

    # ------------------------------------------------------------------
    # Stratégie 2 : Scraping HTML (à surcharger dans les sous-classes)
    # ------------------------------------------------------------------

    def _fetch_html(self) -> list[Article]:
        """À surcharger dans chaque scraper spécifique."""
        return []

    def _get_html(self, url: str) -> Optional[BeautifulSoup]:
        """Récupère et parse une page HTML."""
        try:
            time.sleep(REQUEST_DELAY)
            resp = self.session.get(url, timeout=20)
            if resp.status_code == 200:
                return BeautifulSoup(resp.content, "lxml")
            logger.debug(f"GET {url} → {resp.status_code}")
        except Exception as e:
            logger.debug(f"Erreur GET {url} : {e}")
        return None

    # ------------------------------------------------------------------
    # Stratégie 3 : Playwright (navigateur headless)
    # ------------------------------------------------------------------

    def _fetch_playwright(self) -> list[Article]:
        """À surcharger dans chaque scraper spécifique si besoin."""
        return []

    def _get_playwright_html(self, url: str) -> Optional[BeautifulSoup]:
        """Lance un vrai navigateur Chromium pour récupérer la page."""
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-blink-features=AutomationControlled",
                    ],
                )
                context = browser.new_context(
                    user_agent=BROWSER_HEADERS["User-Agent"],
                    locale="fr-FR",
                    viewport={"width": 1280, "height": 800},
                    extra_http_headers={
                        "Accept-Language": "fr-FR,fr;q=0.9",
                    },
                )
                # Masque le webdriver pour paraître comme un vrai navigateur
                context.add_init_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )
                page = context.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(2)
                html = page.content()
                browser.close()
                return BeautifulSoup(html, "lxml")
        except Exception as e:
            logger.debug(f"Playwright {url} erreur : {e}")
            return None
