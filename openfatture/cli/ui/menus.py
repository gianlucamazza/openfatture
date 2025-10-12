"""Interactive menu system for OpenFatture."""

from pathlib import Path
from typing import TYPE_CHECKING

import questionary
from questionary import Choice
from rich.console import Console

if TYPE_CHECKING:
    from openfatture.storage.database.models import Fattura

from openfatture.cli.ui.dashboard import show_dashboard
from openfatture.cli.ui.helpers import (
    confirm_action,
    press_any_key,
    select_cliente,
    select_fattura,
    select_multiple_fatture,
    text_input,
)
from openfatture.cli.ui.progress import process_with_progress, with_spinner
from openfatture.cli.ui.styles import openfatture_style

console = Console()


# ============================================================================
# MAIN MENU
# ============================================================================


def show_main_menu() -> str:
    """
    Show main menu and return selection.

    Returns:
        Selected menu option
    """
    console.print("\n")

    choices: list[str | Choice] = [
        "🚀 Setup & Configurazione",
        "👤 Gestione Clienti",
        "🧾 Gestione Fatture",
        "📬 Notifiche SDI",
        "📧 Email & Templates",
        "📦 Operazioni Batch",
        "📊 Report & Statistiche",
        "🤖 AI Assistant",
        questionary.Separator(),
        "❌ Esci",
    ]

    choice = questionary.select(
        "Cosa vuoi fare?",
        choices=choices,
        use_shortcuts=True,
        use_arrow_keys=True,
        style=openfatture_style,
        instruction="(Usa i tasti numerici o frecce ↑↓, INVIO per confermare)",
    ).ask()

    return choice


def handle_main_menu(choice: str) -> bool:
    """
    Handle main menu selection and route to appropriate submenu.

    Args:
        choice: Selected menu option

    Returns:
        False if should exit, True to continue
    """
    if choice == "❌ Esci" or choice is None:
        return False

    if "Setup" in choice:
        handle_setup_menu()
    elif "Clienti" in choice:
        handle_clienti_menu()
    elif "Fatture" in choice:
        handle_fatture_menu()
    elif "Notifiche" in choice:
        handle_notifiche_menu()
    elif "Email" in choice:
        handle_email_menu()
    elif "Batch" in choice:
        handle_batch_menu()
    elif "Report" in choice:
        handle_report_menu()
    elif "AI" in choice:
        handle_ai_menu()

    return True


# ============================================================================
# SETUP & CONFIGURATION MENU
# ============================================================================


def show_setup_menu() -> str:
    """Show setup submenu."""
    choices: list[str | Choice] = [
        "🚀 Inizializza OpenFatture",
        "👁️  Mostra configurazione",
        "✏️  Modifica configurazione",
        "📧 Test PEC",
        questionary.Separator(),
        "← Torna al menu principale",
    ]

    return questionary.select(
        "Setup & Configurazione",
        choices=choices,
        use_shortcuts=True,
        use_arrow_keys=True,
        style=openfatture_style,
        instruction="(Usa i tasti numerici o frecce ↑↓, INVIO per confermare)",
    ).ask()


def handle_setup_menu() -> None:
    """Handle setup menu loop."""
    while True:
        choice = show_setup_menu()

        if "Torna" in choice or choice is None:
            break

        if "Inizializza" in choice:
            action_init_openfatture()
        elif "Mostra" in choice:
            action_show_config()
        elif "Modifica" in choice:
            action_edit_config()
        elif "Test PEC" in choice:
            action_test_pec()


# ============================================================================
# CLIENTI MENU
# ============================================================================


def show_clienti_menu() -> str:
    """Show clients submenu."""
    choices: list[str | Choice] = [
        "➕ Crea nuovo cliente",
        "📋 Lista tutti i clienti",
        "🔍 Cerca cliente",
        "✏️  Modifica cliente",
        "🗑️  Elimina cliente",
        questionary.Separator(),
        "← Torna al menu principale",
    ]

    return questionary.select(
        "Gestione Clienti",
        choices=choices,
        use_shortcuts=True,
        use_arrow_keys=True,
        style=openfatture_style,
        instruction="(Usa i tasti numerici o frecce ↑↓, INVIO per confermare)",
    ).ask()


