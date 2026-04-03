"""
Scraper pour Business Immo (businessimmo.com).

Stratégies (dans l'ordre) :
1. Flux RSS officiels (plusieurs catégories)
2. Scraping HTML de la page d'accueil / actualités
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


class BusinessImmoScraper(BaseScraper):
    SOURCE_NAME = "Business Immo"
    BASE_URL = "https://www.businessimmo.com"

    # Business Immo publie des flux RSS par catégorie d'actif
    RSS_URLS = [
        # Flux principaux
        "https://www.businessimmo.com/rss/feed.xml",
        "https://www.businessimmo.com/rss/all/feed.xml",
        "https://www.businessimmo.com/flux-rss",
        "https://www.businessimmo.com/rss",
        "https://www.businessimmo.com/feed",
        "https://www.businessimmo.com/feed.xml",
        # Flux par catégorie (actifs immobiliers)
        "https://www.businessimmo.com/rss/bureau/feed.xml",
        "https://www.businessimmo.com/rss/logement/feed.xml",
        "https://www.businessimmo.com/rss/commerce/feed.xml",
        "https://www.businessimmo.com/rss/investissement/feed.xml",
        "https://www.businessimmo.com/rss/marches/feed.xml",
        "https://www.businessimmo.com/rss/transactions/feed.xml",
    ]

    LISTING_URLS = [
        "https://www.businessimmo.com/actualites",
        "https://www.businessimmo.com/",
        "https://www.businessimmo.com/news",
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

        # Business Immo utilise des classes spécifiques (identifiées via inspection)
        selectors = [
            "article.news",
            "article.article",
            ".news-list__item",
            ".article-list__item",
            ".actu__item",
            ".content-item",
            "article",
            ".article",
            ".news-item",
            "li.item",
            "div[class*='article']",
            "div[class*='news']",
        ]

        items = []
        for selector in selectors:
            items = soup.select(selector)
            if len(items) >= 3:  # Au moins 3 résultats pour valider
                break

        if not items:
            # Fallback générique : liens contenant des titres h2/h3
            for tag in soup.select("h2 a, h3 a, h4 a"):
                href = tag.get("href", "")
                title = tag.get_text(strip=True)
                if title and href:
                    articles.append(
                        Article(
                            title=title,
                            url=urljoin(base_url, href),
                            source=self.SOURCE_NAME,
                        )
                    )
            return articles

        for item in items:
            article = self._parse_article_block(item, base_url)
            if article:
                articles.append(article)

        return articles

    def _parse_article_block(self, item: BeautifulSoup, base_url: str) -> Optional[Article]:
        # Titre + lien
        title_tag = item.select_one(
            "h1 a, h2 a, h3 a, h4 a, .title a, .article-title a, "
            ".news-title a, .headline a, a.title, a.headline"
        )
        if not title_tag:
            title_tag = item.select_one("a")
        if not title_tag:
            return None

        title = title_tag.get_text(strip=True)
        href = title_tag.get("href", "")
        if not title or not href:
            return None

        full_url = urljoin(base_url, href)
        # Filtre : on ne garde que les liens internes au site
        if not full_url.startswith(self.BASE_URL) and not full_url.startswith("/"):
            if not href.startswith("http"):
                full_url = urljoin(base_url, href)
            elif self.BASE_URL not in full_url:
                return None

        # Résumé
        summary_tag = item.select_one(
            "p, .summary, .excerpt, .intro, .chapo, .description, .teaser, .standfirst"
        )
        summary = summary_tag.get_text(strip=True)[:500] if summary_tag else ""

        # Catégorie / rubrique
        cat_tag = item.select_one(
            ".category, .rubrique, .tag, .label, .type, .section, "
            "[class*='category'], [class*='rubrique'], [class*='tag']"
        )
        category = cat_tag.get_text(strip=True) if cat_tag else ""

        # Auteur
        author_tag = item.select_one(".author, .auteur, .byline, [rel='author'], .signature")
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
