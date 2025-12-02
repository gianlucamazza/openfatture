"""Interactive menu system for OpenFatture."""

from typing import TYPE_CHECKING

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
from openfatture.cli.ui.menu_builder import MenuBuilder
from openfatture.cli.ui.progress import process_with_progress
from openfatture.utils.async_bridge import run_async
from openfatture.utils.logging import get_logger

console = Console()
logger = get_logger(__name__)


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

    builder = MenuBuilder("Cosa vuoi fare?")
    builder.add_option("🚀 Setup & Configurazione", "action_setup")
    builder.add_option("👤 Gestione Clienti", "action_clienti")
    builder.add_option("🧾 Gestione Fatture", "action_fatture")
    builder.add_option("📬 Notifiche SDI", "action_notifiche")
    builder.add_option("📧 Email & Templates", "action_email")
    builder.add_option("📦 Operazioni Batch", "action_batch")
    builder.add_option("📊 Report & Statistiche", "action_report")
    builder.add_option("🤖 AI Assistant", "action_ai")
    builder.add_separator()
    builder.add_option("❌ Esci", "action_exit")

    return builder.show()


def handle_main_menu(choice: str) -> bool:
    """
    Handle main menu selection and route to appropriate submenu.

    Args:
        choice: Selected menu option

    Returns:
        False if should exit, True to continue
    """
    if choice == "action_exit" or choice is None:
        return False

    if choice == "action_setup":
        handle_setup_menu()
    elif choice == "action_clienti":
        handle_clienti_menu()
    elif choice == "action_fatture":
        handle_fatture_menu()
    elif choice == "action_notifiche":
        handle_notifiche_menu()
    elif choice == "action_email":
        handle_email_menu()
    elif choice == "action_batch":
        handle_batch_menu()
    elif choice == "action_report":
        handle_report_menu()
    elif choice == "action_ai":
        handle_ai_menu()

    return True


# ============================================================================
# SETUP & CONFIGURATION MENU
# ============================================================================


def handle_setup_menu() -> None:
    """Handle setup menu loop."""
    MenuBuilder("Setup & Configurazione").add_option(
        "🚀 Inizializza OpenFatture", "action_init_openfatture", action_init_openfatture
    ).add_option("👁️  Mostra configurazione", "action_show_config", action_show_config).add_option(
        "✏️  Modifica configurazione", "action_edit_config", action_edit_config
    ).add_option(
        "📧 Test PEC", "action_test_pec", action_test_pec
    ).add_back_option().run()


# ============================================================================
# CLIENTI MENU
# ============================================================================


def handle_clienti_menu() -> None:
    """Handle clients menu loop."""
    MenuBuilder("Gestione Clienti").add_option(
        "➕ Crea nuovo cliente", "action_create_cliente", action_create_cliente
    ).add_option("📋 Lista tutti i clienti", "action_list_clienti", action_list_clienti).add_option(
        "🔍 Cerca cliente", "action_search_cliente", action_search_cliente
    ).add_option(
        "✏️  Modifica cliente", "action_edit_cliente", action_edit_cliente
    ).add_option(
        "🗑️  Elimina cliente", "action_delete_cliente", action_delete_cliente
    ).add_back_option().run()


# ============================================================================
# FATTURE MENU
# ============================================================================


def handle_fatture_menu() -> None:
    """Handle invoices menu loop."""
    MenuBuilder("Gestione Fatture").add_option(
        "➕ Crea nuova fattura (wizard)", "action_create_fattura", action_create_fattura
    ).add_option("📋 Lista fatture", "action_list_fatture", action_list_fatture).add_option(
        "🔍 Cerca fattura", "action_search_fattura", action_search_fattura
    ).add_option(
        "👁️  Mostra dettagli fattura", "action_show_fattura", action_show_fattura
    ).add_option(
        "📄 Genera XML", "action_genera_xml", action_genera_xml
    ).add_option(
        "📤 Invia a SDI", "action_invia_sdi", action_invia_sdi
    ).add_option(
        "🗑️  Elimina fattura", "action_delete_fattura", action_delete_fattura
    ).add_back_option().run()


# ============================================================================
# OTHER MENUS
# ============================================================================


def handle_notifiche_menu() -> None:
    """Handle notifications menu loop."""
    MenuBuilder("Notifiche SDI").add_option(
        "📬 Processa notifica da file", "action_process_notifica", action_process_notifica
    ).add_option(
        "📋 Lista tutte le notifiche", "action_list_notifiche", action_list_notifiche
    ).add_option(
        "👁️  Mostra dettagli notifica", "action_show_notifica", action_show_notifica
    ).add_back_option().run()


def handle_email_menu() -> None:
    """Handle email menu loop."""
    MenuBuilder("Email & Templates").add_option(
        "📧 Invia email di test", "action_test_email", action_test_email
    ).add_option(
        "👁️  Anteprima template", "action_preview_template", action_preview_template
    ).add_option(
        "ℹ️  Info templates", "action_email_info", action_email_info
    ).add_back_option().run()


