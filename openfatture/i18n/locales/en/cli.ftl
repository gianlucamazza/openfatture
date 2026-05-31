# CLI commands translations
# EN

## MAIN CLI

### main - Main CLI
cli-main-title = OpenFatture - Open Source Electronic Invoicing System
cli-main-description = Complete system for managing FatturaPA electronic invoices
cli-main-version = Version { $version }

### main - Command Groups
cli-main-group-invoices = Invoice Management
cli-main-group-clients = Client Management
cli-main-group-products = Product Management
cli-main-group-pec = PEC & SDI
cli-main-group-batch = Batch Operations
cli-main-group-ai = AI Assistant
cli-main-group-payments = Payment Tracking
cli-main-group-preventivi = Quotes
cli-main-group-events = Event System
cli-main-group-lightning = Lightning Network
cli-main-group-web = Web Interface

## FATTURA Commands

### fattura - Help Texts
cli-fattura-help-numero = Invoice number
cli-fattura-help-cliente-id = Client ID
cli-fattura-help-invoice-id = Invoice ID
cli-fattura-help-anno = Year (default: current year)
cli-fattura-help-tipo-documento = Document type (TD01, TD04, TD06, etc.)
cli-fattura-help-data = Invoice date (YYYY-MM-DD)
cli-fattura-help-bollo = Revenue stamp (€ 2.00)
cli-fattura-help-xml-path = Path to XML file
cli-fattura-help-formato = Output format (table, json, yaml)
cli-fattura-help-all = Show all invoices, even old ones
cli-fattura-help-force = Skip confirmation
cli-fattura-help-output = Output path
cli-fattura-help-no-validate = Skip XSD validation
cli-fattura-help-pec = Send via PEC
cli-fattura-help-filter-status = Filter by status
cli-fattura-help-filter-anno = Filter by year
cli-fattura-help-limit = Maximum number of results

### fattura - Console Output
cli-fattura-create-title = [bold blue]Create New Invoice[/bold blue]
cli-fattura-select-client-title = [bold cyan]Client Selection[/bold cyan]
cli-fattura-no-clients-error = [red]No clients found. Add one first with 'cliente add'[/red]
cli-fattura-available-clients = [cyan]Available clients:[/cyan]
cli-fattura-client-prompt = Client number
cli-fattura-client-selected = [green]Client: { $client_name }[/green]
cli-fattura-invalid-client-error = [red]Invalid client selection[/red]

cli-fattura-add-lines-title = [bold cyan]Invoice Lines[/bold cyan]
cli-fattura-line-description-prompt = Description (empty to finish)
cli-fattura-line-quantity-prompt = Quantity
cli-fattura-line-unit-price-prompt = Unit price (€)
cli-fattura-line-vat-rate-prompt = VAT rate (%)
cli-fattura-line-added = [green]Line added: { $description } - € { $amount }[/green]

cli-fattura-payment-terms-title = [bold cyan]Payment Terms[/bold cyan]
cli-fattura-payment-condition-prompt = Payment condition (TP01=Payment due, TP02=Paid)
cli-fattura-payment-method-prompt = Payment method (MP05=Bank transfer, MP01=Cash, MP08=Credit card)
cli-fattura-payment-days-prompt = Payment terms (days)
cli-fattura-payment-date-prompt = Payment date (YYYY-MM-DD, empty=auto)
cli-fattura-payment-iban-prompt = IBAN (optional)

cli-fattura-summary-title = [bold yellow]Invoice Summary[/bold yellow]
cli-fattura-summary-client = Client: { $client_name }
cli-fattura-summary-lines = { $count } { $count ->
    [one] line
   *[other] lines
}
cli-fattura-summary-subtotal = Subtotal: € { $subtotal }
cli-fattura-summary-vat = VAT: € { $vat }
cli-fattura-summary-total = [bold]Total: € { $total }[/bold]
cli-fattura-summary-stamp = Revenue stamp: € { $stamp }

cli-fattura-confirm-prompt = [yellow]Confirm creation?[/yellow]
cli-fattura-created-success = [bold green]Invoice created successfully![/bold green]
cli-fattura-created-number = [green]Invoice number: { $numero }/{ $anno }[/green]
cli-fattura-created-xml = [green]XML saved: { $xml_path }[/green]

cli-fattura-list-title = [bold blue]Invoice List[/bold blue]
cli-fattura-list-empty = [yellow]No invoices found[/yellow]

cli-fattura-show-title = [bold blue]Invoice { $numero }/{ $anno }[/bold blue]
cli-fattura-show-not-found = [red]Invoice not found: { $numero }/{ $anno }[/red]

cli-fattura-invoice-not-found = [red]Invoice { $invoice_id } not found[/red]
cli-fattura-delete-confirm = [yellow]Delete invoice { $numero }/{ $anno }?[/yellow]
cli-fattura-delete-warning = [red]WARNING: This operation cannot be undone[/red]
cli-fattura-delete-status-restriction = [red]Cannot delete invoice in status '{ $status }'[/red]
cli-fattura-delete-success = [green]Invoice { $numero }/{ $anno } deleted[/green]
cli-fattura-delete-cancelled = [yellow]Operation cancelled[/yellow]
cli-fattura-cancelled = Cancelled.
cli-fattura-delete-cannot-delete-sent = [red]Cannot delete invoices in INVIATA or CONSEGNATA state[/red]

cli-fattura-xml-generation-title = [bold blue]Generating FatturaPA XML[/bold blue]
cli-fattura-generating-xml = Generating XML for invoice { $numero }/{ $anno }...
cli-fattura-xml-generation-error = [red]Error: { $error }[/red]
cli-fattura-xml-schema-hint = [yellow]Hint: Download the XSD schema from:[/yellow]
cli-fattura-xml-schema-url = https://www.fatturapa.gov.it/export/documenti/fatturapa/v1.2.2/Schema_del_file_xml_FatturaPA_v1.2.2.xsd
cli-fattura-xml-schema-save-path = And save it to: { $path }
cli-fattura-xml-saved = [green]XML saved to: { $path }[/green]
cli-fattura-xml-generated = [green]XML generated successfully![/green]
cli-fattura-xml-path = Path: { $path }
cli-fattura-xml-preview = [dim]Preview (first 500 chars):[/dim]

cli-fattura-validate-success = [green]XML is valid[/green]
cli-fattura-validate-error = [red]Validation errors found:[/red]

cli-fattura-send-title = [bold blue]Sending Invoice to SDI[/bold blue]
cli-fattura-send-step1-xml = [cyan]1. Generating XML...[/cyan]
cli-fattura-send-step2-signature = [cyan]2. Digital signature...[/cyan]
cli-fattura-send-step3-pec = [cyan]3. Sending via PEC with professional email template...[/cyan]
cli-fattura-send-xml-failed = [red]XML generation failed: { $error }[/red]
cli-fattura-send-xml-success = [green]XML generated[/green]
cli-fattura-send-signature-not-implemented = [yellow]Digital signature not yet implemented[/yellow]
cli-fattura-send-signature-manual-hint = [dim]For now, you can sign manually with external tools.[/dim]
cli-fattura-send-confirm = Send invoice to SDI now?
cli-fattura-send-cancelled = [yellow]Cancelled. Use 'openfatture fattura invia' later to send.[/yellow]
cli-fattura-sent-successfully = [green]Invoice sent to SDI via PEC with professional template[/green]
cli-fattura-sent-success-message = [bold green]Invoice { $numero }/{ $anno } sent successfully![/bold green]
cli-fattura-sent-email-details = [dim]Professional email sent to SDI with:[/dim]
cli-fattura-sent-email-format = • HTML + plain text format
cli-fattura-sent-email-branding = • Company branding ({ $color })
cli-fattura-sent-email-language = • Language: { $language }
cli-fattura-sent-notifications-header = [dim]Automatic notifications:[/dim]
cli-fattura-sent-notifications-enabled = • SDI responses will be emailed to: { $email }
cli-fattura-sent-notifications-process-cmd = • Process notifications with: [cyan]openfatture notifiche process <file>[/cyan]
cli-fattura-sent-notifications-disabled = • Enable with: NOTIFICATION_EMAIL in .env
cli-fattura-sent-monitor-pec = [dim]Monitor your PEC inbox for SDI notifications.[/dim]
cli-fattura-send-failed = [red]Failed to send: { $error }[/red]
cli-fattura-send-manual-steps = [yellow]Manual steps:[/yellow]
cli-fattura-send-manual-step1 = 1. XML saved at: { $path }
cli-fattura-send-manual-step2 = 2. Sign if needed, then send to: { $sdi_address }

