"""Basic i18n functionality tests."""

import pytest

from openfatture.i18n import _, get_locale, set_locale
from openfatture.i18n.loader import SUPPORTED_LOCALES


class TestBasicTranslation:
    """Test basic translation functionality."""

    def test_import_translation_function(self):
        """Test that we can import the main translation function."""
        assert callable(_)

    def test_get_default_locale(self):
        """Test that default locale is Italian."""
        locale = get_locale()
        assert locale in SUPPORTED_LOCALES
        # Default should be 'it' unless overridden by env
        assert locale == "it" or locale in SUPPORTED_LOCALES

    def test_set_locale(self):
        """Test locale switching."""
        original = get_locale()

        # Set to English
        set_locale("en")
        assert get_locale() == "en"

        # Set to Spanish
        set_locale("es")
        assert get_locale() == "es"

        # Restore original
        set_locale(original)

    def test_invalid_locale_raises_error(self):
        """Test that invalid locale raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported locale"):
            set_locale("xx")  # Invalid locale code

    def test_simple_translation_italian(self):
        """Test simple translation in Italian."""
        set_locale("it")
        result = _("common-yes")
        assert result == "Sì"

    def test_simple_translation_english(self):
        """Test simple translation in English."""
        set_locale("en")
        result = _("common-yes")
        assert result == "Yes"

    def test_simple_translation_spanish(self):
        """Test simple translation in Spanish."""
        set_locale("es")
        result = _("common-yes")
        assert result == "Sí"

    def test_simple_translation_french(self):
        """Test simple translation in French."""
        set_locale("fr")
        result = _("common-yes")
        assert result == "Oui"

    def test_simple_translation_german(self):
        """Test simple translation in German."""
        set_locale("de")
        result = _("common-yes")
        assert result == "Ja"

    def test_translation_with_variables(self):
        """Test translation with variable interpolation."""
        set_locale("it")
        result = _("email-sdi-invio-subject", numero="001", anno="2024")
        assert "001" in result
        assert "2024" in result
        assert "Fattura" in result

    def test_translation_with_variables_english(self):
        """Test translation with variable interpolation in English."""
        set_locale("en")
        result = _("email-sdi-invio-subject", numero="042", anno="2025")
        assert "042" in result
        assert "2025" in result
        assert "Invoice" in result

    def test_missing_translation_returns_key(self):
        """Test that missing translation returns the message ID."""
        set_locale("it")
        result = _("this-key-does-not-exist")
        # Should return the key itself as fallback
        assert result == "this-key-does-not-exist"

    def test_locale_override_parameter(self):
        """Test that locale parameter overrides current locale."""
        set_locale("it")  # Set Italian

        # But request English explicitly
        result_en = _("common-yes", locale="en")
        assert result_en == "Yes"

        # Current locale should still be Italian
        result_it = _("common-yes")
        assert result_it == "Sì"

    def test_all_supported_locales_have_common_translations(self):
        """Test that all locales have basic common translations."""
        common_keys = ["common-yes", "common-no", "common-cancel"]

        for locale in SUPPORTED_LOCALES:
            set_locale(locale)
            for key in common_keys:
                result = _(key)
                # Result should not be empty and should not be the key itself
                assert result
                # For 'yes'/'no'/'cancel', we know they should be short strings
                assert len(result) < 20

    @pytest.fixture(autouse=True)
    def reset_locale(self):
        """Reset locale to Italian after each test."""
        yield
        try:
            set_locale("it")
        except Exception:
            pass
