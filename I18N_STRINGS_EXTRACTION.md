# OpenFatture i18n Strings Extraction

Complete extraction of ALL user-facing translatable strings from CLI commands for internationalization migration.

---

## FILE: openfatture/cli/commands/fattura.py

### Help Strings (typer.Option/Argument)
- `help="Client ID"` (line 41)
- `help="Filter by status"` (line 212)
- `help="Filter by year"` (line 213)
- `help="Max results"` (line 214)
- `help="Invoice ID"` (line 270)
- `help="Invoice ID"` (line 348)
- `help="Skip confirmation"` (line 349)
- `help="Invoice ID"` (line 399)
- `help="Output path"` (line 400)
- `help="Skip XSD validation"` (line 401)
- `help="Invoice ID"` (line 491)
- `help="Send via PEC"` (line 492)

### Console Print Strings
- `"\n[bold blue]🧾 Create New Invoice[/bold blue]\n"` (line 56)
- `"[red]No clients found. Add one first with 'cliente add'[/red]"` (line 64)
- `"[cyan]Available clients:[/cyan]"` (line 67)
- `"[green]✓ Client: {cliente.denominazione}[/green]\n"` (line 78)
- `"\n[bold]Add line items[/bold]"` (line 107)
- `"[dim]Enter empty description to finish[/dim]\n"` (line 108)
- `"  [green]✓ Added: {descrizione[:40]} - €{totale:.2f}[/green]"` (line 146)
- `"[yellow]No items added. Invoice creation cancelled.[/yellow]"` (line 150)
- `"\n[bold green]✓ Invoice created successfully![/bold green]\n"` (line 188)
- `"[yellow]No invoices found[/yellow]"` (line 236)
- `"[red]Invalid status: {stato}[/red]"` (line 227)
- `"[red]Invoice {fattura_id} not found[/red]"` (line 279)
- `"\n[bold blue]Invoice {fattura.numero}/{fattura.anno}[/bold blue]\n"` (line 283)
- `"\n[bold]Line Items:[/bold]"` (line 301)
- `"\n[bold]Totals:[/bold]"` (line 323)
- `"[red]Invoice {fattura_id} not found[/red]"` (line 419)
- `"\n[bold blue]🔧 Generating FatturaPA XML[/bold blue]\n"` (line 406)
- `"Generating XML for invoice {fattura.numero}/{fattura.anno}..."` (line 433)
- `"\n[red]❌ Error: {error}[/red]"` (line 439)
- `"\n[yellow]Hint: Download the XSD schema from:[/yellow]\n"` (line 441-445)
- `"\n[green]✓ XML saved to: {xml_path_str}[/green]"` (line 457)
- `"\n[green]✓ XML generated successfully![/green]"` (line 461)
- `"Path: {xml_path_str}"` (line 462)
- `"\n[dim]Preview (first 500 chars):[/dim]"` (line 471)
- `"[dim]{xml_content[:500]}...[/dim]"` (line 472)
- `"\n[bold blue]📤 Sending Invoice to SDI[/bold blue]\n"` (line 506)
- `"[cyan]1. Generating XML...[/cyan]"` (line 516)
- `"[green]✓ XML generated[/green]"` (line 529)
- `"\n[cyan]2. Digital signature...[/cyan]"` (line 532)
- `"[yellow]⚠ Digital signature not yet implemented[/yellow]"` (line 533)
- `"[dim]For now, you can sign manually with external tools.[/dim]"` (line 534)
- `"\n[cyan]3. Sending via PEC with professional email template...[/cyan]"` (line 537)
- `"[red]❌ XML generation failed: {error}[/red]"` (line 526)
- `"[green]✓ Invoice sent to SDI via PEC with professional template[/green]"` (line 556)
- `"\n[bold green]✓ Invoice {fattura.numero}/{fattura.anno} sent successfully![/bold green]"` (line 575)
- `"\n[dim]📧 Professional email sent to SDI with:[/dim]"` (line 577)
- `"  • HTML + plain text format"` (line 578)
- `"  • Company branding ({settings.email_primary_color})"` (line 579)
- `"  • Language: {settings.locale.upper()}"` (line 580)
- `"\n[dim]📬 Automatic notifications:[/dim]"` (line 581)
- `"  • SDI responses will be emailed to: {settings.notification_email}"` (line 584)
- `"  • Process notifications with: [cyan]openfatture notifiche process <file>[/cyan]"` (line 587)
- `"  • Enable with: NOTIFICATION_EMAIL in .env"` (line 590)
- `"\n[dim]Monitor your PEC inbox for SDI notifications.[/dim]"` (line 591)
- `"[red]❌ Failed to send: {error}[/red]"` (line 594)
- `"\n[yellow]Manual steps:[/yellow]"` (line 599)
- `"  1. XML saved at: {xml_path}"` (line 600)
- `"  2. Sign if needed, then send to: {settings.sdi_pec_address}"` (line 601)

