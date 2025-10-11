"""Test-only listeners for payment event bus."""

from openfatture.payment.application.events import PaymentEvent

captured_events: list[PaymentEvent] = []


def custom_listener(event: PaymentEvent) -> None:
    captured_events.append(event)
