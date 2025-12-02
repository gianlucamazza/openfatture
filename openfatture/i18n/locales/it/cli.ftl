# CLI commands translations - Italian
# Traduzioni complete per tutti i comandi CLI di OpenFatture

## ============================================================================
## FATTURA Commands - Gestione Fatture
## ============================================================================

### Help Text - Opzioni e Argomenti
cli-fattura-help-numero = Numero fattura
cli-fattura-help-cliente-id = ID Cliente
cli-fattura-help-invoice-id = ID Fattura
cli-fattura-help-anno = Anno (predefinito: anno corrente)
cli-fattura-help-tipo-documento = Tipo documento (TD01, TD04, TD06, etc.)
cli-fattura-help-data = Data fattura (AAAA-MM-GG)
cli-fattura-help-bollo = Marca da bollo (€ 2,00)
cli-fattura-help-xml-path = Percorso file XML
cli-fattura-help-formato = Formato output (table, json, yaml)
cli-fattura-help-all = Mostra tutte le fatture, anche quelle vecchie
cli-fattura-help-filter-status = Filtra per stato
cli-fattura-help-filter-anno = Filtra per anno
cli-fattura-help-limit = Numero massimo di risultati
cli-fattura-help-force = Salta conferma
cli-fattura-help-output = Percorso di output
cli-fattura-help-no-validate = Salta validazione XSD
cli-fattura-help-pec = Invia via PEC

### Console Output - Messaggi di output
cli-fattura-create-title = [bold blue]🧾 Crea Nuova Fattura[/bold blue]
cli-fattura-select-client-title = [bold cyan]Selezione Cliente[/bold cyan]
cli-fattura-no-clients-error = [red]Nessun cliente trovato. Aggiungine uno con 'cliente add'[/red]
cli-fattura-available-clients = [cyan]Clienti disponibili:[/cyan]
cli-fattura-client-prompt = Numero cliente
cli-fattura-client-selected = [green]✓ Cliente: { $client_name }[/green]
cli-fattura-invalid-client-error = [red]Selezione cliente non valida[/red]

cli-fattura-add-lines-title = [bold cyan]Righe Fattura[/bold cyan]
cli-fattura-line-description-prompt = Descrizione (vuoto per terminare)
cli-fattura-line-quantity-prompt = Quantità
cli-fattura-line-unit-price-prompt = Prezzo unitario (€)
cli-fattura-line-vat-rate-prompt = Aliquota IVA (%)
cli-fattura-line-added = [green]✓ Riga aggiunta: { $description } - € { $amount }[/green]

cli-fattura-payment-terms-title = [bold cyan]Termini di Pagamento[/bold cyan]
cli-fattura-payment-condition-prompt = Condizione di pagamento (TP01=Da pagare, TP02=Pagato)
cli-fattura-payment-method-prompt = Metodo di pagamento (MP05=Bonifico, MP01=Contanti, MP08=Carta)
cli-fattura-payment-days-prompt = Termini di pagamento (giorni)
cli-fattura-payment-date-prompt = Data di pagamento (AAAA-MM-GG, vuoto=auto)
cli-fattura-payment-iban-prompt = IBAN (opzionale)

cli-fattura-summary-title = [bold yellow]Riepilogo Fattura[/bold yellow]
cli-fattura-summary-client = Cliente: { $client_name }
cli-fattura-summary-lines = { $count } { $count ->
    [one] riga
   *[other] righe
}
cli-fattura-summary-subtotal = Imponibile: € { $subtotal }
cli-fattura-summary-vat = IVA: € { $vat }
cli-fattura-summary-total = [bold]Totale: € { $total }[/bold]
cli-fattura-summary-stamp = Marca da bollo: € { $stamp }

cli-fattura-confirm-prompt = [yellow]Confermare la creazione?[/yellow]
cli-fattura-created-success = [bold green]✓ Fattura creata con successo![/bold green]
cli-fattura-created-number = [green]Numero fattura: { $numero }/{ $anno }[/green]
cli-fattura-created-xml = [green]XML salvato: { $xml_path }[/green]

cli-fattura-list-title = [bold blue]Elenco Fatture[/bold blue]
cli-fattura-list-empty = [yellow]Nessuna fattura trovata[/yellow]