def handle_clienti_menu() -> None:
    """Handle clients menu loop."""
    while True:
        choice = show_clienti_menu()

        if "Torna" in choice or choice is None:
            break

        if "Crea nuovo" in choice:
            action_create_cliente()
        elif "Lista" in choice:
            action_list_clienti()
        elif "Cerca" in choice:
            action_search_cliente()
        elif "Modifica" in choice:
            action_edit_cliente()
        elif "Elimina" in choice:
            action_delete_cliente()


# ============================================================================
# FATTURE MENU
# ============================================================================


def show_fatture_menu() -> str:
    """Show invoices submenu."""
    choices: list[str | Choice] = [
        "➕ Crea nuova fattura (wizard)",
        "📋 Lista fatture",
        "🔍 Cerca fattura",
        "👁️  Mostra dettagli fattura",
        "📄 Genera XML",
        "📤 Invia a SDI",
        "🗑️  Elimina fattura",
        questionary.Separator(),
        "← Torna al menu principale",
    ]

    return questionary.select(
        "Gestione Fatture",
        choices=choices,
        use_shortcuts=True,
        use_arrow_keys=True,
        style=openfatture_style,
        instruction="(Usa i tasti numerici o frecce ↑↓, INVIO per confermare)",
    ).ask()


def handle_fatture_menu() -> None:
    """Handle invoices menu loop."""
    while True:
        choice = show_fatture_menu()

        if "Torna" in choice or choice is None:
            break

        if "Crea nuova" in choice:
            action_create_fattura()
        elif "Lista" in choice:
            action_list_fatture()
        elif "Cerca" in choice:
            action_search_fattura()
        elif "Mostra dettagli" in choice:
            action_show_fattura()
        elif "Genera XML" in choice:
            action_genera_xml()
        elif "Invia a SDI" in choice:
            action_invia_sdi()
        elif "Elimina" in choice:
            action_delete_fattura()


# ============================================================================
# OTHER MENUS (stubs for now)
# ============================================================================


def show_notifiche_menu() -> str:
    """Show SDI notifications submenu."""
    choices: list[str | Choice] = [
        "📬 Processa notifica da file",
        "📋 Lista tutte le notifiche",
        "👁️  Mostra dettagli notifica",
        questionary.Separator(),
        "← Torna al menu principale",
    ]

    return questionary.select(
        "Notifiche SDI",
        choices=choices,
        use_shortcuts=True,
        use_arrow_keys=True,
        style=openfatture_style,
        instruction="(Usa i tasti numerici o frecce ↑↓, INVIO per confermare)",
    ).ask()


def handle_notifiche_menu() -> None:
    """Handle notifications menu loop."""
    while True:
        choice = show_notifiche_menu()

        if "Torna" in choice or choice is None:
            break

        if "Processa" in choice:
            action_process_notifica()
        elif "Lista" in choice:
            action_list_notifiche()
        elif "Mostra" in choice:
            action_show_notifica()


def show_email_menu() -> str:
    """Show email templates submenu."""
    choices: list[str | Choice] = [
        "📧 Invia email di test",
        "👁️  Anteprima template",
        "ℹ️  Info templates",
        questionary.Separator(),
        "← Torna al menu principale",
    ]

    return questionary.select(
        "Email & Templates",
        choices=choices,
        use_shortcuts=True,
        use_arrow_keys=True,
        style=openfatture_style,
        instruction="(Usa i tasti numerici o frecce ↑↓, INVIO per confermare)",
    ).ask()


def handle_email_menu() -> None:
    """Handle email menu loop."""
    while True:
        choice = show_email_menu()

        if "Torna" in choice or choice is None:
            break

        if "Invia email" in choice:
            action_test_email()
        elif "Anteprima" in choice:
            action_preview_template()
        elif "Info" in choice:
            action_email_info()