cli-fattura-table-id = ID
cli-fattura-table-numero = No.
cli-fattura-table-number = Number
cli-fattura-table-date = Date
cli-fattura-table-data = Date
cli-fattura-table-cliente = Client
cli-fattura-table-client = Client
cli-fattura-table-importo = Amount
cli-fattura-table-imponibile = Taxable
cli-fattura-table-stato = Status
cli-fattura-table-status = Status
cli-fattura-table-tipo = Type
cli-fattura-table-type = Type
cli-fattura-table-pagamento = Payment
cli-fattura-table-iva = VAT
cli-fattura-table-total = Total
cli-fattura-table-totale = Total
cli-fattura-table-bollo = Stamp
cli-fattura-table-ritenuta = Withholding
cli-fattura-table-descrizione = Description
cli-fattura-table-description = Description
cli-fattura-table-quantita = Qty
cli-fattura-table-qty = Qty
cli-fattura-table-prezzo = Price
cli-fattura-table-price = Price
cli-fattura-table-unit-price = Unit Price
cli-fattura-table-aliquota = Rate
cli-fattura-table-vat-percent = VAT %
cli-fattura-table-importo-riga = Amount
cli-fattura-table-row-number = #
cli-fattura-table-field = Field
cli-fattura-table-value = Value
cli-fattura-table-sdi-number = SDI Number
cli-fattura-table-title-list = Invoices ({ $count })
cli-fattura-line-items-header = Line Items
cli-fattura-totals-header = Totals
cli-fattura-invalid-status = [red]Invalid status: { $status }[/red]
cli-fattura-prompt-select-client = Select client

## CLIENTE Commands

### cliente - Help Texts
cli-cliente-help-id = Client ID
cli-cliente-help-name = Client name/company name (omit to be prompted in --interactive mode)
cli-cliente-help-denominazione = Company name or full name
cli-cliente-help-piva = VAT number (Partita IVA)
cli-cliente-help-partita-iva = VAT number
cli-cliente-help-cf = Tax code (Codice Fiscale)
cli-cliente-help-codice-fiscale = Fiscal code
cli-cliente-help-sdi = SDI code
cli-cliente-help-pec = PEC address
cli-cliente-help-codice-destinatario = SDI destination code
cli-cliente-help-interactive = Interactive mode
cli-cliente-help-formato = Output format (table, json, yaml)
cli-cliente-help-search = Search term
cli-cliente-help-limite = Maximum number of results
cli-cliente-help-limit = Maximum number of results
cli-cliente-help-cliente-id = Client ID
cli-cliente-help-force = Skip confirmation

### cliente - Console Output
cli-cliente-name-required = [red]Error: Client name is required[/red]
cli-cliente-no-clients = [yellow]No clients found. Add one with 'cliente add'[/yellow]
cli-cliente-list-title = Clients ({ $count })
cli-cliente-list-empty = [yellow]No clients found[/yellow]
cli-cliente-added-success = [green]Client added successfully (ID: { $id })[/green]
cli-cliente-updated-success = [green]Client updated successfully[/green]
cli-cliente-deleted-success = [green]Client deleted successfully[/green]
cli-cliente-deleted = [green]Client '{ $name }' deleted[/green]
cli-cliente-cancelled = Cancelled.
cli-cliente-not-found = [red]Client not found: { $id }[/red]
cli-cliente-has-invoices = [yellow]Warning: This client has { $count } { $count ->
    [one] invoice
   *[other] invoices
}[/yellow]
cli-cliente-cannot-delete = [red]Cannot delete client with invoices[/red]
cli-cliente-delete-confirm = [yellow]Delete client { $denominazione }?[/yellow]

### cliente - Prompts
cli-cliente-prompt-denominazione = Company name
cli-cliente-prompt-partita-iva = VAT number
cli-cliente-prompt-codice-fiscale = Fiscal code
cli-cliente-prompt-indirizzo = Address
cli-cliente-prompt-cap = Postal code
cli-cliente-prompt-comune = City
cli-cliente-prompt-provincia = Province
cli-cliente-prompt-nazione = Country
cli-cliente-prompt-pec = PEC address
cli-cliente-prompt-codice-destinatario = SDI destination code
cli-cliente-prompt-email = Email
cli-cliente-prompt-telefono = Phone
cli-cliente-prompt-regime-fiscale = Tax regime (RF01, RF19, etc.)

### cliente - Table Labels
cli-cliente-table-id = ID
cli-cliente-table-denominazione = Name
cli-cliente-table-partita-iva = VAT
cli-cliente-table-codice-fiscale = Fiscal Code
cli-cliente-table-comune = City
cli-cliente-table-provincia = Province
cli-cliente-table-pec = PEC
cli-cliente-table-codice-destinatario = SDI Code
cli-cliente-table-fatture = Invoices
cli-cliente-table-indirizzo = Address
cli-cliente-table-cap = ZIP
cli-cliente-table-nazione = Country
cli-cliente-table-email = Email

cli-cliente-column-id = ID
cli-cliente-column-name = Name
cli-cliente-column-piva = VAT No.
cli-cliente-column-sdi-pec = SDI/PEC
cli-cliente-column-invoices = Invoices

cli-cliente-label-id = ID
cli-cliente-label-name = Name
cli-cliente-label-piva = VAT Number
cli-cliente-label-cf = Fiscal Code
cli-cliente-label-address = Address
cli-cliente-label-sdi = SDI Code
cli-cliente-label-pec = PEC
cli-cliente-label-email = Email
cli-cliente-label-phone = Phone
cli-cliente-label-total-invoices = Total Invoices
cli-cliente-label-created = Created

cli-cliente-show-title = [bold blue]Client Details: { $name }[/bold blue]
cli-cliente-prompt-civic-number = Civic number (optional)
cli-cliente-prompt-pec-address = PEC address (if SDI is 0000000)
cli-cliente-confirm-delete = Are you sure you want to delete?
cli-cliente-confirm-delete-client = Delete client '{ $name }'?

## ============================================================================
## Batch Commands - Batch Operations
## ============================================================================

### batch - Help Text
cli-batch-help-csv-file = Path to CSV file with invoices
cli-batch-help-dry-run = Validate without importing
cli-batch-help-send-summary = Send summary via email
cli-batch-help-output-file = Output CSV file path
cli-batch-help-anno = Filter by year
cli-batch-help-stato = Filter by status
cli-batch-help-limit = Maximum number of results

### batch - Console Output (import)
cli-batch-import-title = [bold blue]Batch Invoice Import[/bold blue]
cli-batch-file-not-found = [red]File not found: { $file }[/red]
cli-batch-file-info-name = [cyan]File:[/cyan] { $name }
cli-batch-file-info-size = [cyan]Size:[/cyan] { $size } bytes
cli-batch-mode-dry-run = [cyan]Mode:[/cyan] Dry run (validation only)
cli-batch-mode-import = [cyan]Mode:[/cyan] Import
cli-batch-dry-run-warning = [yellow]Dry run mode - no data will be saved[/yellow]
cli-batch-warning-dry-run = [yellow]Dry run mode - no data will be saved[/yellow]

cli-batch-results-title = [bold]Import Results:[/bold]
cli-batch-metric-total = Total rows
cli-batch-metric-processed = Processed
cli-batch-metric-succeeded = Succeeded
cli-batch-metric-failed = Failed
cli-batch-metric-success-rate = Success rate
cli-batch-metric-duration = Duration
cli-batch-metric-label = Metric
cli-batch-metric-value = Value