### Prompts (Rich Prompt/IntPrompt/FloatPrompt)
- `"Select client ID"` (line 71)
- `"Invoice number"` (line 91)
- `"Issue date (YYYY-MM-DD)"` (line 92)
- `"Item {riga_num} description"` (line 115)
- `"Quantity"` (line 119)
- `"Unit price (€)"` (line 120)
- `"VAT rate (%)"` (line 121)
- `"Apply ritenuta d'acconto (withholding tax)?"` (line 160)
- `"Ritenuta rate (%)"` (line 161)
- `"Add bollo (€2.00)?"` (line 168)
- `"Delete invoice {fattura.numero}/{fattura.anno}?"` (line 371)
- `"Send invoice to SDI now?"` (line 539)

### Confirmation Prompts
- `"Cancelled."` (line 373)
- `"\n[yellow]Cancelled. Use 'openfatture fattura invia' later to send.[/yellow]"` (line 541)

### Table/Panel Titles
- `Table(title=f"Invoice {numero}/{anno}")` (line 190)
- `Table(title=f"Invoices ({len(fatture)})")` (line 239)
- `"Field"` (column header, multiple tables)
- `"Value"` (column header, multiple tables)
- `"Client"` (row label, line 194)
- `"Date"` (row label, line 195)
- `"Line items"` (row label, line 196)
- `"Imponibile"` (row label, line 197)
- `"IVA"` (row label, line 198)
- `"Ritenuta"` (row label, line 200)
- `"Bollo"` (row label, line 202)
- `"TOTALE"` (row label, line 203)
- `"ID"` (column, line 240)
- `"Number"` (column, line 241)
- `"Client"` (column, line 243)
- `"Total"` (column, line 244)
- `"Status"` (column, line 245)
- `"SDI Number"` (row label, line 296)
- `"Type"` (row label, line 292)
- `"#"` (column, line 303)
- `"Description"` (column, line 304)
- `"Qty"` (column, line 305)
- `"Price"` (column, line 306)
- `"VAT%"` (column, line 307)
- `"Total"` (column, line 308)

---

## FILE: openfatture/cli/commands/cliente.py

### Help Strings (typer.Option/Argument)
- `help="Client name/company name (omit to be prompted in --interactive mode)"` (line 34)
- `help="Partita IVA"` (line 36)
- `help="Codice Fiscale"` (line 37)
- `help="SDI code"` (line 38)
- `help="PEC address"` (line 39)
- `help="Interactive mode"` (line 40)
- `help="Max number of results"` (line 179)
- `help="Client ID"` (line 214)
- `help="Skip confirmation"` (line 260)

### Console Print Strings
- `"[yellow]Warning: Invalid Partita IVA, skipping[/yellow]"` (line 73)
- `"[yellow]Warning: Invalid Codice Fiscale, skipping[/yellow]"` (line 79)
- `"[red]Error: Client name is required[/red]"` (line 106)
- `"\n[green]✓ Client added successfully (ID: {cliente.id})[/green]"` (line 158)
- `"[yellow]No clients found. Add one with 'cliente add'[/yellow]"` (line 188)
- `"[red]Client with ID {cliente_id} not found[/red]"` (line 223)
- `"[yellow]Warning: This client has {len(cliente.fatture)} invoices[/yellow]"` (line 275)
- `"[red]Client with ID {cliente_id} not found[/red]"` (line 269)
- `"Cancelled."` (line 278, 284)
- `"[green]✓ Client '{client_name}' deleted[/green]"` (line 307)

### Prompts (Rich Prompt)
- `"Client name/Company"` (line 66)
- `"Partita IVA (optional)"` (line 69)
- `"Codice Fiscale (optional)"` (line 75)
- `"Address (Via/Piazza)"` (line 82)
- `"Civic number (optional)"` (line 83)
- `"CAP"` (line 84)
- `"City"` (line 85)
- `"Province (2 letters)"` (line 86)
- `"SDI Code (7 chars, or 0000000 for PEC)"` (line 89)
- `"PEC address (if SDI is 0000000)"` (line 93)
- `"Regular email (optional)"` (line 97)
- `"Phone (optional)"` (line 98)
- `"Notes (optional)"` (line 99)

