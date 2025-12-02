"""Test CLI translations for all supported locales."""

import pytest

from openfatture.i18n import _, set_locale


class TestItalianCLI:
    """Test Italian CLI translations."""

    def setup_method(self):
        """Set locale to Italian."""
        set_locale("it")

    def test_fattura_create_title(self):
        """Test invoice creation title."""
        result = _("cli-fattura-create-title")
        assert "Crea" in result
        assert "Fattura" in result

    def test_fattura_client_selected(self):
        """Test client selection message with variable."""
        result = _("cli-fattura-client-selected", client_name="Test SRL")
        assert "Cliente" in result
        assert "Test SRL" in result

    def test_ai_forecast_pluralization_singular(self):
        """Test pluralization with singular."""
        result = _("cli-ai-forecast-results-title", months=1)
        assert "mese" in result.lower()
        assert "mesi" not in result.lower()

    def test_ai_forecast_pluralization_plural(self):
        """Test pluralization with plural."""
        result = _("cli-ai-forecast-results-title", months=3)
        assert "mesi" in result.lower()

    def test_main_title(self):
        """Test main CLI title."""
        result = _("cli-main-title")
        assert "OpenFatture" in result
        assert "Fatturazione" in result

    def test_cliente_list_title(self):
        """Test client list title with count."""
        result = _("cli-cliente-list-title", count=5)
        assert "Clienti" in result
        assert "5" in result


class TestEnglishCLI:
    """Test English CLI translations."""

    def setup_method(self):
        """Set locale to English."""
        set_locale("en")

    def test_fattura_create_title(self):
        """Test invoice creation title."""
        result = _("cli-fattura-create-title")
        assert "Create" in result
        assert "Invoice" in result

    def test_fattura_client_selected(self):
        """Test client selection message with variable."""
        result = _("cli-fattura-client-selected", client_name="Test Corp")
        assert "Client" in result
        assert "Test Corp" in result

    def test_ai_forecast_pluralization_singular(self):
        """Test pluralization with singular."""
        result = _("cli-ai-forecast-results-title", months=1)
        assert "month" in result.lower()
        assert "months" not in result.lower()

    def test_ai_forecast_pluralization_plural(self):
        """Test pluralization with plural."""
        result = _("cli-ai-forecast-results-title", months=3)
        assert "months" in result.lower()

    def test_main_title(self):
        """Test main CLI title."""
        result = _("cli-main-title")
        assert "OpenFatture" in result
        assert "Invoicing" in result

    def test_cliente_list_title(self):
        """Test client list title with count."""
        result = _("cli-cliente-list-title", count=5)
        assert "Clients" in result
        assert "5" in result


class TestCLIRichMarkup:
    """Test that Rich markup is preserved in CLI translations."""

    def test_italian_rich_markup(self):
        """Test Italian Rich markup preservation."""
        set_locale("it")
        result = _("cli-fattura-create-title")
        assert "[bold blue]" in result
        assert "[/bold blue]" in result

    def test_english_rich_markup(self):
        """Test English Rich markup preservation."""
        set_locale("en")
        result = _("cli-fattura-create-title")
        assert "[bold blue]" in result
        assert "[/bold blue]" in result


class TestCLIVariableInterpolation:
    """Test variable interpolation in CLI strings."""

    @pytest.mark.parametrize(
        "locale,msg_id,variables,expected_substrings",
        [
            (
                "it",
                "cli-fattura-invoice-header",
                {"numero": "001", "anno": "2024"},
                ["001", "2024"],
            ),
            (
                "en",
                "cli-fattura-invoice-header",
                {"numero": "001", "anno": "2024"},
                ["001", "2024"],
            ),
            ("it", "cli-cliente-has-invoices", {"count": 3}, ["3"]),
            ("en", "cli-cliente-has-invoices", {"count": 3}, ["3"]),
        ],
    )
    def test_variable_interpolation(self, locale, msg_id, variables, expected_substrings):
        """Test variable interpolation across locales."""
        set_locale(locale)
        result = _(msg_id, **variables)

        for substring in expected_substrings:
            assert substring in result


class TestCLIEmoji:
    """Test that emoji are preserved in CLI translations."""

    @pytest.mark.parametrize(
        "locale,msg_id,expected_emoji",
        [
            ("it", "cli-fattura-create-title", "🧾"),
            ("en", "cli-fattura-create-title", "🧾"),
            ("it", "cli-ai-voice-title", "🎤"),
            ("en", "cli-ai-voice-title", "🎤"),
            ("it", "cli-ai-vat-title", "🧮"),  # Italian uses abacus
            ("en", "cli-ai-vat-title", "🧾"),  # English uses receipt
        ],
    )
    def test_emoji_preservation(self, locale, msg_id, expected_emoji):
        """Test emoji preservation across locales."""
        set_locale(locale)
        result = _(msg_id)
        assert expected_emoji in result


class TestCLICommandGroups:
    """Test main CLI command group translations."""

    @pytest.mark.parametrize("locale", ["it", "en"])
    def test_all_command_groups_present(self, locale):
        """Test that all command groups are translated."""
        set_locale(locale)

        command_groups = [
            "cli-main-group-invoices",
            "cli-main-group-clients",
            "cli-main-group-products",
            "cli-main-group-pec",
            "cli-main-group-batch",
            "cli-main-group-ai",
            "cli-main-group-payments",
            "cli-main-group-preventivi",
            "cli-main-group-events",
            "cli-main-group-lightning",
            "cli-main-group-web",
        ]

        for group_id in command_groups:
            result = _(group_id)
            # Should not return the key itself (means translation not found)
            assert result != group_id, f"Missing translation for {group_id} in {locale}"
            # Should have some content
            assert len(result) > 0