cli-batch-errors-title = [bold red]Errors:[/bold red]
cli-batch-errors-more = [dim]... and { $count } more errors[/dim]

cli-batch-success-all = [bold green]All invoices imported successfully![/bold green]
cli-batch-warning-failed = [yellow]{ $count } invoices not imported[/yellow]

cli-batch-email-not-configured = [yellow]Email notification not configured.[/yellow]
cli-batch-sending-email = [dim]Sending summary email...[/dim]
cli-batch-email-sending = [dim]Sending summary email...[/dim]
cli-batch-email-sent = [dim]Summary sent to { $email }[/dim]
cli-batch-email-failed = [yellow]Failed to send summary: { $error }[/yellow]

cli-batch-error-general = [red]Error: { $error }[/red]

### batch - Console Output (export)
cli-batch-export-title = [bold blue]Batch Invoice Export[/bold blue]
cli-batch-filter-year = [cyan]Filter:[/cyan] Year = { $anno }
cli-batch-filter-status = [cyan]Filter:[/cyan] Status = { $stato }
cli-batch-invalid-status = [red]Invalid status: { $stato }[/red]
cli-batch-no-invoices = [yellow]No invoices found[/yellow]
cli-batch-invoices-count = [cyan]Invoices:[/cyan] { $count }

cli-batch-export-success = [bold green]Exported { $count } invoices![/bold green]
cli-batch-export-file-path = [cyan]File:[/cyan] { $path }
cli-batch-export-file = [cyan]File:[/cyan] { $path }
cli-batch-export-file-size = [cyan]Size:[/cyan] { $size } bytes
cli-batch-export-size = [cyan]Size:[/cyan] { $size } bytes
cli-batch-export-failed = [red]Export failed[/red]

### batch - Console Output (history)
cli-batch-history-title = [bold blue]Batch Operations History[/bold blue]
cli-batch-history-not-implemented = [yellow]History tracking not fully implemented yet[/yellow]
cli-batch-history-future-features = [dim]In production, will show:[/dim]
cli-batch-history-will-show = [dim]In production, will show:[/dim]
cli-batch-history-feature-datetime = • Operation date/time
cli-batch-history-feature-type = • Type (import/export)
cli-batch-history-feature-records = • Records processed
cli-batch-history-feature-counts = • Success/failure counts
cli-batch-history-feature-errors = • Error summaries

cli-batch-history-example-title = [bold]Example history:[/bold]
cli-batch-history-example = [bold]Example history:[/bold]
cli-batch-history-column-date = Date
cli-batch-history-col-date = Date
cli-batch-history-column-type = Type
cli-batch-history-col-type = Type
cli-batch-history-column-records = Records
cli-batch-history-col-records = Records
cli-batch-history-column-success = Success
cli-batch-history-col-success = Success
cli-batch-history-column-failed = Failed
cli-batch-history-col-failed = Failed

cli-batch-history-todo = [dim]TODO: Add BatchOperation model to database[/dim]

## ============================================================================
## Preventivo Commands - Quote Management
## ============================================================================

### preventivo - Help Text
cli-preventivo-help-cliente-id = Client ID
cli-preventivo-help-validita = Validity period in days
cli-preventivo-help-stato = Filter by status
cli-preventivo-help-anno = Filter by year
cli-preventivo-help-cliente = Filter by client ID
cli-preventivo-help-limit = Maximum number of results
cli-preventivo-help-preventivo-id = Quote ID
cli-preventivo-help-force = Skip confirmation
cli-preventivo-help-tipo-documento = Invoice document type (TD01, TD06, etc.)
cli-preventivo-help-new-stato = New status (draft, sent, accepted, rejected, expired)

### preventivo - Console Output (crea)
cli-preventivo-create-title = [bold blue]Create New Quote[/bold blue]
cli-preventivo-no-clients = [red]No clients found. Add a client first with 'openfatture cliente add'[/red]
cli-preventivo-select-client = [cyan]Available clients:[/cyan]
cli-preventivo-client-id-prompt = Select client ID
cli-preventivo-client-not-found = [red]Client { $id } not found[/red]
cli-preventivo-client-selected = [green]Client: { $name }[/green]
cli-preventivo-validity-info = [dim]Validity: { $days } days (expiration: { $date })[/dim]

cli-preventivo-add-items-title = [bold]Add line items[/bold]
cli-preventivo-add-items-hint = [dim]Enter empty description to finish[/dim]
cli-preventivo-item-description-prompt = Item description { $num }
cli-preventivo-item-quantity-prompt = Quantity
cli-preventivo-item-price-prompt = Unit price (€)
cli-preventivo-item-vat-prompt = VAT rate (%)
cli-preventivo-item-unit-prompt = Unit of measure
cli-preventivo-item-added = [green]Added: { $desc } - €{ $total }[/green]

cli-preventivo-no-items = [yellow]No line items added. Quote creation cancelled.[/yellow]
cli-preventivo-add-notes-prompt = Add notes?
cli-preventivo-notes-prompt = Notes
cli-preventivo-add-conditions-prompt = Add terms and conditions?
cli-preventivo-conditions-prompt = Terms and conditions

cli-preventivo-error-general = [red]Error: { $error }[/red]
cli-preventivo-created-success = [bold green]Quote created successfully![/bold green]
cli-preventivo-next-convert = [dim]Next: openfatture preventivo converti { $id } (to create invoice)[/dim]

### preventivo - Console Output (lista)
cli-preventivo-invalid-status = [red]Invalid status: { $stato }[/red]
cli-preventivo-valid-statuses = Valid: { $statuses }
cli-preventivo-no-preventivi = [yellow]No quotes found[/yellow]
cli-preventivo-list-title = Quotes ({ $count })

cli-preventivo-column-id = ID
cli-preventivo-column-number = Number
cli-preventivo-column-date = Date
cli-preventivo-column-expiration = Expiration
cli-preventivo-column-client = Client
cli-preventivo-column-total = Total
cli-preventivo-column-status = Status

### preventivo - Console Output (show)
cli-preventivo-not-found = [red]Quote { $id } not found[/red]
cli-preventivo-show-title = [bold blue]Quote { $numero }/{ $anno }[/bold blue]

cli-preventivo-field-client = Client
cli-preventivo-field-issue-date = Issue date
cli-preventivo-field-expiration = Expiration date
cli-preventivo-field-validity = Validity
cli-preventivo-field-validity-days = { $days } days
cli-preventivo-field-status = Status
cli-preventivo-warning-expired = [red]WARNING[/red]
cli-preventivo-expired = [red]Expired![/red]

cli-preventivo-line-items-title = [bold]Line Items:[/bold]
cli-preventivo-line-item-number = #
cli-preventivo-line-item-description = Description
cli-preventivo-line-item-quantity = Qty
cli-preventivo-line-item-price = Price
cli-preventivo-line-item-vat = VAT%
cli-preventivo-line-item-total = Total

cli-preventivo-totals-title = [bold]Totals:[/bold]
cli-preventivo-total-imponibile = Taxable amount
cli-preventivo-total-iva = VAT
cli-preventivo-total-total = [bold]TOTAL[/bold]

cli-preventivo-notes-title = [bold]Notes:[/bold]
cli-preventivo-conditions-title = [bold]Terms and Conditions:[/bold]

### preventivo - Console Output (delete)
cli-preventivo-confirm-delete = Delete quote { $numero }/{ $anno }?
cli-preventivo-cancelled = Cancelled.
cli-preventivo-deleted = [green]Quote { $numero }/{ $anno } deleted[/green]

