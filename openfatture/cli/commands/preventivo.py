"""Preventivo (quote/estimate) management commands."""

from datetime import date, timedelta
from decimal import Decimal

import typer
from rich.console import Console
from rich.prompt import Confirm, FloatPrompt, IntPrompt, Prompt
from rich.table import Table

from openfatture.core.preventivi.service import PreventivoService
from openfatture.i18n import _
from openfatture.storage.database.base import init_db
from openfatture.storage.database.models import Cliente, StatoPreventivo, TipoDocumento
from openfatture.storage.session import db_session
from openfatture.utils.config import get_settings

app = typer.Typer(no_args_is_help=True)
console = Console()


def ensure_db() -> None:
    """Ensure database is initialized."""
    settings = get_settings()
    init_db(str(settings.database_url))


@app.command("crea")
def crea_preventivo(
    cliente_id: int | None = typer.Option(None, "--cliente", help=_("cli-preventivo-cliente-help")),
    validita_giorni: int = typer.Option(30, "--validita", help=_("cli-preventivo-validita-help")),
) -> None:
    """
    Create a new preventivo (quote/estimate).
    """
    ensure_db()

    console.print(f"\n{_('cli-preventivo-create-title')}\n")

    with db_session() as db:
        # Select client
        if not cliente_id:
            clienti = db.query(Cliente).order_by(Cliente.denominazione).all()

            if not clienti:
                console.print(_("cli-preventivo-no-clients"))
                raise typer.Exit(1)

            console.print(_("cli-preventivo-available-clients"))
            for i, c in enumerate(clienti[:10], 1):
                console.print(f"  {c.id}. {c.denominazione} ({c.partita_iva or 'N/A'})")

            cliente_id = IntPrompt.ask(_("cli-preventivo-client-id-prompt"), default=clienti[0].id)

        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cliente:
            console.print(_("cli-preventivo-client-not-found", id=cliente_id))
            raise typer.Exit(1)

        # At this point cliente_id is guaranteed to be int (not None)
        assert cliente_id is not None  # Type narrowing for mypy

        console.print(_("cli-preventivo-client-selected", name=cliente.denominazione))

        # Preventivo details
        data_emissione = date.today()
        data_scadenza = data_emissione + timedelta(days=validita_giorni)

        console.print(
            _("cli-preventivo-validity-info", days=validita_giorni, date=data_scadenza.isoformat())
        )

        # Add line items
        console.print(_("cli-preventivo-add-items-title"))
        console.print(_("cli-preventivo-add-items-hint"))

        righe = []
        riga_num = 1
        totale_imponibile = Decimal("0")
        totale_iva = Decimal("0")

        while True:
            descrizione = Prompt.ask(
                _("cli-preventivo-item-description-prompt", num=riga_num), default=""
            )
            if not descrizione:
                break

            quantita = FloatPrompt.ask(_("cli-preventivo-item-quantity-prompt"), default=1.0)
            prezzo = FloatPrompt.ask(_("cli-preventivo-item-price-prompt"), default=100.0)
            aliquota_iva = FloatPrompt.ask(_("cli-preventivo-item-vat-prompt"), default=22.0)
            unita_misura = Prompt.ask(_("cli-preventivo-item-unit-prompt"), default="ore")

            # Calculate
            imponibile = Decimal(str(quantita)) * Decimal(str(prezzo))
            iva = imponibile * Decimal(str(aliquota_iva)) / Decimal("100")
            totale = imponibile + iva

            righe.append(
                {
                    "descrizione": descrizione,
                    "quantita": quantita,
                    "prezzo_unitario": prezzo,
                    "aliquota_iva": aliquota_iva,
                    "unita_misura": unita_misura,
                }
            )

            totale_imponibile += imponibile
            totale_iva += iva

            console.print(
                _("cli-preventivo-item-added", description=descrizione[:40], total=f"{totale:.2f}")
            )
            riga_num += 1

        if not righe:
            console.print(_("cli-preventivo-no-items"))
            return

        # Optional: notes and conditions
        note = None
        condizioni = None

        if Confirm.ask(_("cli-preventivo-add-notes-prompt"), default=False):
            note = Prompt.ask(_("cli-preventivo-notes-input"))

        if Confirm.ask(_("cli-preventivo-add-conditions-prompt"), default=False):
            condizioni = Prompt.ask(_("cli-preventivo-conditions-input"))

        # Create preventivo using service
        settings = get_settings()
        service = PreventivoService(settings)

        preventivo, error = service.create_preventivo(
            db=db,
            cliente_id=cliente_id,
            righe=righe,
            validita_giorni=validita_giorni,
            note=note,
            condizioni=condizioni,
        )

        if error or not preventivo:
            console.print(
                _("cli-preventivo-error", error=error or _("cli-preventivo-unknown-error"))
            )
            raise typer.Exit(1)

        # Summary
        console.print(_("cli-preventivo-created-success"))

        table = Table(
            title=_("cli-preventivo-table-title", numero=preventivo.numero, anno=preventivo.anno)
        )
        table.add_column(_("cli-preventivo-field-column"), style="cyan", width=20)
        table.add_column(_("cli-preventivo-value-column"), style="white", justify="right")

        table.add_row(_("cli-preventivo-field-client"), cliente.denominazione)
        table.add_row(_("cli-preventivo-field-issue-date"), preventivo.data_emissione.isoformat())
        table.add_row(
            _("cli-preventivo-field-expiration-date"), preventivo.data_scadenza.isoformat()
        )
        table.add_row(_("cli-preventivo-field-line-items"), str(len(preventivo.righe)))
        table.add_row(_("cli-preventivo-field-imponibile"), f"€{preventivo.imponibile:.2f}")
        table.add_row(_("cli-preventivo-field-iva"), f"€{preventivo.iva:.2f}")
        table.add_row(_("cli-preventivo-field-totale"), f"[bold]€{preventivo.totale:.2f}[/bold]")

        console.print(table)

        console.print(_("cli-preventivo-next-convert", id=preventivo.id))


