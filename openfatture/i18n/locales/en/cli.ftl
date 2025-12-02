# CLI commands translations
# EN

## MAIN CLI

### main - Main CLI
cli-main-title = OpenFatture - Open Source Electronic Invoicing System
cli-main-description = Complete system for managing FatturaPA electronic invoices
cli-main-version = Version { $version }

### main - Command Groups
cli-main-group-invoices = 📄 Invoice Management
cli-main-group-clients = 👥 Client Management
cli-main-group-products = 📦 Product Management
cli-main-group-pec = 📧 PEC & SDI
cli-main-group-batch = 📊 Batch Operations
cli-main-group-ai = 🤖 AI Assistant
cli-main-group-payments = 💰 Payment Tracking
cli-main-group-preventivi = 📋 Quotes
cli-main-group-events = 📅 Event System
cli-main-group-lightning = ⚡ Lightning Network
cli-main-group-web = 🌐 Web Interface

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
cli-fattura-create-title = [bold blue]🧾 Create New Invoice[/bold blue]
cli-fattura-select-client-title = [bold cyan]Client Selection[/bold cyan]
cli-fattura-no-clients-error = [red]No clients found. Add one first with 'cliente add'[/red]
cli-fattura-available-clients = [cyan]Available clients:[/cyan]
cli-fattura-client-prompt = Client number
cli-fattura-client-selected = [green]✓ Client: { $client_name }[/green]
cli-fattura-invalid-client-error = [red]Invalid client selection[/red]

cli-fattura-add-lines-title = [bold cyan]Invoice Lines[/bold cyan]
cli-fattura-line-description-prompt = Description (empty to finish)
cli-fattura-line-quantity-prompt = Quantity
cli-fattura-line-unit-price-prompt = Unit price (€)
cli-fattura-line-vat-rate-prompt = VAT rate (%)
cli-fattura-line-added = [green]✓ Line added: { $description } - € { $amount }[/green]

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
cli-fattura-created-success = [bold green]✓ Invoice created successfully![/bold green]
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
cli-fattura-delete-success = [green]✓ Invoice { $numero }/{ $anno } deleted[/green]
cli-fattura-delete-cancelled = [yellow]Operation cancelled[/yellow]
cli-fattura-cancelled = Cancelled.
cli-fattura-delete-cannot-delete-sent = [red]Cannot delete invoices in INVIATA or CONSEGNATA state[/red]

cli-fattura-xml-generation-title = [bold blue]🔧 Generating FatturaPA XML[/bold blue]
cli-fattura-generating-xml = Generating XML for invoice { $numero }/{ $anno }...
cli-fattura-xml-generation-error = [red]❌ Error: { $error }[/red]
cli-fattura-xml-schema-hint = [yellow]Hint: Download the XSD schema from:[/yellow]
cli-fattura-xml-schema-url = https://www.fatturapa.gov.it/export/documenti/fatturapa/v1.2.2/Schema_del_file_xml_FatturaPA_v1.2.2.xsd
cli-fattura-xml-schema-save-path = And save it to: { $path }
cli-fattura-xml-saved = [green]✓ XML saved to: { $path }[/green]
cli-fattura-xml-generated = [green]✓ XML generated successfully![/green]
cli-fattura-xml-path = Path: { $path }
cli-fattura-xml-preview = [dim]Preview (first 500 chars):[/dim]

cli-fattura-validate-success = [green]✓ XML is valid[/green]
cli-fattura-validate-error = [red]Validation errors found:[/red]