### preventivo - Console Output (converti)
cli-preventivo-convert-title = [bold blue]Converting Quote to Invoice[/bold blue]
cli-preventivo-convert-summary-numero = [cyan]Quote: { $numero }/{ $anno }[/cyan]
cli-preventivo-convert-summary-client = [cyan]Client: { $name }[/cyan]
cli-preventivo-convert-summary-total = [cyan]Total: €{ $total }[/cyan]
cli-preventivo-invalid-doc-type = [red]Invalid document type: { $tipo }[/red]
cli-preventivo-valid-doc-types = Valid: TD01, TD06, etc.
cli-preventivo-confirm-convert = Convert to invoice?
cli-preventivo-convert-cancelled = [yellow]Cancelled.[/yellow]
cli-preventivo-converted-success = [bold green]Quote converted successfully![/bold green]

cli-preventivo-invoice-title = Invoice { $numero }/{ $anno }
cli-preventivo-invoice-field-client = Client
cli-preventivo-invoice-field-date = Date
cli-preventivo-invoice-field-doc-type = Document type
cli-preventivo-invoice-field-items = Items
cli-preventivo-invoice-field-imponibile = Taxable amount
cli-preventivo-invoice-field-iva = VAT
cli-preventivo-invoice-field-total = [bold]TOTAL[/bold]

cli-preventivo-invoice-id-info = [dim]Invoice ID: { $id }[/dim]
cli-preventivo-original-preventivo-info = [dim]Original quote: { $numero }/{ $anno } (ID: { $id })[/dim]
cli-preventivo-next-send = [dim]Next: openfatture fattura invia { $id } --pec[/dim]

### preventivo - Console Output (aggiorna-stato)
cli-preventivo-status-updated = [green]Quote status updated: { $stato }[/green]

## AI Commands

### ai - Help Texts
cli-ai-help-text = Text to process
cli-ai-help-invoice-id = Invoice ID
cli-ai-help-provider = AI provider (openai, anthropic, ollama)
cli-ai-help-model = AI model name
cli-ai-help-temperature = Temperature (0.0-2.0)
cli-ai-help-max-tokens = Maximum tokens
cli-ai-help-interactive = Interactive mode
cli-ai-help-session-id = Chat session ID
cli-ai-help-stream = Enable streaming
cli-ai-help-save-session = Save session after chat
cli-ai-help-list-sessions = List available sessions
cli-ai-help-months = Number of months to forecast
cli-ai-help-confidence = Confidence level (0.0-1.0)
cli-ai-help-retrain = Retrain model with latest data
cli-ai-help-show-metrics = Show model metrics
cli-ai-help-invoice-numero = Invoice number
cli-ai-help-year = Invoice year
cli-ai-help-context = Additional context
cli-ai-help-language = Language code
cli-ai-help-format = Output format
cli-ai-help-embedding-model = Embedding model
cli-ai-help-chunk-size = Chunk size for documents
cli-ai-help-collection = RAG collection name
cli-ai-help-query = Search query
cli-ai-help-top-k = Number of results
cli-ai-help-rating = Rating (1-5)
cli-ai-help-comment = Comment text
cli-ai-help-duration = Recording duration in seconds
cli-ai-help-save-audio = Save audio files for debugging
cli-ai-help-no-playback = Disable audio playback
cli-ai-help-sample-rate = Audio sample rate
cli-ai-help-service-description = Service description to expand
cli-ai-help-hours-worked = Hours worked
cli-ai-help-hourly-rate = Hourly rate (€)
cli-ai-help-project-name = Project name
cli-ai-help-technologies = Technologies used (comma-separated)
cli-ai-help-json-output = JSON output format
cli-ai-help-stream = Real-time response streaming
cli-ai-help-client-pa = Client is Public Administration
cli-ai-help-client-foreign = Foreign client (outside Italy)
cli-ai-help-country-code = Client country code (IT, FR, DE, etc.)
cli-ai-help-service-category = Service category
cli-ai-help-amount-eur = Amount in euros
cli-ai-help-ateco-code = ATECO code
cli-ai-help-chat-message = Message to send to chat

### ai - Console Output (describe)
cli-ai-describe-title = [bold cyan]AI Invoice Description Generation[/bold cyan]
cli-ai-describe-input-prompt = [cyan]Enter brief description:[/cyan]
cli-ai-describe-processing = [yellow]Processing with AI...[/yellow]
cli-ai-describe-result-title = [bold green]Generated Description:[/bold green]
cli-ai-describe-result-text = [white]{ $text }[/white]
cli-ai-describe-copy-hint = [dim]You can copy this description when creating an invoice[/dim]
cli-ai-describe-error = [red]Error generating description: { $error }[/red]
cli-ai-describe-activity = Activity: [yellow]{ $activity }[/yellow]
cli-ai-describe-generating = Generating detailed description...
cli-ai-describe-input-service = Service
cli-ai-describe-input-hours = Hours worked
cli-ai-describe-input-rate = Hourly rate
cli-ai-describe-input-project = Project
cli-ai-describe-input-technologies = Technologies
cli-ai-describe-input-client-pa = PA client
cli-ai-describe-input-client-foreign = Foreign client
cli-ai-describe-input-country = Country
cli-ai-describe-input-category = Category
cli-ai-describe-input-amount = Amount
cli-ai-describe-input-ateco = ATECO code

### ai - Console Output (suggest-vat)
cli-ai-vat-title = [bold cyan]VAT Rate Suggestion with AI[/bold cyan]
cli-ai-vat-input-prompt = [cyan]Service/product description:[/cyan]
cli-ai-vat-processing = [yellow]Analyzing with AI...[/yellow]
cli-ai-vat-result-title = [bold green]Suggested VAT Rate:[/bold green]
cli-ai-vat-rate = [white]{ $rate }%[/white]
cli-ai-vat-reasoning-title = [bold yellow]Reasoning:[/bold yellow]
cli-ai-vat-reasoning-text = [white]{ $reasoning }[/white]
cli-ai-vat-warning = [yellow]Always verify with a tax advisor for complex cases[/yellow]
cli-ai-vat-error = [red]Error suggesting VAT rate: { $error }[/red]
cli-ai-vat-query = Query: [yellow]{ $query }[/yellow]
cli-ai-vat-analyzing = Analyzing VAT regulations...
cli-ai-vat-disclaimer = [yellow]This is a suggestion. Always consult an accountant.[/yellow]
cli-ai-vat-processing = Processing VAT suggestion...
cli-ai-vat-input-service = Service
cli-ai-vat-input-client-pa = PA client
cli-ai-vat-input-client-foreign = Foreign client
cli-ai-input-country = Country
cli-ai-vat-input-category = Category
cli-ai-vat-input-amount = Amount
cli-ai-vat-input-ateco = ATECO code
cli-ai-vat-result-rate = Recommended VAT rate
cli-ai-vat-result-nature = Nature (if applicable)
cli-ai-vat-result-reasoning = Rationale
cli-ai-vat-result-legal-ref = Legal reference
cli-ai-vat-result-confidence = Confidence level
cli-ai-vat-result-warnings = Warnings
cli-ai-vat-result-note = Additional note

### ai - Console Output (chat)
cli-ai-chat-title = [bold cyan]Chat Vocale AI[/bold cyan]
cli-ai-chat-welcome = [cyan]Welcome to OpenFatture AI Assistant![/cyan]
cli-ai-chat-welcome-help = [dim]Type your questions or 'exit' to quit[/dim]
cli-ai-chat-session-loaded = [green]Session loaded: { $session_id }[/green]
cli-ai-chat-session-created = [green]New session created: { $session_id }[/green]
cli-ai-chat-prompt = [bold cyan]You:[/bold cyan]
cli-ai-chat-assistant-prefix = [bold green]Assistant:[/bold green]
cli-ai-chat-thinking = [yellow]Thinking...[/yellow]
cli-ai-chat-tool-calling = [yellow]Executing tool: { $tool_name }[/yellow]
cli-ai-chat-tool-result = [dim]Tool result: { $result }[/dim]
cli-ai-chat-session-saved = [green]Session saved[/green]
cli-ai-chat-goodbye = [cyan]Goodbye! Session saved.[/cyan]
cli-ai-chat-error = [red]Error: { $error }[/red]
cli-ai-chat-cost-info = [dim]Tokens: { $tokens } | Cost: €{ $cost }[/dim]
cli-ai-chat-assistant-response = [bold cyan]Assistant:[/bold cyan]
cli-ai-chat-you = [bold green]You:[/bold green]
cli-ai-chat-instructions = Instructions: Ask questions about invoices, clients, VAT, or tax management
cli-ai-chat-invalid-session = [red]Session not found: { $session_id }[/red]
cli-ai-chat-no-sessions = [yellow]No sessions available[/yellow]
cli-ai-chat-exported = [green]Conversation exported: { $path }[/green]
cli-ai-chat-export-error = [red]Export error: { $error }[/red]