cli-fattura-show-title = [bold blue]Fattura { $numero }/{ $anno }[/bold blue]
cli-fattura-show-not-found = [red]Fattura non trovata: { $numero }/{ $anno }[/red]

cli-fattura-invalid-status = [red]Stato non valido: { $status }[/red]
cli-fattura-invoice-not-found = [red]Fattura { $invoice_id } non trovata[/red]
cli-fattura-line-items-header = Righe Fattura
cli-fattura-totals-header = Totali
cli-fattura-xml-generation-title = [bold blue]🔧 Generazione XML FatturaPA[/bold blue]
cli-fattura-generating-xml = Generazione XML per fattura { $numero }/{ $anno }...
cli-fattura-xml-generation-error = [red]❌ Errore: { $error }[/red]
cli-fattura-xml-schema-hint = [yellow]Suggerimento: Scarica lo schema XSD da:[/yellow]
cli-fattura-xml-schema-url = https://www.fatturapa.gov.it/export/documenti/fatturapa/v1.2.2/Schema_del_file_xml_FatturaPA_v1.2.2.xsd
cli-fattura-xml-schema-save-path = E salvalo in: { $path }
cli-fattura-xml-saved = [green]✓ XML salvato in: { $path }[/green]
cli-fattura-xml-generated = [green]✓ XML generato con successo![/green]
cli-fattura-xml-path = Percorso: { $path }
cli-fattura-xml-preview = [dim]Anteprima (primi 500 caratteri):[/dim]
cli-fattura-validate-success = [green]✓ XML valido[/green]
cli-fattura-validate-error = [red]Errori di validazione trovati:[/red]
cli-fattura-send-title = [bold blue]📤 Invio Fattura a SDI[/bold blue]
cli-fattura-send-step1-xml = [cyan]1. Generazione XML...[/cyan]
cli-fattura-send-step2-signature = [cyan]2. Firma digitale...[/cyan]
cli-fattura-send-step3-pec = [cyan]3. Invio via PEC con template email professionale...[/cyan]
cli-fattura-send-xml-failed = [red]❌ Generazione XML fallita: { $error }[/red]
cli-fattura-send-xml-success = [green]✓ XML generato[/green]
cli-fattura-send-signature-not-implemented = [yellow]⚠ Firma digitale non ancora implementata[/yellow]
cli-fattura-send-signature-manual-hint = [dim]Per ora, puoi firmare manualmente con strumenti esterni.[/dim]
cli-fattura-send-confirm = Inviare fattura a SDI ora?
cli-fattura-send-cancelled = [yellow]Annullato. Usa 'openfatture fattura invia' più tardi per inviare.[/yellow]
cli-fattura-sent-successfully = [green]✓ Fattura inviata a SDI via PEC con template professionale[/green]
cli-fattura-sent-success-message = [bold green]✓ Fattura { $numero }/{ $anno } inviata con successo![/bold green]
cli-fattura-sent-email-details = [dim]📧 Email professionale inviata a SDI con:[/dim]
cli-fattura-sent-email-format = • Formato HTML + testo semplice
cli-fattura-sent-email-branding = • Branding aziendale ({ $color })
cli-fattura-sent-email-language = • Lingua: { $language }
cli-fattura-sent-notifications-header = [dim]📬 Notifiche automatiche:[/dim]
cli-fattura-sent-notifications-enabled = • Le risposte SDI saranno inviate a: { $email }
cli-fattura-sent-notifications-process-cmd = • Elabora le notifiche con: [cyan]openfatture notifiche process <file>[/cyan]
cli-fattura-sent-notifications-disabled = • Abilita con: NOTIFICATION_EMAIL in .env
cli-fattura-sent-monitor-pec = [dim]Monitora la tua casella PEC per le notifiche SDI.[/dim]
cli-fattura-send-failed = [red]❌ Invio fallito: { $error }[/red]
cli-fattura-send-manual-steps = [yellow]Passi manuali:[/yellow]
cli-fattura-send-manual-step1 = 1. XML salvato in: { $path }
cli-fattura-send-manual-step2 = 2. Firma se necessario, poi invia a: { $sdi_address }