@app.command("lista")
def list_preventivi(
    stato: str | None = typer.Option(None, "--stato", help=_("cli-preventivo-list-stato-help")),
    anno: int | None = typer.Option(None, "--anno", help=_("cli-preventivo-list-anno-help")),
    cliente_id: int | None = typer.Option(
        None, "--cliente", help=_("cli-preventivo-list-cliente-help")
    ),
    limit: int = typer.Option(50, "--limit", "-l", help=_("cli-preventivo-list-limit-help")),
) -> None:
    """List preventivi (quotes)."""
    ensure_db()

    with db_session() as db:
        settings = get_settings()
        service = PreventivoService(settings)

        stato_enum = None
        if stato:
            try:
                stato_enum = StatoPreventivo(stato.lower())
            except ValueError:
                console.print(_("cli-preventivo-list-invalid-status", status=stato))
                console.print(
                    _(
                        "cli-preventivo-list-valid-statuses",
                        statuses=", ".join([s.value for s in StatoPreventivo]),
                    )
                )
                raise typer.Exit(1)

        preventivi = service.list_preventivi(
            db=db, stato=stato_enum, cliente_id=cliente_id, anno=anno, limit=limit
        )

        if not preventivi:
            console.print(_("cli-preventivo-list-no-results"))
            return

        table = Table(title=_("cli-preventivo-list-title", count=len(preventivi)), show_lines=False)
        table.add_column(_("cli-preventivo-list-col-id"), style="cyan", width=6)
        table.add_column(_("cli-preventivo-list-col-number"), style="white", width=12)
        table.add_column(_("cli-preventivo-list-col-date"), style="white", width=12)
        table.add_column(_("cli-preventivo-list-col-expiration"), style="white", width=12)
        table.add_column(_("cli-preventivo-list-col-client"), style="bold white")
        table.add_column(
            _("cli-preventivo-list-col-total"), style="green", justify="right", width=12
        )
        table.add_column(_("cli-preventivo-list-col-status"), style="yellow", width=15)

        for p in preventivi:
            status_color = {
                StatoPreventivo.BOZZA: "dim",
                StatoPreventivo.INVIATO: "yellow",
                StatoPreventivo.ACCETTATO: "green",
                StatoPreventivo.RIFIUTATO: "red",
                StatoPreventivo.SCADUTO: "red dim",
                StatoPreventivo.CONVERTITO: "blue",
            }.get(p.stato, "white")

            # Check if expired
            is_expired = p.data_scadenza < date.today() and p.stato not in [
                StatoPreventivo.CONVERTITO,
                StatoPreventivo.SCADUTO,
            ]
            expiration_style = "red" if is_expired else "white"

            table.add_row(
                str(p.id),
                f"{p.numero}/{p.anno}",
                p.data_emissione.isoformat(),
                f"[{expiration_style}]{p.data_scadenza.isoformat()}[/{expiration_style}]",
                p.cliente.denominazione[:30],
                f"€{p.totale:.2f}",
                f"[{status_color}]{p.stato.value}[/{status_color}]",
            )

        console.print(table)


