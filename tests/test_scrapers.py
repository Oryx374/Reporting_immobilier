"""
Tests unitaires des scrapers (sans appels réseau réels).
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from scrapers.base_scraper import Article, BaseScraper
from scrapers.cfnews_scraper import CFNewsScraper
from scrapers.businessimmo_scraper import BusinessImmoScraper


class TestArticle:
    def test_to_dict_basic(self):
        a = Article(title="Test", url="https://example.com", source="Test Source")
        d = a.to_dict()
        assert d["title"] == "Test"
        assert d["url"] == "https://example.com"
        assert d["source"] == "Test Source"
        assert d["published_at"] is None

    def test_to_dict_with_date(self):
        dt = datetime(2024, 6, 1, 9, 0, tzinfo=timezone.utc)
        a = Article(title="Test", url="https://example.com", source="X", published_at=dt)
        d = a.to_dict()
        assert "2024-06-01" in d["published_at"]


class TestCFNewsScraper:
    def test_instantiation(self):
        scraper = CFNewsScraper()
        assert scraper.SOURCE_NAME == "CFNEWS Immo"
        assert len(scraper.RSS_URLS) > 0

    def test_parse_html_fallback(self):
        """Vérifie que le parsing HTML générique fonctionne."""
        from bs4 import BeautifulSoup
        scraper = CFNewsScraper()
        html = """
        <html><body>
          <h2><a href="/immo/article-1">Marché bureaux : stabilisation des valeurs</a></h2>
          <h3><a href="/immo/article-2">Investissement logistique en hausse</a></h3>
        </body></html>
        """
        soup = BeautifulSoup(html, "lxml")
        articles = scraper._parse_listing(soup, "https://www.cfnews.net")
        assert len(articles) >= 2
        assert articles[0].title == "Marché bureaux : stabilisation des valeurs"
        assert "cfnews.net" in articles[0].url

    def test_parse_article_block(self):
        from bs4 import BeautifulSoup
        scraper = CFNewsScraper()
        html = """
        <article>
          <h2><a href="/deal/123">Acquisition d'un portefeuille de bureaux</a></h2>
          <p>Un fonds paneuropéen acquiert 3 actifs de bureaux prime en IDF.</p>
          <span class="category">Bureaux</span>
        </article>
        """
        soup = BeautifulSoup(html, "lxml")
        item = soup.select_one("article")
        article = scraper._parse_article_block(item, "https://www.cfnews.net")
        assert article is not None
        assert article.title == "Acquisition d'un portefeuille de bureaux"
        assert article.category == "Bureaux"
        assert "fonds paneuropéen" in article.summary


class TestBusinessImmoScraper:
    def test_instantiation(self):
        scraper = BusinessImmoScraper()
        assert scraper.SOURCE_NAME == "Business Immo"
        assert len(scraper.RSS_URLS) > 0

    def test_filters_external_links(self):
        """Les liens externes au domaine businessimmo.com doivent être ignorés."""
        from bs4 import BeautifulSoup
        scraper = BusinessImmoScraper()
        html = """
        <article>
          <h2><a href="https://www.autre-site.com/article">Article externe</a></h2>
          <p>Résumé externe.</p>
        </article>
        """
        soup = BeautifulSoup(html, "lxml")
        item = soup.select_one("article")
        article = scraper._parse_article_block(item, "https://www.businessimmo.com")
        assert article is None


class TestReportSynthesizer:
    def test_empty_articles(self):
        from report.synthesizer import ReportSynthesizer
        synth = ReportSynthesizer()
        result = synth.synthesize([])
        assert result["article_count"] == 0
        assert "Aucun article" in result["ai_report"]

    def test_format_articles_for_prompt(self):
        from report.synthesizer import ReportSynthesizer
        synth = ReportSynthesizer()
        articles = [
            Article(title="Deal IDF", url="https://example.com/1", source="CFNEWS Immo",
                    summary="Acquisition d'un immeuble de bureaux à La Défense."),
        ]
        text = synth._format_articles_for_prompt(articles)
        assert "Deal IDF" in text
        assert "CFNEWS Immo" in text


class TestReportFormatter:
    def test_markdown_to_html_bold(self):
        from report.formatter import ReportFormatter
        fmt = ReportFormatter()
        result = fmt._markdown_to_html("**Texte gras**")
        assert "<strong>Texte gras</strong>" in result

    def test_markdown_to_html_heading(self):
        from report.formatter import ReportFormatter
        fmt = ReportFormatter()
        result = fmt._markdown_to_html("## Titre section")
        assert "<h2>Titre section</h2>" in result

    def test_to_text(self):
        from report.formatter import ReportFormatter
        fmt = ReportFormatter()
        synthesis = {
            "ai_report": "Résumé du marché",
            "articles": [
                {"source": "CFNEWS Immo", "title": "Article test",
                 "url": "https://example.com", "summary": ""}
            ],
            "article_count": 1,
        }
        text = fmt.to_text(synthesis)
        assert "RAPPORT IMMOBILIER" in text
        assert "Article test" in text
