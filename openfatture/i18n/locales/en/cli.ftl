### main - Main CLI

## CONFIG Commands - Configuration Management
cli-config-help-key = Configuration key (e.g., pec.address)
cli-config-help-value = Configuration value
cli-config-show-title = OpenFatture Configuration
cli-config-column-setting = Setting
cli-config-column-value = Value
cli-config-label-app-version = App Version
cli-config-label-debug-mode = Debug Mode
cli-config-label-database-url = Database URL
cli-config-label-data-dir = Data Directory
cli-config-label-archive-dir = Archive Directory
cli-config-label-certificates-dir = Certificates Directory
cli-config-label-company-name = Company Name
cli-config-label-partita-iva = Partita IVA
cli-config-label-codice-fiscale = Codice Fiscale
cli-config-label-tax-regime = Tax Regime
cli-config-label-pec-address = PEC Address
cli-config-label-pec-smtp-server = PEC SMTP Server
cli-config-label-sdi-pec-address = SDI PEC Address
cli-config-label-notification-email = Notification Email
cli-config-label-notifications-enabled = Notifications Enabled
cli-config-label-locale = Locale
cli-config-label-email-logo-url = Email Logo URL
cli-config-label-primary-color = Primary Color
cli-config-label-secondary-color = Secondary Color
cli-config-label-email-footer = Email Footer
cli-config-label-ai-provider = AI Provider
cli-config-label-ai-model = AI Model
cli-config-label-ai-base-url = AI Base URL
cli-config-label-ai-api-key = AI API Key
cli-config-label-chat-enabled = Chat Enabled
cli-config-label-chat-auto-save = Chat Auto-Save
cli-config-label-max-messages = Max Messages/Session
cli-config-label-max-tokens = Max Tokens/Session
cli-config-label-tools-enabled = Tools Enabled
cli-config-label-tool-access = AI Tool Access
cli-config-label-extra-tools = Extra Tools
cli-config-not-set = [red]Not set[/red]
cli-config-not-set-optional = [yellow]Not set[/yellow]
cli-config-set = [green]Set[/green]
cli-config-yes = [green]Yes[/green]
cli-config-no = [red]No[/red]
cli-config-auto-generated = [dim]Auto-generated[/dim]
cli-config-reload-success = [green]Configuration reloaded[/green]
cli-config-set-success = [green]Set { $key } = { $value }[/green]
cli-config-saved-to = [dim]Saved to { $path }[/dim]
cli-config-invalid-key = [red]Invalid configuration key: { $key }[/red]
cli-config-error = [red]Error: { $error }[/red]
cli-config-column-source = Source
cli-config-source-env = environment
cli-config-source-keyring = keychain
cli-config-source-file = credentials file
cli-config-source-config = config.toml
cli-config-source-default = default
cli-config-file-path = [dim]Configuration file: { $path }[/dim]
cli-config-secret-backend = [dim]Secrets: { $backend }[/dim]
cli-config-secret-saved = [green]{ $key } saved to: { $backend }[/green]
cli-config-env-override = [yellow]{ $key } is set by an environment variable: the saved value is ignored while it stays set.[/yellow]
cli-config-unset-success = [green]Removed { $key }[/green]
cli-config-unset-missing = [yellow]{ $key } was not set[/yellow]
cli-config-invalid-value = [red]Invalid value for { $key }: { $error }[/red]
cli-config-migrate-moved = [green]Moved to { $backend }: { $keys }[/green]
cli-config-migrate-imported = [green]Imported into config.toml: { $keys }[/green]
cli-config-migrate-conflicts = [yellow]Already set, not overwritten: { $keys }[/yellow]
cli-config-migrate-nothing = Nothing to migrate.
cli-config-migrate-source-kept = [dim]{ $path } was not modified: delete it once you have checked.[/dim]
assistant-describe-what-you-need = Describe what you need. /help for commands · /exit to quit
assistant-thinking = Thinking…
assistant-request-error = Request failed. Use --debug for details.
assistant-confirm-operation = Confirm this operation? [y/N]
assistant-help = Slash commands
    /help     Show this help
    /exit     Exit (also: exit, quit, q)
    /session  Show session ID
    /clear    Clear session messages
assistant-input = You ›
assistant-operation = Operation: { $name }
assistant-tool-running = Running · { $name }
assistant-incomplete = Incomplete response.
assistant-session = Session: { $session }
assistant-not-persisted = not persisted
assistant-cleared = Session messages cleared.
assistant-no-session = No persisted session to clear.
assistant-unknown-command = Unknown command: { $command }. Try /help.
assistant-turn-failed = Request not completed. Use --debug for details.
assistant-interrupted = Request interrupted. Operations already started may have taken effect: check their status before trying again.
assistant-missing-extra = Missing AI dependencies: reinstall OpenFatture with the ai extra.
assistant-tool-completed = Completed · { $name }
assistant-tool-failed = Not completed · { $name }
status-blocking-fields = Fields blocking invoicing
status-field = Field
status-problem = Problem
status-missing = Missing
status-invalid = Invalid
status-local-only = Checks describe local configuration. AI authentication and SDI delivery are not verified by this command.
cli-database-unavailable = Database unavailable. Check DATABASE_URL and permissions; use --debug for details.
assistant-reconciled = Verified outcome recorded. Use /resume to continue.
assistant-reconcile-invalid = Invalid reconciliation: call_id, result and evidence are required.
assistant-resolve-pending-first = Resolve the pending turn with /resume before clearing the history.
assistant-resuming = Resuming the interrupted turn…
assistant-uncertain-tool = Uncertain tool outcome: use /pending and /reconcile before /resume.
assistant-no-pending = No pending turn.