@app.command("show")
def show_preventivo(
    preventivo_id: int = typer.Argument(..., help=_("cli-preventivo-show-id-help")),
) -> None:
    """Show preventivo details."""
    ensure_db()

    with db_session() as db:
        settings = get_settings()
        service = PreventivoService(settings)

        preventivo = service.get_preventivo(db, preventivo_id)

        if not preventivo:
            console.print(_("cli-preventivo-show-not-found", id=preventivo_id))
            raise typer.Exit(1)

        # Header
        console.print(
            _("cli-preventivo-show-header", numero=preventivo.numero, anno=preventivo.anno)
        )

        # Info table
        info = Table(show_header=False, box=None)
        info.add_column(_("cli-preventivo-show-info-field"), style="cyan", width=20)
        info.add_column(_("cli-preventivo-show-info-value"), style="white")

        info.add_row(_("cli-preventivo-show-field-client"), preventivo.cliente.denominazione)
        info.add_row(
            _("cli-preventivo-show-field-issue-date"), preventivo.data_emissione.isoformat()
        )
        info.add_row(
            _("cli-preventivo-show-field-expiration-date"), preventivo.data_scadenza.isoformat()
        )
        info.add_row(
            _("cli-preventivo-show-field-validity"),
            _("cli-preventivo-show-validity-days", days=preventivo.validita_giorni),
        )
        info.add_row(_("cli-preventivo-show-field-status"), preventivo.stato.value)

        # Check if expired
        is_expired = preventivo.data_scadenza < date.today()
        if is_expired and preventivo.stato not in [
            StatoPreventivo.CONVERTITO,
            StatoPreventivo.SCADUTO,
        ]:
            info.add_row(
                _("cli-preventivo-show-warning-label"), _("cli-preventivo-show-expired-warning")
            )

        console.print(info)

        # Line items
        console.print(_("cli-preventivo-show-items-title"))
        items_table = Table(show_lines=True)
        items_table.add_column(_("cli-preventivo-show-col-num"), width=4, justify="right")
        items_table.add_column(_("cli-preventivo-show-col-description"))
        items_table.add_column(_("cli-preventivo-show-col-qty"), justify="right", width=8)
        items_table.add_column(_("cli-preventivo-show-col-price"), justify="right", width=10)
        items_table.add_column(_("cli-preventivo-show-col-vat"), justify="right", width=8)
        items_table.add_column(_("cli-preventivo-show-col-total"), justify="right", width=12)

        for riga in preventivo.righe:
            items_table.add_row(
                str(riga.numero_riga),
                riga.descrizione,
                str(riga.quantita),
                f"€{riga.prezzo_unitario:.2f}",
                f"{riga.aliquota_iva:.0f}%",
                f"€{riga.totale:.2f}",
            )

        console.print(items_table)

        # Totals
        console.print(_("cli-preventivo-show-totals-title"))
        totals = Table(show_header=False, box=None)
        totals.add_column("", style="cyan", justify="right", width=30)
        totals.add_column("", style="white", justify="right", width=15)

        totals.add_row(_("cli-preventivo-show-totals-imponibile"), f"€{preventivo.imponibile:.2f}")
        totals.add_row(_("cli-preventivo-show-totals-iva"), f"€{preventivo.iva:.2f}")
        totals.add_row(
            _("cli-preventivo-show-totals-totale"), f"[bold]€{preventivo.totale:.2f}[/bold]"
        )

        console.print(totals)

        # Notes and conditions
        if preventivo.note:
            console.print(_("cli-preventivo-show-notes-title"))
            console.print(f"[dim]{preventivo.note}[/dim]")

        if preventivo.condizioni:
            console.print(_("cli-preventivo-show-conditions-title"))
            console.print(f"[dim]{preventivo.condizioni}[/dim]")

        console.print()


@app.command("delete")
def delete_preventivo(
    preventivo_id: int = typer.Argument(..., help=_("cli-preventivo-delete-id-help")),
    force: bool = typer.Option(False, "--force", "-f", help=_("cli-preventivo-delete-force-help")),
) -> None:
    """Delete a preventivo."""
    ensure_db()

    with db_session() as db:
        settings = get_settings()
        service = PreventivoService(settings)

        preventivo = service.get_preventivo(db, preventivo_id)

        if not preventivo:
            console.print(_("cli-preventivo-delete-not-found", id=preventivo_id))
            raise typer.Exit(1)

        if not force and not Confirm.ask(
            _("cli-preventivo-delete-confirm", numero=preventivo.numero, anno=preventivo.anno),
            default=False,
        ):
            console.print(_("cli-preventivo-delete-cancelled"))
            return

        success, error = service.delete_preventivo(db, preventivo_id)

        if error:
            console.print(_("cli-preventivo-delete-error", error=error))
            raise typer.Exit(1)

        console.print(
            _("cli-preventivo-delete-success", numero=preventivo.numero, anno=preventivo.anno)
        )


