"""Shared chat prompt builders for product backends (chat + langgraph).

Keeps system prompt and message assembly identical so backend parity tests
compare orchestration, not copy-paste drift.
"""

from __future__ import annotations

from openfatture.ai.domain.context import ChatContext
from openfatture.ai.domain.message import Message, Role
from openfatture.platform.logging import get_logger

logger = get_logger(__name__)


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
        "- Usa un tono professionale ma friendly",
        "- Rispondi in italiano (salvo richiesta diversa)",
        "- Se non hai informazioni sufficienti, chiedi chiarimenti",
        "- Prima di eseguire azioni distruttive, chiedi conferma",
        "- Cita i dati specifici quando disponibili (numeri, date, importi)",
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
                f"- Hai accesso a {len(context.available_tools)} tools",
                "- Usa i tools per recuperare dati o eseguire azioni",
                "- I tools includono: ricerca fatture, statistiche, info clienti",
            ]
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
