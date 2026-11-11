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
    """The product system prompt followed by the text protocol for tool calls.

    The product rules are the same as with native tool calling; this adds only
    the tags the parser reads and the tool catalogue, which such providers
    cannot receive as a schema.
    """
    from openfatture.ai.runtime.prompt import build_chat_system_prompt

    catalogue = []
    for tool in tools:
        line = f"- {tool.name}: {tool.description}"
        if tool.parameters:
            params = "; ".join(
                f"{p.name} ({p.type.value}{', obbligatorio' if p.required else ''}): "
                f"{p.description}"
                for p in tool.parameters
            )
            line += f"\n  Parametri: {params}"
        catalogue.append(line)

    protocol = f"""Formato delle risposte

Questo modello non riceve gli strumenti come schema: li chiami scrivendo dei tag, \
che OpenFatture legge ed esegue. Per chiamare uno strumento scrivi soltanto:

<thought>perché ti serve lo strumento</thought>
<action>nome_strumento</action>
<action_input>{{"parametro": "valore"}}</action_input>

action_input è un oggetto JSON valido con i parametri dello strumento. Il \
risultato ti torna in un messaggio che inizia con "Observation:"; puoi allora \
chiamare un altro strumento o rispondere. Quando hai la risposta per \
l'utente, scrivila dentro <final_answer>...</final_answer>. Le risposte sui \
dati dell'utente si basano sui risultati degli strumenti; saluti e domande \
generali non ne richiedono.

Strumenti
{chr(10).join(catalogue) if catalogue else "Nessuno strumento disponibile."}"""

    return build_chat_system_prompt(context) + "\n\n" + protocol