### Prompts - Richieste input utente
cli-fattura-prompt-select-client = Seleziona ID cliente
cli-fattura-prompt-invoice-number = Numero fattura
cli-fattura-prompt-issue-date = Data emissione (AAAA-MM-GG)
cli-fattura-prompt-item-description = Descrizione riga { $num }
cli-fattura-prompt-quantity = Quantità
cli-fattura-prompt-unit-price = Prezzo unitario (€)
cli-fattura-prompt-vat-rate = Aliquota IVA (%)
cli-fattura-prompt-ritenuta = Applicare ritenuta d'acconto?
cli-fattura-prompt-ritenuta-rate = Percentuale ritenuta (%)
cli-fattura-prompt-bollo = Aggiungere bollo (€2.00)?
cli-fattura-prompt-delete-confirm = Eliminare fattura { $numero }/{ $anno }?
cli-fattura-cancelled = Annullato.
cli-fattura-delete-confirm = [yellow]Eliminare fattura { $numero }/{ $anno }?[/yellow]
cli-fattura-delete-warning = [red]ATTENZIONE: Questa operazione non può essere annullata[/red]
cli-fattura-delete-status-restriction = [red]Impossibile eliminare fattura nello stato '{ $status }'[/red]
cli-fattura-delete-success = [green]✓ Fattura { $numero }/{ $anno } eliminata[/green]
cli-fattura-delete-cancelled = [yellow]Operazione annullata[/yellow]
cli-fattura-delete-cannot-delete-sent = [red]Impossibile eliminare fatture nello stato INVIATA o CONSEGNATA[/red]

### Table Labels - Etichette tabelle
cli-fattura-table-title-single = Fattura { $numero }/{ $anno }
cli-fattura-table-title-list = Fatture ({ $count })
cli-fattura-table-field = Campo
cli-fattura-table-value = Valore
cli-fattura-table-id = ID
cli-fattura-table-numero = N.
cli-fattura-table-number = Numero
cli-fattura-table-date = Data
cli-fattura-table-data = Data
cli-fattura-table-client = Cliente
cli-fattura-table-cliente = Cliente
cli-fattura-table-line-items = Righe
cli-fattura-table-importo = Importo
cli-fattura-table-imponibile = Imponibile
cli-fattura-table-stato = Stato
cli-fattura-table-status = Stato
cli-fattura-table-tipo = Tipo
cli-fattura-table-type = Tipo
cli-fattura-table-pagamento = Pagamento
cli-fattura-table-iva = IVA
cli-fattura-table-total = Totale
cli-fattura-table-totale = TOTALE
cli-fattura-table-bollo = Bollo
cli-fattura-table-ritenuta = Ritenuta
cli-fattura-table-descrizione = Descrizione
cli-fattura-table-description = Descrizione
cli-fattura-table-quantita = Qta
cli-fattura-table-qty = Qta
cli-fattura-table-prezzo = Prezzo
cli-fattura-table-price = Prezzo
cli-fattura-table-unit-price = Prezzo Unitario
cli-fattura-table-aliquota = Aliquota
cli-fattura-table-vat-percent = IVA%
cli-fattura-table-importo-riga = Importo
cli-fattura-table-row-number = #
cli-fattura-table-sdi-number = Numero SDI
cli-fattura-prompt-select-client = Seleziona cliente

## ============================================================================
## CLIENTE Commands - Gestione Clienti
## ============================================================================

### Help Text - Opzioni e Argomenti
cli-cliente-help-name = Nome cliente/ragione sociale (ometti per inserirlo in modalità --interactive)
cli-cliente-help-piva = Partita IVA
cli-cliente-help-cf = Codice Fiscale
cli-cliente-help-sdi = Codice SDI
cli-cliente-help-pec = Indirizzo PEC
cli-cliente-help-interactive = Modalità interattiva
cli-cliente-help-limit = Numero massimo di risultati
cli-cliente-help-cliente-id = ID Cliente
cli-cliente-help-force = Salta conferma

