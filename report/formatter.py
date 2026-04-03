"""
Formate le rapport synthétisé en HTML et en texte brut pour l'email.
"""

from __future__ import annotations

import re
from datetime import datetime

from jinja2 import Environment, FileSystemLoader, select_autoescape

import os

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")


class ReportFormatter:
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATE_DIR),
            autoescape=select_autoescape(["html"]),
        )

    def to_html(self, synthesis: dict) -> str:
        """Génère le HTML complet de l'email."""
        template = self.env.get_template("weekly_report.html")
        return template.render(
            report_date=datetime.now().strftime("%d %B %Y"),
            ai_report_html=self._markdown_to_html(synthesis["ai_report"]),
            articles=synthesis["articles"],
            article_count=synthesis["article_count"],
        )

    def to_text(self, synthesis: dict) -> str:
        """Version texte brut (fallback email)."""
        lines = [
            f"RAPPORT IMMOBILIER HEBDOMADAIRE — {datetime.now().strftime('%d/%m/%Y')}",
            "=" * 60,
            "",
            synthesis["ai_report"],
            "",
            "=" * 60,
            f"Sources : {synthesis['article_count']} articles collectés",
            "",
        ]
        for a in synthesis["articles"]:
            lines.append(f"• [{a['source']}] {a['title']}")
            lines.append(f"  {a['url']}")
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _markdown_to_html(text: str) -> str:
        """Conversion Markdown → HTML (gras, titres, listes, sauts de ligne)."""
        # Titres H1-H4
        text = re.sub(r"^#### (.+)$", r"<h4>\1</h4>", text, flags=re.MULTILINE)
        text = re.sub(r"^### (.+)$", r"<h3>\1</h3>", text, flags=re.MULTILINE)
        text = re.sub(r"^## (.+)$", r"<h2>\1</h2>", text, flags=re.MULTILINE)
        text = re.sub(r"^# (.+)$", r"<h1>\1</h1>", text, flags=re.MULTILINE)

        # Gras et italique
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)

        # Listes à puces (lignes commençant par - ou *)
        lines = text.split("\n")
        html_lines = []
        in_list = False
        for line in lines:
            if re.match(r"^\s*[-•]\s+", line):
                if not in_list:
                    html_lines.append("<ul>")
                    in_list = True
                item = re.sub(r"^\s*[-•]\s+", "", line)
                html_lines.append(f"<li>{item}</li>")
            else:
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                html_lines.append(line)
        if in_list:
            html_lines.append("</ul>")

        text = "\n".join(html_lines)

        # Paragraphes : double saut de ligne → <p>
        paragraphs = re.split(r"\n{2,}", text)
        result = []
        for p in paragraphs:
            p = p.strip()
            if not p:
                continue
            if p.startswith("<h") or p.startswith("<ul") or p.startswith("<li"):
                result.append(p)
            else:
                p = p.replace("\n", "<br>")
                result.append(f"<p>{p}</p>")

        return "\n".join(result)
