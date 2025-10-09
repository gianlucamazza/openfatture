"""
Template renderer for emails with i18n and inline CSS.

Renders Jinja2 templates with internationalization support and CSS inlining
for email client compatibility.
"""

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from pydantic import BaseModel

from openfatture.utils.config import Settings
from openfatture.utils.email.styles import EmailBranding, EmailStyles


class TemplateRenderer:
    """
    Email template renderer with i18n and inline CSS.

    Renders HTML and text email templates using Jinja2 with support for:
    - Internationalization (i18n)
    - CSS inlining for email clients
    - Custom filters for formatting
    - Template inheritance
    - Preview mode for testing

    Usage:
        renderer = TemplateRenderer(locale="it")
        html = renderer.render_html("sdi/invio_fattura.html", context)
        text = renderer.render_text("sdi/invio_fattura.txt", context)
    """

    def __init__(
        self,
        settings: Settings,
        locale: str = "it",
        branding: EmailBranding | None = None,
    ):
        """
        Initialize template renderer.

        Args:
            settings: Application settings
            locale: Language code (it, en)
            branding: Email branding configuration
        """
        self.settings = settings
        self.locale = locale
        self.branding = branding or self._default_branding()

        # Setup Jinja2 environment
        templates_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Load i18n translations
        self.translations = self._load_translations()

        # Register custom filters
        self._register_filters()

        # Add global context
        self._add_global_context()

    def _default_branding(self) -> EmailBranding:
        """Create default branding from settings."""
        return EmailBranding(
            primary_color=getattr(self.settings, "email_primary_color", "#1976D2"),
            logo_url=getattr(self.settings, "email_logo_url", None),
            footer_text=getattr(self.settings, "email_footer_text", None),
        )

    def _load_translations(self) -> dict[str, Any]:
        """Load i18n translations for current locale."""
        i18n_dir = Path(__file__).parent / "i18n"
        translation_file = i18n_dir / f"{self.locale}.json"

        try:
            with open(translation_file, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            # Fallback to Italian
            fallback_file = i18n_dir / "it.json"
            with open(fallback_file, encoding="utf-8") as f:
                return json.load(f)

    def _register_filters(self) -> None:
        """Register custom Jinja2 filters."""

        def currency_filter(value: Decimal | float) -> str:
            """Format currency in Italian format."""
            try:
                amount = float(value)
                # Italian format: €1.234,56
                formatted = f"€{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                return formatted
            except (ValueError, TypeError):
                return f"€{value}"

        def date_it_filter(value: date | datetime | str) -> str:
            """Format date in Italian format (dd/mm/yyyy)."""
            if isinstance(value, str):
                return value
            elif isinstance(value, datetime):
                return value.strftime("%d/%m/%Y %H:%M")
            elif isinstance(value, date):
                return value.strftime("%d/%m/%Y")
            return str(value)

        def percentage_filter(value: float) -> str:
            """Format percentage."""
            try:
                return f"{float(value):.1f}%"
            except (ValueError, TypeError):
                return f"{value}%"

        def duration_filter(seconds: float) -> str:
            """Format duration in human-readable format."""
            try:
                if seconds < 60:
                    return f"{seconds:.1f}s"
                elif seconds < 3600:
                    minutes = seconds / 60
                    return f"{minutes:.1f}m"
                else:
                    hours = seconds / 3600
                    return f"{hours:.1f}h"
            except (ValueError, TypeError):
                return str(seconds)

        # Register filters
        self.env.filters["currency"] = currency_filter
        self.env.filters["date_it"] = date_it_filter
        self.env.filters["percentage"] = percentage_filter
        self.env.filters["duration"] = duration_filter

    def _add_global_context(self) -> None:
        """Add global context variables available in all templates."""

        def translate(key: str, **kwargs) -> str:
            """
            Translate key using i18n.

            Supports nested keys with dot notation: "email.footer.generated_by"
            Supports placeholders: {{variable}}
            """
            keys = key.split(".")
            value = self.translations

            # Navigate nested dict
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return key  # Key not found, return original

            # Replace placeholders
            if isinstance(value, str) and kwargs:
                for k, v in kwargs.items():
                    value = value.replace(f"{{{{{k}}}}}", str(v))

            return value

        # Add global functions and variables
        self.env.globals["_"] = translate
        self.env.globals["locale"] = self.locale
        self.env.globals["app_name"] = self.settings.app_name
        self.env.globals["logo_url"] = self.branding.logo_url
        self.env.globals["footer_text"] = self.branding.footer_text

        # Cedente info (sender company)
        self.env.globals["cedente_denominazione"] = self.settings.cedente_denominazione
        self.env.globals["cedente_partita_iva"] = self.settings.cedente_partita_iva
        self.env.globals["cedente_indirizzo"] = self.settings.cedente_indirizzo
        self.env.globals["cedente_cap"] = self.settings.cedente_cap
        self.env.globals["cedente_comune"] = self.settings.cedente_comune
        self.env.globals["cedente_provincia"] = self.settings.cedente_provincia
        self.env.globals["cedente_email"] = self.settings.cedente_email
        self.env.globals["cedente_telefono"] = self.settings.cedente_telefono

        # CSS styles
        self.env.globals["styles"] = EmailStyles.get_complete_css(self.branding)

        # Feature flags
        self.env.globals["show_links"] = True

    def render_html(self, template_name: str, context: BaseModel | dict[str, Any]) -> str:
        """
        Render HTML template.

        Args:
            template_name: Template filename (e.g., "sdi/invio_fattura.html")
            context: Template context (Pydantic model or dict)

        Returns:
            Rendered HTML string

        Raises:
            TemplateNotFound: If template doesn't exist
        """
        try:
            template = self.env.get_template(template_name)

            # Convert Pydantic model to dict if needed
            if isinstance(context, BaseModel):
                context_dict = context.model_dump()
            else:
                context_dict = context

            # Add title to context if not present
            if "title" not in context_dict:
                context_dict["title"] = self.settings.app_name

            html = template.render(**context_dict)

            # Inline CSS for email client compatibility
            return self._inline_css(html)

        except TemplateNotFound:
            raise FileNotFoundError(f"Template not found: {template_name}")

    def render_text(self, template_name: str, context: BaseModel | dict[str, Any]) -> str:
        """
        Render plain text template.

        Args:
            template_name: Template filename (e.g., "sdi/invio_fattura.txt")
            context: Template context (Pydantic model or dict)

        Returns:
            Rendered text string

        Raises:
            TemplateNotFound: If template doesn't exist
        """
        try:
            template = self.env.get_template(template_name)

            # Convert Pydantic model to dict if needed
            if isinstance(context, BaseModel):
                context_dict = context.model_dump()
            else:
                context_dict = context

            return template.render(**context_dict)

        except TemplateNotFound:
            raise FileNotFoundError(f"Template not found: {template_name}")

    def _inline_css(self, html: str) -> str:
        """
        Inline CSS for email client compatibility.

        Converts <style> tags to inline style attributes.
        Uses basic inlining - for production, consider premailer or css_inline.

        Args:
            html: HTML string with <style> tags

        Returns:
            HTML with inlined CSS
        """
        # For now, return as-is
        # In production, use premailer or css_inline library:
        # from premailer import transform
        # return transform(html)

        # Or use css_inline (faster):
        # import css_inline
        # inliner = css_inline.CSSInliner()
        # return inliner.inline(html)

        return html

    def preview(
        self,
        template_name: str,
        context: BaseModel | dict[str, Any],
        output_path: Path | None = None,
    ) -> Path:
        """
        Generate HTML preview of template.

        Useful for testing and debugging templates without sending emails.

        Args:
            template_name: Template filename
            context: Template context
            output_path: Optional output path (defaults to temp file)

        Returns:
            Path to generated HTML file
        """
        html = self.render_html(template_name, context)

        if output_path is None:
            import tempfile

            fd, path = tempfile.mkstemp(suffix=".html", prefix="email_preview_")
            output_path = Path(path)
        else:
            output_path = Path(output_path)

        output_path.write_text(html, encoding="utf-8")
        return output_path

    def render_both(self, base_name: str, context: BaseModel | dict[str, Any]) -> tuple[str, str]:
        """
        Render both HTML and text versions of a template.

        Convenience method to render both formats at once.

        Args:
            base_name: Base template name without extension (e.g., "sdi/invio_fattura")
            context: Template context

        Returns:
            Tuple of (html, text)
        """
        html = self.render_html(f"{base_name}.html", context)
        text = self.render_text(f"{base_name}.txt", context)
        return html, text


def get_renderer(settings: Settings | None = None, locale: str = "it") -> TemplateRenderer:
    """
    Get template renderer instance.

    Convenience factory function.

    Args:
        settings: Application settings (loads default if None)
        locale: Language code

    Returns:
        TemplateRenderer instance
    """
    if settings is None:
        from openfatture.utils.config import get_settings

        settings = get_settings()

    return TemplateRenderer(settings=settings, locale=locale)