### AI Metrics
cli-ai-metrics-provider = Provider
cli-ai-metrics-model = Model
cli-ai-metrics-tokens = Tokens used
cli-ai-metrics-cost = Estimated cost
cli-ai-metrics-latency = Latency

### General AI Errors
cli-ai-error-unknown = Unknown error during AI command execution
cli-ai-error-provider-init = AI provider initialization error: { $error }
cli-ai-error-context-load = Business context loading error: { $error }

### ai - Console Output (voice-chat)
cli-ai-voice-title = [bold cyan]AI Voice Chat[/bold cyan]
cli-ai-voice-welcome = [cyan]Welcome to Voice Chat![/cyan]
cli-ai-voice-recording-prompt = [yellow]Press ENTER to start recording ({ $duration }s)...[/yellow]
cli-ai-voice-recording = [bold yellow]Recording...[/bold yellow]
cli-ai-voice-processing = [yellow]Processing audio...[/yellow]
cli-ai-voice-transcription-title = [bold green]You said:[/bold green]
cli-ai-voice-transcription-text = [white]{ $text }[/white]
cli-ai-voice-language-detected = [dim]Language: { $language }[/dim]
cli-ai-voice-thinking = [yellow]Assistant thinking...[/yellow]
cli-ai-voice-response-title = [bold green]Assistant:[/bold green]
cli-ai-voice-response-text = [white]{ $text }[/white]
cli-ai-voice-playing = [cyan]Playing response...[/cyan]
cli-ai-voice-audio-saved = [dim]Audio saved: { $path }[/dim]
cli-ai-voice-goodbye = [cyan]Goodbye![/cyan]
cli-ai-voice-error = [red]Error: { $error }[/red]

### ai - Console Output (forecast)
cli-ai-forecast-title = [bold cyan]Cash Flow Forecasting with AI[/bold cyan]
cli-ai-forecast-loading-data = [yellow]Loading historical data...[/yellow]
cli-ai-forecast-data-stats = [cyan]Invoices: { $invoices } | Payments: { $payments }[/cyan]
cli-ai-forecast-training = [yellow]Training ML models...[/yellow]
cli-ai-forecast-training-progress = [yellow]{ $progress }%[/yellow]
cli-ai-forecast-predicting = [yellow]Generating forecast...[/yellow]
cli-ai-forecast-results-title = [bold green]Cash Flow Forecast - Next { $months } { $months ->
    [one] month
   *[other] months
}[/bold green]
cli-ai-forecast-month = [cyan]{ $month }[/cyan]
cli-ai-forecast-predicted = Predicted: € { $amount }
cli-ai-forecast-confidence = Confidence: { $confidence }%
cli-ai-forecast-lower-bound = Lower bound: € { $lower }
cli-ai-forecast-upper-bound = Upper bound: € { $upper }
cli-ai-forecast-metrics-title = [bold yellow]Model Metrics:[/bold yellow]
cli-ai-forecast-mae = MAE: { $mae }
cli-ai-forecast-rmse = RMSE: { $rmse }
cli-ai-forecast-mape = MAPE: { $mape }%
cli-ai-forecast-insufficient-data = [yellow]Insufficient data. Need at least { $required } invoices/payments for training.[/yellow]
cli-ai-forecast-error = [red]Forecasting error: { $error }[/red]

### ai - Console Output (intelligence)
cli-ai-intelligence-title = [bold cyan]Business Intelligence Analysis[/bold cyan]
cli-ai-intelligence-analyzing = [yellow]Analyzing business data...[/yellow]
cli-ai-intelligence-report-title = [bold green]Business Insights:[/bold green]
cli-ai-intelligence-section = [bold yellow]{ $section }[/bold yellow]
cli-ai-intelligence-insight = • { $insight }
cli-ai-intelligence-error = [red]Analysis error: { $error }[/red]

### ai - Console Output (compliance)
cli-ai-compliance-title = [bold cyan]Compliance Verification[/bold cyan]
cli-ai-compliance-checking = [yellow]Checking invoice { $numero }/{ $anno }...[/yellow]
cli-ai-compliance-passed = [bold green]All compliance checks passed[/bold green]
cli-ai-compliance-warnings = [yellow]{ $count } { $count ->
    [one] warning found
   *[other] warnings found
}[/yellow]
cli-ai-compliance-errors = [red]{ $count } { $count ->
    [one] error found
   *[other] errors found
}[/red]
cli-ai-compliance-check-item = [{ $status }] { $message }
cli-ai-compliance-error = [red]Compliance check error: { $error }[/red]

### ai - Console Output (rag)
cli-ai-rag-title = [bold cyan]RAG Document Search[/bold cyan]
cli-ai-rag-indexing = [yellow]Indexing documents...[/yellow]
cli-ai-rag-indexed = [green]{ $count } { $count ->
    [one] document indexed
   *[other] documents indexed
}[/green]
cli-ai-rag-searching = [yellow]Searching knowledge base...[/yellow]
cli-ai-rag-results-title = [bold green]Search Results:[/bold green]
cli-ai-rag-result-item = { $rank }. [bold]{ $title }[/bold] (score: { $score })
cli-ai-rag-result-text = { $text }
cli-ai-rag-no-results = [yellow]No results found[/yellow]
cli-ai-rag-error = [red]RAG error: { $error }[/red]

### ai - Console Output (feedback)
cli-ai-feedback-title = [bold cyan]AI Feedback[/bold cyan]
cli-ai-feedback-prompt-rating = [cyan]Rate response (1-5):[/cyan]
cli-ai-feedback-prompt-comment = [cyan]Comment (optional):[/cyan]
cli-ai-feedback-thanks = [green]Thank you for your feedback![/green]
cli-ai-feedback-saved = [green]Feedback saved to session { $session_id }[/green]
cli-ai-feedback-error = [red]Feedback error: { $error }[/red]

## ============================================================================
## EVENTS Commands - Event History and Audit Trail
## ============================================================================

### Help Texts - Commands and Options
cli-events-help = View and analyze event history

# list command
cli-events-list-help-type = Filter by event type
cli-events-list-help-entity = Filter by entity type (invoice, client, payment, etc.)
cli-events-list-help-entity-id = Filter by entity ID
cli-events-list-help-last-hours = Show events from last N hours
cli-events-list-help-last-days = Show events from last N days
cli-events-list-help-limit = Maximum number of events to show

# show command
cli-events-show-help-event-id = Event ID (UUID)

# stats command
cli-events-stats-help-last-hours = Stats for last N hours
cli-events-stats-help-last-days = Stats for last N days

# timeline command
cli-events-timeline-help-entity-type = Entity type (invoice, client, etc.)
cli-events-timeline-help-entity-id = Entity ID

# search command
cli-events-search-help-query = Search query string
cli-events-search-help-limit = Maximum number of results

# dashboard command
cli-events-dashboard-help-days = Number of days to analyze

# trends command
cli-events-trends-help-days = Number of days to analyze
cli-events-trends-help-type = Filter by event type

### Table Columns - Column Headers
cli-events-column-timestamp = Timestamp
cli-events-column-event-type = Event Type
cli-events-column-entity = Entity
cli-events-column-entity-type = Entity Type
cli-events-column-summary = Summary
cli-events-column-count = Count
cli-events-column-percentage = Percentage
cli-events-column-match = Match

