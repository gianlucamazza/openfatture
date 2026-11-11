"""PDF of a year's invoice situation: totals, documents, overdue amounts, clients.

The data comes from ``billing.application.report_queries.invoice_situation``;
this module only lays it out. Platypus handles pagination and repeats the table
headers on every page.
"""

from datetime import date
from html import escape
from pathlib import Path
from typing import Any

from babel.numbers import format_currency
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from openfatture.pdf.generator import PDFGeneratorConfig

SUMMARY_NOTE = "Riepilogo gestionale: non costituisce documento fiscale."

PAYMENT_STATUS_LABELS = {
    "fully_paid": "Saldata",
    "partially_paid": "Parziale",
    "unpaid": "Non incassata",
    "no_payment_record": "Incasso non registrato",
}

_BODY = ParagraphStyle("Body", fontName="Helvetica", fontSize=9, leading=12)
_SMALL = ParagraphStyle("Small", parent=_BODY, fontSize=8, leading=10)
_CELL = ParagraphStyle("Cell", parent=_BODY, fontSize=8, leading=10)


def _eur(amount: float) -> str:
    return format_currency(amount, "EUR", locale="it_IT")


def _documents(count: int) -> str:
    return "1 documento" if count == 1 else f"{count} documenti"


def _date(value: str | None) -> str:
    return date.fromisoformat(value).strftime("%d/%m/%Y") if value else "—"


def _heading(text: str, color: str, size: int = 12) -> Paragraph:
    style = ParagraphStyle(
        f"H{size}",
        fontName="Helvetica-Bold",
        fontSize=size,
        leading=size + 4,
        textColor=HexColor(color),
        spaceBefore=10,
        spaceAfter=4,
    )
    return Paragraph(escape(text), style)


def _table(rows: list[list[Any]], widths: list[float], color: str, numeric_from: int) -> Table:
    table = Table(rows, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), HexColor(color)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (numeric_from, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, HexColor("#F4F6F7")]),
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, HexColor("#D5D8DC")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def _note(row: dict[str, Any]) -> str:
    if row["nota_credito"]:
        return "Nota di credito"
    parts = [PAYMENT_STATUS_LABELS.get(row["payment_status"], row["payment_status"])]
    if row["overdue"]:
        parts.append(f"scaduto {_eur(row['overdue'])}")
    elif row["next_due_date"]:
        parts.append(f"scade il {_date(row['next_due_date'])}")
    if row["issued_elsewhere"]:
        parts.append("emessa altrove")
    return ", ".join(parts)