### Console Output - Messaggi di output
cli-cliente-list-title = Clienti ({ $count })
cli-cliente-invalid-piva = [yellow]Attenzione: Partita IVA non valida, salto validazione[/yellow]
cli-cliente-invalid-cf = [yellow]Attenzione: Codice Fiscale non valido, salto validazione[/yellow]
cli-cliente-name-required = [red]Errore: Nome cliente obbligatorio[/red]
cli-cliente-added-success = [green]✓ Cliente aggiunto con successo (ID: { $id })[/green]
cli-cliente-no-clients = [yellow]Nessun cliente trovato. Aggiungine uno con 'cliente add'[/yellow]
cli-cliente-not-found = [red]Cliente con ID { $id } non trovato[/red]
cli-cliente-has-invoices = [yellow]Attenzione: Questo cliente ha { $count } fatture[/yellow]
cli-cliente-cancelled = Annullato.
cli-cliente-deleted = [green]✓ Cliente '{ $name }' eliminato[/green]

### Prompts - Richieste input utente
cli-cliente-prompt-company-name = Nome cliente/Ragione sociale
cli-cliente-prompt-piva = Partita IVA (opzionale)
cli-cliente-prompt-cf = Codice Fiscale (opzionale)
cli-cliente-prompt-address = Indirizzo (Via/Piazza)
cli-cliente-prompt-civic = Numero civico (opzionale)
cli-cliente-prompt-cap = CAP
cli-cliente-prompt-city = Città
cli-cliente-prompt-province = Provincia (2 lettere)
cli-cliente-prompt-sdi = Codice SDI (7 caratteri, oppure 0000000 per PEC)
cli-cliente-prompt-pec = Indirizzo PEC (se SDI è 0000000)
cli-cliente-prompt-email = Email normale (opzionale)
cli-cliente-prompt-phone = Telefono (opzionale)
cli-cliente-prompt-notes = Note (opzionale)
cli-cliente-prompt-delete-confirm = Eliminare cliente '{ $name }'?

### Table Labels - Etichette tabelle
cli-cliente-table-title = Clienti ({ $count })
cli-cliente-table-id = ID
cli-cliente-table-name = Nome/Ragione Sociale
cli-cliente-table-piva = P.IVA
cli-cliente-table-cf = C.F.
cli-cliente-table-city = Città
cli-cliente-table-sdi-pec = SDI/PEC
cli-cliente-table-invoices = Fatture
cli-cliente-table-field = Campo
cli-cliente-table-value = Valore
cli-cliente-table-company = Ragione Sociale
cli-cliente-table-address = Indirizzo
cli-cliente-table-cap = CAP
cli-cliente-table-province = Provincia
cli-cliente-table-sdi = Codice SDI
cli-cliente-table-pec = PEC
cli-cliente-table-email = Email
cli-cliente-table-phone = Telefono
cli-cliente-table-notes = Note

## ============================================================================
## AI Commands - Assistente AI
## ============================================================================

### Help Text - Opzioni e Argomenti
cli-ai-help-activity-description = Descrizione attività (es: "3 ore di consulenza sviluppo web")
cli-ai-help-activity-type = Tipo di attività/servizio fornito
cli-ai-help-vat-query = Descrizione attività o domanda fiscale
cli-ai-help-interactive = Modalità chat interattiva
cli-ai-help-voice = Usa input/output vocale
cli-ai-help-duration = Durata registrazione audio (secondi)
cli-ai-help-save-audio = Salva file audio (debug)
cli-ai-help-no-playback = Disabilita riproduzione audio
cli-ai-help-sample-rate = Sample rate audio (Hz)
cli-ai-help-channels = Canali audio (1=mono, 2=stereo)
cli-ai-help-session-id = ID sessione chat
cli-ai-help-list-sessions = Elenca tutte le sessioni
cli-ai-help-message = Messaggio da inviare
cli-ai-help-export = Esporta in formato (json, md, txt)
cli-ai-help-retrain = Ri-addestra i modelli ML
cli-ai-help-months = Mesi di previsione
cli-ai-help-min-invoices = Minimo fatture richieste
cli-ai-help-client-id = ID cliente
cli-ai-help-top-n = Numero massimo risultati
cli-ai-help-export-format = Formato export (json, csv)
cli-ai-help-invoice-id = ID fattura
cli-ai-help-auto-fix = Correggi automaticamente
cli-ai-help-strict = Modalità strict (tutte le regole)
cli-ai-help-check-type = Tipo verifica (formal, substantial, sdi, all)
cli-ai-help-export-report = Esporta report
cli-ai-help-query = Query documenti
cli-ai-help-doc-type = Tipo documento
cli-ai-help-top-k = Numero risultati
cli-ai-help-threshold = Soglia similarità
cli-ai-help-no-feedback = Salta richiesta feedback
cli-ai-help-feedback-type = Tipo feedback
cli-ai-help-comment = Commento