### Titles and Headers - Titles and Headers
cli-events-list-title = Event History ({ $count } events)
cli-events-show-panel-title = [bold]Event Details: { $event_type }[/bold]
cli-events-stats-table-by-type = Events by Type
cli-events-stats-table-by-entity = Events by Entity Type
cli-events-stats-panel-title = [bold]Event Statistics - { $range }[/bold]
cli-events-timeline-panel-title = [bold]Event Timeline: { $entity_type } #{ $entity_id }[/bold]
cli-events-search-results-title = Search Results: '{ $query }' ({ $count } events)
cli-events-types-table-title = Available Event Types
cli-events-dashboard-panel-title = [bold]Event Analytics Dashboard - Last { $days } Days[/bold]
cli-events-dashboard-table-entity-activity = Entity Activity
cli-events-trends-panel-title = [bold]Event Trends - Last { $days } Days[/bold]
cli-events-trends-panel-title-filtered = [bold]Event Trends - Last { $days } Days ({ $event_type })[/bold]

### Labels - Field Labels
cli-events-show-label-event-id = Event ID
cli-events-show-label-event-type = Event Type
cli-events-show-label-occurred-at = Occurred At
cli-events-show-label-published-at = Published At
cli-events-show-label-entity-type = Entity Type
cli-events-show-label-entity-id = Entity ID
cli-events-show-label-user-id = User ID
cli-events-show-label-event-data = Event Data
cli-events-show-label-metadata = Metadata

### Dashboard Metrics - Dashboard Metrics
cli-events-dashboard-metric-total = Total Events
cli-events-dashboard-metric-types = Event Types
cli-events-dashboard-metric-velocity = Events/Hour (24h)
cli-events-dashboard-metric-trend = Trend
cli-events-dashboard-section-top-types = [bold]Top Event Types[/bold]
cli-events-dashboard-column-events = Events

### Messages - Output Messages
cli-events-no-events = [yellow]No events found matching the criteria[/yellow]
cli-events-show-not-found = [red]Event with ID '{ $event_id }' not found[/red]
cli-events-filters-applied =
    [dim]Filters: { $filters }[/dim]
cli-events-stats-all-time = All Time
cli-events-stats-last-hours = Last { $hours } hours
cli-events-stats-last-days = Last { $days } days
cli-events-stats-total =
    [bold]Total Events:[/bold] { $total }

cli-events-stats-most-recent = [bold]Most Recent Event:[/bold] { $event_type } at { $timestamp }
cli-events-stats-oldest = [bold]Oldest Event:[/bold] { $event_type } at { $timestamp }
cli-events-timeline-no-events = [yellow]No events found for { $entity_type } with ID { $entity_id }[/yellow]
cli-events-timeline-total =
    [dim]Total events: { $total }[/dim]
cli-events-search-no-results = [yellow]No events found matching '{ $query }'[/yellow]
cli-events-types-no-events = [yellow]No events recorded yet[/yellow]
cli-events-dashboard-most-recent = [dim]Most Recent: { $event_type } at { $timestamp }[/dim]
cli-events-trends-no-events = [yellow]No events found for the specified period[/yellow]
cli-events-trends-summary = [dim]Total: { $total } events | Average: { $avg } events/day[/dim]

## ============================================================================
## LIGHTNING Commands - Lightning Network and Compliance
## ============================================================================

### Help Texts - Commands and Options
cli-lightning-help = Lightning Network payment management
cli-lightning-report-help = Generate compliance reports
cli-lightning-aml-help = Anti-Money Laundering management

### Status Command
cli-lightning-status-title = Lightning Network Status
cli-lightning-status-disabled = Status: Disabled
cli-lightning-status-disabled-hint-env = Set lightning_enabled=true in .env to enable Lightning payments
cli-lightning-status-disabled-hint-cmd = Use 'openfatture config set lightning_enabled true' to enable
cli-lightning-status-enabled = Status: Enabled
cli-lightning-status-host = Host: { $host }
cli-lightning-status-timeout = Timeout: { $timeout }s
cli-lightning-status-max-retries = Max retries: { $max_retries }
cli-lightning-status-btc-provider = BTC Provider: { $provider }
cli-lightning-status-liquidity = Liquidity monitoring: { $status }

cli-lightning-btc-provider-coingecko = CoinGecko
cli-lightning-btc-provider-cmc = CoinMarketCap
cli-lightning-btc-provider-fallback = Fallback
cli-lightning-liquidity-enabled = Enabled
cli-lightning-liquidity-disabled = Disabled

### Invoice Command
cli-lightning-disabled-error = Lightning is disabled. Enable with: openfatture config set lightning_enabled true
cli-lightning-invoice-title = Lightning Invoice Creation
cli-lightning-invoice-not-available = Feature not yet available - Lightning integration in development

### Channels Command
cli-lightning-channels-title = Lightning Channels
cli-lightning-channels-not-available = No channels configured - Lightning integration in development

### Liquidity Command
cli-lightning-liquidity-title = Channel Liquidity
cli-lightning-liquidity-not-available = Liquidity monitoring not available - Lightning integration in development

### Compliance Check Command
cli-lightning-compliance-opt-tax-year = Tax year to check (default: current year)
cli-lightning-compliance-opt-verbose = Show detailed information

cli-lightning-compliance-title =

    [bold cyan]Lightning Compliance Check - { $year }[/bold cyan]

cli-lightning-compliance-summary-title = [bold]Tax Year Summary[/bold]
cli-lightning-compliance-summary-payments = Number of payments:
cli-lightning-compliance-summary-revenue = Total revenue (EUR):
cli-lightning-compliance-summary-gains = Total capital gains (EUR):
cli-lightning-compliance-summary-tax = Estimated tax owed (EUR):

cli-lightning-compliance-aml-title = [bold]AML Compliance (Threshold: 5,000 EUR)[/bold]
cli-lightning-compliance-aml-total = Total over threshold:
cli-lightning-compliance-aml-verified = Verified:
cli-lightning-compliance-aml-unverified = Unverified:
cli-lightning-compliance-aml-status-ok = OK
cli-lightning-compliance-aml-status-require = { $count } REQUIRE VERIFICATION

cli-lightning-compliance-quadro-title = [bold]Quadro RW Declaration (Mandatory from 2025)[/bold]
cli-lightning-compliance-quadro-count = Invoices requiring declaration:
cli-lightning-compliance-action-required = Action required:
cli-lightning-compliance-quadro-action = [yellow]Declare all crypto holdings in Quadro RW[/yellow]
cli-lightning-compliance-status = Status:
cli-lightning-compliance-quadro-status-ok = [green]No declarations required[/green]

cli-lightning-compliance-data-quality-title = [bold]Data Quality[/bold]
cli-lightning-compliance-data-quality-missing = Invoices with missing tax data:
cli-lightning-compliance-data-quality-action = [red]Add BTC/EUR rate and EUR amount for tax compliance[/red]
cli-lightning-compliance-data-quality-status-ok = [green]All settled invoices have tax data[/green]

cli-lightning-compliance-issue-aml = { $count } unverified AML payment(s)
cli-lightning-compliance-issue-missing-data = { $count } invoice(s) missing tax data
cli-lightning-compliance-issues-found = [bold red]Compliance Issues Found: { $issues }[/bold red]

cli-lightning-compliance-passed = [bold green]All Compliance Checks Passed[/bold green]

cli-lightning-compliance-verbose-title = [bold]Unverified AML Payments:[/bold]
cli-lightning-compliance-verbose-item =   • { $hash }... - { $amount } EUR - Settled: { $date }

cli-lightning-compliance-error = [bold red]Error running compliance check: { $error }[/bold red]

### Report Commands - Common Options
cli-lightning-report-opt-tax-year = Tax year for report
cli-lightning-report-opt-format = Output format: json or csv
cli-lightning-report-opt-output = Output file path (optional, prints to stdout if not provided)

cli-lightning-report-invalid-format = [bold red]Invalid format. Use 'json' or 'csv'[/bold red]
cli-lightning-report-saved = [green]Report saved to: { $path }[/green]

cli-lightning-report-summary = [cyan]Total invoices in report: { $count }[/cyan]

