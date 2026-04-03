"""
Scraper pour CFNEWS Immo (cfnews.net/Immo et cfnewsimmo.net).

Stratégies (dans l'ordre) :
1. Flux RSS officiel
2. Scraping HTML de la page d'accueil
3. Playwright (navigateur headless) si les deux précédents échouent
"""

from __future__ import annotations

import logging
import time
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import REQUEST_DELAY
from .base_scraper import Article, BaseScraper

logger = logging.getLogger(__name__)


class CFNewsScraper(BaseScraper):
    SOURCE_NAME = "CFNEWS Immo"
    BASE_URL = "https://www.cfnews.net"

    # CFNEWS expose plusieurs flux RSS par thématique
    RSS_URLS = [
        "https://www.cfnews.net/rss/immo",
        "https://www.cfnews.net/rss/list/immo",
        "https://www.cfnews.net/Immo/rss",
        "https://www.cfnews.net/feed/immo",
        "https://www.cfnewsimmo.net/rss",
        "https://www.cfnewsimmo.net/feed",
        # Flux global (fallback)
        "https://www.cfnews.net/rss",
        "https://www.cfnews.net/feed",
    ]

    LISTING_URLS = [
        "https://www.cfnews.net/Immo",
        "https://www.cfnewsimmo.net",
    ]

    # ------------------------------------------------------------------
    # Stratégie 2 : Scraping HTML
    # ------------------------------------------------------------------

    def _fetch_html(self) -> list[Article]:
        for url in self.LISTING_URLS:
            soup = self._get_html(url)
            if soup:
                articles = self._parse_listing(soup, url)
                if articles:
                    return articles
            time.sleep(REQUEST_DELAY)
        return []

    def _parse_listing(self, soup: BeautifulSoup, base_url: str) -> list[Article]:
        articles: list[Article] = []

        # Sélecteurs CSS classiques des portails de news
        selectors = [
            "article",
            ".article",
            ".news-item",
            ".actu-item",
            ".post",
            ".item",
            "li.article",
            "div[class*='article']",
            "div[class*='news']",
            "div[class*='actu']",
        ]

        items = []
        for selector in selectors:
            items = soup.select(selector)
            if items:
                break

        # Fallback : tous les titres h2/h3 avec un lien
        if not items:
            items = soup.select("h2 a, h3 a, h4 a")
            for a_tag in items:
                href = a_tag.get("href", "")
                title = a_tag.get_text(strip=True)
                if not title or not href:
                    continue
                full_url = urljoin(base_url, href)
                articles.append(
                    Article(
                        title=title,
                        url=full_url,
                        source=self.SOURCE_NAME,
                        summary="",
                    )
                )
            return articles

        for item in items:
            article = self._parse_article_block(item, base_url)
            if article:
                articles.append(article)

        return articles

    def _parse_article_block(self, item: BeautifulSoup, base_url: str) -> Optional[Article]:
        """Extrait les données d'un bloc article."""
        # Titre + lien
        title_tag = item.select_one("h2 a, h3 a, h4 a, .title a, .article-title a, a.title")
        if not title_tag:
            title_tag = item.select_one("a")
        if not title_tag:
            return None

        title = title_tag.get_text(strip=True)
        href = title_tag.get("href", "")
        if not title or not href:
            return None

        full_url = urljoin(base_url, href)

        # Résumé
        summary_tag = item.select_one(
            "p, .summary, .excerpt, .intro, .chapo, .description, .teaser"
        )
        summary = summary_tag.get_text(strip=True)[:500] if summary_tag else ""

        # Catégorie
        cat_tag = item.select_one(".category, .rubrique, .tag, .label, .type")
        category = cat_tag.get_text(strip=True) if cat_tag else ""

        # Auteur
        author_tag = item.select_one(".author, .auteur, .byline, [rel='author']")
        author = author_tag.get_text(strip=True) if author_tag else ""

        return Article(
            title=title,
            url=full_url,
            source=self.SOURCE_NAME,
            summary=summary,
            category=category,
            author=author,
        )

    # ------------------------------------------------------------------
    # Stratégie 3 : Playwright
    # ------------------------------------------------------------------

    def _fetch_playwright(self) -> list[Article]:
        for url in self.LISTING_URLS:
            soup = self._get_playwright_html(url)
            if soup:
                articles = self._parse_listing(soup, url)
                if articles:
                    return articles
        return []