## Shared command output
cli-common-error = [red]Error:[/red] { $error }
## FATTURA Commands
cli-fattura-journal-submission = Submission #{ $id } · invoice { $invoice } · { $filename } · { $outcome }
cli-fattura-journal-receipt = Receipt #{ $id } · invoice { $invoice } · { $outcome } · source { $source }
cli-fattura-journal-empty = No SDI submissions or receipts recorded.
cli-fattura-associate-confirm = Associate receipt { $receipt } with invoice { $invoice }?
cli-fattura-receipt-associated = Receipt associated
cli-fattura-resolve-confirm = Confirm that submission { $attempt } { $sent ->
        [yes] was transmitted
       *[no] was not transmitted
    }?
cli-fattura-submission-resolved = Verification recorded

## CLIENTE Commands
## PAGAMENTO Commands
## INIT Command
cli-init-title = [bold blue]OpenFatture Setup[/bold blue]
cli-init-structured-needs-no-interactive = Use --no-interactive with a structured output format
cli-init-creating-dirs = [cyan]Creating directories...[/cyan]
cli-init-dirs-created = Data directories created
cli-init-initializing-db = [cyan]Initializing database...[/cyan]
cli-init-backup = Backup before upgrade: { $path }
cli-init-database = Database { $state ->
        [empty] created
        [current] up to date
        [outdated] upgraded
        [unversioned] adopted and upgraded
       *[other] { $state }
    }: { $url }
cli-init-configure-company = [bold yellow]Let's configure your company data[/bold yellow]
cli-init-overwrite-confirm = [yellow]An OpenFatture profile already exists. Overwrite company/AI settings?[/yellow]
cli-init-config-preserved = [green]Existing configuration preserved.[/green] Directories and database were still ensured.
cli-init-company-section = [bold]Company information (Cedente Prestatore)[/bold]
cli-init-prompt-name = Company or your name
cli-init-prompt-partita-iva = Partita IVA (11 digits)
cli-init-invalid-partita-iva = [red]Invalid Partita IVA. Please try again.[/red]
cli-init-prompt-codice-fiscale = Codice fiscale (16 characters)
cli-init-invalid-codice-fiscale = [red]Invalid codice fiscale. Please try again.[/red]
cli-init-prompt-regime = Tax regime (use your actual RF code)
cli-init-invalid-regime = [red]Enter a tax regime supported by FatturaPA.[/red]
cli-init-prompt-address = Address (street)
cli-init-prompt-cap = Postal code (CAP)
cli-init-prompt-city = City (Comune)
cli-init-prompt-province = Province (2 letters, e.g. RM)
cli-init-pec-section = [bold]PEC configuration[/bold]
cli-init-prompt-pec-address = Your PEC address
cli-init-prompt-pec-password = PEC password
cli-init-prompt-pec-smtp = PEC SMTP server
cli-init-notifications-section = [bold]Email notifications[/bold]
cli-init-prompt-notification-email = Email for notifications (SDI alerts, summaries)
cli-init-prompt-locale = Language (it/en/de/es/fr)
cli-init-ai-section = [bold]AI configuration (optional)[/bold]
cli-init-ai-description = [dim]Configure AI features: invoice descriptions, tax suggestions and the chat assistant.[/dim]
cli-init-ai-confirm = Configure AI features now? (You can also do this later with openfatture config)
cli-init-ai-provider = AI provider
cli-init-ai-skip = Skip for now
cli-init-api-key-from = [cyan]{ $provider } selected - get an API key from:[/cyan]
cli-init-ollama-selected = [cyan]Ollama selected - free local model![/cyan]
cli-init-ollama-install = Install: [bold]ollama pull { $model }[/bold]
cli-init-ollama-start = Start: [bold]ollama serve[/bold]
cli-init-prompt-api-key = API key (leave empty to set it later)
cli-init-config-saved = Configuration saved to: { $path }
cli-init-secrets-saved = Secrets saved to the { $backend ->
        [keyring] system keychain
       *[file] private credentials file
    }
cli-init-complete-title = Setup complete
cli-init-complete-body = [bold green]Setup finished[/bold green]

    Next steps:
      • Check readiness: [cyan]openfatture status[/cyan]
      • Review settings: [cyan]openfatture config show[/cyan]
      • Assistant (needs [cyan]uv sync --extra ai[/cyan]): [cyan]openfatture assistant "List the open invoices"[/cyan]
      • Help: [cyan]openfatture --help[/cyan]