### Quadro RW Report
cli-lightning-report-quadro-title =

    [bold cyan]Generating Quadro RW Report - { $year } ({ $format })[/bold cyan]

cli-lightning-report-quadro-error = [bold red]Error generating Quadro RW report: { $error }[/bold red]

### Capital Gains Report
cli-lightning-report-gains-title =

    [bold cyan]Generating Capital Gains Report - { $year } ({ $format })[/bold cyan]

cli-lightning-report-gains-summary-count = [cyan]Total invoices with gains: { $count }[/cyan]
cli-lightning-report-gains-summary-total = [yellow]Total capital gains: { $total } EUR[/yellow]
cli-lightning-report-gains-summary-tax = [red]Estimated tax ({ $rate }%): { $tax } EUR[/red]
cli-lightning-report-gains-error = [bold red]Error generating capital gains report: { $error }[/bold red]

### AML Report
cli-lightning-aml-opt-threshold = AML threshold in EUR
cli-lightning-aml-opt-format = Output format: json only
cli-lightning-aml-opt-verbose = Show detailed information

cli-lightning-aml-report-title =

    [bold cyan]Generating AML Compliance Report (Threshold: { $threshold } EUR)[/bold cyan]

cli-lightning-aml-report-summary-total = [cyan]Total over threshold: { $total }[/cyan]
cli-lightning-aml-report-summary-verified = [green]Verified: { $verified }[/green]
cli-lightning-aml-report-summary-unverified-ok = Unverified: 0
cli-lightning-aml-report-summary-unverified-warning = Unverified: { $count }
cli-lightning-aml-report-summary-rate = [yellow]Compliance rate: { $rate }%[/yellow]

cli-lightning-aml-report-action-required =

    [bold yellow]Action Required: Verify unverified payments with AML process[/bold yellow]
cli-lightning-aml-report-action-hint = [dim]Use: openfatture lightning aml list-unverified to see details[/dim]

cli-lightning-aml-report-error = [bold red]Error generating AML report: { $error }[/bold red]

### AML List Unverified Command
cli-lightning-aml-list-title =

    [bold cyan]Unverified AML Payments (Threshold: { $threshold } EUR)[/bold cyan]

cli-lightning-aml-list-empty = [green]No unverified payments found[/green]

cli-lightning-aml-list-table-title = Unverified Payments ({ $count } total)
cli-lightning-aml-list-col-hash = Payment Hash
cli-lightning-aml-list-col-amount = Amount (EUR)
cli-lightning-aml-list-col-settled = Settled At
cli-lightning-aml-list-col-fattura = Fattura ID
cli-lightning-aml-list-col-client = Client ID
cli-lightning-aml-list-col-description = Description

cli-lightning-aml-list-action-required = [bold yellow]Action Required: These payments require client identity verification[/bold yellow]
cli-lightning-aml-list-action-hint = [dim]Use: openfatture lightning aml verify <payment-hash> --verified-by <email>[/dim]

cli-lightning-aml-list-error = [bold red]Error listing unverified payments: { $error }[/bold red]

### AML Verify Command
cli-lightning-aml-verify-arg-hash = Payment hash to verify
cli-lightning-aml-verify-opt-by = Email of person verifying
cli-lightning-aml-verify-opt-notes = Verification notes (optional)
cli-lightning-aml-verify-opt-client = Client ID (optional)

cli-lightning-aml-verify-title =

    [bold cyan]Verifying AML Payment: { $hash }...[/bold cyan]

cli-lightning-aml-verify-not-found = [bold red]Invoice not found: { $hash }[/bold red]
cli-lightning-aml-verify-already-verified = [yellow]Payment already verified on { $date }[/yellow]
cli-lightning-aml-verify-below-threshold = [yellow]Payment does not exceed AML threshold, but marking as verified anyway[/yellow]
cli-lightning-aml-verify-success = [green]Payment verified successfully[/green]

cli-lightning-aml-verify-label-hash = Payment Hash:
cli-lightning-aml-verify-label-amount = Amount (EUR):
cli-lightning-aml-verify-label-settled = Settled At:
cli-lightning-aml-verify-label-by = Verified By:
cli-lightning-aml-verify-label-at = Verified At:
cli-lightning-aml-verify-label-notes = Notes:

cli-lightning-aml-verify-error = [bold red]Error verifying payment: { $error }[/bold red]

## ============================================================================
## REPORT Commands - Reports and Statistics
## ============================================================================

### Help Texts - Commands and Options
cli-report-iva-help-anno = Year
cli-report-iva-help-trimestre = Quarter (Q1-Q4)
cli-report-clienti-help-anno = Year
cli-report-scadenze-help-finestra = Number of days considered "due soon" (default: 14)

### Titles and Headers - VAT Report
cli-report-iva-title =

    [bold blue]VAT Report - { $anno }[/bold blue]

cli-report-iva-quarter =

    [cyan]Quarter: { $trimestre } ({ $mese_inizio }-{ $mese_fine })[/cyan]

cli-report-iva-full-year =

    [cyan]Full year[/cyan]

cli-report-iva-summary-title = VAT Summary
cli-report-iva-breakdown-title =

    [bold]Breakdown by VAT rate:[/bold]

### Titles and Headers - Client Report
cli-report-clienti-title =

    [bold blue]Client Revenue Report - { $anno }[/bold blue]

cli-report-clienti-table-title = Top Clients - { $anno }

### Titles and Headers - Due Dates Report
cli-report-scadenze-title =

    [bold blue]Payment Due Dates Overview[/bold blue]

### Table Columns - VAT Report
cli-report-iva-column-metric = Metric
cli-report-iva-column-amount = Amount
cli-report-iva-column-vat-rate = VAT Rate
cli-report-iva-column-imponibile = Taxable Base
cli-report-iva-column-vat = VAT

### Table Columns - Client Report
cli-report-clienti-column-rank = Rank
cli-report-clienti-column-client = Client
cli-report-clienti-column-invoices = Invoices
cli-report-clienti-column-revenue = Revenue

### Table Columns - Due Dates Report
cli-report-scadenze-column-invoice = Invoice
cli-report-scadenze-column-client = Client
cli-report-scadenze-column-due-date = Due Date
cli-report-scadenze-column-days-delta = Δ days
cli-report-scadenze-column-residual = Outstanding
cli-report-scadenze-column-paid = Paid
cli-report-scadenze-column-total = Total
cli-report-scadenze-column-status = Status

### Labels - VAT Report
cli-report-iva-label-num-invoices = Number of invoices
cli-report-iva-label-imponibile = Total taxable base
cli-report-iva-label-total-vat = Total VAT
cli-report-iva-label-total-revenue-bold = [bold]Total revenue[/bold]

### Messages - General
cli-report-no-invoices = [yellow]No invoices found for the selected period[/yellow]
cli-report-no-invoices-year = [yellow]No invoices found for the selected year[/yellow]

### Messages - VAT Report
cli-report-iva-error-invalid-quarter = [red]Invalid quarter. Use Q1, Q2, Q3, or Q4[/red]

### Messages - Client Report
cli-report-clienti-total-revenue =

    [bold]Total revenue: { $totale }[/bold]

### Messages - Due Dates Report
cli-report-scadenze-no-outstanding =

    [green]No outstanding payments. All invoices are settled![/green]

cli-report-scadenze-hidden-upcoming =

    [dim]… { $count } additional future payments not shown. Use --finestra or export data from the payment module for more details.[/dim]

cli-report-scadenze-total-outstanding =

    [bold]Total outstanding balance: { $totale }[/bold]

### Section Titles - Due Dates Report
cli-report-scadenze-section-overdue = [red]Overdue[/red]
cli-report-scadenze-section-due-soon = [yellow]Due soon (<= { $finestra } days)[/yellow]
cli-report-scadenze-section-upcoming = [cyan]Upcoming payments[/cyan]

cli-report-scadenze-section-total = [bold { $color }]Total outstanding: { $totale } • Payments: { $count }[/]

### Payment Status Labels - Due Dates Report
cli-report-scadenze-status-overdue = Overdue
cli-report-scadenze-status-partial = Partial
cli-report-scadenze-status-due = Due

