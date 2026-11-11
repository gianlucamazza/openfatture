"""Shared chat prompt builders for product backends (chat + langgraph).

Keeps system prompt and message assembly identical so backend parity tests
compare orchestration, not copy-paste drift.
"""

from __future__ import annotations

from openfatture.ai.domain.context import ChatContext
from openfatture.ai.domain.message import Message, Role
from openfatture.platform.logging import get_logger

logger = get_logger(__name__)

_CATEGORY_LABELS = {
    "batch": "import/export CSV e aggiornamenti massivi",
    "clients": "gestione clienti",
    "invoices": "gestione fatture e righe",
    "knowledge": "base di conoscenza normativa",
    "payments": "pagamenti e incassi",
    "pdf": "generazione PDF di fatture, preventivi e riepiloghi",
    "preventivi": "preventivi",
    "prodotti": "catalogo prodotti",
    "reports": "report",
    "sdi": "notifiche SDI",
    "signature": "firma digitale",
}


def build_chat_system_prompt(context: ChatContext, *, enable_tools: bool = True) -> str:
    """Build the product assistant system prompt with optional tool/context hints."""
    parts = [
        "Sei un assistente AI specializzato per OpenFatture, un sistema di "
        "fatturazione elettronica italiana.",
        "",
        "Il tuo ruolo è:",
        "- Rispondere a domande su fatture e clienti",
        "- Fornire statistiche e insights",
        "- Guidare l'utente attraverso i workflow",
        "- Eseguire azioni tramite tools quando necessario",
        "",
        "Regole:",
        "- Risposte proporzionate alla richiesta: a un saluto rispondi con un saluto breve e una domanda, senza cataloghi di funzionalità.",
        "- Fornisci dettagli quando servono; evita emoji decorative e introduzioni ripetitive.",
        "- Distingui capacità disponibili da configurazione pronta. Conferma il completamento solo dopo un risultato positivo degli strumenti.",
        "- Le fatture issued_elsewhere sono documenti storici emessi altrove, non vere bozze. Nei riepiloghi usa per_documento e distingui stato tecnico, stato SDI e incassi. Non dedurre mai da bozza che una fattura storica non sia stata emessa o trasmessa: senza evidenza SDI dichiara stato non verificato. Nessun pagamento registrato non prova il mancato incasso.",
        "- Se submission_state è pending o uncertain oppure invii_da_verificare non è vuoto, dichiara esito PEC da verificare: non dedurre da bozza o da un errore che non sia stata trasmessa, e non proporre retry automatici. Usa sdi_evidence e submission_evidence per indicare la provenienza dello stato.",
        "- Gli incassi provengono dal registro: separa importo ricevuto, allocato, disponibile e residuo fattura. Usa get_collections per la cronologia. Una dichiarazione not_settled è una fonte sul mancato saldo, non un importo incassato pari a zero. Date mancanti restano sconosciute; non inventare scadenze o date di incasso.",
        "- Per registrare o allocare incassi usa gli strumenti collection con request_id stabile e riutilizzalo nei retry. Uno storno corregge una allocazione e rende denaro nuovamente disponibile: non è un rimborso bancario. Non allocare addebiti o movimenti non EUR. Gli importi bancari non allocati restano disponibili e non saldano automaticamente altre fatture.",
        "- Usa un tono professionale ma friendly",
        "- Rispondi in italiano (salvo richiesta diversa)",
        "- Se non hai informazioni sufficienti, chiedi chiarimenti",
        "- Prima di eseguire azioni distruttive, chiedi conferma",
        "- Cita i dati specifici quando disponibili (numeri, date, importi)",
        "- Il PDF di una fattura è una copia di cortesia: l'originale fiscale è l'XML transitato da SDI. Puoi generarlo anche per le fatture issued_elsewhere, dicendo che è una copia di cortesia. Riporta il percorso del file restituito dallo strumento.",
        "- Per il file XML FatturaPA di una fattura (da caricare su un portale, da dare a un intermediario o da firmare) usa generate_invoice_xml: lo valida con lo schema XSD, lo salva nell'archivio solo se valido e non trasmette nulla. Riporta il percorso o gli errori di validazione.",
        "- Per un riepilogo o report in PDF della situazione fatture usa generate_invoice_summary_pdf: i numeri del documento li calcola lo strumento, non ricomporli tu. Riporta il percorso e i totali restituiti.",
        "- OpenFatture è un'applicazione a riga di comando: non esiste un'interfaccia grafica, non descriverne una.",
    ]

    if context.current_year_stats:
        stats = context.current_year_stats
        parts.extend(
            [
                "",
                "Contesto corrente:",
                f"- Anno: {stats.get('anno', 'N/A')}",
                f"- Fatture totali: {stats.get('totale_fatture', 0)}",
                f"- Importo totale: €{stats.get('importo_totale', 0):.2f}",
            ]
        )

    if enable_tools and context.available_tools:
        parts.extend(
            [
                "",
                "Strumenti disponibili:",
                f"- Puoi chiamare esattamente i {len(context.available_tools)} strumenti nello schema; usali per recuperare dati o eseguire azioni.",
            ]
        )

    if enable_tools and context.disabled_capabilities:
        parts.extend(["", "Capacità di OpenFatture disattivate per l'assistente:"])
        for category, command in context.disabled_capabilities.items():
            label = _CATEGORY_LABELS.get(category, category)
            parts.append(f"- {label}: l'utente può attivarla con `{command}`")
        parts.append(
            "- Se una richiesta richiede una capacità disattivata, non dire che OpenFatture "
            "non la supporta: spiega che è disattivata per l'assistente e indica il comando "
            "per attivarla."
        )

    if context.relevant_documents:
        parts.extend(
            [
                "",
                "Documenti rilevanti dal sistema (fatture correlate):",
            ]
        )
        for doc in context.relevant_documents[:5]:
            parts.append(f"- {doc}")

    if context.knowledge_snippets:
        parts.extend(
            [
                "",
                "Fonti normative e note operative da consultare (cita come [numero]):",
            ]
        )
        for idx, snippet in enumerate(context.knowledge_snippets[:5], 1):
            citation = snippet.get("citation") or snippet.get("source") or f"Fonte {idx}"
            excerpt = snippet.get("excerpt", "")
            parts.append(f"[{idx}] {citation} — {excerpt}")

        parts.extend(
            [
                "",
                "Usa le fonti sopra per supportare la risposta e indica il riferimento con [numero].",
            ]
        )

    return "\n".join(parts)


def build_chat_messages(
    context: ChatContext,
    *,
    enable_tools: bool = True,
    include_system: bool = True,
) -> list[Message]:
    """Build the message list for one assistant turn (system + history + user)."""
    messages: list[Message] = []

    if include_system:
        messages.append(
            Message(
                role=Role.SYSTEM,
                content=build_chat_system_prompt(context, enable_tools=enable_tools),
            )
        )

    for msg in context.conversation_history.get_messages(include_system=False):
        messages.append(msg)

    if not messages or messages[-1].role != Role.USER:
        messages.append(Message(role=Role.USER, content=context.user_input))

    logger.debug(
        "chat_prompt_built",
        total_messages=len(messages),
        history_messages=len(context.conversation_history.messages),
        tools=len(context.available_tools),
    )
    return messages
