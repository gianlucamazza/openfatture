"""Boxed sections of an invoice PDF below the totals.

Payment details, notes, cassa previdenziale and the stamp duty notice. Each
function draws from ``y_position`` downwards and returns the next Y position.
"""

from decimal import Decimal
from typing import Any

from reportlab.lib.colors import Color, HexColor
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas

MODALITA_LABELS = {
    "MP05": "Bonifico bancario",
    "MP08": "Carta di credito",
    "MP01": "Contanti",
    "Bonifico": "Bonifico bancario",
    "Carta di credito": "Carta di credito",
    "Contanti": "Contanti",
}

TIPO_CASSA_LABELS = {
    "TC01": "Cassa nazionale previdenza avvocati",
    "TC02": "Cassa previdenza dottori commercialisti",
    "TC03": "Cassa previdenza e assistenza geometri",
    "TC04": "Cassa nazionale previdenza e assistenza ingegneri e architetti",
    "TC05": "Cassa nazionale del notariato",
    "TC06": "Cassa nazionale previdenza e assistenza ragionieri e periti commerciali",
    "TC07": "ENPACL (Consulenti del lavoro)",
    "TC08": "ENPAM (Medici)",
    "TC09": "ENPAP (Psicologi)",
    "TC10": "ENPAF (Farmacisti)",
    "TC11": "ENPAV (Veterinari)",
    "TC12": "ENPAIA (Periti agrari e agrotecnici)",
    "TC13": "EPPI (Periti industriali)",
    "TC14": "EPAP (Attuari, chimici, dottori agronomi e forestali, geologi)",
    "TC15": "ENPAB (Biologi)",
    "TC16": "ENPAPI (Infermieri)",
    "TC17": "ENPAP (Psicologi - duplicato)",
    "TC18": "ENPAIA (Agrotecnici e periti agrari - duplicato)",
    "TC19": "EPPI (Periti industriali - duplicato)",
    "TC20": "EPAP (Attuari, chimici, ecc. - duplicato)",
    "TC21": "ENPAB (Biologi - duplicato)",
    "TC22": "INPS",
}

CASSA_NATURA_LABELS = {
    "N1": "Esclusa ex art.15",
    "N2.2": "Non soggette - altri casi",
}


def draw_payment_info(
    canvas: Canvas,
    pagamento_data: dict[str, Any] | None,
    y_position: float,
    primary_color: Color,
) -> float:
    """Draw the DATI PAGAMENTO box (method, due date, IBAN, BIC)."""
    if not pagamento_data:
        return y_position

    # Add spacing before payment info
    y_position -= 0.5 * cm

    # Calculate block height based on content
    giorni_scadenza = pagamento_data.get("giorni_scadenza", 30)

    line_count = 1  # Payment description ("Pagamento completo" or method)
    if pagamento_data.get("data_scadenza") or giorni_scadenza == 0:
        line_count += 1  # Rif. termini or Scadenza
    if pagamento_data.get("iban"):
        line_count += 1
    if pagamento_data.get("bic_swift"):
        line_count += 1

    block_height = (line_count * 0.5 + 0.8) * cm
    block_width = 8 * cm

    # Draw background box
    canvas.setFillColor(HexColor("#F8F9FA"))
    canvas.setStrokeColor(primary_color)
    canvas.setLineWidth(1)
    canvas.rect(
        2 * cm, y_position - block_height, block_width, block_height, fill=True, stroke=True
    )

    # Title
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(primary_color)
    canvas.drawString(2.3 * cm, y_position - 0.6 * cm, "DATI PAGAMENTO")

    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(HexColor("#333333"))
    y = y_position - 1.1 * cm

    # Always show payment method (Bonifico, etc.)
    modalita_label = MODALITA_LABELS.get(
        pagamento_data.get("modalita", ""),
        pagamento_data.get("modalita", "Bonifico bancario"),
    )

    if giorni_scadenza == 0:
        # Immediate payment: show both "Pagamento completo" and modality
        canvas.drawString(2.3 * cm, y, f"Pagamento completo - {modalita_label}")
    else:
        # N-day terms: show payment method
        canvas.drawString(2.3 * cm, y, f"Modalità: {modalita_label}")
    y -= 0.5 * cm

    # Rif. termini pagamento or Scadenza
    if pagamento_data.get("data_scadenza"):
        scadenza = pagamento_data["data_scadenza"].strftime("%d/%m/%Y")
        if giorni_scadenza == 0:
            # Immediate: show as "Rif. termini pagamento"
            canvas.drawString(
                2.3 * cm,
                y,
                f"Rif. termini pagamento: {scadenza} (giorni di termine di pagamento)",
            )
        else:
            # N-day: show as "Scadenza"
            canvas.drawString(2.3 * cm, y, f"Scadenza: {scadenza}")
        y -= 0.5 * cm

    # IBAN (prominent for bank transfers)
    if pagamento_data.get("iban"):
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(2.3 * cm, y, f"IBAN: {pagamento_data['iban']}")
        canvas.setFont("Helvetica", 9)
        y -= 0.5 * cm

    # BIC (optional - only show if present)
    if pagamento_data.get("bic_swift"):
        canvas.drawString(2.3 * cm, y, f"BIC: {pagamento_data['bic_swift']}")
        y -= 0.5 * cm

    return y_position - block_height - 0.5 * cm