def show_batch_menu() -> str:
    """Show batch operations submenu."""
    choices: list[str | Choice] = [
        "📤 Invia multiple fatture a SDI",
        "📥 Importa fatture da CSV",
        "💾 Esporta fatture selezionate",
        "🗑️  Elimina fatture multiple",
        "📜 Storico operazioni",
        questionary.Separator(),
        "← Torna al menu principale",
    ]

    return questionary.select(
        "Operazioni Batch",
        choices=choices,
        use_shortcuts=True,
        use_arrow_keys=True,
        style=openfatture_style,
        instruction="(Usa i tasti numerici o frecce ↑↓, INVIO per confermare)",
    ).ask()


def handle_batch_menu() -> None:
    """Handle batch operations menu loop."""
    while True:
        choice = show_batch_menu()

        if "Torna" in choice or choice is None:
            break

        if "Invia multiple" in choice:
            action_batch_send()
        elif "Importa" in choice:
            action_batch_import()
        elif "Esporta" in choice:
            action_batch_export()
        elif "Elimina fatture" in choice:
            action_batch_delete()
        elif "Storico" in choice:
            action_batch_history()


def show_report_menu() -> str:
    """Show reports submenu."""
    choices: list[str | Choice] = [
        "📊 Dashboard Interattiva",
        "📈 Report mensile",
        "📅 Report annuale",
        "👤 Report per cliente",
        "📋 Export Excel",
        questionary.Separator(),
        "← Torna al menu principale",
    ]

    return questionary.select(
        "Report & Statistiche",
        choices=choices,
        use_shortcuts=True,
        use_arrow_keys=True,
        style=openfatture_style,
        instruction="(Usa i tasti numerici o frecce ↑↓, INVIO per confermare)",
    ).ask()


def handle_report_menu() -> None:
    """Handle reports menu loop."""
    while True:
        choice = show_report_menu()

        if "Torna" in choice or choice is None:
            break

        if "Dashboard" in choice:
            action_show_dashboard()
        elif "mensile" in choice:
            action_report_mensile()
        elif "annuale" in choice:
            action_report_annuale()
        elif "cliente" in choice:
            action_report_cliente()
        elif "Excel" in choice:
            action_export_excel()


def show_ai_menu() -> str:
    """Show AI assistant submenu."""
    choices: list[str | Choice] = [
        "💬 Chat con assistente AI",
        "💡 Suggerimenti fattura",
        questionary.Separator(),
        "← Torna al menu principale",
    ]

    return questionary.select(
        "AI Assistant",
        choices=choices,
        use_shortcuts=True,
        use_arrow_keys=True,
        style=openfatture_style,
        instruction="(Usa i tasti numerici o frecce ↑↓, INVIO per confermare)",
    ).ask()


def handle_ai_menu() -> None:
    """Handle AI menu loop."""
    while True:
        choice = show_ai_menu()

        if "Torna" in choice or choice is None:
            break

        if "Chat" in choice:
            action_ai_chat()
        elif "Suggerimenti" in choice:
            action_ai_suggestions()


# ============================================================================
# ACTION HANDLERS - SETUP
# ============================================================================


def action_init_openfatture() -> None:
    """Initialize OpenFatture (calls init command)."""
    from openfatture.cli.commands.init import init

    console.print("\n")
    try:
        # Call the existing init command interactively
        init(interactive=True)
        press_any_key("\n[dim]Premi INVIO per tornare al menu...[/dim]")
    except Exception as e:
        console.print(f"\n[red]Errore: {e}[/red]")
        press_any_key()


def action_show_config() -> None:
    """Show configuration."""
    from openfatture.cli.commands.config import show_config

    console.print("\n")
    try:
        show_config()
        press_any_key()
    except Exception as e:
        console.print(f"[red]Errore: {e}[/red]")
        press_any_key()


def action_edit_config() -> None:
    """Edit configuration."""
    from openfatture.cli.ui.config_wizard import interactive_config_wizard

    try:
        interactive_config_wizard()
    except Exception as e:
        console.print(f"\n[red]Errore: {e}[/red]")
        press_any_key()


def action_test_pec() -> None:
    """Test PEC configuration."""
    from openfatture.cli.commands.pec import test_pec

    console.print("\n")
    try:
        test_pec()
        press_any_key()
    except Exception as e:
        console.print(f"[red]Errore: {e}[/red]")
        press_any_key()


