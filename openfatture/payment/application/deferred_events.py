"""Publish observations only after the financial transaction commits."""

from collections.abc import Callable

from sqlalchemy import event
from sqlalchemy.orm import Session, SessionTransaction


def after_commit(session: Session, callback: Callable[[], None]) -> None:
    queue = session.info.setdefault("collection_after_commit", [])
    transaction = session.get_nested_transaction() or session.get_transaction()
    queue.append((transaction, callback))
    if session.info.get("collection_event_hooks"):
        return
    session.info["collection_event_hooks"] = True

    def committed(current: Session) -> None:
        if current.in_nested_transaction():
            return
        callbacks = list(current.info.pop("collection_after_commit", []))
        for _, deliver in callbacks:
            deliver()

    def rolled_back(current: Session, previous: SessionTransaction) -> None:
        def belongs_to_rollback(transaction: SessionTransaction | None) -> bool:
            while transaction is not None:
                if transaction is previous:
                    return True
                transaction = transaction.parent
            return False

        current.info["collection_after_commit"] = [
            (transaction, deliver)
            for transaction, deliver in current.info.get("collection_after_commit", [])
            if not belongs_to_rollback(transaction)
        ]

    def ended(current: Session, transaction: SessionTransaction) -> None:
        if transaction.parent is None:
            current.info.pop("collection_after_commit", None)

    event.listen(session, "after_commit", committed)
    event.listen(session, "after_soft_rollback", rolled_back)
    event.listen(session, "after_transaction_end", ended)