cli-fattura-send-title = [bold blue]📤 Sending Invoice to SDI[/bold blue]
cli-fattura-send-step1-xml = [cyan]1. Generating XML...[/cyan]
cli-fattura-send-step2-signature = [cyan]2. Digital signature...[/cyan]
cli-fattura-send-step3-pec = [cyan]3. Sending via PEC with professional email template...[/cyan]
cli-fattura-send-xml-failed = [red]❌ XML generation failed: { $error }[/red]
cli-fattura-send-xml-success = [green]✓ XML generated[/green]
cli-fattura-send-signature-not-implemented = [yellow]⚠ Digital signature not yet implemented[/yellow]
cli-fattura-send-signature-manual-hint = [dim]For now, you can sign manually with external tools.[/dim]
cli-fattura-send-confirm = Send invoice to SDI now?
cli-fattura-send-cancelled = [yellow]Cancelled. Use 'openfatture fattura invia' later to send.[/yellow]
cli-fattura-sent-successfully = [green]✓ Invoice sent to SDI via PEC with professional template[/green]
cli-fattura-sent-success-message = [bold green]✓ Invoice { $numero }/{ $anno } sent successfully![/bold green]
cli-fattura-sent-email-details = [dim]📧 Professional email sent to SDI with:[/dim]
cli-fattura-sent-email-format = • HTML + plain text format
cli-fattura-sent-email-branding = • Company branding ({ $color })
cli-fattura-sent-email-language = • Language: { $language }
cli-fattura-sent-notifications-header = [dim]📬 Automatic notifications:[/dim]
cli-fattura-sent-notifications-enabled = • SDI responses will be emailed to: { $email }
cli-fattura-sent-notifications-process-cmd = • Process notifications with: [cyan]openfatture notifiche process <file>[/cyan]
cli-fattura-sent-notifications-disabled = • Enable with: NOTIFICATION_EMAIL in .env
cli-fattura-sent-monitor-pec = [dim]Monitor your PEC inbox for SDI notifications.[/dim]
cli-fattura-send-failed = [red]❌ Failed to send: { $error }[/red]
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
cli-cliente-help-denominazione = Company name or full name
cli-cliente-help-partita-iva = VAT number
cli-cliente-help-codice-fiscale = Fiscal code
cli-cliente-help-pec = PEC address
cli-cliente-help-codice-destinatario = SDI destination code
cli-cliente-help-formato = Output format (table, json, yaml)
cli-cliente-help-search = Search term
cli-cliente-help-limit = Maximum number of results

### cliente - Console Output
cli-cliente-list-title = Clients ({ $count })
cli-cliente-list-empty = [yellow]No clients found[/yellow]
cli-cliente-added-success = [green]✓ Client added successfully (ID: { $id })[/green]
cli-cliente-updated-success = [green]✓ Client updated successfully[/green]
cli-cliente-deleted-success = [green]✓ Client deleted successfully[/green]
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

### ai - Console Output (describe)
cli-ai-describe-title = [bold cyan]🤖 AI Invoice Description Generation[/bold cyan]
cli-ai-describe-input-prompt = [cyan]Enter brief description:[/cyan]
cli-ai-describe-processing = [yellow]Processing with AI...[/yellow]
cli-ai-describe-result-title = [bold green]Generated Description:[/bold green]
cli-ai-describe-result-text = [white]{ $text }[/white]
cli-ai-describe-copy-hint = [dim]You can copy this description when creating an invoice[/dim]
cli-ai-describe-error = [red]Error generating description: { $error }[/red]

### ai - Console Output (suggest-vat)
cli-ai-vat-title = [bold cyan]🧾 VAT Rate Suggestion with AI[/bold cyan]
cli-ai-vat-input-prompt = [cyan]Service/product description:[/cyan]
cli-ai-vat-processing = [yellow]Analyzing with AI...[/yellow]
cli-ai-vat-result-title = [bold green]Suggested VAT Rate:[/bold green]
cli-ai-vat-rate = [white]{ $rate }%[/white]
cli-ai-vat-reasoning-title = [bold yellow]Reasoning:[/bold yellow]
cli-ai-vat-reasoning-text = [white]{ $reasoning }[/white]
cli-ai-vat-warning = [yellow]⚠️  Always verify with a tax advisor for complex cases[/yellow]
cli-ai-vat-error = [red]Error suggesting VAT rate: { $error }[/red]

### ai - Console Output (chat)
cli-ai-chat-title = [bold cyan]🎤 Chat Vocale AI[/bold cyan]
cli-ai-chat-welcome = [cyan]Welcome to OpenFatture AI Assistant![/cyan]
cli-ai-chat-welcome-help = [dim]Type your questions or 'exit' to quit[/dim]
cli-ai-chat-session-loaded = [green]✓ Session loaded: { $session_id }[/green]
cli-ai-chat-session-created = [green]✓ New session created: { $session_id }[/green]
cli-ai-chat-prompt = [bold cyan]You:[/bold cyan]
cli-ai-chat-assistant-prefix = [bold green]Assistant:[/bold green]
cli-ai-chat-thinking = [yellow]Thinking...[/yellow]
cli-ai-chat-tool-calling = [yellow]Executing tool: { $tool_name }[/yellow]
cli-ai-chat-tool-result = [dim]Tool result: { $result }[/dim]
cli-ai-chat-session-saved = [green]✓ Session saved[/green]
cli-ai-chat-goodbye = [cyan]Goodbye! Session saved.[/cyan]
cli-ai-chat-error = [red]Error: { $error }[/red]
cli-ai-chat-cost-info = [dim]Tokens: { $tokens } | Cost: €{ $cost }[/dim]