@app.command("converti")
def converti_preventivo(
    preventivo_id: int = typer.Argument(..., help=_("cli-preventivo-convert-id-help")),
    tipo_documento: str = typer.Option(
        "TD01", "--tipo", help=_("cli-preventivo-convert-tipo-help")
    ),
) -> None:
    """
    Convert preventivo to fattura (invoice).
    """
    ensure_db()

    console.print(f"\n{_('cli-preventivo-convert-title')}\n")

    with db_session() as db:
        settings = get_settings()
        service = PreventivoService(settings)

        # Get preventivo
        preventivo = service.get_preventivo(db, preventivo_id)

        if not preventivo:
            console.print(_("cli-preventivo-convert-not-found", id=preventivo_id))
            raise typer.Exit(1)

        # Show preventivo summary
        console.print(
            _(
                "cli-preventivo-convert-summary-numero",
                numero=preventivo.numero,
                anno=preventivo.anno,
            )
        )
        console.print(
            _("cli-preventivo-convert-summary-client", client=preventivo.cliente.denominazione)
        )
        console.print(_("cli-preventivo-convert-summary-total", total=f"{preventivo.totale:.2f}"))

        # Parse tipo_documento
        try:
            tipo_doc_enum = TipoDocumento(tipo_documento.upper())
        except ValueError:
            console.print(_("cli-preventivo-convert-invalid-tipo", tipo=tipo_documento))
            console.print(_("cli-preventivo-convert-valid-tipos"))
            raise typer.Exit(1)

        # Confirm
        if not Confirm.ask(_("cli-preventivo-convert-confirm"), default=True):
            console.print(_("cli-preventivo-convert-cancelled"))
            return

        # Convert
        fattura, error = service.converti_a_fattura(db, preventivo_id, tipo_doc_enum)

        if error or not fattura:
            console.print(
                _("cli-preventivo-convert-error", error=error or _("cli-preventivo-unknown-error"))
            )
            raise typer.Exit(1)

        # Success
        console.print(_("cli-preventivo-convert-success"))

        table = Table(
            title=_(
                "cli-preventivo-convert-invoice-title", numero=fattura.numero, anno=fattura.anno
            )
        )
        table.add_column(_("cli-preventivo-convert-field-column"), style="cyan", width=20)
        table.add_column(_("cli-preventivo-convert-value-column"), style="white", justify="right")

        table.add_row(_("cli-preventivo-convert-field-client"), fattura.cliente.denominazione)
        table.add_row(_("cli-preventivo-convert-field-date"), fattura.data_emissione.isoformat())
        table.add_row(_("cli-preventivo-convert-field-doc-type"), fattura.tipo_documento.value)
        table.add_row(_("cli-preventivo-convert-field-line-items"), str(len(fattura.righe)))
        table.add_row(_("cli-preventivo-convert-field-imponibile"), f"€{fattura.imponibile:.2f}")
        table.add_row(_("cli-preventivo-convert-field-iva"), f"€{fattura.iva:.2f}")
        table.add_row(
            _("cli-preventivo-convert-field-totale"), f"[bold]€{fattura.totale:.2f}[/bold]"
        )

        console.print(table)

        console.print(_("cli-preventivo-convert-invoice-id", id=fattura.id))
        console.print(
            _(
                "cli-preventivo-convert-original",
                numero=preventivo.numero,
                anno=preventivo.anno,
                id=preventivo.id,
            )
        )
        console.print(_("cli-preventivo-convert-next-send", id=fattura.id))


@app.command("aggiorna-stato")
def aggiorna_stato(
    preventivo_id: int = typer.Argument(..., help=_("cli-preventivo-update-status-id-help")),
    stato: str = typer.Argument(..., help=_("cli-preventivo-update-status-stato-help")),
) -> None:
    """Update preventivo status."""
    ensure_db()

    with db_session() as db:
        settings = get_settings()
        service = PreventivoService(settings)

        # Parse status
        try:
            stato_enum = StatoPreventivo(stato.lower())
        except ValueError:
            console.print(_("cli-preventivo-update-status-invalid", status=stato))
            console.print(
                _(
                    "cli-preventivo-update-status-valid",
                    statuses=", ".join([s.value for s in StatoPreventivo]),
                )
            )
            raise typer.Exit(1)

        # Update
        success, error = service.update_stato(db, preventivo_id, stato_enum)

        if error:
            console.print(_("cli-preventivo-update-status-error", error=error))
            raise typer.Exit(1)

        console.print(_("cli-preventivo-update-status-success", status=stato_enum.value))