class InvoiceSummaryPDF:
    """Render ``invoice_situation`` output as an A4 PDF."""

    def __init__(self, config: PDFGeneratorConfig) -> None:
        self.config = config

    def generate(self, situation: dict[str, Any], output_path: str) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        doc = SimpleDocTemplate(
            str(path),
            pagesize=A4,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2.5 * cm,
            title=f"Riepilogo fatture {situation['anno']}",
            author=self.config.company_name,
        )
        doc.build(self._story(situation), onFirstPage=self._footer, onLaterPages=self._footer)
        return path

    def _footer(self, canvas: Canvas, doc: SimpleDocTemplate) -> None:
        canvas.saveState()
        page = canvas.getPageNumber()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(HexColor("#999999"))
        canvas.drawString(2 * cm, 1 * cm, SUMMARY_NOTE)
        canvas.drawRightString(19 * cm, 1 * cm, f"Pagina {page}")
        canvas.restoreState()

    def _story(self, situation: dict[str, Any]) -> list[Flowable]:
        color = self.config.primary_color
        totals = situation["totals"]
        company = [
            part
            for part in (
                self.config.company_vat and f"P.IVA {self.config.company_vat}",
                self.config.company_address,
                self.config.company_city,
            )
            if part
        ]
        story: list[Flowable] = [
            _heading(self.config.company_name or "OpenFatture", color, 14),
            Paragraph(escape(" · ".join(company)), _SMALL),
            _heading(f"Situazione fatture {situation['anno']}", color, 16),
            Paragraph(
                f"Generato il {_date(situation['generated_on'])} · "
                f"{_documents(situation['documents_count'])}",
                _SMALL,
            ),
            Spacer(1, 0.3 * cm),
        ]

        kpis = [
            ("Fatturato", totals["net_invoiced"]),
            ("Incassato", totals["collected"]),
            ("Residuo", totals["outstanding"]),
            ("Scaduto", totals["overdue"]),
        ]
        kpi_table = Table(
            [[label for label, _ in kpis], [_eur(value) for _, value in kpis]],
            colWidths=[4.25 * cm] * 4,
        )
        kpi_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, 0), 8),
                    ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#7F8C8D")),
                    ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 1), (-1, 1), 13),
                    ("TEXTCOLOR", (0, 1), (-1, 1), HexColor(color)),
                    ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#D5D8DC")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, HexColor("#D5D8DC")),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(kpi_table)

        if not situation["documents"]:
            story.append(Spacer(1, 0.5 * cm))
            empty = f"Nessuna fattura emessa per il {situation['anno']}."
            if situation["excluded_drafts"]:
                empty += f" Bozze locali non emesse: {situation['excluded_drafts']}."
            story.append(Paragraph(empty, _BODY))
            return story

        story.append(_heading("Documenti", color))
        rows: list[list[Any]] = [
            ["Numero", "Data", "Cliente", "Totale", "Incassato", "Residuo", "Note"]
        ]
        for row in situation["documents"]:
            rows.append(
                [
                    row["numero"],
                    _date(row["data"]),
                    Paragraph(escape(row["cliente"]), _CELL),
                    _eur(-row["totale"] if row["nota_credito"] else row["totale"]),
                    _eur(row["amount_paid"]),
                    _eur(row["outstanding"]),
                    Paragraph(escape(_note(row)), _CELL),
                ]
            )
        documents = _table(
            rows,
            [1.6 * cm, 1.9 * cm, 3.6 * cm, 2.2 * cm, 2.2 * cm, 2.0 * cm, 3.5 * cm],
            color,
            numeric_from=3,
        )
        # The notes column is text: keep it left-aligned.
        documents.setStyle(TableStyle([("ALIGN", (6, 0), (6, -1), "LEFT")]))
        story.append(documents)

        if situation["clients"]:
            story.append(_heading("Clienti", color))
            client_rows: list[list[Any]] = [["Cliente", "Fatturato", "Quota"]]
            client_rows += [
                [
                    Paragraph(escape(c["cliente"]), _CELL),
                    _eur(c["totale"]),
                    f"{c['quota']:.1f}%".replace(".", ","),
                ]
                for c in situation["clients"]
            ]
            story.append(_table(client_rows, [9 * cm, 4 * cm, 4 * cm], color, numeric_from=1))

        story.append(_heading("Avvertenze", color))
        for text in self._warnings(situation):
            story.append(Paragraph(f"• {escape(text)}", _SMALL))
        return story

    @staticmethod
    def _warnings(situation: dict[str, Any]) -> list[str]:
        totals = situation["totals"]
        warnings = [
            "Gli incassi riportati sono quelli registrati in OpenFatture: l'assenza di un "
            "incasso registrato non prova che non sia avvenuto."
        ]
        if totals["unscheduled"]:
            warnings.append(
                f"{_eur(totals['unscheduled'])} di residuo non hanno una scadenza registrata."
            )
        if situation["historical_count"]:
            warnings.append(
                f"Emessi altrove: {_documents(situation['historical_count'])}; "
                "lo stato locale non indica una mancata emissione."
            )
        if situation["sdi_unverified_count"]:
            warnings.append(
                f"Senza ricevuta SDI: {_documents(situation['sdi_unverified_count'])}; "
                "la trasmissione non è verificata."
            )
        if situation["excluded_drafts"]:
            warnings.append(
                f"Bozze locali non emesse escluse dai totali: {situation['excluded_drafts']}."
            )
        if totals["credit_notes"]:
            warnings.append(
                f"Il fatturato è al netto di {_eur(totals['credit_notes'])} di note di credito."
            )
        return warnings
