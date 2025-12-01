"""Fixtures for menu testing."""

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_questionary_select():
    """Mock questionary.select for menu tests.

    Returns a mock that can be configured to return specific menu choices.

    Usage:
        def test_something(mock_questionary_select):
            mock_questionary_select.return_value.ask.return_value = "action_setup"
            result = show_main_menu()
            assert result == "action_setup"
    """
    with patch("openfatture.cli.ui.menus.questionary.select") as mock:
        yield mock


@pytest.fixture
def mock_all_action_handlers():
    """Mock all action_* functions to prevent actual execution during tests.

    This fixture patches all action handler functions in the menus module
    to prevent them from actually executing commands during tests.

    Returns a dictionary of mocked functions for assertion purposes.
    """
    action_handlers = [
        # Setup actions
        "action_init_openfatture",
        "action_show_config",
        "action_edit_config",
        "action_test_pec",
        # Client actions
        "action_create_cliente",
        "action_list_clienti",
        "action_search_cliente",
        "action_edit_cliente",
        "action_delete_cliente",
        # Invoice actions
        "action_create_fattura",
        "action_list_fatture",
        "action_search_fattura",
        "action_show_fattura",
        "action_genera_xml",
        "action_invia_sdi",
        "action_delete_fattura",
        # Notification actions
        "action_process_notifica",
        "action_list_notifiche",
        "action_show_notifica",
        # Email actions
        "action_test_email",
        "action_preview_template",
        "action_email_info",
        # Batch actions
        "action_batch_send",
        "action_batch_import",
        "action_batch_export",
        "action_batch_delete",
        "action_batch_history",
        # Report actions
        "action_show_dashboard",
        "action_report_mensile",
        "action_report_annuale",
        "action_report_cliente",
        "action_export_excel",
        # AI actions
        "action_ai_chat",
        "action_ai_suggestions",
    ]

    mocks = {}
    patches = []

    for handler in action_handlers:
        patcher = patch(f"openfatture.cli.ui.menus.{handler}")
        mock = patcher.start()
        mocks[handler] = mock
        patches.append(patcher)

    yield mocks

    for patcher in patches:
        patcher.stop()


@pytest.fixture
def mock_submenu_handlers():
    """Mock all handle_*_menu submenu functions.

    This is useful for testing main menu routing without actually
    entering submenus.
    """
    submenu_handlers = [
        "handle_setup_menu",
        "handle_clienti_menu",
        "handle_fatture_menu",
        "handle_notifiche_menu",
        "handle_email_menu",
        "handle_batch_menu",
        "handle_report_menu",
        "handle_ai_menu",
    ]

    mocks = {}
    patches = []

    for handler in submenu_handlers:
        patcher = patch(f"openfatture.cli.ui.menus.{handler}")
        mock = patcher.start()
        mocks[handler] = mock
        patches.append(patcher)

    yield mocks

    for patcher in patches:
        patcher.stop()