### ai - Console Output (voice-chat)
cli-ai-voice-title = [bold cyan]🎤 AI Voice Chat[/bold cyan]
cli-ai-voice-welcome = [cyan]Welcome to Voice Chat![/cyan]
cli-ai-voice-recording-prompt = [yellow]Press ENTER to start recording ({ $duration }s)...[/yellow]
cli-ai-voice-recording = [bold yellow]🔴 Recording...[/bold yellow]
cli-ai-voice-processing = [yellow]Processing audio...[/yellow]
cli-ai-voice-transcription-title = [bold green]You said:[/bold green]
cli-ai-voice-transcription-text = [white]{ $text }[/white]
cli-ai-voice-language-detected = [dim]Language: { $language }[/dim]
cli-ai-voice-thinking = [yellow]Assistant thinking...[/yellow]
cli-ai-voice-response-title = [bold green]Assistant:[/bold green]
cli-ai-voice-response-text = [white]{ $text }[/white]
cli-ai-voice-playing = [cyan]🔊 Playing response...[/cyan]
cli-ai-voice-audio-saved = [dim]Audio saved: { $path }[/dim]
cli-ai-voice-goodbye = [cyan]Goodbye![/cyan]
cli-ai-voice-error = [red]Error: { $error }[/red]

### ai - Console Output (forecast)
cli-ai-forecast-title = [bold cyan]📊 Cash Flow Forecasting with AI[/bold cyan]
cli-ai-forecast-loading-data = [yellow]Loading historical data...[/yellow]
cli-ai-forecast-data-stats = [cyan]Invoices: { $invoices } | Payments: { $payments }[/cyan]
cli-ai-forecast-training = [yellow]Training ML models...[/yellow]
cli-ai-forecast-training-progress = [yellow]{ $progress }%[/yellow]
cli-ai-forecast-predicting = [yellow]Generating forecast...[/yellow]
cli-ai-forecast-results-title = [bold green]📊 Cash Flow Forecast - Next { $months } { $months ->
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
cli-ai-intelligence-title = [bold cyan]🧠 Business Intelligence Analysis[/bold cyan]
cli-ai-intelligence-analyzing = [yellow]Analyzing business data...[/yellow]
cli-ai-intelligence-report-title = [bold green]Business Insights:[/bold green]
cli-ai-intelligence-section = [bold yellow]{ $section }[/bold yellow]
cli-ai-intelligence-insight = • { $insight }
cli-ai-intelligence-error = [red]Analysis error: { $error }[/red]

### ai - Console Output (compliance)
cli-ai-compliance-title = [bold cyan]✅ Compliance Verification[/bold cyan]
cli-ai-compliance-checking = [yellow]Checking invoice { $numero }/{ $anno }...[/yellow]
cli-ai-compliance-passed = [bold green]✓ All compliance checks passed[/bold green]
cli-ai-compliance-warnings = [yellow]⚠️  { $count } { $count ->
    [one] warning found
   *[other] warnings found
}[/yellow]
cli-ai-compliance-errors = [red]❌ { $count } { $count ->
    [one] error found
   *[other] errors found
}[/red]
cli-ai-compliance-check-item = [{ $status }] { $message }
cli-ai-compliance-error = [red]Compliance check error: { $error }[/red]

### ai - Console Output (rag)
cli-ai-rag-title = [bold cyan]📚 RAG Document Search[/bold cyan]
cli-ai-rag-indexing = [yellow]Indexing documents...[/yellow]
cli-ai-rag-indexed = [green]✓ { $count } { $count ->
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
cli-ai-feedback-title = [bold cyan]📝 AI Feedback[/bold cyan]
cli-ai-feedback-prompt-rating = [cyan]Rate response (1-5):[/cyan]
cli-ai-feedback-prompt-comment = [cyan]Comment (optional):[/cyan]
cli-ai-feedback-thanks = [green]✓ Thank you for your feedback![/green]
cli-ai-feedback-saved = [green]Feedback saved to session { $session_id }[/green]
cli-ai-feedback-error = [red]Feedback error: { $error }[/red]