def draw_notes(canvas: Canvas, note: str | None, y_position: float) -> float:
    """Draw the invoice notes, wrapped at 80 characters."""
    if not note:
        return y_position

    # Add spacing before notes
    y_position -= 0.8 * cm

    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(HexColor("#333333"))
    canvas.drawString(2 * cm, y_position, "Note:")

    canvas.setFont("Helvetica", 9)
    y = y_position - 0.5 * cm

    words = note.split()
    lines = []
    current_line = ""

    for word in words:
        if len(current_line) + len(word) + 1 <= 80:
            current_line += word + " "
        else:
            lines.append(current_line.strip())
            current_line = word + " "

    if current_line:
        lines.append(current_line.strip())

    for line in lines:
        canvas.drawString(2 * cm, y, line)
        y -= 0.4 * cm

    return y - 0.3 * cm


def draw_cassa_previdenziale(
    canvas: Canvas,
    cassa_data: list[dict[str, Any]],
    y_position: float,
    primary_color: Color,
) -> float:
    """Draw the social security contribution (DatiCassaPrevidenziale) box."""
    if not cassa_data:
        return y_position

    # Add spacing before block
    y_position -= 0.8 * cm

    # Calculate block dimensions
    entries_count = len(cassa_data)
    line_height = 0.5 * cm
    block_height = (entries_count * 4 * line_height) + 1.2 * cm
    block_width = 8 * cm

    # Draw background box
    canvas.setFillColor(HexColor("#F8F9FA"))
    canvas.setStrokeColor(primary_color)
    canvas.setLineWidth(1)
    canvas.rect(
        2 * cm, y_position - block_height, block_width, block_height, fill=True, stroke=True
    )

    # Title
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(primary_color)
    canvas.drawString(2.3 * cm, y_position - 0.6 * cm, "CASSA PREVIDENZIALE")

    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(HexColor("#333333"))
    y = y_position - 1.1 * cm

    for cassa in cassa_data:
        tipo_cassa = cassa.get("tipo_cassa", "")
        tipo_label = TIPO_CASSA_LABELS.get(tipo_cassa, tipo_cassa)

        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(2.3 * cm, y, f"Tipo: {tipo_label}")
        y -= line_height

        canvas.setFont("Helvetica", 9)
        canvas.drawString(2.3 * cm, y, f"Aliquota: {cassa.get('al_cassa', 0):.2f}%")
        y -= line_height

        if cassa.get("imponibile_cassa"):
            canvas.drawString(2.3 * cm, y, f"Imponibile: € {cassa.get('imponibile_cassa', 0):.2f}")
            y -= line_height

        canvas.drawString(2.3 * cm, y, f"Importo: € {cassa.get('importo_contributo_cassa', 0):.2f}")
        y -= line_height

        if cassa.get("natura"):
            natura = cassa.get("natura", "")
            natura_label = CASSA_NATURA_LABELS.get(natura, natura)
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(HexColor("#666666"))
            canvas.drawString(2.3 * cm, y, f"Natura: {natura_label}")
            canvas.setFillColor(HexColor("#333333"))
            y -= line_height

    return y_position - block_height - 0.5 * cm


def draw_bollo_footer(
    canvas: Canvas, importo_bollo: Decimal, y_position: float, primary_color: Color
) -> float:
    """Draw the stamp duty box with the MEF reference (the bollo is always virtual)."""
    if importo_bollo <= 0:
        return y_position

    # Add spacing before footer
    y_position -= 0.8 * cm

    box_width = 8 * cm
    box_height = 1.2 * cm

    canvas.setFillColor(HexColor("#F8F9FA"))
    canvas.setStrokeColor(primary_color)
    canvas.setLineWidth(1)
    canvas.rect(2 * cm, y_position - box_height, box_width, box_height, fill=True, stroke=True)

    # Title
    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(primary_color)
    canvas.drawString(2.3 * cm, y_position - 0.5 * cm, "Bollo")

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(HexColor("#333333"))

    # Show bollo type and MEF reference
    y = y_position - 0.9 * cm
    canvas.drawString(
        2.3 * cm,
        y,
        "Tipo: Bollo assolto ai sensi del decreto MEF 17 GIUGNO 2014 (ART. 6)",
    )

    # Show amount
    canvas.setFont("Helvetica", 9)
    canvas.drawString(11 * cm - 2 * cm, y_position - 0.5 * cm, f"Importo: € {importo_bollo:.2f}")

    return y_position - box_height - 0.5 * cm