### Console Output - Comandi AI
cli-ai-describe-title = [bold cyan]🤖 Generazione Descrizione Fattura con AI[/bold cyan]
cli-ai-describe-activity = Attività: [yellow]{ $activity }[/yellow]
cli-ai-describe-generating = Generazione descrizione dettagliata...
cli-ai-describe-result-title = [bold green]✓ Descrizione Generata:[/bold green]
cli-ai-describe-copy-hint = [dim]Copia questa descrizione quando crei una fattura[/dim]
cli-ai-describe-error = [red]❌ Errore: { $error }[/red]

cli-ai-vat-title = [bold cyan]🧮 Suggerimento Aliquota IVA[/bold cyan]
cli-ai-vat-query = Query: [yellow]{ $query }[/yellow]
cli-ai-vat-analyzing = Analisi normativa IVA...
cli-ai-vat-result-title = [bold green]✓ Raccomandazione IVA:[/bold green]
cli-ai-vat-disclaimer = [yellow]⚠ Questo è un suggerimento. Consulta sempre un commercialista.[/yellow]
cli-ai-vat-error = [red]❌ Errore: { $error }[/red]

cli-ai-chat-title = [bold cyan]💬 Chat Assistente AI[/bold cyan]
cli-ai-chat-welcome = Benvenuto nella chat AI di OpenFatture! Chiedi qualsiasi cosa su fatture, tasse, clienti.
cli-ai-chat-commands-title = [bold]Comandi disponibili:[/bold]
cli-ai-chat-exit = • [cyan]/exit, /quit, /q[/cyan] - Esci dalla chat
cli-ai-chat-clear = • [cyan]/clear[/cyan] - Pulisci schermo
cli-ai-chat-help = • [cyan]/help[/cyan] - Mostra questo messaggio
cli-ai-chat-sessions = • [cyan]/sessions[/cyan] - Elenca sessioni
cli-ai-chat-load = • [cyan]/load <id>[/cyan] - Carica sessione
cli-ai-chat-export = • [cyan]/export[/cyan] - Esporta conversazione
cli-ai-chat-stats = • [cyan]/stats[/cyan] - Statistiche sessione
cli-ai-chat-interactive-hint = [dim]Modalità interattiva. Scrivi i tuoi messaggi o usa i comandi preceduti da /[/dim]
cli-ai-chat-session-loaded = [green]✓ Sessione caricata: { $session_id }[/green]
cli-ai-chat-session-saved = [dim]Sessione salvata: { $session_id }[/dim]
cli-ai-chat-thinking = [dim]🤔 Pensando...[/dim]
cli-ai-chat-error = [red]❌ Errore: { $error }[/red]
cli-ai-chat-goodbye = [cyan]👋 Alla prossima![/cyan]

cli-ai-voice-title = [bold cyan]🎤 Chat Vocale AI[/bold cyan]
cli-ai-voice-welcome = Chat vocale con OpenFatture AI
cli-ai-voice-recording = [yellow]🔴 Registrazione in corso... ({ $duration }s)[/yellow]
cli-ai-voice-press-enter = [cyan]Premi INVIO quando pronto...[/cyan]
cli-ai-voice-processing = [dim]Elaborazione audio...[/dim]
cli-ai-voice-transcribing = [dim]📝 Trascrizione...[/dim]
cli-ai-voice-you-said = [green]Tu:[/green] { $text }
cli-ai-voice-detected-language = [dim]Lingua rilevata: { $language }[/dim]
cli-ai-voice-thinking = [dim]🤔 Elaborazione risposta...[/dim]
cli-ai-voice-ai-response = [cyan]AI:[/cyan] { $response }
cli-ai-voice-generating-audio = [dim]🔊 Generazione audio...[/dim]
cli-ai-voice-playing = [green]▶️  Riproduzione...[/green]
cli-ai-voice-saved = [dim]💾 Audio salvato: { $path }[/dim]
cli-ai-voice-next-hint = [dim]Premi INVIO per continuare, o CTRL+C per uscire...[/dim]
cli-ai-voice-error = [red]❌ Errore: { $error }[/red]
cli-ai-voice-goodbye = [cyan]👋 Chat vocale terminata![/cyan]