### Confirmation Prompts
- `"Are you sure you want to delete?"` (line 277)
- `"Delete client '{cliente.denominazione}'?"` (line 282)

### Table/Panel Titles
- `Table(title=f"Client: {denominazione}")` (line 161)
- `Table(title=f"Clients ({len(clienti)})")` (line 191)
- `Table(title=f"Client Details: {cliente.denominazione}")` (line 226)
- `"Field"` (column header, multiple tables)
- `"Value"` (column header, multiple tables)
- `"Name"` (column, line 193)
- `"P.IVA"` (column, line 194)
- `"SDI/PEC"` (column, line 195)
- `"Invoices"` (column, line 196)
- `"ID"` (column, line 192)
- `"Partita IVA"` (row label, line 166, 234)
- `"Codice Fiscale"` (row label, line 168, 236)
- `"SDI Code"` (row label, line 170, 243)
- `"PEC"` (row label, line 172, 245)
- `"Address"` (row label, line 240)
- `"Email"` (row label, line 247)
- `"Phone"` (row label, line 249)
- `"Total Invoices"` (row label, line 251)
- `"Created"` (row label, line 252)

---

## FILE: openfatture/cli/commands/ai.py (PARTIAL - Priority Items)

### Help Strings (typer.Option/Argument)
- `help="Manage RAG knowledge base"` (line 38)
- `help="Manage user feedback and ML predictions"` (line 39)
- `help="Manage automatic ML model retraining"` (line 40)
- `help="Manage RAG auto-update on data changes"` (line 41)
- `help="Source ID defined in manifest (repeatable option)"` (line 71)
- `help="Semantic query to execute on knowledge base"` (line 80)
- `help="Maximum number of results to show"` (line 81)
- `help="Limit search to a single source"` (line 83)
- `help="Number of days to analyze"` (line 211)
- `help="Output file path"` (line 298)
- `help="Number of days to export"` (line 299)
- `help="Number of patterns to show"` (line 319)
- `help="Confidence threshold for low-confidence predictions"` (line 321)
- `help="Force retraining even if triggers not met"` (line 390)
- `help="Number of versions to show"` (line 529)
- `help="Version ID to rollback to"` (line 587)
- `help="Skip confirmation"` (line 588)
- `help="Entity type to reindex (invoice, client)"` (line 809)
- `help="Entity IDs to reindex (space-separated)"` (line 810)
- `help="Service description to expand"` (line 1020)
- `help="Hours worked"` (line 1021)
- `help="Hourly rate (€)"` (line 1022)
- `help="Project name"` (line 1023)
- `help="Technologies used (comma-separated)"` (line 1025)
- `help="Output as JSON (deprecated, use --format json)"` (line 1028)
- `help="Service/product description"` (line 1286)
- `help="Client is Public Administration"` (line 1287)
- `help="Foreign client"` (line 1288)
- `help="Client country code (IT, FR, US, etc.)"` (line 1290)
- `help="Service category"` (line 1292)
- `help="Amount in EUR"` (line 1293)
- `help="ATECO code"` (line 1294)
- `help="Output as JSON (deprecated, use --format json)"` (line 1296)
- `help="Months to forecast"` (line 1535)
- `help="Filter by client ID"` (line 1536)
- `help="Force model retraining"` (line 1537)
- `help="Output as JSON (deprecated, use --format json)"` (line 1539)
- `help="Invoice ID to check"` (line 1718)
- `help="Check level: basic, standard, advanced"` (line 1722)
- `help="Output as JSON (deprecated, use --format json)"` (line 1726)
- `help="Show all issues (including INFO)"` (line 1728)
- `help="Service description"` (line 1968)
- `help="Client ID"` (line 1969)
- `help="Invoice amount (€)"` (line 1970)
- `help="Hours worked"` (line 1971)
- `help="Hourly rate (€)"` (line 1972)
- `help="Project name"` (line 1973)
- `help="Technologies used (comma-separated)"` (line 1975)
- `help="Require human approval at each step"` (line 1978)
- `help="Confidence threshold for auto-approval (0.0-1.0)"` (line 1981)
- `help="Output as JSON (deprecated, use --format json)"` (line 1984)
- `help="Message to send (interactive if not provided)"` (line 2133)
- `help="Enable streaming responses"` (line 2135)
- `help="Output as JSON (deprecated, use --format json)"` (line 2137)
- `help="Recording duration in seconds"` (line 2328)
- `help="Audio sample rate (Hz)"` (line 2329)
- `help="Number of audio channels"` (line 2330)
- `help="Interactive mode (press Enter to record)"` (line 2332)
- `help="Save audio files to disk"` (line 2334)
- `help="Disable audio playback"` (line 2335)

