"""
Scraping des actualités immobilières depuis CFNews Immo et Business Immo.
Utilise Playwright pour contourner la protection anti-bot.
"""

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from playwright.async_api import async_playwright, Page


@dataclass
class Article:
    titre: str
    lien: str
    resume: Optional[str]
    date: Optional[str]
    source: str


async def _scroll_and_wait(page: Page, max_scroll: int = 3) -> None:
    """Scrolle la page pour déclencher le chargement lazy."""
    for _ in range(max_scroll):
        await page.evaluate("window.scrollBy(0, window.innerHeight)")
        await page.wait_for_timeout(800)


async def _scrape_cfnews_immo(page: Page) -> list[Article]:
    """Scrape les articles de CFNews Immo."""
    articles = []
    try:
        await page.goto("https://www.cfnews-immo.com/", wait_until="domcontentloaded", timeout=30000)
        await _scroll_and_wait(page)

        # Sélecteurs possibles pour les articles
        selectors = [
            "article",
            ".article",
            ".news-item",
            ".post",
            "[class*='article']",
            "[class*='news']",
            "h2 a",
            "h3 a",
        ]

        elements = []
        for selector in selectors:
            elements = await page.query_selector_all(selector)
            if len(elements) >= 3:
                break

        seen_links = set()
        for el in elements[:20]:
            try:
                # Titre
                titre_el = await el.query_selector("h1, h2, h3, h4, .title, .titre, [class*='title'], [class*='titre']")
                if not titre_el:
                    titre_el = el if await el.evaluate("el => ['H1','H2','H3','H4','A'].includes(el.tagName)") else None

                titre = ""
                if titre_el:
                    titre = (await titre_el.inner_text()).strip()

                if not titre or len(titre) < 10:
                    continue

                # Lien
                lien_el = await el.query_selector("a")
                lien = ""
                if lien_el:
                    lien = await lien_el.get_attribute("href") or ""
                    if lien and not lien.startswith("http"):
                        lien = "https://www.cfnews-immo.com" + lien

                if lien in seen_links:
                    continue
                seen_links.add(lien)

                # Résumé
                resume_el = await el.query_selector("p, .excerpt, .resume, .description, [class*='excerpt'], [class*='summary']")
                resume = ""
                if resume_el:
                    resume = (await resume_el.inner_text()).strip()[:300]

                # Date
                date_el = await el.query_selector("time, .date, [class*='date'], [datetime]")
                date = ""
                if date_el:
                    date = await date_el.get_attribute("datetime") or (await date_el.inner_text()).strip()

                articles.append(Article(
                    titre=titre,
                    lien=lien,
                    resume=resume or None,
                    date=date or None,
                    source="CFNews Immo"
                ))
            except Exception:
                continue

        # Fallback : récupérer tous les liens h2/h3 si pas d'articles trouvés
        if not articles:
            links = await page.query_selector_all("h2 a, h3 a, .headline a")
            for link in links[:15]:
                try:
                    titre = (await link.inner_text()).strip()
                    lien = await link.get_attribute("href") or ""
                    if lien and not lien.startswith("http"):
                        lien = "https://www.cfnews-immo.com" + lien
                    if titre and len(titre) > 10:
                        articles.append(Article(titre=titre, lien=lien, resume=None, date=None, source="CFNews Immo"))
                except Exception:
                    continue

    except Exception as e:
        print(f"[CFNews Immo] Erreur: {e}")

    return articles


async def _scrape_business_immo(page: Page) -> list[Article]:
    """Scrape les articles de Business Immo."""
    articles = []
    try:
        await page.goto("https://www.businessimmo.com/", wait_until="domcontentloaded", timeout=30000)
        await _scroll_and_wait(page)

        selectors = [
            "article",
            ".article",
            ".news-item",
            ".post",
            "[class*='article']",
            "[class*='news']",
            ".content-item",
        ]

        elements = []
        for selector in selectors:
            elements = await page.query_selector_all(selector)
            if len(elements) >= 3:
                break

        seen_links = set()
        for el in elements[:20]:
            try:
                titre_el = await el.query_selector("h1, h2, h3, h4, .title, .titre, [class*='title']")
                if not titre_el:
                    continue

                titre = (await titre_el.inner_text()).strip()
                if not titre or len(titre) < 10:
                    continue

                lien_el = await el.query_selector("a")
                lien = ""
                if lien_el:
                    lien = await lien_el.get_attribute("href") or ""
                    if lien and not lien.startswith("http"):
                        lien = "https://www.businessimmo.com" + lien

                if lien in seen_links:
                    continue
                seen_links.add(lien)

                resume_el = await el.query_selector("p, .excerpt, .chapo, [class*='excerpt']")
                resume = ""
                if resume_el:
                    resume = (await resume_el.inner_text()).strip()[:300]

                date_el = await el.query_selector("time, .date, [class*='date'], [datetime]")
                date = ""
                if date_el:
                    date = await date_el.get_attribute("datetime") or (await date_el.inner_text()).strip()

                articles.append(Article(
                    titre=titre,
                    lien=lien,
                    resume=resume or None,
                    date=date or None,
                    source="Business Immo"
                ))
            except Exception:
                continue

        if not articles:
            links = await page.query_selector_all("h2 a, h3 a, .headline a, .article-title a")
            for link in links[:15]:
                try:
                    titre = (await link.inner_text()).strip()
                    lien = await link.get_attribute("href") or ""
                    if lien and not lien.startswith("http"):
                        lien = "https://www.businessimmo.com" + lien
                    if titre and len(titre) > 10:
                        articles.append(Article(titre=titre, lien=lien, resume=None, date=None, source="Business Immo"))
                except Exception:
                    continue

    except Exception as e:
        print(f"[Business Immo] Erreur: {e}")

    return articles


async def scrape_all() -> list[Article]:
    """Lance le scraping des deux sources en parallèle."""
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
            ]
        )

        # Contexte avec un User-Agent réaliste
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
            locale="fr-FR",
        )

        # Masquer les traces d'automatisation
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['fr-FR', 'fr', 'en'] });
        """)

        page1 = await context.new_page()
        page2 = await context.new_page()

        cfnews_articles, business_articles = await asyncio.gather(
            _scrape_cfnews_immo(page1),
            _scrape_business_immo(page2),
        )

        await browser.close()

    all_articles = cfnews_articles + business_articles
    print(f"[Scraping] {len(cfnews_articles)} articles CFNews Immo, {len(business_articles)} articles Business Immo")
    return all_articles


def scrape() -> list[Article]:
    """Point d'entrée synchrone."""
    return asyncio.run(scrape_all())


if __name__ == "__main__":
    articles = scrape()
    for a in articles:
        print(f"[{a.source}] {a.titre}")
        if a.lien:
            print(f"  → {a.lien}")
