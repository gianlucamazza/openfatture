"""SDI journal and the resolutions that need a person's evidence.

Everything else about invoices (search, editing, PDF, FatturaPA XML, sending)
goes through the assistant. These commands stay out of it on purpose: the
evidence that a PEC was or was not sent must be typed by a person, never
supplied by the model.
"""

import typer
from rich.console import Console
from rich.markup import escape

from openfatture.cli.database import ensure_database
from openfatture.cli.output import error_message, remember_result
from openfatture.i18n import _

app = typer.Typer(name="fattura")
console = Console()


@app.command("sdi-journal", help=_("cli-help-sdi-journal"))
def sdi_journal() -> None:
    """List PEC submissions and SDI receipts."""
    ensure_database()
    from openfatture.sdi.application.journal_ops import list_sdi_journal

    journal = list_sdi_journal()
    remember_result(journal)
    if not journal["submissions"] and not journal["receipts"]:
        console.print(_("cli-fattura-journal-empty"))
    for attempt in journal["submissions"]:
        console.print(
            _(
                "cli-fattura-journal-submission",
                id=str(attempt["id"]),
                invoice=str(attempt["invoice_id"]),
                filename=attempt["filename"],
                outcome=attempt["outcome"],
            ),
            markup=False,
        )
    for receipt in journal["receipts"]:
        console.print(
            _(
                "cli-fattura-journal-receipt",
                id=str(receipt["id"]),
                invoice=str(receipt["invoice_id"]),
                outcome=receipt["outcome"],
                source=receipt["source"],
            ),
            markup=False,
        )


@app.command("associate-receipt", help=_("cli-help-associate-receipt"))
def associate_receipt(
    receipt_id: int = typer.Argument(..., help=_("cli-help-receipt-id")),
    invoice_id: int = typer.Argument(..., help=_("cli-help-invoice-id")),
    evidence: str = typer.Option(..., "--evidence", help=_("cli-help-receipt-evidence")),
) -> None:
    """Associate a receipt after human verification."""
    ensure_database()
    from openfatture.sdi.application import journal_ops

    if not typer.confirm(
        _("cli-fattura-associate-confirm", receipt=str(receipt_id), invoice=str(invoice_id)),
        default=False,
    ):
        raise typer.Abort()
    result = journal_ops.associate_receipt(receipt_id, invoice_id, evidence)
    remember_result(result)
    if "error" in result:
        console.print(_("cli-common-error", error=escape(error_message(result))))
        raise typer.Exit(1)
    console.print(_("cli-fattura-receipt-associated"))


@app.command("resolve-submission", help=_("cli-help-resolve-submission"))
def resolve_submission_command(
    attempt_id: int = typer.Argument(..., help=_("cli-help-attempt-id")),
    sent: bool = typer.Option(..., "--sent/--not-sent", help=_("cli-help-resolve-sent")),
    evidence: str = typer.Option(..., "--evidence", help=_("cli-help-resolve-evidence")),
) -> None:
    """Resolve an uncertain PEC submission."""
    ensure_database()
    from openfatture.sdi.application.journal_ops import resolve_submission_attempt

    if not typer.confirm(
        _(
            "cli-fattura-resolve-confirm",
            attempt=str(attempt_id),
            sent="yes" if sent else "no",
        ),
        default=False,
    ):
        raise typer.Abort()
    result = resolve_submission_attempt(attempt_id, sent=sent, evidence=evidence)
    remember_result(result)
    if "error" in result:
        console.print(_("cli-common-error", error=escape(error_message(result))))
        raise typer.Exit(1)
    console.print(_("cli-fattura-submission-resolved"))