### Console Print Strings (Sample - there are many)
- `"[bold red]Errore:[/bold red] {exc}"` (lines 114, 153, 171)
- `"\n[bold blue]📊 User Feedback Statistics[/bold blue]\n"` (line 219)
- `"\n[bold blue]🤖 ML Prediction Feedback Statistics[/bold blue]\n"` (line 251)
- `"[bold cyan]By Type:[/bold cyan]"` (line 238)
- `"[bold cyan]By Agent:[/bold cyan]"` (line 245)
- `"[bold cyan]By Prediction Type:[/bold cyan]"` (line 270)
- `"[bold cyan]By Model Version:[/bold cyan]"` (line 277)
- `"[yellow]Nessun risultato trovato.[/yellow]"` (line 185)
- `"\n[bold blue]🔄 Manual Model Retraining[/bold blue]\n"` (line 406)
- `"[bold green]✅ {result['message']}[/bold green]\n"` (line 415)
- `"\n[bold]New Model Metrics:[/bold]"` (line 425)
- `"[bold red]❌ {result['message']}[/bold red]\n"` (line 438)
- `"\n[bold blue]🔄 Retraining Scheduler Status[/bold blue]\n"` (line 459)
- `"[bold yellow]⚠️  Retraining Triggers Met[/bold yellow]\n"` (line 494)
- `"[bold green]✅ No Retraining Needed[/bold green]\n"` (line 496)
- `"[bold]Feedback Status:[/bold]"` (line 500)
- `"[bold]Time Status:[/bold]"` (line 509)
- `"[bold yellow]Active Triggers:[/bold yellow]"` (line 521)
- `"\n[bold blue]📦 Model Version History[/bold blue]\n"` (line 544)
- `"[dim]No model versions found.[/dim]\n"` (line 547)
- `"\n[bold blue]🔄 Model Rollback[/bold blue]\n"` (line 603)
- `"[bold red]❌ Version '{version_id}' not found[/bold red]\n"` (line 609)
- `"[bold]Rolling back to version:[/bold] {version_id}"` (line 613)
- `"[bold]Created:[/bold] {version.created_at.strftime('%Y-%m-%d %H:%M:%S')}"` (line 614)
- `"[bold]Notes:[/bold] {version.notes}"` (line 616)
- `"[bold]Metrics:[/bold]"` (line 620)
- `"\n[bold blue]🔄 RAG Auto-Update Service Status[/bold blue]\n"` (line 663)
- `"[bold]Configuration:[/bold]"` (line 682)
- `"[bold]Queue Statistics:[/bold]"` (line 693)
- `"[bold]Tracker Statistics:[/bold]"` (line 704)
- `"\n[bold blue]🔄 Starting RAG Auto-Update Service[/bold blue]\n"` (line 725)
- `"[bold green]✅ Service started successfully[/bold green]\n"` (line 730)
- `"\n[bold blue]🔄 Stopping RAG Auto-Update Service[/bold blue]\n"` (line 748)
- `"[bold yellow]⏸️  Service stopped[/bold yellow]\n"` (line 753)
- `"\n[bold blue]📊 RAG Auto-Update Queue Statistics[/bold blue]\n"` (line 770)
- `"\n[bold blue]🔄 Manual Reindexing[/bold blue]\n"` (line 826)
- `"[bold green]✅ Reindexing completed[/bold green]\n"` (line 834)
- `"\n[bold blue]🤖 Self-Learning System Dashboard[/bold blue]\n"` (line 879)
- `"[bold cyan]═══ RAG Auto-Update ═══[/bold cyan]\n"` (line 882)
- `"[bold cyan]═══ ML Model Retraining ═══[/bold cyan]\n"` (line 924)
- `"[bold cyan]═══ Feedback Collection ═══[/bold cyan]\n"` (line 972)
- `"\n[bold blue]🤖 AI Invoice Description Generator[/bold blue]\n"` (line 1064)
- `"[bold green]Generating description with AI..."` (line 1120)
- `"\n[bold red]❌ Error:[/bold red] {response.error}\n"` (line 1132)
- `"[bold blue]📄 Professional Description[/bold]"` (line 1222)
- `"[bold cyan]📦 Deliverables:[/bold cyan]"` (line 1229)
- `"[bold cyan]🔧 Technical Skills:[/bold cyan]"` (line 1235)
- `"[bold cyan]⏱️  Duration:[/bold cyan] {data['durata_ore']}h"` (line 1241)
- `"[bold cyan]📌 Notes:[/bold cyan] {data['note']}"` (line 1245)
- `"[bold blue]🧾 AI Tax Advisor - Suggerimento Fiscale[/bold blue]\n"` (line 1337)
- `"[bold green]Analizzando trattamento fiscale..."` (line 1393)
- `"\n[bold red]❌ Errore:[/bold red] {response.error}\n"` (line 1402)
- `"[bold]📊 Trattamento Fiscale[/bold]"` (line 1496)
- `"\n[bold cyan]📋 Spiegazione:[/bold cyan]"` (line 1502)
- `"[bold cyan]📜 Riferimento normativo:[/bold cyan]"` (line 1506)
- `"[bold cyan]📝 Nota per fattura:[/bold cyan]"` (line 1511)
- `"[bold cyan]💡 Raccomandazioni:[/bold cyan]"` (line 1516)
- `"\n[bold blue]💰 AI Cash Flow Forecasting[/bold blue]\n"` (line 1572)
- `"[bold green]Initializing ML models..."` (line 1600)
- `"[bold]📊 Cash Flow Summary[/bold]"` (line 1667)
- `"[bold green]Initializing ML models..."` (line 1600)
- `"[bold cyan]💡 Recommendations:[/bold cyan]\n"` (line 1709)
- `"\n[bold blue]🔍 Compliance Check (Level: {level.value})[/bold blue]\n"` (line 1777)
- `"[bold green]Analyzing invoice..."` (line 1799)
- `"[bold red]❌ Invalid level: {level_str}[/bold red]"` (line 1772)
- `"[bold red]❌ Error:[/bold red] {e}\n"` (line 1820, 1636, 1640, 1822, 1823)
- `"[bold]Invoice:[/bold] {report.invoice_number}"` (line 1844)
- `"[bold]Check Level:[/bold] {report.level.value}"` (line 1845)
- `"[bold green]✓ COMPLIANT[/bold green]\n\nThe invoice is ready for SDI submission"` (line 1851)
- `"[bold red]✗ NOT COMPLIANT[/bold red]\n\nFound {len(report.get_errors())} critical errors"` (line 1855)
- `"[bold]Compliance Status[/bold]"` (line 1861)
- `"[red]❌ Errors (Must Fix):[/red]\n"` (line 1918)
- `"[bold yellow]⚠️  Warnings:[/bold yellow]\n"` (line 1930)
- `"[bold blue]ℹ️  Informational:[/bold blue]\n"` (line 1940)
- `"[bold cyan]💡 Recommendations:[/bold cyan]\n"` (line 1949)
- `"[bold]Next Steps:[/bold]"` (line 1956)
- `"[bold green]✅ Invoice is ready for SDI submission![/bold green]\n"` (line 1962)
- `"[bold green]✅ Invoice created successfully![/bold green]"` (line 2087)
- `"[yellow]⚠️ Workflow completed with status: {result.status}[/yellow]"` (line 2090)
- `"[bold blue]🤖 OpenFatture AI Assistant[/bold blue]"` (line 2237)
- `"Type your questions about invoices, taxes, or business. Type 'exit' to quit.\n"` (line 2239)
- `"[dim]Goodbye! 👋[/dim]"` (line 2250, 2290)
- `"[bold blue]🎤 Voice Chat Assistant[/bold blue]\n"` (line 2408)
- `"[bold yellow]⚠️  Voice features are not enabled in settings.[/bold yellow]\n"` (line 2396)
- `"[bold red]❌ Error:[/bold red] OPENAI_API_KEY not set.\n"` (line 2402)
- `"[bold green]Initializing voice assistant..."` (line 2435)
- `"[green]✓ Voice assistant ready[/green]\n"` (line 2445)

