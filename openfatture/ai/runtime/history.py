"""Which part of a stored conversation the model receives on each turn.

The stored transcript keeps every message (up to the session cap); the model
gets the most recent ones that fit a token budget, starting at a user message,
so a long chat neither overflows the context window nor slows every turn.
Counting is approximate (about four characters per token), which is enough to
keep the input bounded.
"""

from __future__ import annotations

from collections.abc import Sequence

from openfatture.ai.domain.message import Message, Role

HISTORY_TOKEN_BUDGET = 12_000
OMITTED_NOTE = "[Messaggi precedenti di questa conversazione omessi per lunghezza.]"


def approximate_tokens(message: Message) -> int:
    """Rough token count of one message (content plus a small framing cost)."""
    return len(message.content or "") // 4 + 4


def trim_history(messages: Sequence[Message], budget: int = HISTORY_TOKEN_BUDGET) -> list[Message]:
    """The newest messages within ``budget`` tokens, beginning with a user message.

    When older messages are left out, the first kept user message says so, so
    the model knows the conversation started earlier. The latest exchange is
    always kept, even when it alone exceeds the budget.
    """
    users = [index for index, message in enumerate(messages) if message.role == Role.USER]
    if not users:
        return []
    # The latest exchange starts at the last user message and is always kept.
    start = users[-1]
    used = sum(approximate_tokens(m) for m in messages[start:])
    for index in reversed(users[:-1]):
        cost = sum(approximate_tokens(m) for m in messages[index:start])
        if used + cost > budget:
            break
        start, used = index, used + cost
    kept = list(messages[start:])
    if len(kept) < len(messages) and kept:
        first = kept[0]
        kept[0] = Message(role=first.role, content=f"{OMITTED_NOTE}\n\n{first.content}")
    return kept