## ============================================================================
## PEC Commands - PEC Testing and Configuration
## ============================================================================

### Titles
cli-pec-test-title = [bold blue]Testing PEC Configuration[/bold blue]
cli-pec-info-title = [bold blue]PEC Configuration[/bold blue]

### Labels
cli-pec-label-address = [cyan]PEC Address:[/cyan]
cli-pec-label-smtp-server = [cyan]SMTP Server:[/cyan]
cli-pec-label-smtp-port = [cyan]SMTP Port:[/cyan]
cli-pec-label-template = [cyan]Template:[/cyan] test/test_email.html + .txt
cli-pec-label-locale = [cyan]Locale:[/cyan]
cli-pec-label-password = Password
cli-pec-label-sdi-pec = SDI PEC

### Table Headers
cli-pec-table-setting = Setting
cli-pec-table-value = Value

### Error Messages
cli-pec-error-no-address = [red]PEC address not configured[/red]
cli-pec-error-no-address-hint = Run: [cyan]openfatture init[/cyan] to configure
cli-pec-error-no-password = [red]PEC password not configured[/red]
cli-pec-error-no-password-hint = Set it in your .env file: PEC_PASSWORD=your_password

### Test Messages
cli-pec-sending-test = Sending test email with professional template...
cli-pec-test-success = [bold green]Test email sent successfully![/bold green]
cli-pec-test-check-inbox = Check your PEC inbox: { $pec_address }
cli-pec-test-email-includes = [dim]The email includes:[/dim]
cli-pec-test-feature-html = • Professional HTML + plain text
cli-pec-test-feature-branding = • Your company branding
cli-pec-test-feature-language = • Language: { $language }
cli-pec-test-more-testing = [dim]For more email testing:[/dim]
cli-pec-test-cmd-email-test = [cyan]openfatture email test[/cyan]  - Full email test
cli-pec-test-cmd-email-preview = [cyan]openfatture email preview[/cyan] - Preview templates

cli-pec-test-failed =
    [red]Test failed: { $error }[/red]
cli-pec-test-common-issues = [yellow]Common issues:[/yellow]
cli-pec-issue-credentials = • Wrong PEC credentials
cli-pec-issue-smtp = • Incorrect SMTP server
cli-pec-issue-firewall = • Firewall blocking port 465
cli-pec-issue-mailbox = • PEC mailbox full

### Info Messages
cli-pec-not-set = [red]Not set[/red]
cli-pec-password-set = [green]Set[/green]

## ============================================================================
## NOTIFICHE Commands - SDI Notifications Management
## ============================================================================

### Help Text
cli-notifiche-help-file-path = Path to SDI notification XML file
cli-notifiche-help-no-email = Skip automatic email notification
cli-notifiche-help-tipo = Filter by type (AT, RC, NS, MC, NE)
cli-notifiche-help-limit = Maximum number of results
cli-notifiche-help-notification-id = Notification ID

### Titles
cli-notifiche-process-title = [bold blue]Processing SDI Notification[/bold blue]
cli-notifiche-list-title = [bold blue]SDI Notifications[/bold blue]
cli-notifiche-show-title = [bold blue]{ $emoji } Notification { $id }: { $tipo }[/bold blue]

### Table Headers
cli-notifiche-table-field = Field
cli-notifiche-table-value = Value
cli-notifiche-column-id = ID
cli-notifiche-column-type = Type
cli-notifiche-column-date = Date
cli-notifiche-column-invoice = Invoice
cli-notifiche-column-client = Client
cli-notifiche-column-sdi-id = SDI ID

### Labels
cli-notifiche-label-type = Type
cli-notifiche-label-sdi-id = SDI ID
cli-notifiche-label-file = File
cli-notifiche-label-date = Date
cli-notifiche-label-message = Message
cli-notifiche-label-errors = Errors
cli-notifiche-label-invoice = Invoice
cli-notifiche-label-client = Client
cli-notifiche-label-invoice-status = Invoice Status
cli-notifiche-label-received = Received
cli-notifiche-label-description = Description
cli-notifiche-label-xml-path = XML Path

### Messages
cli-notifiche-file-not-found = [red]File not found: { $file_path }[/red]
cli-notifiche-file-label = [cyan]File:[/cyan] { $name }
cli-notifiche-size-label = [cyan]Size:[/cyan] { $size } bytes
cli-notifiche-auto-email-enabled =
    [dim]Auto-email enabled { $email }[/dim]

cli-notifiche-processing = Processing notification...
cli-notifiche-error =
    [red]Error: { $error }[/red]
cli-notifiche-success = [bold green]Notification processed successfully![/bold green]
cli-notifiche-errors-count = { $count } error(s)
cli-notifiche-email-sent =
    [dim]Email notification sent to { $email }[/dim]

cli-notifiche-no-notifications = [yellow]No notifications found[/yellow]
cli-notifiche-process-hint = [dim]Process notifications with:[/dim]
cli-notifiche-process-cmd = [cyan]openfatture notifiche process <file.xml>[/cyan]
cli-notifiche-list-table-title = Notifications ({ $count })

cli-notifiche-not-found = [red]Notification { $notification_id } not found[/red]

## ============================================================================
## CONFIG Commands - Configuration Management
## ============================================================================

### Help Text
cli-config-help-key = Configuration key (e.g., pec.address)
cli-config-help-value = Configuration value

### Titles
cli-config-show-title = OpenFatture Configuration

### Table Headers
cli-config-column-setting = Setting
cli-config-column-value = Value

### Section Labels - Application
cli-config-label-app-version = App Version
cli-config-label-debug-mode = Debug Mode

### Section Labels - Database
cli-config-label-database-url = Database URL

### Section Labels - Paths
cli-config-label-data-dir = Data Directory
cli-config-label-archive-dir = Archive Directory
cli-config-label-certificates-dir = Certificates Directory

### Section Labels - Company Data
cli-config-label-company-name = Company Name
cli-config-label-partita-iva = Partita IVA
cli-config-label-codice-fiscale = Codice Fiscale
cli-config-label-tax-regime = Tax Regime

### Section Labels - PEC
cli-config-label-pec-address = PEC Address
cli-config-label-pec-smtp-server = PEC SMTP Server
cli-config-label-sdi-pec-address = SDI PEC Address

### Section Labels - Email & Notifications
cli-config-label-notification-email = Notification Email
cli-config-label-notifications-enabled = Notifications Enabled
cli-config-label-locale = Locale
cli-config-label-email-logo-url = Email Logo URL
cli-config-label-primary-color = Primary Color
cli-config-label-secondary-color = Secondary Color
cli-config-label-email-footer = Email Footer

### Section Labels - AI Configuration
cli-config-label-ai-provider = AI Provider
cli-config-label-ai-model = AI Model
cli-config-label-ai-base-url = AI Base URL
cli-config-label-ai-api-key = AI API Key
cli-config-label-chat-enabled = Chat Enabled
cli-config-label-chat-auto-save = Chat Auto-Save
cli-config-label-max-messages = Max Messages/Session
cli-config-label-max-tokens = Max Tokens/Session
cli-config-label-tools-enabled = Tools Enabled
cli-config-label-enabled-tools = Enabled Tools

### Status Values
cli-config-not-set = [red]Not set[/red]
cli-config-not-set-optional = [yellow]Not set[/yellow]
cli-config-set = [green]Set[/green]
cli-config-yes = [green]Yes[/green]
cli-config-no = [red]No[/red]
cli-config-auto-generated = [dim]Auto-generated[/dim]
cli-config-all-tools = all
cli-config-tools-count = { $count } tools

### Messages
cli-config-reload-success = [green]Configuration reloaded[/green]
cli-config-set-success = [green]Set { $key } = { $value }[/green]
cli-config-saved-to = [dim]Saved to { $path }[/dim]
cli-config-invalid-key = [red]Invalid configuration key: { $key }[/red]
cli-config-error = [red]Error: { $error }[/red]