### Prompts (Rich Prompt/IntPrompt/Input)
- `console.input("[bold green]You:[/bold green] ").strip()` (line 2246)

### Typer Confirm Prompts
- `typer.confirm("⚠️  This will overwrite the current model. Continue?")` (line 629)

### Table/Panel Titles
- Multiple tables with titles like `"Knowledge Base Sources"`, `"Vector Store"`, `"Last {days} Days"`, `"By Type"`, etc.

### Key Display Functions
- `_display_input()` - shows context fields (lines 1185-1206)
- `_display_result()` - shows structured invoice description (lines 1212-1257)
- `_display_metrics()` - shows response metrics (lines 1260-1280)
- `_display_tax_input()` - shows tax context (lines 1445-1469)
- `_display_tax_result()` - shows tax treatment (lines 1472-1529)
- `_display_forecast()` - shows cash flow forecast (lines 1658-1712)
- `_display_compliance_report()` - shows compliance check results (lines 1841-1962)

---

## FILE: openfatture/cli/main.py

### Help Strings (typer.Option)
- `help="Show the version and exit."` (line 123)
- `help="Launch interactive mode with menus"` (line 129)
- `help="Output format: rich, json, markdown, stream-json, html"` (line 135)

### Console Print Strings
- `f"[bold blue]OpenFatture[/bold blue] version {__version__}"` (line 103)
- `f"[yellow]Warning: Plugin system initialization failed: {e}[/yellow]"` (line 74)

