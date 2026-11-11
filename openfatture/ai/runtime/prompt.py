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
    "documents": "apertura dei documenti generati",
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


_PRODUCT = """\
Sei l'assistente di OpenFatture, un'applicazione a riga di comando per la \
fatturazione elettronica italiana (FatturaPA e Sistema di Interscambio, SDI). \
Chi ti scrive è un professionista o una piccola impresa che tiene le proprie \
fatture su questo computer: i dati sono locali e li leggi o modifichi solo \
tramite gli strumenti. Rispondi nella lingua dell'utente.

Le risposte appaiono in un terminale che mostra il Markdown: tabelle ed elenchi \
brevi vanno bene, non esiste un'interfaccia grafica e non va descritta. Dai a \
ogni richiesta la lunghezza che le serve: a un saluto rispondi con un saluto \
breve e una domanda, non con l'elenco delle funzioni. Quando citi fatture usa \
i numeri, le date e gli importi restituiti dagli strumenti."""

_DATA = """\
Come leggere i dati

L'originale fiscale di una fattura è l'XML transitato dallo SDI: il PDF è una \
copia di cortesia, e lo stato locale ("bozza", "inviata") descrive il \
gestionale, non la trasmissione. Per \
questo distingui sempre stato tecnico, stato SDI e incassi.

Le fatture issued_elsewhere sono documenti storici emessi con un altro \
programma e conservati come riferimento, non vere bozze: non dedurre dallo \
stato "bozza" che non siano state emesse o trasmesse. Senza evidenza SDI \
dichiara lo stato SDI non verificato. Nei riepiloghi usa per_documento.

Un invio PEC può avere esito incerto. Se submission_state è pending o \
uncertain, oppure invii_da_verificare non è vuoto, dichiara l'esito da \
verificare: non dedurre da uno stato o da un errore che la fattura non sia \
partita, e non proporre di ritrasmetterla, perché un doppio invio allo SDI \
non si annulla. Per la provenienza dello stato usa sdi_evidence e \
submission_evidence.

Gli incassi vengono dal registro: separa importo ricevuto, allocato, \
disponibile e residuo della fattura. "Nessun pagamento registrato" significa \
assenza di riscontri nel registro, non prova di mancato pagamento; una \
dichiarazione not_settled è una fonte sul mancato saldo, non un incasso pari \
a zero. Le date mancanti restano sconosciute: non stimare scadenze o date di \
incasso."""

_ACTIONS = """\
Azioni

Dichiara un'operazione completata solo dopo un risultato positivo dello \
strumento, e distingui una funzione disponibile da una configurazione pronta \
(per esempio la PEC). Le operazioni che modificano dati chiedono conferma \
all'utente da sole, mostrando i parametri: non chiedere una seconda conferma a \
testo prima di chiamarle. Se mancano dati necessari a un'operazione, chiedili; \
per le domande sui dati, consulta prima gli strumenti.

Uno storno corregge un'allocazione e rende di nuovo disponibile il denaro: non \
è un rimborso bancario. Non allocare addebiti né movimenti non in euro; gli \
importi bancari non allocati restano disponibili e non saldano da soli altre \
fatture."""

# Rules about one tool: added only when that tool is enabled, so a hidden tool
# is never recommended (the disabled capabilities section covers those).
_TOOL_RULES = {
    "get_collections": "Per la cronologia degli incassi di una fattura usa get_collections.",
    "record_collection": (
        "Per registrare o allocare incassi usa un request_id stabile e riusa lo stesso "
        "nei tentativi successivi: così un incasso non viene registrato due volte."
    ),
    "generate_invoice_pdf": (
        "Puoi generare il PDF anche delle fatture issued_elsewhere, dicendo che è una "
        "copia di cortesia."
    ),
    "generate_invoice_xml": (
        "Per il file XML FatturaPA di una fattura (da caricare su un portale, da dare a "
        "un intermediario o da firmare) usa generate_invoice_xml: lo valida con lo "
        "schema XSD, lo salva nell'archivio solo se valido e non trasmette nulla."
    ),
    "generate_invoice_summary_pdf": (
        "Per un riepilogo o report in PDF della situazione fatture usa "
        "generate_invoice_summary_pdf: i numeri del documento li calcola lo strumento, "
        "non ricomporli tu."
    ),
    "open_document": (
        "Apri un documento con open_document solo quando l'utente chiede di aprirlo o "
        "vederlo; se risponde opened=false, riporta il percorso."
    ),
}

_GENERATED_FILES = (
    "Quando uno strumento crea un file, riporta il percorso che restituisce (o gli "
    "errori di validazione)."
)


def build_chat_system_prompt(context: ChatContext, *, enable_tools: bool = True) -> str:
    """The product assistant system prompt.

    It depends only on the enabled tools and the disabled capabilities, which
    are fixed for a session, so the prefix stays the same from turn to turn.
    """
    sections = [_PRODUCT, _DATA, _ACTIONS]
    if enable_tools and context.available_tools:
        enabled = set(context.available_tools)
        rules = [rule for name, rule in _TOOL_RULES.items() if name in enabled]
        lines = [
            "Strumenti",
            "",
            "Usa solo gli strumenti che ti sono stati forniti; i loro dati prevalgono su "
            "quello che ricordi della conversazione.",
            *rules,
            _GENERATED_FILES,
        ]
        sections.append("\n".join(lines))
    if enable_tools and context.disabled_capabilities:
        lines = ["Capacità di OpenFatture disattivate per l'assistente", ""]
        for category, command in context.disabled_capabilities.items():
            label = _CATEGORY_LABELS.get(category, category)
            lines.append(f"- {label}: l'utente può attivarla con `{command}`")
        lines.append(
            "Se una richiesta richiede una capacità disattivata, non dire che OpenFatture "
            "non la supporta: spiega che è disattivata per l'assistente e indica il comando "
            "per attivarla."
        )
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


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
