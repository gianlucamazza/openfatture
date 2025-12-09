"""PEC testing and configuration commands."""

import typer
from rich.console import Console

from openfatture.i18n import _
from openfatture.utils.config import get_settings
from openfatture.utils.email.sender import TemplatePECSender

PECSender = TemplatePECSender

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("test")
def test_pec() -> None:
    """
    Test PEC configuration with professional email template.

    This verifies that:
    - PEC credentials are correct
    - SMTP server is reachable
    - Email templates render correctly
    - You can send emails via PEC

    Note: This uses the new TemplatePECSender with HTML + text templates.
    """
    console.print(f"\n{_('cli-pec-test-title')}\n")

    settings = get_settings()

    # Check configuration
    if not settings.pec_address:
        console.print(_("cli-pec-error-no-address"))
        console.print(_("cli-pec-error-no-address-hint"))
        raise typer.Exit(1)

    if not settings.pec_password:
        console.print(_("cli-pec-error-no-password"))
        console.print(_("cli-pec-error-no-password-hint"))
        raise typer.Exit(1)

    console.print(f"{_('cli-pec-label-address')} {settings.pec_address}")
    console.print(
        f"{_('cli-pec-label-smtp-server')} {settings.pec_smtp_server}:{settings.pec_smtp_port}"
    )
    console.print(_("cli-pec-label-template"))
    console.print(f"{_('cli-pec-label-locale')} {settings.locale}\n")

    console.print(_("cli-pec-sending-test"))

    sender = PECSender(settings=settings, locale=settings.locale)
    success, error = sender.send_test_email()

    if success:
        console.print(f"\n{_('cli-pec-test-success')}")
        console.print(_("cli-pec-test-check-inbox", pec_address=settings.pec_address))
        console.print(f"\n{_('cli-pec-test-email-includes')}")
        console.print(_("cli-pec-test-feature-html"))
        console.print(_("cli-pec-test-feature-branding"))
        console.print(_("cli-pec-test-feature-language", language=settings.locale.upper()))
        console.print(f"\n{_('cli-pec-test-more-testing')}")
        console.print(_("cli-pec-test-cmd-email-test"))
        console.print(_("cli-pec-test-cmd-email-preview"))
    else:
        console.print(_("cli-pec-test-failed", error=error))
        console.print(f"\n{_('cli-pec-test-common-issues')}")
        console.print(_("cli-pec-issue-credentials"))
        console.print(_("cli-pec-issue-smtp"))
        console.print(_("cli-pec-issue-firewall"))
        console.print(_("cli-pec-issue-mailbox"))
        raise typer.Exit(1)


@app.command("info")
def pec_info() -> None:
    """Show PEC configuration."""
    console.print(f"\n{_('cli-pec-info-title')}\n")

    settings = get_settings()

    from rich.table import Table

    table = Table(show_header=False)
    table.add_column(_("cli-pec-table-setting"), style="cyan", width=20)
    table.add_column(_("cli-pec-table-value"), style="white")

    table.add_row(_("cli-pec-label-address"), settings.pec_address or _("cli-pec-not-set"))
    table.add_row(
        _("cli-pec-label-password"),
        _("cli-pec-password-set") if settings.pec_password else _("cli-pec-not-set"),
    )
    table.add_row(_("cli-pec-label-smtp-server"), settings.pec_smtp_server)
    table.add_row(_("cli-pec-label-smtp-port"), str(settings.pec_smtp_port))
    table.add_row(_("cli-pec-label-sdi-pec"), settings.sdi_pec_address)

    console.print(table)
    console.print()
