"""ReAct (Reasoning + Acting) prompt for providers without native tool calling.

The assistant graph (``openfatture.ai.runtime.graph``) runs the tool loop for
every provider. For providers that cannot call tools natively it seeds the
conversation with :func:`build_react_messages`, parses each reply with
``orchestration.parsers.ToolCallParser`` and sends tool results back as
``Observation:`` messages.

Reference: https://arxiv.org/abs/2210.03629
"""

from openfatture.ai.domain.context import ChatContext
from openfatture.ai.domain.message import Message, Role
from openfatture.ai.tools.models import Tool


def build_react_messages(context: ChatContext, tools: list[Tool]) -> list[Message]:
    """System prompt with the ReAct instructions, then the history and the user input."""
    messages = [Message(role=Role.SYSTEM, content=build_react_system_prompt(context, tools))]
    messages.extend(context.conversation_history.get_messages(include_system=False))

    # Add current user input if not already in history
    if messages[-1].role != Role.USER:
        messages.append(Message(role=Role.USER, content=context.user_input))

    return messages


def build_react_system_prompt(context: ChatContext, tools: list[Tool]) -> str:
    """ReAct instructions with XML tags, few-shot examples and the tool catalogue."""
    tool_descriptions = []
    for tool in tools:
        if tool.parameters:
            params_desc = ", ".join(
                f"{param.name}: {param.description}" for param in tool.parameters
            )
            tool_descriptions.append(
                f"- {tool.name}: {tool.description}\n  Parametri: {params_desc}"
            )
        else:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

    tools_section = "\n".join(tool_descriptions) if tool_descriptions else "Nessun tool disponibile"

    prompt = f"""Sei un assistente AI per OpenFatture, sistema di fatturazione elettronica italiana.

CRITICAL: Devi SEMPRE usare i tools disponibili per ottenere dati reali. NON INVENTARE MAI dati.

USA QUESTO FORMATO ESATTO con tag XML:

<thought>Il tuo ragionamento qui</thought>
<action>nome_tool</action>
<action_input>{{"parametro": "valore"}}</action_input>

OPPURE quando hai la risposta completa:

<final_answer>La tua risposta formattata per l'utente</final_answer>

TOOLS DISPONIBILI:
{tools_section}

═══════════════════════════════════════════════════════════════
ESEMPI COMPLETI:
═══════════════════════════════════════════════════════════════

ESEMPIO 1: Statistiche fatture
User: Quante fatture ho emesso quest'anno?

<thought>Devo ottenere le statistiche delle fatture per l'anno corrente 2025 usando il tool get_invoice_stats</thought>
<action>get_invoice_stats</action>
<action_input>{{"year": 2025}}</action_input>

Observation: {{"totale_fatture": 42, "importo_totale": 15000.0, "per_stato": {{"bozza": 5, "da_inviare": 10, "inviata": 27}}}}

<thought>Ho ricevuto i dati reali dal sistema. Ora posso fornire una risposta completa e formattata</thought>
<final_answer>Hai emesso **42 fatture** nel 2025 per un totale di **€15.000,00**.

Distribuzione per stato:
- Bozze: 5
- Da inviare: 10
- Inviate: 27</final_answer>

═══════════════════════════════════════════════════════════════

ESEMPIO 2: Ricerca fatture
User: Mostrami le ultime 3 fatture

<thought>Devo cercare le fatture più recenti usando search_invoices con limit=3</thought>
<action>search_invoices</action>
<action_input>{{"limit": 3}}</action_input>

Observation: [{{"numero": "003/2025", "cliente": "Acme Corp", "totale": 1200.0, "data": "2025-01-20"}}, {{"numero": "002/2025", "cliente": "Beta Ltd", "totale": 850.0, "data": "2025-01-15"}}, {{"numero": "001/2025", "cliente": "Gamma SpA", "totale": 2100.0, "data": "2025-01-10"}}]

<thought>Ho ricevuto la lista delle fatture. Le presento in una tabella chiara</thought>
<final_answer>Ecco le ultime 3 fatture:

| N. Fattura | Data       | Cliente    | Importo    |
|------------|------------|------------|------------|
| 003/2025   | 20/01/2025 | Acme Corp  | €1.200,00  |
| 002/2025   | 15/01/2025 | Beta Ltd   | €850,00    |
| 001/2025   | 10/01/2025 | Gamma SpA  | €2.100,00  |</final_answer>

═══════════════════════════════════════════════════════════════

REGOLE CRITICHE:
USA SEMPRE i tools - non inventare dati
Segui ESATTAMENTE il formato XML
JSON valido in <action_input>
Rispondi in italiano
Formatta con tabelle/liste quando appropriato

NON inventare numeri fattura
NON inventare nomi clienti
NON inventare importi
NON rispondere senza usare tools quando sono disponibili

Ora rispondi alla domanda dell'utente seguendo gli esempi sopra."""

    # Add business context if available
    if context.current_year_stats:
        stats = context.current_year_stats
        prompt += "\n\nCONTESTO SISTEMA:\n"
        prompt += f"- Anno corrente: {stats.get('anno', 'N/A')}\n"
        prompt += f"- Fatture totali YTD: {stats.get('totale_fatture', 0)}\n"
        prompt += f"- Importo totale YTD: €{stats.get('importo_totale', 0):.2f}\n"

    return prompt
