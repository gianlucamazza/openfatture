#!/usr/bin/env python3
"""
Internationalization (i18n) Demo for OpenFatture

This script demonstrates the multi-language capabilities of the new i18n system.
"""

from datetime import date
from decimal import Decimal

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from openfatture.i18n import _, get_locale, set_locale
from openfatture.i18n.context import locale_context
from openfatture.i18n.formatters import (
    format_date_localized,
    format_euro,
    format_number,
    format_percentage,
)

console = Console()


def demo_basic_translations():
    """Demonstrate basic translations across languages."""
    console.print("\n[bold cyan]1. Basic Translations[/bold cyan]\n")

    languages = ["it", "en", "es", "fr", "de"]
    keys = ["common-yes", "common-no", "common-cancel", "common-invoice", "common-client"]

    table = Table(title="Common UI Strings")
    table.add_column("Message ID", style="cyan")
    for lang in languages:
        table.add_column(lang.upper(), style="yellow" if lang == "it" else "white")

    for key in keys:
        row = [key]
        for lang in languages:
            set_locale(lang)
            row.append(_(key))
        table.add_row(*row)

    console.print(table)


def demo_variable_interpolation():
    """Demonstrate variable interpolation in translations."""
    console.print("\n[bold cyan]2. Variable Interpolation[/bold cyan]\n")

    languages = ["it", "en"]

    for lang in languages:
        set_locale(lang)
        msg = _("email-sdi-invio-subject", numero="042", anno="2024")
        console.print(f"[{lang.upper()}] {msg}")


def demo_locale_context():
    """Demonstrate temporary locale switching with context managers."""
    console.print("\n[bold cyan]3. Locale Context Manager[/bold cyan]\n")

    set_locale("it")  # Default Italian

    console.print(f"Default: {_('common-yes')}")

    with locale_context("en"):
        console.print(f"In English context: {_('common-yes')}")

    with locale_context("fr"):
        console.print(f"In French context: {_('common-yes')}")

    console.print(f"Back to default: {_('common-yes')}")


def demo_formatters():
    """Demonstrate custom formatters for currency, dates, numbers."""
    console.print("\n[bold cyan]4. Custom Formatters (Locale-Aware)[/bold cyan]\n")

    languages = ["it", "en", "de"]

    # Currency
    amount = Decimal("1234.56")
    console.print("[bold]Currency Formatting:[/bold]")
    for lang in languages:
        formatted = format_euro(amount, locale=lang)
        console.print(f"  [{lang.upper()}] {formatted}")

    # Numbers
    big_number = Decimal("1234567.89")
    console.print("\n[bold]Number Formatting:[/bold]")
    for lang in languages:
        formatted = format_number(big_number, locale=lang)
        console.print(f"  [{lang.upper()}] {formatted}")

    # Percentages
    rate = Decimal("0.22")  # 22%
    console.print("\n[bold]Percentage Formatting:[/bold]")
    for lang in languages:
        formatted = format_percentage(rate, locale=lang)
        console.print(f"  [{lang.upper()}] {formatted}")

    # Dates
    invoice_date = date(2024, 3, 15)
    console.print("\n[bold]Date Formatting (medium):[/bold]")
    for lang in languages:
        formatted = format_date_localized(invoice_date, format_str="medium", locale=lang)
        console.print(f"  [{lang.upper()}] {formatted}")


def demo_pluralization():
    """Demonstrate Fluent pluralization."""
    console.print("\n[bold cyan]5. Pluralization Support[/bold cyan]\n")

    set_locale("en")

    for count in [1, 5, 10]:
        msg = _("email-sdi-scarto-error-count", count=count)
        console.print(f"Count={count}: {msg}")


def demo_email_translations():
    """Demonstrate email template translations."""
    console.print("\n[bold cyan]6. Email Template Translations[/bold cyan]\n")

    email_keys = [
        "email-footer-generated-by",
        "email-sdi-consegna-title",
        "email-sdi-scarto-title",
        "email-batch-summary-title",
    ]

    table = Table(title="Email Template Strings")
    table.add_column("Message ID", style="cyan")
    table.add_column("Italian", style="yellow")
    table.add_column("English", style="white")

    for key in email_keys:
        set_locale("it")
        italian = _(key)
        set_locale("en")
        english = _(key)
        table.add_row(key, italian, english)

    console.print(table)


def main():
    """Run all i18n demos."""
    console.print(
        Panel.fit(
            "[bold green]OpenFatture i18n System Demo[/bold green]\n\n"
            "Demonstrating Mozilla Fluent-powered multi-language support\n"
            f"Current locale: [yellow]{get_locale().upper()}[/yellow]",
            border_style="green",
        )
    )

    demo_basic_translations()
    demo_variable_interpolation()
    demo_locale_context()
    demo_formatters()
    demo_pluralization()
    demo_email_translations()

    console.print("\n[bold green]✅ Demo complete![/bold green]")
    console.print("\n[dim]All features demonstrated successfully.[/dim]")


if __name__ == "__main__":
    main()
