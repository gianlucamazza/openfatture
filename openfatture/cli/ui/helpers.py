"""UI helper functions for interactive mode."""

from collections.abc import Callable

import questionary
from rich.console import Console

from openfatture.cli.ui.styles import openfatture_style
from openfatture.storage.database.base import SessionLocal
from openfatture.storage.database.models import Cliente, Fattura

console = Console()


def select_cliente(message: str = "Seleziona cliente:", allow_none: bool = False) -> Cliente | None:
    """
    Interactive client selector with search.

    Args:
        message: Prompt message
        allow_none: If True, adds "None" option

    Returns:
        Selected Client or None
    """
    db = SessionLocal()
    try:
        clienti = db.query(Cliente).order_by(Cliente.denominazione).all()

        if not clienti:
            console.print("[yellow]Nessun cliente trovato. Creane uno prima.[/yellow]")
            return None

        choices = []

        if allow_none:
            choices.append(questionary.Choice(title="[Nessuno]", value=None))

        choices.extend(
            [
                questionary.Choice(
                    title=f"{c.denominazione} ({c.partita_iva or 'N/A'})",
                    value=c.id,
                )
                for c in clienti
            ]
        )

        cliente_id = questionary.select(
            message,
            choices=choices,
            style=openfatture_style,
            use_arrow_keys=True,
            use_jk_keys=False,  # Disable j/k to avoid conflicts with typing
            instruction="(Digita per cercare, ↑↓ per navigare, INVIO per selezionare)",
        ).ask()

        if cliente_id is None:
            return None

        # Fetch fresh instance from database
        return db.query(Cliente).filter(Cliente.id == cliente_id).first()
    finally:
        db.close()


def select_fattura(
    message: str = "Seleziona fattura:",
    anno: int | None = None,
    stato: str | None = None,
) -> Fattura | None:
    """
    Interactive invoice selector.

    Args:
        message: Prompt message
        anno: Filter by year
        stato: Filter by status

    Returns:
        Selected Invoice or None
    """
    db = SessionLocal()
    try:
        query = db.query(Fattura).order_by(Fattura.anno.desc(), Fattura.numero.desc())

        if anno:
            query = query.filter(Fattura.anno == anno)
        if stato:
            from openfatture.storage.database.models import StatoFattura

            query = query.filter(Fattura.stato == StatoFattura(stato))

        fatture = query.limit(50).all()

        if not fatture:
            console.print("[yellow]Nessuna fattura trovata.[/yellow]")
            return None

        choices = [
            questionary.Choice(
                title=(
                    f"{f.numero}/{f.anno} - {f.cliente.denominazione} - "
                    f"€{f.totale:.2f} [{f.stato.value}]"
                ),
                value=f.id,
            )
            for f in fatture
        ]

        fattura_id = questionary.select(
            message,
            choices=choices,
            style=openfatture_style,
            use_arrow_keys=True,
            use_jk_keys=False,
            instruction="(Digita per cercare, ↑↓ per navigare, INVIO per selezionare)",
        ).ask()

        if fattura_id is None:
            return None

        # Fetch fresh instance from database
        return db.query(Fattura).filter(Fattura.id == fattura_id).first()
    finally:
        db.close()


def confirm_action(message: str, default: bool = False) -> bool:
    """
    Confirm yes/no action.

    Args:
        message: Confirmation message
        default: Default answer

    Returns:
        True if confirmed, False otherwise
    """
    return questionary.confirm(message, default=default, style=openfatture_style).ask()


def text_input(message: str, default: str = "", validate: Callable | None = None) -> str:
    """
    Text input prompt.

    Args:
        message: Input message
        default: Default value
        validate: Optional validation function

    Returns:
        User input string
    """
    return questionary.text(
        message, default=default, validate=validate, style=openfatture_style
    ).ask()


def select_multiple(choices: list[str], message: str = "Seleziona opzioni:") -> list[str]:
    """
    Multi-select with checkboxes.

    Args:
        choices: List of choices
        message: Prompt message

    Returns:
        List of selected items
    """
    return questionary.checkbox(message, choices=choices, style=openfatture_style).ask()


def select_multiple_fatture(
    message: str = "Seleziona fatture (SPAZIO per selezionare):",
    anno: int | None = None,
    stato: str | None = None,
    max_items: int = 50,
) -> list[Fattura]:
    """
    Multi-select for invoices with checkboxes.

    Args:
        message: Prompt message
        anno: Filter by year
        stato: Filter by status
        max_items: Maximum items to show

    Returns:
        List of selected invoices
    """
    db = SessionLocal()
    try:
        query = db.query(Fattura).order_by(Fattura.anno.desc(), Fattura.numero.desc())

        if anno:
            query = query.filter(Fattura.anno == anno)
        if stato:
            from openfatture.storage.database.models import StatoFattura

            query = query.filter(Fattura.stato == StatoFattura(stato))

        fatture = query.limit(max_items).all()

        if not fatture:
            console.print("[yellow]Nessuna fattura trovata.[/yellow]")
            return []

        choices = [
            questionary.Choice(
                title=(
                    f"{f.numero}/{f.anno} - {f.cliente.denominazione} - "
                    f"€{f.totale:.2f} [{f.stato.value}]"
                ),
                value=f.id,
                checked=False,  # None pre-selected
            )
            for f in fatture
        ]

        selected_ids = questionary.checkbox(
            message,
            choices=choices,
            style=openfatture_style,
            instruction="(SPAZIO per selezionare/deselezionare, INVIO per confermare)",
        ).ask()

        if not selected_ids:
            return []

        # Fetch selected invoices
        return db.query(Fattura).filter(Fattura.id.in_(selected_ids)).all()
    finally:
        db.close()


def select_multiple_clienti(
    message: str = "Seleziona clienti (SPAZIO per selezionare):",
) -> list[Cliente]:
    """
    Multi-select for clients with checkboxes.

    Returns:
        List of selected clients
    """
    db = SessionLocal()
    try:
        clienti = db.query(Cliente).order_by(Cliente.denominazione).all()

        if not clienti:
            console.print("[yellow]Nessun cliente trovato.[/yellow]")
            return []

        choices = [
            questionary.Choice(
                title=f"{c.denominazione} ({c.partita_iva or 'N/A'}) - {len(c.fatture)} fatture",
                value=c.id,
                checked=False,
            )
            for c in clienti
        ]

        selected_ids = questionary.checkbox(
            message,
            choices=choices,
            style=openfatture_style,
            instruction="(SPAZIO per selezionare/deselezionare, INVIO per confermare)",
        ).ask()

        if not selected_ids:
            return []

        return db.query(Cliente).filter(Cliente.id.in_(selected_ids)).all()
    finally:
        db.close()


def press_any_key(message: str = "\nPremi INVIO per continuare...") -> None:
    """Wait for user to press enter."""
    questionary.press_any_key_to_continue(message, style=openfatture_style).ask()