# ============================================================================
# ACTION HANDLERS - CLIENTI
# ============================================================================


def action_create_cliente() -> None:
    """Create new client with wizard."""
    from openfatture.cli.commands.cliente import add_cliente

    console.print("\n[bold blue]👤 Crea Nuovo Cliente[/bold blue]\n")
    try:
        # Use the existing interactive mode from cliente command
        add_cliente(
            denominazione="",  # Will be prompted
            interactive=True,
        )
        press_any_key()
    except Exception as e:
        console.print(f"[red]Errore: {e}[/red]")
        press_any_key()


def action_list_clienti() -> None:
    """List all clients."""
    from openfatture.cli.commands.cliente import list_clienti

    console.print("\n")
    try:
        list_clienti()
        press_any_key()
    except Exception as e:
        console.print(f"[red]Errore: {e}[/red]")
        press_any_key()


def action_search_cliente() -> None:
    """Search and show client."""
    cliente = select_cliente(message="Cerca cliente:")
    if cliente:
        from openfatture.cli.commands.cliente import show_cliente

        show_cliente(cliente.id)
        press_any_key()


def action_edit_cliente() -> None:
    """Edit client."""
    console.print("\n[yellow]This feature is not yet implemented[/yellow]")
    console.print(
        "[dim]Usa: openfatture cliente add --interactive per creare un nuovo cliente[/dim]"
    )
    press_any_key()


def action_delete_cliente() -> None:
    """Delete client."""
    cliente = select_cliente(message="Seleziona cliente da eliminare:")
    if cliente and confirm_action(f"Eliminare '{cliente.denominazione}'?", default=False):
        from openfatture.cli.commands.cliente import delete_cliente

        try:
            delete_cliente(cliente.id, force=False)
            press_any_key()
        except Exception as e:
            console.print(f"[red]Errore: {e}[/red]")
            press_any_key()


# ============================================================================
# ACTION HANDLERS - FATTURE
# ============================================================================


def action_create_fattura() -> None:
    """Create new invoice with wizard."""
    from openfatture.cli.commands.fattura import crea_fattura

    console.print("\n")
    try:
        crea_fattura()
        press_any_key()
    except Exception as e:
        console.print(f"[red]Errore: {e}[/red]")
        press_any_key()


def action_list_fatture() -> None:
    """List invoices."""
    from openfatture.cli.commands.fattura import list_fatture

    console.print("\n")
    try:
        list_fatture()
        press_any_key()
    except Exception as e:
        console.print(f"[red]Errore: {e}[/red]")
        press_any_key()


def action_search_fattura() -> None:
    """Search and show invoice."""
    fattura = select_fattura(message="Cerca fattura:")
    if fattura:
        from openfatture.cli.commands.fattura import show_fattura

        show_fattura(fattura.id)
        press_any_key()


def action_show_fattura() -> None:
    """Show invoice details."""
    fattura = select_fattura(message="Seleziona fattura:")
    if fattura:
        from openfatture.cli.commands.fattura import show_fattura

        show_fattura(fattura.id)
        press_any_key()


def action_genera_xml() -> None:
    """Generate FatturaPA XML."""
    fattura = select_fattura(message="Seleziona fattura per generare XML:")
    if fattura:
        from openfatture.cli.commands.fattura import genera_xml

        try:
            genera_xml(fattura.id)
            press_any_key()
        except Exception as e:
            console.print(f"[red]Errore: {e}[/red]")
            press_any_key()


def action_invia_sdi() -> None:
    """Send invoice to SDI."""
    fattura = select_fattura(message="Seleziona fattura da inviare:")
    if fattura:
        from openfatture.cli.commands.fattura import invia_fattura

        try:
            invia_fattura(fattura.id)
            press_any_key()
        except Exception as e:
            console.print(f"[red]Errore: {e}[/red]")
            press_any_key()


def action_delete_fattura() -> None:
    """Delete invoice."""
    fattura = select_fattura(message="Seleziona fattura da eliminare:")
    if fattura and confirm_action(
        f"Eliminare fattura {fattura.numero}/{fattura.anno}?", default=False
    ):
        from openfatture.cli.commands.fattura import delete_fattura

        try:
            delete_fattura(fattura.id, force=False)
            press_any_key()
        except Exception as e:
            console.print(f"[red]Errore: {e}[/red]")
            press_any_key()