cli-ai-forecast-title = [bold cyan]📈 Previsione Cash Flow[/bold cyan]
cli-ai-forecast-checking = Verifica modelli ML...
cli-ai-forecast-no-models = [yellow]⚠ Modelli non addestrati. Uso --retrain per addestrare.[/yellow]
cli-ai-forecast-training = [cyan]🔧 Addestramento modelli ML...[/cyan]
cli-ai-forecast-min-data = [yellow]⚠ Dati insufficienti. Servono almeno { $min } fatture/pagamenti.[/yellow]
cli-ai-forecast-loading-data = Caricamento dati storico...
cli-ai-forecast-loaded = Caricate { $invoices } fatture e { $payments } pagamenti
cli-ai-forecast-training-prophet = Addestramento Prophet...
cli-ai-forecast-training-xgboost = Addestramento XGBoost...
cli-ai-forecast-saving = Salvataggio modelli...
cli-ai-forecast-trained = [green]✓ Modelli addestrati e salvati[/green]
cli-ai-forecast-generating = Generazione previsioni...
cli-ai-forecast-results-title = [bold green]📊 Previsione Cash Flow - Prossimi { $months } { $months ->
    [one] mese
   *[other] mesi
}[/bold green]
cli-ai-forecast-summary = [bold]Riepilogo:[/bold]
cli-ai-forecast-total-expected = Totale previsto: [green]€{ $amount }[/green]
cli-ai-forecast-avg-monthly = Media mensile: €{ $amount }
cli-ai-forecast-confidence = Confidenza: { $confidence }%
cli-ai-forecast-chart-title = [bold]Previsione Mensile:[/bold]
cli-ai-forecast-metrics-title = [bold]Metriche Modello:[/bold]
cli-ai-forecast-mae = • MAE: €{ $mae }
cli-ai-forecast-rmse = • RMSE: €{ $rmse }
cli-ai-forecast-r2 = • R²: { $r2 }
cli-ai-forecast-export-hint = [dim]Esporta con: openfatture ai forecast --export json[/dim]
cli-ai-forecast-error = [red]❌ Errore: { $error }[/red]

cli-ai-client-intel-title = [bold cyan]🔍 Analisi Intelligente Cliente[/bold cyan]
cli-ai-client-analyzing = Analisi cliente...
cli-ai-client-not-found = [red]Cliente { $id } non trovato[/red]
cli-ai-client-results-title = [bold green]📊 Profilo Cliente: { $name }[/bold green]
cli-ai-client-overview = [bold]Panoramica:[/bold]
cli-ai-client-invoices-count = • Fatture totali: { $count }
cli-ai-client-total-revenue = • Ricavi totali: €{ $amount }
cli-ai-client-avg-invoice = • Fattura media: €{ $amount }
cli-ai-client-payment-behavior = [bold]Comportamento Pagamenti:[/bold]
cli-ai-client-avg-delay = • Ritardo medio: { $days } giorni
cli-ai-client-on-time-rate = • Tasso puntualità: { $rate }%
cli-ai-client-risk-score = • Punteggio rischio: { $score }/10
cli-ai-client-insights = [bold]Insights:[/bold]
cli-ai-client-top-services = [bold]Servizi Principali:[/bold]
cli-ai-client-recommendations = [bold]Raccomandazioni:[/bold]
cli-ai-client-error = [red]❌ Errore: { $error }[/red]

