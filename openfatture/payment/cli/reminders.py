"""Payment reminder scheduling and management commands."""

import os
from datetime import date, datetime

import typer
from rich.table import Table

from ..application.notifications import ConsoleNotifier, EmailNotifier, SMTPConfig
from ..application.services import ReminderRepository, ReminderScheduler
from ..domain.enums import ReminderStatus, ReminderStrategy
from ..infrastructure.repository import PaymentRepository
from ._app import _run, app, console, get_db_session


@app.command(name="schedule-reminders")
def schedule_reminders(
    payment_id: int = typer.Argument(..., help="Payment ID"),
    strategy: str = typer.Option(
        "default", "--strategy", "-s", help="Reminder strategy: default|aggressive|gentle|minimal"
    ),
) -> None:
    """Schedule payment reminders.

    Strategies:
        - default: [-7, -3, 0, 7, 30] days
        - aggressive: [-10, -7, -3, -1, 0, 3, 7, 15, 30] days
        - gentle: [-7, 0, 15, 30] days
        - minimal: [0, 30] days

    Examples:
        openfatture payment schedule-reminders 123
        openfatture payment schedule-reminders 124 --strategy aggressive
    """
    strategy_map = {
        "default": ReminderStrategy.DEFAULT,
        "aggressive": ReminderStrategy.AGGRESSIVE,
        "gentle": ReminderStrategy.GENTLE,
        "minimal": ReminderStrategy.MINIMAL,
    }

    if strategy not in strategy_map:
        console.print(f"[red]Invalid strategy: {strategy}[/]")
        console.print("Available: default, aggressive, gentle, minimal")
        raise typer.Exit(1)

    with get_db_session() as session:
        # Initialize scheduler
        notifier = ConsoleNotifier()  # Or EmailNotifier with SMTP config
        scheduler = ReminderScheduler(
            ReminderRepository(session), PaymentRepository(session), notifier
        )

        try:
            reminders = _run(scheduler.schedule_reminders(payment_id, strategy_map[strategy]))

            console.print(f"\n[green]Scheduled {len(reminders)} reminders[/]")

            # Display schedule
            table = Table(title="Reminder Schedule")
            table.add_column("Date", style="cyan")
            table.add_column("Days to Due", justify="right", style="yellow")
            table.add_column("Status", style="dim")

            for reminder in reminders:
                payment = getattr(reminder, "payment", None)
                due_date = getattr(payment, "data_scadenza", None) if payment is not None else None
                reminder_date = getattr(reminder, "reminder_date", None)

                days_until_due: int | None
                if isinstance(due_date, date) and isinstance(reminder_date, date):
                    days_until_due = (due_date - reminder_date).days
                else:
                    days_until_due = getattr(reminder, "days_before_due", None)

                if days_until_due is None:
                    status = "Unknown"
                elif days_until_due > 0:
                    status = "Before due"
                elif days_until_due == 0:
                    status = "Due today"
                else:
                    status = "After due"

                table.add_row(
                    getattr(reminder, "reminder_date", date.today()).strftime("%d/%m/%Y"),
                    str(days_until_due) if days_until_due is not None else "-",
                    status,
                )

            console.print(table)

        except ValueError as e:
            console.print(f"[red]Error: {e}[/]")
            raise typer.Exit(1)


@app.command(name="process-reminders")
def process_reminders(
    target_date: str | None = typer.Option(
        None, "--date", help="Date to process (YYYY-MM-DD), default: today"
    ),
) -> None:
    """Process due reminders (background job).

    Run this daily via cron to send reminders.

    Examples:
        # Process today's reminders
        openfatture payment process-reminders

        # Process specific date
        openfatture payment process-reminders --date 2024-12-25
    """
    process_date = (
        datetime.strptime(target_date, "%Y-%m-%d").date() if target_date else date.today()
    )

    with get_db_session() as session:
        # Email notifier (requires SMTP config)
        smtp_config = SMTPConfig(
            host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
            port=int(os.getenv("SMTP_PORT", 587)),
            username=os.getenv("SMTP_USER", ""),
            password=os.getenv("SMTP_PASSWORD", ""),
            from_email=os.getenv("SMTP_FROM", "noreply@openfatture.com"),
        )

        notifier = EmailNotifier(smtp_config) if os.getenv("SMTP_HOST") else ConsoleNotifier()
        scheduler = ReminderScheduler(
            ReminderRepository(session), PaymentRepository(session), notifier
        )

        console.print(f"[cyan]Processing reminders for {process_date.strftime('%d/%m/%Y')}...[/]")

        count = _run(scheduler.process_due_reminders(process_date))

        console.print(f"\n[green]Sent {count} reminders[/]")


@app.command(name="list-reminders")
def list_reminders(
    status: ReminderStatus | None = typer.Option(
        None,
        "--status",
        help="Filter by status (PENDING|SENT|FAILED|CANCELLED)",
        case_sensitive=False,
    ),
    payment_id: int | None = typer.Option(None, "--payment", help="Filter by payment ID"),
    limit: int | None = typer.Option(50, "--limit", "-l", help="Limit results (default: 50)"),
) -> None:
    """List scheduled payment reminders."""

    with get_db_session() as session:
        repo = ReminderRepository(session)
        effective_limit = None if limit is None or limit <= 0 else limit
        reminders = repo.list_reminders(status=status, payment_id=payment_id, limit=effective_limit)

        if not reminders:
            console.print("[yellow]No reminders found for the given filters.[/]")
            return

        table = Table(title="Payment Reminders")
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Payment", justify="right")
        table.add_column("Date", justify="center")
        table.add_column("Status", justify="center")
        table.add_column("Strategy", justify="center")
        table.add_column("Days", justify="right")
        table.add_column("Sent", justify="center")
        table.add_column("Notes", overflow="fold")

        for reminder in reminders:
            due_date = getattr(reminder.payment, "data_scadenza", None)
            table.add_row(
                str(reminder.id),
                str(reminder.payment_id),
                reminder.reminder_date.strftime("%d/%m/%Y"),
                reminder.status.value,
                reminder.strategy.value,
                str(reminder.days_before_due),
                reminder.sent_date.strftime("%d/%m/%Y") if reminder.sent_date else "-",
                f"Due: {due_date.strftime('%d/%m/%Y')}" if due_date else "-",
            )

        console.print(table)


@app.command(name="cancel-reminder")
def cancel_reminder(reminder_id: int = typer.Argument(..., help="Reminder ID to cancel")) -> None:
    """Cancel a scheduled reminder if it hasn't been sent yet."""

    with get_db_session() as session:
        repo = ReminderRepository(session)
        reminder = repo.get_by_id(reminder_id)
        if not reminder:
            console.print(f"[red]Reminder {reminder_id} not found[/]")
            raise typer.Exit(1)

        if reminder.status == ReminderStatus.SENT:
            console.print(f"[yellow]Reminder {reminder_id} already sent; cannot cancel.[/]")
            raise typer.Exit(1)

        reminder.cancel()
        repo.update(reminder)
        session.commit()

        console.print(f"[green]Reminder {reminder_id} cancelled[/]")