# ============================================================================
# ACTION HANDLERS - OTHER (stubs)
# ============================================================================


def action_process_notifica() -> None:
    """Process SDI notification."""
    filename = text_input("Percorso file notifica XML:")
    if filename:
        from openfatture.cli.commands.notifiche import process_notification

        try:
            process_notification(filename)
            press_any_key()
        except Exception as e:
            console.print(f"[red]Errore: {e}[/red]")
            press_any_key()


def action_list_notifiche() -> None:
    """List notifications."""
    from openfatture.cli.commands.notifiche import list_notifications

    try:
        list_notifications()
        press_any_key()
    except Exception as e:
        console.print(f"[red]Errore: {e}[/red]")
        press_any_key()


def action_show_notifica() -> None:
    """Show notification details."""
    notif_id = text_input("ID notifica:")
    if notif_id:
        from openfatture.cli.commands.notifiche import show_notification

        try:
            show_notification(int(notif_id))
            press_any_key()
        except Exception as e:
            console.print(f"[red]Errore: {e}[/red]")
            press_any_key()


def action_test_email() -> None:
    """Send test email."""
    from openfatture.cli.commands.email import test_email

    try:
        test_email()
        press_any_key()
    except Exception as e:
        console.print(f"[red]Errore: {e}[/red]")
        press_any_key()


def action_preview_template() -> None:
    """Preview email template."""
    from openfatture.cli.commands.email import preview_template

    try:
        template_name = text_input("Nome template (es: sdi/invio_fattura.html):")
        if template_name:
            preview_template(template_name)
        press_any_key()
    except Exception as e:
        console.print(f"[red]Errore: {e}[/red]")
        press_any_key()


def action_email_info() -> None:
    """Show email templates info."""
    from openfatture.cli.commands.email import email_info as show_info

    try:
        show_info()
        press_any_key()
    except Exception as e:
        console.print(f"[red]Errore: {e}[/red]")
        press_any_key()


def action_batch_send() -> None:
    """Send multiple invoices to SDI with progress bar."""
    console.print("\n[bold blue]📤 Invio Multiple Fatture a SDI[/bold blue]\n")

    # Select multiple invoices
    fatture = select_multiple_fatture(
        message="Seleziona le fatture da inviare (SPAZIO per selezionare):",
        stato="da_inviare",
    )

    if not fatture:
        console.print("[yellow]Nessuna fattura selezionata.[/yellow]")
        press_any_key()
        return

    # Confirm
    if not confirm_action(f"Inviare {len(fatture)} fatture a SDI?"):
        console.print("[yellow]Operazione annullata.[/yellow]")
        press_any_key()
        return

    # Process with progress bar
    from openfatture.cli.commands.fattura import invia_fattura

    def send_invoice(fattura: "Fattura") -> tuple[bool, str | None]:
        try:
            invia_fattura(fattura.id)
            return True, None
        except Exception as e:
            return False, f"Fattura {fattura.numero}/{fattura.anno}: {str(e)}"

    success, errors, error_msgs = process_with_progress(
        fatture,
        send_invoice,
        description="Invio fatture a SDI...",
        success_message="Fatture inviate con successo",
        error_message="Errori durante l'invio",
    )

    press_any_key()


def action_batch_import() -> None:
    """Import invoices from CSV."""
    console.print("\n[yellow]Batch import is not fully integrated yet[/yellow]")
    console.print("[dim]Usa: openfatture batch import <file.csv>[/dim]")
    press_any_key()