cli-ai-invoice-analysis-title = [bold cyan]📄 Analisi Fattura AI[/bold cyan]
cli-ai-invoice-analyzing = Analisi fattura...
cli-ai-invoice-not-found = [red]Fattura { $id } non trovata[/red]
cli-ai-invoice-results-title = [bold green]📊 Analisi Fattura { $numero }/{ $anno }[/bold green]
cli-ai-invoice-summary = [bold]Riepilogo:[/bold]
cli-ai-invoice-client = • Cliente: { $client }
cli-ai-invoice-amount = • Importo: €{ $amount }
cli-ai-invoice-status = • Stato: { $status }
cli-ai-invoice-quality = [bold]Qualità Descrizioni:[/bold]
cli-ai-invoice-quality-score = • Punteggio: { $score }/10
cli-ai-invoice-compliance = [bold]Conformità:[/bold]
cli-ai-invoice-issues = [bold]Problemi Rilevati:[/bold]
cli-ai-invoice-suggestions = [bold]Suggerimenti:[/bold]
cli-ai-invoice-error = [red]❌ Errore: { $error }[/red]

cli-ai-compliance-title = [bold cyan]✅ Verifica Conformità Fattura[/bold cyan]
cli-ai-compliance-checking = Verifica conformità...
cli-ai-compliance-not-found = [red]Fattura { $id } non trovata[/red]
cli-ai-compliance-results-title = [bold]Risultati Verifica - Fattura { $numero }/{ $anno }[/bold]
cli-ai-compliance-all-passed = [bold green]✓ Tutti i controlli superati![/bold green]
cli-ai-compliance-issues-found = [yellow]⚠ Trovati { $count } problemi[/yellow]
cli-ai-compliance-errors = [bold red]Errori ({ $count }):[/bold red]
cli-ai-compliance-warnings = [bold yellow]Avvertimenti ({ $count }):[/bold yellow]
cli-ai-compliance-suggestions = [bold cyan]Suggerimenti ({ $count }):[/bold cyan]
cli-ai-compliance-auto-fixed = [green]✓ { $count } problemi corretti automaticamente[/green]
cli-ai-compliance-manual-action = [yellow]{ $count } problemi richiedono intervento manuale[/yellow]
cli-ai-compliance-error = [red]❌ Errore: { $error }[/red]

cli-ai-rag-title = [bold cyan]📚 RAG - Ricerca Documenti Fiscali[/bold cyan]
cli-ai-rag-query = Query: [yellow]{ $query }[/yellow]
cli-ai-rag-searching = Ricerca nella knowledge base...
cli-ai-rag-no-results = [yellow]Nessun risultato trovato[/yellow]
cli-ai-rag-results-title = [bold green]Risultati Trovati ({ $count }):[/bold green]
cli-ai-rag-result-item = [bold]{ $num }. { $title }[/bold] (similarità: { $score }%)
cli-ai-rag-source = Fonte: { $source }
cli-ai-rag-summary = Riepilogo: { $summary }
cli-ai-rag-error = [red]❌ Errore: { $error }[/red]

cli-ai-feedback-title = [bold cyan]⭐ Feedback Risposta AI[/bold cyan]
cli-ai-feedback-prompt = Come valuti questa risposta?
cli-ai-feedback-rating = Valutazione (1-5)
cli-ai-feedback-comment = Commento (opzionale)
cli-ai-feedback-thanks = [green]✓ Grazie per il feedback![/green]
cli-ai-feedback-saved = Feedback salvato (ID: { $id })
cli-ai-feedback-error = [red]❌ Errore: { $error }[/red]

## ============================================================================
## MAIN CLI - Aiuto Principale
## ============================================================================

cli-main-title = OpenFatture - Sistema di Fatturazione Elettronica Open Source
cli-main-description = Sistema completo per fatturazione elettronica italiana con integrazione SDI e AI
cli-main-version = Versione { $version }

### Command Groups
cli-main-group-invoices = 🧾 Gestione Fatture
cli-main-group-clients = 👥 Gestione Clienti
cli-main-group-products = 📦 Gestione Prodotti
cli-main-group-ai = 🤖 Assistente AI
cli-main-group-payments = 💰 Pagamenti e Riconciliazione
cli-main-group-batch = 📊 Operazioni Batch
cli-main-group-pec = 📧 PEC e SDI
cli-main-group-notifiche = 📬 Notifiche SDI
cli-main-group-preventivi = 📋 Preventivi
cli-main-group-lightning = ⚡ Lightning Network
cli-main-group-events = 📋 Eventi e Audit
cli-main-group-hooks = 🪝 Hooks e Automazione
cli-main-group-wizard = 🧙 Wizard Configurazione
cli-main-group-web = 🌐 Interfaccia Web
