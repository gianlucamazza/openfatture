"""Unit tests for billing application query services (no AI layer)."""

from unittest.mock import MagicMock, patch

from openfatture.billing.application import client_queries, invoice_queries


@patch("openfatture.billing.application.invoice_queries.get_session")
def test_search_invoices_empty(mock_session: MagicMock) -> None:
    session = MagicMock()
    mock_session.return_value = session
    q = MagicMock()
    session.query.return_value = q
    q.options.return_value = q
    q.filter.return_value = q
    q.order_by.return_value = q
    q.limit.return_value = q
    q.all.return_value = []
    result = invoice_queries.search_invoices()
    assert result["count"] == 0
    assert result["fatture"] == []


@patch("openfatture.billing.application.client_queries.get_session")
def test_get_client_stats(mock_session: MagicMock) -> None:
    session = MagicMock()
    mock_session.return_value = session
    session.query.return_value.count.return_value = 3
    session.query.return_value.filter.return_value.count.return_value = 1
    result = client_queries.get_client_stats()
    assert "totale_clienti" in result