def action_batch_export() -> None:
    """Export selected invoices to CSV with progress bar."""
    console.print("\n[bold blue]💾 Esporta Fatture Selezionate[/bold blue]\n")

    # Select multiple invoices
    fatture = select_multiple_fatture(
        message="Seleziona le fatture da esportare (SPAZIO per selezionare):",
    )

    if not fatture:
        console.print("[yellow]Nessuna fattura selezionata.[/yellow]")
        press_any_key()
        return

    filename = text_input("Nome file CSV:", default="fatture_export.csv")
    if not filename:
        console.print("[yellow]Operazione annullata.[/yellow]")
        press_any_key()
        return

    # Show message with spinner
    def export_invoices() -> Path:
        import csv
        from pathlib import Path

        output_path = Path.cwd() / filename
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Numero", "Anno", "Data", "Cliente", "Totale", "Stato"])
            for fattura in fatture:
                writer.writerow(
                    [
                        fattura.numero,
                        fattura.anno,
                        fattura.data_emissione.strftime("%Y-%m-%d"),
                        fattura.cliente.denominazione,
                        float(fattura.totale),
                        fattura.stato.value,
                    ]
                )
        return output_path

    try:
        output = with_spinner(
            export_invoices,
            message=f"Esportazione di {len(fatture)} fatture...",
            success_message=f"Fatture esportate in {filename}",
        )
        console.print(f"[green]✓ File salvato: {output}[/green]")
    except Exception as e:
        console.print(f"[red]Errore durante l'export: {e}[/red]")

    press_any_key()


def action_batch_delete() -> None:
    """Delete multiple invoices with progress bar."""
    console.print("\n[bold blue]🗑️  Elimina Fatture Multiple[/bold blue]\n")

    # Select multiple invoices
    fatture = select_multiple_fatture(
        message="Seleziona le fatture da eliminare (SPAZIO per selezionare):",
    )

    if not fatture:
        console.print("[yellow]Nessuna fattura selezionata.[/yellow]")
        press_any_key()
        return

    # Confirm
    if not confirm_action(
        f"[red]WARNING: Delete {len(fatture)} invoices? This action cannot be undone![/red]",
        default=False,
    ):
        console.print("[yellow]Operazione annullata.[/yellow]")
        press_any_key()
        return

    # Process with progress bar
    from openfatture.cli.commands.fattura import delete_fattura

    def delete_invoice(fattura: "Fattura") -> tuple[bool, str | None]:
        try:
            delete_fattura(fattura.id, force=True)
            return True, None
        except Exception as e:
            return False, f"Fattura {fattura.numero}/{fattura.anno}: {str(e)}"

    success, errors, error_msgs = process_with_progress(
        fatture,
        delete_invoice,
        description="Eliminazione fatture...",
        success_message="Fatture eliminate con successo",
        error_message="Errori durante l'eliminazione",
    )

    press_any_key()


def action_batch_history() -> None:
    """Show batch operations history."""
    console.print("\n[yellow]Batch history is not fully integrated yet[/yellow]")
    console.print("[dim]Usa: openfatture batch history[/dim]")
    press_any_key()


def action_show_dashboard() -> None:
    """Show interactive dashboard with statistics."""
    try:
        show_dashboard()
    except Exception as e:
        console.print(f"[red]Errore durante la visualizzazione della dashboard: {e}[/red]")
        press_any_key()


def action_report_mensile() -> None:
    """Generate monthly report."""
    console.print("\n[yellow]Report mensile non ancora implementato[/yellow]")
    press_any_key()


def action_report_annuale() -> None:
    """Generate annual report."""
    console.print("\n[yellow]Report annuale non ancora implementato[/yellow]")
    press_any_key()


def action_report_cliente() -> None:
    """Generate client report."""
    console.print("\n[yellow]Report cliente non ancora implementato[/yellow]")
    press_any_key()


def action_export_excel() -> None:
    """Export to Excel."""
    console.print("\n[yellow]Export Excel non ancora implementato[/yellow]")
    press_any_key()


def action_ai_chat() -> None:
    """AI chat assistant."""
    import asyncio

    from openfatture.cli.ui.chat import start_interactive_chat

    try:
        # Run async chat
        asyncio.run(start_interactive_chat())
    except Exception as e:
        console.print(f"\n[red]Errore: {e}[/red]")
        press_any_key()


def action_ai_suggestions() -> None:
    """AI invoice suggestions."""
    console.print("\n[yellow]AI Suggestions non ancora implementato[/yellow]")
    console.print("[dim]Usa: openfatture ai suggest[/dim]")
    press_any_key()