### Command Group Registrations (Help Strings)
- `help="🎯 Interactive mode with menus"` (line 186)
- `help="🚀 Initialize OpenFatture"` (line 187)
- `help="⚙️  Manage configuration"` (line 188)
- `help="👤 Manage clients"` (line 189)
- `help="🧾 Manage invoices"` (line 190)
- `help="📋 Manage quotes/estimates"` (line 191)
- `help="📧 PEC configuration and testing"` (line 192)
- `help="📧 Email templates & testing"` (line 193)
- `help="📬 SDI notifications"` (line 194)
- `help="📦 Batch operations"` (line 195)
- `help="🤖 AI-powered assistance"` (line 196)
- `help="⚡ Lightning Network payments"` (line 197)
- `help="🎬 Media automation & VHS generation"` (line 198)
- `help="🪝 Manage lifecycle hooks"` (line 199)
- `help="📜 View event history & audit log"` (line 200)
- `help="📊 Generate reports"` (line 201)
- `help="🕷️ Regulatory web scraping"` (line 202)
- `help="🔌 Manage plugins"` (line 203)
- `help="💰 Payment tracking & reconciliation"` (line 204)

### Main Help Text
- `help="🧾 Open-source electronic invoicing for Italian freelancers"` (line 38)
- Docstring: `"""OpenFatture - Electronic invoicing made simple.\n\nA modern, CLI-first tool for Italian freelancers to create and manage\nFatturaPA electronic invoices with AI-powered workflows."""` (lines 138-142)

---

## Summary Statistics

### By File:
- **fattura.py**: ~75 translatable strings (help, prompts, console output, table labels)
- **cliente.py**: ~45 translatable strings (help, prompts, console output, table labels)
- **ai.py**: ~200+ translatable strings (extensive help, console output, prompts, table titles)
- **main.py**: ~25 translatable strings (help texts for command groups)

### Total: ~345+ translatable strings across all priority files

### String Categories:
1. **Help Texts** (~80): typer.Option/Argument help parameters
2. **Console Output** (~150): console.print() with Rich markup
3. **Prompts** (~60): IntPrompt, FloatPrompt, Prompt.ask()
4. **Table/Panel Titles** (~35): Table titles, column headers, row labels
5. **Confirmations** (~20): Confirmation messages, status updates

---

## Notes for Translation

1. **Rich Markup Preservation**: All `[bold]`, `[red]`, `[green]` etc. markup must be preserved in translations
2. **Emoji Handling**: Emoji characters (🧾 📤 🤖 etc.) should be kept as-is
3. **Variable Placeholders**: Format strings with `{variable}` or `f-string` syntax must be preserved
4. **Line References**: All line numbers match the current file versions
5. **Language Detection**: CLAUDE.md indicates Italian locale support - many strings are already Italian
6. **Currency**: EUR amounts use € symbol which should be preserved
7. **Technical Terms**: Keep terms like "PEC", "SDI", "IVA", "ATECO", "Partita IVA" as per Italian conventions

---

## Recommended FTL Structure

For each translatable string, create entries like:

```fluent
# fattura.py - line 56
invoice-create-title = [bold blue]🧾 Create New Invoice[/bold blue]

# fattura.py - line 64
invoice-no-clients-error = [red]No clients found. Add one first with 'cliente add'[/red]

# fattura.py - line 71
invoice-select-prompt = Select client ID

# etc.
```

Consider organizing by:
- Command/module (fattura, cliente, ai)
- Message type (help, error, success, prompt)
- Severity level (error, warning, info)