def handle_batch_menu() -> None:
    """Handle batch operations menu loop."""
    MenuBuilder("Operazioni Batch").add_option(
        "📤 Invia multiple fatture a SDI", "action_batch_send", action_batch_send
    ).add_option(
        "📥 Importa fatture da CSV", "action_batch_import", action_batch_import
    ).add_option(
        "💾 Esporta fatture selezionate", "action_batch_export", action_batch_export
    ).add_option(
        "🗑️  Elimina fatture multiple", "action_batch_delete", action_batch_delete
    ).add_option(
        "📜 Storico operazioni", "action_batch_history", action_batch_history
    ).add_back_option().run()


def handle_report_menu() -> None:
    """Handle reports menu loop."""
    MenuBuilder("Report & Statistiche").add_option(
        "📊 Dashboard Interattiva", "action_show_dashboard", action_show_dashboard
    ).add_option("📈 Report mensile", "action_report_mensile", action_report_mensile).add_option(
        "📅 Report annuale", "action_report_annuale", action_report_annuale
    ).add_option(
        "👤 Report per cliente", "action_report_cliente", action_report_cliente
    ).add_option(
        "📋 Export Excel", "action_export_excel", action_export_excel
    ).add_back_option().run()


def handle_ai_menu() -> None:
    """Handle AI menu loop."""
    MenuBuilder("AI Assistant").add_option(
        "💬 Chat con assistente AI", "action_ai_chat", action_ai_chat
    ).add_option(
        "💡 Suggerimenti fattura", "action_ai_suggestions", action_ai_suggestions
    ).add_back_option().run()


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

    # Confirm
    if not confirm_action(f"Esportare {len(fatture)} fatture?"):
        console.print("[yellow]Operazione annullata.[/yellow]")
        press_any_key()
        return

    # Process with progress bar
    # TODO: Implement actual export logic
    console.print("[yellow]Export logic placeholder[/yellow]")
    press_any_key()


def action_batch_delete() -> None:
    """Delete multiple invoices."""
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
    if not confirm_action(f"Eliminare DEFINITIVAMENTE {len(fatture)} fatture?", default=False):
        console.print("[yellow]Operazione annullata.[/yellow]")
        press_any_key()
        return

    # Process with progress bar
    from openfatture.cli.commands.fattura import delete_fattura

    def delete_invoice_wrapper(fattura: "Fattura") -> tuple[bool, str | None]:
        try:
            delete_fattura(fattura.id, force=True)
            return True, None
        except Exception as e:
            return False, f"Fattura {fattura.numero}/{fattura.anno}: {str(e)}"

    success, errors, error_msgs = process_with_progress(
        fatture,
        delete_invoice_wrapper,
        description="Eliminazione fatture...",
        success_message="Fatture eliminate con successo",
        error_message="Errori durante l'eliminazione",
    )

    press_any_key()


def action_batch_history() -> None:
    """Show batch operations history."""
    console.print("\n[yellow]Batch history is not yet implemented[/yellow]")
    press_any_key()


def action_show_dashboard() -> None:
    """Show interactive dashboard."""
    try:
        show_dashboard()
    except Exception as e:
        console.print(f"[red]Errore dashboard: {e}[/red]")
        press_any_key()


def action_report_mensile() -> None:
    """Generate monthly report."""
    # from openfatture.cli.commands.report import report_mensile
    console.print("[yellow]Report mensile non ancora implementato[/yellow]")
    press_any_key()


def action_report_annuale() -> None:
    """Generate annual report."""
    # from openfatture.cli.commands.report import report_annuale
    console.print("[yellow]Report annuale non ancora implementato[/yellow]")
    press_any_key()


def action_report_cliente() -> None:
    """Generate client report."""
    # from openfatture.cli.commands.report import report_cliente
    console.print("[yellow]Report cliente non ancora implementato[/yellow]")
    press_any_key()


def action_export_excel() -> None:
    """Export to Excel."""
    console.print("\n[yellow]Excel export is not yet implemented[/yellow]")
    press_any_key()


def action_ai_chat() -> None:
    """Start AI chat."""

    from openfatture.cli.ui.chat import InteractiveChatUI
    from openfatture.storage.database import init_db

    try:
        # Initialize database before starting chat
        # This ensures tools can access DB when needed
        try:
            init_db()
            logger.debug("database_initialized_for_chat")
        except Exception as db_error:
            logger.warning(
                "database_init_failed",
                error=str(db_error),
                message="Chat will continue but tools may have limited functionality",
            )

        # Run async chat
        chat_ui = InteractiveChatUI()
        run_async(chat_ui.start())
    except Exception as e:
        console.print(f"\n[red]Errore: {e}[/red]")
        press_any_key()


def action_ai_suggestions() -> None:
    """AI invoice suggestions."""
    console.print("\n[yellow]AI Suggestions non ancora implementato[/yellow]")
    console.print("[dim]Usa: openfatture ai suggest[/dim]")
    press_any_key()