## STATUS Command
cli-status-readiness = [bold]Readiness[/bold]  core: [cyan]{ $core ->
        [yes] ready
       *[no] not ready
    }[/cyan]  assistant: [cyan]{ $assistant ->
        [yes] configured
       *[no] not configured
    }[/cyan]
cli-status-title = OpenFatture status
cli-status-label-ai-api-key-configured = AI API key configured
cli-status-label-assistant-backend = Assistant backend
cli-status-label-assistant-backend-id = Assistant backend ID
cli-status-label-config-file = Config file
cli-status-label-secret-backend = Secret backend
cli-status-checks-title = Readiness checks
cli-status-column-check = Check
cli-status-yes = yes
cli-status-no = no
cli-status-next-steps = [bold]Next steps[/bold]
cli-status-extras-title = Optional extras (feature modules)
cli-status-column-extra = Extra
cli-status-column-installed = Installed
cli-status-extensions-title = Extensions
cli-status-column-mechanism = Mechanism
cli-status-column-detail = Detail
cli-status-hooks = hooks (supported)
cli-status-hooks-detail = { $path } ({ $count ->
        [one] 1 script
       *[other] { $count } scripts
    })
cli-status-plugins = in-process plugins

## Global
cli-main-version = [bold blue]OpenFatture[/bold blue] version { $version }
cli-output-unsupported-format = Supported formats: { $formats }

## Rich formatter
cli-formatter-error = [bold red]Error:[/bold red] { $error }
cli-formatter-unknown-error = Unknown error
cli-formatter-ai-response = [bold]AI Response[/bold]
cli-formatter-unknown = unknown
cli-formatter-provider = Provider: { $provider }
cli-formatter-model = Model: { $model }
cli-formatter-tokens = Tokens: { $tokens }
cli-formatter-cost = Cost: { $cost }
cli-formatter-latency = Latency: { $latency } ms

## Localized refusals of application services (error_code)
cli-error-receipt-not-associable = The receipt does not exist or is already associated.
cli-error-evidence-required = Verified evidence is required (--evidence).
cli-error-submission-not-found = Submission attempt not found.
cli-error-submission-already-resolved = The submission attempt is already resolved.
cli-error-sdi-evidence-contradicts = Recorded SDI evidence contradicts a "not sent" outcome.
cli-error-submission-concurrent-update = The attempt was resolved meanwhile: reload and retry.

## Command-line help
cli-help-app = Electronic invoicing with an assistant. Run openfatture to start a conversation.
cli-help-epilog = Examples: openfatture · openfatture assistant "Show unpaid invoices"
cli-help-version = Show the version and exit.
cli-help-debug = Show diagnostic logs and tracebacks.
cli-help-format = Output format: rich, json, markdown, stream-json, html
cli-help-panel-assistant = Assistant
cli-help-panel-setup = Setup and diagnostics
cli-help-panel-sdi = SDI checks
cli-help-assistant = Send a request or resume a session
cli-help-init = Initialize OpenFatture
cli-help-config = Manage the configuration
cli-help-status = Check configuration and readiness
cli-help-fattura = SDI journal and resolutions backed by manual evidence
cli-help-assistant-message = A request for the assistant.
cli-help-assistant-stream = Show the response while it is generated.
cli-help-assistant-json = Emit the response as JSON.
cli-help-assistant-session = Resume a saved session by its ID (enables persistence).
cli-help-init-interactive = Interactive setup wizard
cli-help-status-json = Emit the status as JSON.
cli-help-config-show =
    Show the effective configuration.

    For each value it shows the source: environment, keychain or credentials file, config.toml, default.
cli-help-config-reload = Reload the configuration from the environment, secret store and config.toml.
cli-help-config-set =
    Set a configuration value.

    Only KEY is written. Secrets (API keys, passwords) go to the OS keychain, or to the private credentials file when there is no keychain; other values go to config.toml. Nested keys use dots, e.g. debug_config.enable_debug_logging.
cli-help-config-unset = Remove KEY from config.toml or the secret store, restoring its default.
cli-help-config-migrate =
    Move plaintext secrets out of config.toml and optionally import a .env file.

    Secrets go to the OS keychain (or the private credentials file); other values from --env-file are added to config.toml only when not already set. The source file is never modified.
cli-help-config-env-file = Import settings from a dotenv file (existing values are kept).
cli-help-invoice-id = Invoice ID
cli-help-sdi-journal = Show recorded PEC submissions and SDI receipts, without sending anything.
cli-help-associate-receipt = Associate an unresolved receipt with an invoice, after a manual check.
cli-help-receipt-id = SDI receipt ID
cli-help-receipt-evidence = Verified evidence (e.g. a reference)
cli-help-resolve-submission = Resolve an uncertain PEC submission, after checking the transport outcome.
cli-help-attempt-id = Submission attempt ID
cli-help-resolve-sent = Verified outcome: sent or not sent
cli-help-resolve-evidence = Verified evidence (e.g. the provider reference)
cli-help-install-completion = Install completion for the current shell.
cli-help-show-completion = Show completion for the current shell, to copy it or customize the installation.
cli-help-help-option = Show this message and exit.
