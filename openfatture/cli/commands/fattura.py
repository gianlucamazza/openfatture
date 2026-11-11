"""Invoice commands without an assistant equivalent: XML file and SDI journal.

Searching, creating and editing invoices, and their PDFs, go through the assistant.
"""

import typer
from rich.console import Console

from openfatture.cli.output import remember_result
from openfatture.i18n import _

app = typer.Typer(name="fattura", help="FatturaPA XML and SDI journal")
console = Console()


@app.callback()
def prepare_database() -> None:
    from openfatture.cli.database import ensure_database

    ensure_database()


@app.command("generate-xml")
def generate_xml(
    fattura_id: int = typer.Argument(..., help="Invoice ID"),
    output: str = typer.Option(None, "--output", "-o", help="Output XML file path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show XML without writing file"),
) -> None:
    """Generate FatturaPA XML for an invoice."""
    from openfatture.sdi.application.invoice_sdi_ops import generate_invoice_xml

    result = generate_invoice_xml(fattura_id, output_path=output, dry_run=dry_run)
    remember_result(result)
    if "error" in result:
        console.print(_("cli-common-error", error=result["error"]))
        raise typer.Exit(code=1)

    if dry_run:
        console.print(_("cli-fattura-xml-generated-dry-run"))
        console.print("\n" + _("cli-fattura-xml-content"))
        console.print(result["xml_content"])
        return
    console.print(_("cli-fattura-xml-generated"))
    console.print(_("cli-fattura-output", path=str(result["xml_path"])))
    console.print(_("cli-fattura-size", size=result["file_size"]))


@app.command("sdi-journal")
def sdi_journal() -> None:
    """Inspect recorded submissions and imported receipts without sending anything."""
    from openfatture.sdi.application.journal_ops import list_sdi_journal

    journal = list_sdi_journal()
    remember_result(journal)
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


@app.command("associate-receipt")
def associate_receipt(
    receipt_id: int, invoice_id: int, evidence: str = typer.Option(..., "--evidence")
) -> None:
    """Associate an unresolved receipt after explicit human verification."""
    from openfatture.sdi.application import journal_ops

    if not typer.confirm(
        _("cli-fattura-associate-confirm", receipt=str(receipt_id), invoice=str(invoice_id)),
        default=False,
    ):
        raise typer.Abort()
    result = journal_ops.associate_receipt(receipt_id, invoice_id, evidence)
    remember_result(result)
    if "error" in result:
        console.print(result["error"], markup=False)
        raise typer.Exit(1)
    console.print(_("cli-fattura-receipt-associated"))


@app.command("resolve-submission")
def resolve_submission_command(
    attempt_id: int,
    sent: bool = typer.Option(..., "--sent/--not-sent"),
    evidence: str = typer.Option(..., "--evidence"),
) -> None:
    """Resolve an uncertain PEC attempt only after checking transport evidence."""
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
        console.print(result["error"], markup=False)
        raise typer.Exit(1)
    console.print(_("cli-fattura-submission-resolved"))
