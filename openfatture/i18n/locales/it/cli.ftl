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
cli-fattura-create-title = [bold blue]Crea Nuova Fattura[/bold blue]
cli-fattura-select-client-title = [bold cyan]Selezione Cliente[/bold cyan]
cli-fattura-no-clients-error = [red]Nessun cliente trovato. Aggiungine uno con 'cliente add'[/red]
cli-fattura-available-clients = [cyan]Clienti disponibili:[/cyan]
cli-fattura-client-prompt = Numero cliente
cli-fattura-client-selected = [green]Cliente: { $client_name }[/green]
cli-fattura-invalid-client-error = [red]Selezione cliente non valida[/red]

cli-fattura-add-lines-title = [bold cyan]Righe Fattura[/bold cyan]
cli-fattura-line-description-prompt = Descrizione (vuoto per terminare)
cli-fattura-line-quantity-prompt = Quantità
cli-fattura-line-unit-price-prompt = Prezzo unitario (€)
cli-fattura-line-vat-rate-prompt = Aliquota IVA (%)
cli-fattura-line-added = [green]Riga aggiunta: { $description } - € { $amount }[/green]

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
cli-fattura-created-success = [bold green]Fattura creata con successo![/bold green]
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
cli-fattura-xml-generation-title = [bold blue]Generazione XML FatturaPA[/bold blue]
cli-fattura-generating-xml = Generazione XML per fattura { $numero }/{ $anno }...
cli-fattura-xml-generation-error = [red]Errore: { $error }[/red]
cli-fattura-xml-schema-hint = [yellow]Suggerimento: Scarica lo schema XSD da:[/yellow]
cli-fattura-xml-schema-url = https://www.fatturapa.gov.it/export/documenti/fatturapa/v1.2.2/Schema_del_file_xml_FatturaPA_v1.2.2.xsd
cli-fattura-xml-schema-save-path = E salvalo in: { $path }
cli-fattura-xml-saved = [green]XML salvato in: { $path }[/green]
cli-fattura-xml-generated = [green]XML generato con successo![/green]
cli-fattura-xml-path = Percorso: { $path }
cli-fattura-xml-preview = [dim]Anteprima (primi 500 caratteri):[/dim]
cli-fattura-validate-success = [green]XML valido[/green]
cli-fattura-validate-error = [red]Errori di validazione trovati:[/red]
cli-fattura-send-title = [bold blue]Invio Fattura a SDI[/bold blue]
cli-fattura-send-step1-xml = [cyan]1. Generazione XML...[/cyan]
cli-fattura-send-step2-signature = [cyan]2. Firma digitale...[/cyan]
cli-fattura-send-step3-pec = [cyan]3. Invio via PEC con template email professionale...[/cyan]
cli-fattura-send-xml-failed = [red]Generazione XML fallita: { $error }[/red]
cli-fattura-send-xml-success = [green]XML generato[/green]
cli-fattura-send-signature-not-implemented = [yellow]Firma digitale non ancora implementata[/yellow]
cli-fattura-send-signature-manual-hint = [dim]Per ora, puoi firmare manualmente con strumenti esterni.[/dim]
cli-fattura-send-confirm = Inviare fattura a SDI ora?
cli-fattura-send-cancelled = [yellow]Annullato. Usa 'openfatture fattura invia' più tardi per inviare.[/yellow]
cli-fattura-sent-successfully = [green]Fattura inviata a SDI via PEC con template professionale[/green]
cli-fattura-sent-success-message = [bold green]Fattura { $numero }/{ $anno } inviata con successo![/bold green]
cli-fattura-sent-email-details = [dim]Email professionale inviata a SDI con:[/dim]
cli-fattura-sent-email-format = • Formato HTML + testo semplice
cli-fattura-sent-email-branding = • Branding aziendale ({ $color })
cli-fattura-sent-email-language = • Lingua: { $language }
cli-fattura-sent-notifications-header = [dim]Notifiche automatiche:[/dim]
cli-fattura-sent-notifications-enabled = • Le risposte SDI saranno inviate a: { $email }
cli-fattura-sent-notifications-process-cmd = • Elabora le notifiche con: [cyan]openfatture notifiche process <file>[/cyan]
cli-fattura-sent-notifications-disabled = • Abilita con: NOTIFICATION_EMAIL in .env
cli-fattura-sent-monitor-pec = [dim]Monitora la tua casella PEC per le notifiche SDI.[/dim]
cli-fattura-send-failed = [red]Invio fallito: { $error }[/red]
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
cli-fattura-delete-success = [green]Fattura { $numero }/{ $anno } eliminata[/green]
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
cli-cliente-added-success = [green]Cliente aggiunto con successo (ID: { $id })[/green]
cli-cliente-no-clients = [yellow]Nessun cliente trovato. Aggiungine uno con 'cliente add'[/yellow]
cli-cliente-not-found = [red]Cliente con ID { $id } non trovato[/red]
cli-cliente-has-invoices = [yellow]Attenzione: Questo cliente ha { $count } fatture[/yellow]
cli-cliente-cancelled = Annullato.
cli-cliente-deleted = [green]Cliente '{ $name }' eliminato[/green]

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

cli-cliente-column-id = ID
cli-cliente-column-name = Nome
cli-cliente-column-piva = P.IVA
cli-cliente-column-sdi-pec = SDI/PEC
cli-cliente-column-invoices = Fatture

cli-cliente-label-id = ID
cli-cliente-label-name = Nome
cli-cliente-label-piva = Partita IVA
cli-cliente-label-cf = Codice Fiscale
cli-cliente-label-address = Indirizzo
cli-cliente-label-sdi = Codice SDI
cli-cliente-label-pec = PEC
cli-cliente-label-email = Email
cli-cliente-label-phone = Telefono
cli-cliente-label-total-invoices = Fatture Totali
cli-cliente-label-created = Creato

cli-cliente-show-title = [bold blue]Dettagli Cliente: { $name }[/bold blue]
cli-cliente-prompt-civic-number = Numero civico (opzionale)
cli-cliente-prompt-pec-address = Indirizzo PEC (se SDI è 0000000)
cli-cliente-confirm-delete = Sei sicuro di voler eliminare?
cli-cliente-confirm-delete-client = Eliminare cliente '{ $name }'?

## ============================================================================
## Batch Commands - Operazioni Batch
## ============================================================================

### batch - Help Text
cli-batch-help-csv-file = Percorso al file CSV con le fatture
cli-batch-help-dry-run = Valida senza importare
cli-batch-help-send-summary = Invia riepilogo via email
cli-batch-help-output-file = Percorso file CSV di output
cli-batch-help-anno = Filtra per anno
cli-batch-help-stato = Filtra per stato
cli-batch-help-limit = Numero massimo di risultati

### batch - Console Output (import)
cli-batch-import-title = [bold blue]Importazione Batch Fatture[/bold blue]
cli-batch-file-not-found = [red]File non trovato: { $file }[/red]
cli-batch-file-info-name = [cyan]File:[/cyan] { $name }
cli-batch-file-info-size = [cyan]Dimensione:[/cyan] { $size } bytes
cli-batch-mode-dry-run = [cyan]Modalità:[/cyan] Dry run (solo validazione)
cli-batch-mode-import = [cyan]Modalità:[/cyan] Importazione
cli-batch-dry-run-warning = [yellow]Modalità dry run - nessun dato verrà salvato[/yellow]
cli-batch-warning-dry-run = [yellow]Modalità dry run - nessun dato verrà salvato[/yellow]

cli-batch-results-title = [bold]Risultati Importazione:[/bold]
cli-batch-metric-label = Metrica
cli-batch-metric-value = Valore
cli-batch-metric-total = Righe totali
cli-batch-metric-processed = Processate
cli-batch-metric-succeeded = Riuscite
cli-batch-metric-failed = Fallite
cli-batch-metric-success-rate = Tasso di successo
cli-batch-metric-duration = Durata

cli-batch-errors-title = [bold red]Errori:[/bold red]
cli-batch-errors-more = [dim]... e altri { $count } errori[/dim]

cli-batch-success-all = [bold green]Tutte le fatture importate con successo![/bold green]
cli-batch-warning-failed = [yellow]{ $count } fatture non importate[/yellow]

cli-batch-email-not-configured = [yellow]Email di notifica non configurata.[/yellow]
cli-batch-sending-email = [dim]Invio riepilogo email...[/dim]
cli-batch-email-sending = [dim]Invio riepilogo email...[/dim]
cli-batch-email-sent = [dim]Riepilogo inviato a { $email }[/dim]
cli-batch-email-failed = [yellow]Invio riepilogo fallito: { $error }[/yellow]

cli-batch-error-general = [red]Errore: { $error }[/red]

### batch - Console Output (export)
cli-batch-export-title = [bold blue]Esportazione Batch Fatture[/bold blue]
cli-batch-filter-year = [cyan]Filtro:[/cyan] Anno = { $anno }
cli-batch-filter-status = [cyan]Filtro:[/cyan] Stato = { $stato }
cli-batch-invalid-status = [red]Stato non valido: { $stato }[/red]
cli-batch-no-invoices = [yellow]Nessuna fattura trovata[/yellow]
cli-batch-invoices-count = [cyan]Fatture:[/cyan] { $count }

cli-batch-export-success = [bold green]Esportate { $count } fatture![/bold green]
cli-batch-export-file-path = [cyan]File:[/cyan] { $path }
cli-batch-export-file = [cyan]File:[/cyan] { $path }
cli-batch-export-file-size = [cyan]Dimensione:[/cyan] { $size } bytes
cli-batch-export-size = [cyan]Dimensione:[/cyan] { $size } bytes
cli-batch-export-failed = [red]Esportazione fallita[/red]

### batch - Console Output (history)
cli-batch-history-title = [bold blue]Storico Operazioni Batch[/bold blue]
cli-batch-history-not-implemented = [yellow]Tracciamento storico non ancora completamente implementato[/yellow]
cli-batch-history-future-features = [dim]In produzione, mostrerà:[/dim]
cli-batch-history-will-show = [dim]In produzione, mostrerà:[/dim]
cli-batch-history-feature-datetime = • Data/ora dell'operazione
cli-batch-history-feature-type = • Tipo (import/export)
cli-batch-history-feature-records = • Record processati
cli-batch-history-feature-counts = • Conteggi successo/fallimento
cli-batch-history-feature-errors = • Riepiloghi errori

cli-batch-history-example-title = [bold]Esempio storico:[/bold]
cli-batch-history-example = [bold]Esempio storico:[/bold]
cli-batch-history-column-date = Data
cli-batch-history-col-date = Data
cli-batch-history-column-type = Tipo
cli-batch-history-col-type = Tipo
cli-batch-history-column-records = Record
cli-batch-history-col-records = Record
cli-batch-history-column-success = Successo
cli-batch-history-col-success = Successo
cli-batch-history-column-failed = Falliti
cli-batch-history-col-failed = Falliti

cli-batch-history-todo = [dim]Da implementare: Aggiungere modello BatchOperation al database[/dim]

## ============================================================================
## Preventivo Commands - Gestione Preventivi
## ============================================================================

### preventivo - Help Text
cli-preventivo-help-cliente-id = ID Cliente
cli-preventivo-help-validita = Periodo di validità in giorni
cli-preventivo-help-stato = Filtra per stato
cli-preventivo-help-anno = Filtra per anno
cli-preventivo-help-cliente = Filtra per ID cliente
cli-preventivo-help-limit = Numero massimo di risultati
cli-preventivo-help-preventivo-id = ID Preventivo
cli-preventivo-help-force = Salta conferma
cli-preventivo-help-tipo-documento = Tipo documento fattura (TD01, TD06, ecc.)
cli-preventivo-help-new-stato = Nuovo stato (bozza, inviato, accettato, rifiutato, scaduto)

### preventivo - Console Output (crea)
cli-preventivo-create-title = [bold blue]Crea Nuovo Preventivo[/bold blue]
cli-preventivo-no-clients = [red]Nessun cliente trovato. Aggiungi prima un cliente con 'openfatture cliente add'[/red]
cli-preventivo-select-client = [cyan]Clienti disponibili:[/cyan]
cli-preventivo-client-id-prompt = Seleziona ID cliente
cli-preventivo-client-not-found = [red]Cliente { $id } non trovato[/red]
cli-preventivo-client-selected = [green]Cliente: { $name }[/green]
cli-preventivo-validity-info = [dim]Validità: { $days } giorni (scadenza: { $date })[/dim]

cli-preventivo-add-items-title = [bold]Aggiungi righe[/bold]
cli-preventivo-add-items-hint = [dim]Inserisci descrizione vuota per terminare[/dim]
cli-preventivo-item-description-prompt = Descrizione articolo { $num }
cli-preventivo-item-quantity-prompt = Quantità
cli-preventivo-item-price-prompt = Prezzo unitario (€)
cli-preventivo-item-vat-prompt = Aliquota IVA (%)
cli-preventivo-item-unit-prompt = Unità di misura
cli-preventivo-item-added = [green]Aggiunto: { $desc } - €{ $total }[/green]

cli-preventivo-no-items = [yellow]Nessuna riga aggiunta. Creazione preventivo annullata.[/yellow]
cli-preventivo-add-notes-prompt = Aggiungi note?
cli-preventivo-notes-prompt = Note
cli-preventivo-add-conditions-prompt = Aggiungi termini e condizioni?
cli-preventivo-conditions-prompt = Termini e condizioni

cli-preventivo-error-general = [red]Errore: { $error }[/red]
cli-preventivo-created-success = [bold green]Preventivo creato con successo![/bold green]
cli-preventivo-next-convert = [dim]Successivo: openfatture preventivo converti { $id } (per creare fattura)[/dim]

### preventivo - Console Output (lista)
cli-preventivo-invalid-status = [red]Stato non valido: { $stato }[/red]
cli-preventivo-valid-statuses = Valid: { $statuses }
cli-preventivo-no-preventivi = [yellow]Nessun preventivo trovato[/yellow]
cli-preventivo-list-title = Preventivi ({ $count })

cli-preventivo-column-id = ID
cli-preventivo-column-number = Numero
cli-preventivo-column-date = Data
cli-preventivo-column-expiration = Scadenza
cli-preventivo-column-client = Cliente
cli-preventivo-column-total = Totale
cli-preventivo-column-status = Stato

### preventivo - Console Output (show)
cli-preventivo-not-found = [red]Preventivo { $id } non trovato[/red]
cli-preventivo-show-title = [bold blue]Preventivo { $numero }/{ $anno }[/bold blue]

cli-preventivo-field-client = Cliente
cli-preventivo-field-issue-date = Data emissione
cli-preventivo-field-expiration = Data scadenza
cli-preventivo-field-validity = Validità
cli-preventivo-field-validity-days = { $days } giorni
cli-preventivo-field-status = Stato
cli-preventivo-warning-expired = [red]ATTENZIONE[/red]
cli-preventivo-expired = [red]Scaduto![/red]

cli-preventivo-line-items-title = [bold]Righe:[/bold]
cli-preventivo-line-item-number = #
cli-preventivo-line-item-description = Descrizione
cli-preventivo-line-item-quantity = Qtà
cli-preventivo-line-item-price = Prezzo
cli-preventivo-line-item-vat = IVA%
cli-preventivo-line-item-total = Totale

cli-preventivo-totals-title = [bold]Totali:[/bold]
cli-preventivo-total-imponibile = Imponibile
cli-preventivo-total-iva = IVA
cli-preventivo-total-total = [bold]TOTALE[/bold]

cli-preventivo-notes-title = [bold]Note:[/bold]
cli-preventivo-conditions-title = [bold]Termini e Condizioni:[/bold]

### preventivo - Console Output (delete)
cli-preventivo-confirm-delete = Eliminare preventivo { $numero }/{ $anno }?
cli-preventivo-cancelled = Annullato.
cli-preventivo-deleted = [green]Preventivo { $numero }/{ $anno } eliminato[/green]

### preventivo - Console Output (converti)
cli-preventivo-convert-title = [bold blue]Conversione Preventivo in Fattura[/bold blue]
cli-preventivo-convert-summary-numero = [cyan]Preventivo: { $numero }/{ $anno }[/cyan]
cli-preventivo-convert-summary-client = [cyan]Cliente: { $name }[/cyan]
cli-preventivo-convert-summary-total = [cyan]Totale: €{ $total }[/cyan]
cli-preventivo-invalid-doc-type = [red]Tipo documento non valido: { $tipo }[/red]
cli-preventivo-valid-doc-types = Validi: TD01, TD06, ecc.
cli-preventivo-confirm-convert = Convertire in fattura?
cli-preventivo-convert-cancelled = [yellow]Annullato.[/yellow]
cli-preventivo-converted-success = [bold green]Preventivo convertito con successo![/bold green]

cli-preventivo-invoice-title = Fattura { $numero }/{ $anno }
cli-preventivo-invoice-field-client = Cliente
cli-preventivo-invoice-field-date = Data
cli-preventivo-invoice-field-doc-type = Tipo documento
cli-preventivo-invoice-field-items = Righe
cli-preventivo-invoice-field-imponibile = Imponibile
cli-preventivo-invoice-field-iva = IVA
cli-preventivo-invoice-field-total = [bold]TOTALE[/bold]

cli-preventivo-invoice-id-info = [dim]ID Fattura: { $id }[/dim]
cli-preventivo-original-preventivo-info = [dim]Preventivo originale: { $numero }/{ $anno } (ID: { $id })[/dim]
cli-preventivo-next-send = [dim]Successivo: openfatture fattura invia { $id } --pec[/dim]

### preventivo - Console Output (aggiorna-stato)
cli-preventivo-status-updated = [green]Stato preventivo aggiornato: { $stato }[/green]

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
cli-ai-help-service-description = Descrizione del servizio da espandere
cli-ai-help-hours-worked = Ore lavorate
cli-ai-help-hourly-rate = Tariffa oraria (€)
cli-ai-help-project-name = Nome progetto
cli-ai-help-technologies = Tecnologie usate (separate da virgola)
cli-ai-help-json-output = Output in formato JSON
cli-ai-help-stream = Streaming risposta in tempo reale
cli-ai-help-client-pa = Cliente è Pubblica Amministrazione
cli-ai-help-client-foreign = Cliente estero (fuori Italia)
cli-ai-help-country-code = Codice paese cliente (IT, FR, DE, ecc.)
cli-ai-help-service-category = Categoria servizio
cli-ai-help-amount-eur = Importo in euro
cli-ai-help-ateco-code = Codice ATECO
cli-ai-help-chat-message = Messaggio da inviare alla chat

### Console Output - Comandi AI
cli-ai-describe-title = [bold cyan]Generazione Descrizione Fattura con AI[/bold cyan]
cli-ai-describe-activity = Attività: [yellow]{ $activity }[/yellow]
cli-ai-describe-generating = Generazione descrizione dettagliata...
cli-ai-describe-result-title = [bold green]Descrizione Generata:[/bold green]
cli-ai-describe-copy-hint = [dim]Copia questa descrizione quando crei una fattura[/dim]
cli-ai-describe-error = [red]Errore: { $error }[/red]
cli-ai-describe-input-service = Servizio
cli-ai-describe-input-hours = Ore lavorate
cli-ai-describe-input-rate = Tariffa oraria
cli-ai-describe-input-project = Progetto
cli-ai-describe-input-technologies = Tecnologie
cli-ai-describe-input-client-pa = Cliente PA
cli-ai-describe-input-client-foreign = Cliente estero
cli-ai-describe-input-country = Paese
cli-ai-describe-input-category = Categoria
cli-ai-describe-input-amount = Importo
cli-ai-describe-input-ateco = Codice ATECO

cli-ai-vat-title = [bold cyan]Suggerimento Aliquota IVA[/bold cyan]
cli-ai-vat-query = Query: [yellow]{ $query }[/yellow]
cli-ai-vat-analyzing = Analisi normativa IVA...
cli-ai-vat-result-title = [bold green]Raccomandazione IVA:[/bold green]
cli-ai-vat-disclaimer = [yellow]Questo è un suggerimento. Consulta sempre un commercialista.[/yellow]
cli-ai-vat-error = [red]Errore: { $error }[/red]
cli-ai-vat-processing = Elaborazione suggerimento IVA...
cli-ai-vat-input-service = Servizio
cli-ai-vat-input-client-pa = Cliente PA
cli-ai-vat-input-client-foreign = Cliente estero
cli-ai-vat-input-country = Paese
cli-ai-vat-input-category = Categoria
cli-ai-vat-input-amount = Importo
cli-ai-vat-input-ateco = Codice ATECO
cli-ai-vat-result-rate = Aliquota IVA raccomandata
cli-ai-vat-result-nature = Natura (se applicabile)
cli-ai-vat-result-reasoning = Motivazione
cli-ai-vat-result-legal-ref = Riferimento normativo
cli-ai-vat-result-confidence = Livello di confidenza
cli-ai-vat-result-warnings = Avvisi
cli-ai-vat-result-note = Nota aggiuntiva

cli-ai-chat-title = [bold cyan]Chat Assistente AI[/bold cyan]
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
cli-ai-chat-session-loaded = [green]Sessione caricata: { $session_id }[/green]
cli-ai-chat-session-saved = [dim]Sessione salvata: { $session_id }[/dim]
cli-ai-chat-thinking = [dim]Pensando...[/dim]
cli-ai-chat-error = [red]Errore: { $error }[/red]
cli-ai-chat-assistant-response = [bold cyan]Assistente:[/bold cyan]
cli-ai-chat-you = [bold green]Tu:[/bold green]
cli-ai-chat-instructions = Istruzioni: Fai domande su fatture, clienti, IVA o gestione fiscale
cli-ai-chat-invalid-session = [red]Sessione non trovata: { $session_id }[/red]
cli-ai-chat-no-sessions = [yellow]Nessuna sessione disponibile[/yellow]
cli-ai-chat-exported = [green]Conversazione esportata: { $path }[/green]
cli-ai-chat-export-error = [red]Errore esportazione: { $error }[/red]
cli-ai-chat-goodbye = [cyan]Alla prossima![/cyan]

### Metriche AI
cli-ai-metrics-provider = Provider
cli-ai-metrics-model = Modello
cli-ai-metrics-tokens = Token usati
cli-ai-metrics-cost = Costo stimato
cli-ai-metrics-latency = Latenza

### Errori generali AI
cli-ai-error-unknown = Errore sconosciuto durante l'esecuzione del comando AI
cli-ai-error-provider-init = Errore inizializzazione provider AI: { $error }
cli-ai-error-context-load = Errore caricamento contesto business: { $error }

cli-ai-voice-title = [bold cyan]Chat Vocale AI[/bold cyan]
cli-ai-voice-welcome = Chat vocale con OpenFatture AI
cli-ai-voice-recording = [yellow]Registrazione in corso... ({ $duration }s)[/yellow]
cli-ai-voice-press-enter = [cyan]Premi INVIO quando pronto...[/cyan]
cli-ai-voice-processing = [dim]Elaborazione audio...[/dim]
cli-ai-voice-transcribing = [dim]Trascrizione...[/dim]
cli-ai-voice-you-said = [green]Tu:[/green] { $text }
cli-ai-voice-detected-language = [dim]Lingua rilevata: { $language }[/dim]
cli-ai-voice-thinking = [dim]Elaborazione risposta...[/dim]
cli-ai-voice-ai-response = [cyan]AI:[/cyan] { $response }
cli-ai-voice-generating-audio = [dim]Generazione audio...[/dim]
cli-ai-voice-playing = [green]▶Riproduzione...[/green]
cli-ai-voice-saved = [dim]Audio salvato: { $path }[/dim]
cli-ai-voice-next-hint = [dim]Premi INVIO per continuare, o CTRL+C per uscire...[/dim]
cli-ai-voice-error = [red]Errore: { $error }[/red]
cli-ai-voice-goodbye = [cyan]Chat vocale terminata![/cyan]

cli-ai-forecast-title = [bold cyan]Previsione Cash Flow[/bold cyan]
cli-ai-forecast-checking = Verifica modelli ML...
cli-ai-forecast-no-models = [yellow]Modelli non addestrati. Uso --retrain per addestrare.[/yellow]
cli-ai-forecast-training = [cyan]Addestramento modelli ML...[/cyan]
cli-ai-forecast-min-data = [yellow]Dati insufficienti. Servono almeno { $min } fatture/pagamenti.[/yellow]
cli-ai-forecast-loading-data = Caricamento dati storico...
cli-ai-forecast-loaded = Caricate { $invoices } fatture e { $payments } pagamenti
cli-ai-forecast-training-prophet = Addestramento Prophet...
cli-ai-forecast-training-xgboost = Addestramento XGBoost...
cli-ai-forecast-saving = Salvataggio modelli...
cli-ai-forecast-trained = [green]Modelli addestrati e salvati[/green]
cli-ai-forecast-generating = Generazione previsioni...
cli-ai-forecast-results-title = [bold green]Previsione Cash Flow - Prossimi { $months } { $months ->
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
cli-ai-forecast-error = [red]Errore: { $error }[/red]

cli-ai-client-intel-title = [bold cyan]Analisi Intelligente Cliente[/bold cyan]
cli-ai-client-analyzing = Analisi cliente...
cli-ai-client-not-found = [red]Cliente { $id } non trovato[/red]
cli-ai-client-results-title = [bold green]Profilo Cliente: { $name }[/bold green]
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
cli-ai-client-error = [red]Errore: { $error }[/red]

cli-ai-invoice-analysis-title = [bold cyan]Analisi Fattura AI[/bold cyan]
cli-ai-invoice-analyzing = Analisi fattura...
cli-ai-invoice-not-found = [red]Fattura { $id } non trovata[/red]
cli-ai-invoice-results-title = [bold green]Analisi Fattura { $numero }/{ $anno }[/bold green]
cli-ai-invoice-summary = [bold]Riepilogo:[/bold]
cli-ai-invoice-client = • Cliente: { $client }
cli-ai-invoice-amount = • Importo: €{ $amount }
cli-ai-invoice-status = • Stato: { $status }
cli-ai-invoice-quality = [bold]Qualità Descrizioni:[/bold]
cli-ai-invoice-quality-score = • Punteggio: { $score }/10
cli-ai-invoice-compliance = [bold]Conformità:[/bold]
cli-ai-invoice-issues = [bold]Problemi Rilevati:[/bold]
cli-ai-invoice-suggestions = [bold]Suggerimenti:[/bold]
cli-ai-invoice-error = [red]Errore: { $error }[/red]

cli-ai-compliance-title = [bold cyan]Verifica Conformità Fattura[/bold cyan]
cli-ai-compliance-checking = Verifica conformità...
cli-ai-compliance-not-found = [red]Fattura { $id } non trovata[/red]
cli-ai-compliance-results-title = [bold]Risultati Verifica - Fattura { $numero }/{ $anno }[/bold]
cli-ai-compliance-all-passed = [bold green]Tutti i controlli superati![/bold green]
cli-ai-compliance-issues-found = [yellow]Trovati { $count } problemi[/yellow]
cli-ai-compliance-errors = [bold red]Errori ({ $count }):[/bold red]
cli-ai-compliance-warnings = [bold yellow]Avvertimenti ({ $count }):[/bold yellow]
cli-ai-compliance-suggestions = [bold cyan]Suggerimenti ({ $count }):[/bold cyan]
cli-ai-compliance-auto-fixed = [green]{ $count } problemi corretti automaticamente[/green]
cli-ai-compliance-manual-action = [yellow]{ $count } problemi richiedono intervento manuale[/yellow]
cli-ai-compliance-error = [red]Errore: { $error }[/red]

cli-ai-rag-title = [bold cyan]RAG - Ricerca Documenti Fiscali[/bold cyan]
cli-ai-rag-query = Query: [yellow]{ $query }[/yellow]
cli-ai-rag-searching = Ricerca nella knowledge base...
cli-ai-rag-no-results = [yellow]Nessun risultato trovato[/yellow]
cli-ai-rag-results-title = [bold green]Risultati Trovati ({ $count }):[/bold green]
cli-ai-rag-result-item = [bold]{ $num }. { $title }[/bold] (similarità: { $score }%)
cli-ai-rag-source = Fonte: { $source }
cli-ai-rag-summary = Riepilogo: { $summary }
cli-ai-rag-error = [red]Errore: { $error }[/red]

cli-ai-feedback-title = [bold cyan]Feedback Risposta AI[/bold cyan]
cli-ai-feedback-prompt = Come valuti questa risposta?
cli-ai-feedback-rating = Valutazione (1-5)
cli-ai-feedback-comment = Commento (opzionale)
cli-ai-feedback-thanks = [green]Grazie per il feedback![/green]
cli-ai-feedback-saved = Feedback salvato (ID: { $id })
cli-ai-feedback-error = [red]Errore: { $error }[/red]

## ============================================================================
## EVENTS Commands - Cronologia Eventi e Audit Trail
## ============================================================================

### Help Texts - Comandi e Opzioni
cli-events-help = Visualizza e analizza cronologia eventi

# list command
cli-events-list-help-type = Filtra per tipo evento
cli-events-list-help-entity = Filtra per tipo entità (fattura, cliente, pagamento, etc.)
cli-events-list-help-entity-id = Filtra per ID entità
cli-events-list-help-last-hours = Mostra eventi dalle ultime N ore
cli-events-list-help-last-days = Mostra eventi dagli ultimi N giorni
cli-events-list-help-limit = Numero massimo di eventi da mostrare

# show command
cli-events-show-help-event-id = ID Evento (UUID)

# stats command
cli-events-stats-help-last-hours = Statistiche ultime N ore
cli-events-stats-help-last-days = Statistiche ultimi N giorni

# timeline command
cli-events-timeline-help-entity-type = Tipo entità (invoice, client, etc.)
cli-events-timeline-help-entity-id = ID Entità

# search command
cli-events-search-help-query = Stringa di ricerca
cli-events-search-help-limit = Numero massimo di risultati

# dashboard command
cli-events-dashboard-help-days = Numero di giorni da analizzare

# trends command
cli-events-trends-help-days = Numero di giorni da analizzare
cli-events-trends-help-type = Filtra per tipo evento

### Table Columns - Intestazioni Colonne
cli-events-column-timestamp = Data/Ora
cli-events-column-event-type = Tipo Evento
cli-events-column-entity = Entità
cli-events-column-entity-type = Tipo Entità
cli-events-column-summary = Riepilogo
cli-events-column-count = Conteggio
cli-events-column-percentage = Percentuale
cli-events-column-match = Corrispondenza

### Titles and Headers - Titoli e Intestazioni
cli-events-list-title = Cronologia Eventi ({ $count } eventi)
cli-events-show-panel-title = [bold]Dettagli Evento: { $event_type }[/bold]
cli-events-stats-table-by-type = Eventi per Tipo
cli-events-stats-table-by-entity = Eventi per Tipo Entità
cli-events-stats-panel-title = [bold]Statistiche Eventi - { $range }[/bold]
cli-events-timeline-panel-title = [bold]Cronologia Eventi: { $entity_type } #{ $entity_id }[/bold]
cli-events-search-results-title = Risultati Ricerca: '{ $query }' ({ $count } eventi)
cli-events-types-table-title = Tipi di Evento Disponibili
cli-events-dashboard-panel-title = [bold]Dashboard Analisi Eventi - Ultimi { $days } Giorni[/bold]
cli-events-dashboard-table-entity-activity = Attività per Entità
cli-events-trends-panel-title = [bold]Tendenze Eventi - Ultimi { $days } Giorni[/bold]
cli-events-trends-panel-title-filtered = [bold]Tendenze Eventi - Ultimi { $days } Giorni ({ $event_type })[/bold]

### Labels - Etichette Campi
cli-events-show-label-event-id = ID Evento
cli-events-show-label-event-type = Tipo Evento
cli-events-show-label-occurred-at = Avvenuto il
cli-events-show-label-published-at = Pubblicato il
cli-events-show-label-entity-type = Tipo Entità
cli-events-show-label-entity-id = ID Entità
cli-events-show-label-user-id = ID Utente
cli-events-show-label-event-data = Dati Evento
cli-events-show-label-metadata = Metadati

### Dashboard Metrics - Metriche Dashboard
cli-events-dashboard-metric-total = Eventi Totali
cli-events-dashboard-metric-types = Tipi di Evento
cli-events-dashboard-metric-velocity = Eventi/Ora (24h)
cli-events-dashboard-metric-trend = Tendenza
cli-events-dashboard-section-top-types = [bold]Tipi di Evento Principali[/bold]
cli-events-dashboard-column-events = Eventi

### Messages - Messaggi Output
cli-events-no-events = [yellow]Nessun evento trovato corrispondente ai criteri[/yellow]
cli-events-show-not-found = [red]Evento con ID '{ $event_id }' non trovato[/red]
cli-events-filters-applied =
    [dim]Filtri: { $filters }[/dim]
cli-events-stats-all-time = Tutto il Periodo
cli-events-stats-last-hours = Ultime { $hours } ore
cli-events-stats-last-days = Ultimi { $days } giorni
cli-events-stats-total =
    [bold]Eventi Totali:[/bold] { $total }

cli-events-stats-most-recent = [bold]Evento Più Recente:[/bold] { $event_type } il { $timestamp }
cli-events-stats-oldest = [bold]Evento Più Vecchio:[/bold] { $event_type } il { $timestamp }
cli-events-timeline-no-events = [yellow]Nessun evento trovato per { $entity_type } con ID { $entity_id }[/yellow]
cli-events-timeline-total =
    [dim]Totale eventi: { $total }[/dim]
cli-events-search-no-results = [yellow]Nessun evento trovato corrispondente a '{ $query }'[/yellow]
cli-events-types-no-events = [yellow]Nessun evento registrato ancora[/yellow]
cli-events-dashboard-most-recent = [dim]Più Recente: { $event_type } il { $timestamp }[/dim]
cli-events-trends-no-events = [yellow]Nessun evento trovato per il periodo specificato[/yellow]
cli-events-trends-summary = [dim]Totale: { $total } eventi | Media: { $avg } eventi/giorno[/dim]

## ============================================================================
## MAIN CLI - Aiuto Principale
## ============================================================================

cli-main-title = OpenFatture - Sistema di Fatturazione Elettronica Open Source
cli-main-description = Sistema completo per fatturazione elettronica italiana con integrazione SDI e AI
cli-main-version = Versione { $version }

### Command Groups
cli-main-group-invoices = Gestione Fatture
cli-main-group-clients = Gestione Clienti
cli-main-group-products = Gestione Prodotti
cli-main-group-ai = Assistente AI
cli-main-group-payments = Pagamenti e Riconciliazione
cli-main-group-batch = Operazioni Batch
cli-main-group-pec = PEC e SDI
cli-main-group-notifiche = Notifiche SDI
cli-main-group-preventivi = Preventivi
cli-main-group-lightning = Lightning Network
cli-main-group-events = Eventi e Audit
cli-main-group-hooks = Hooks e Automazione
cli-main-group-wizard = Wizard Configurazione
cli-main-group-web = Interfaccia Web

## ============================================================================
## LIGHTNING Commands - Lightning Network e Compliance
## ============================================================================

### Help Texts - Comandi e Opzioni
cli-lightning-help = Gestione pagamenti Lightning Network
cli-lightning-report-help = Genera report di compliance
cli-lightning-aml-help = Gestione Anti-Riciclaggio

### Status Command
cli-lightning-status-title = Stato Lightning Network
cli-lightning-status-disabled = Stato: Disabilitato
cli-lightning-status-disabled-hint-env = Imposta lightning_enabled=true in .env per abilitare i pagamenti Lightning
cli-lightning-status-disabled-hint-cmd = Usa 'openfatture config set lightning_enabled true' per abilitare
cli-lightning-status-enabled = Stato: Abilitato
cli-lightning-status-host = Host: { $host }
cli-lightning-status-timeout = Timeout: { $timeout }s
cli-lightning-status-max-retries = Max tentativi: { $max_retries }
cli-lightning-status-btc-provider = Provider BTC: { $provider }
cli-lightning-status-liquidity = Monitoraggio liquidità: { $status }

cli-lightning-btc-provider-coingecko = CoinGecko
cli-lightning-btc-provider-cmc = CoinMarketCap
cli-lightning-btc-provider-fallback = Fallback
cli-lightning-liquidity-enabled = Abilitato
cli-lightning-liquidity-disabled = Disabilitato

### Invoice Command
cli-lightning-disabled-error = Lightning è disabilitato. Abilita con: openfatture config set lightning_enabled true
cli-lightning-invoice-title = Creazione Fattura Lightning
cli-lightning-invoice-not-available = Funzionalità non ancora disponibile - Integrazione Lightning in sviluppo

### Channels Command
cli-lightning-channels-title = Canali Lightning
cli-lightning-channels-not-available = Nessun canale configurato - Integrazione Lightning in sviluppo

### Liquidity Command
cli-lightning-liquidity-title = Liquidità Canali
cli-lightning-liquidity-not-available = Monitoraggio liquidità non disponibile - Integrazione Lightning in sviluppo

### Compliance Check Command
cli-lightning-compliance-opt-tax-year = Anno fiscale da verificare (predefinito: anno corrente)
cli-lightning-compliance-opt-verbose = Mostra informazioni dettagliate

cli-lightning-compliance-title =

    [bold cyan]Controllo Compliance Lightning - { $year }[/bold cyan]

cli-lightning-compliance-summary-title = [bold]Riepilogo Anno Fiscale[/bold]
cli-lightning-compliance-summary-payments = Numero di pagamenti:
cli-lightning-compliance-summary-revenue = Ricavi totali (EUR):
cli-lightning-compliance-summary-gains = Plusvalenze totali (EUR):
cli-lightning-compliance-summary-tax = Tasse stimate (EUR):

cli-lightning-compliance-aml-title = [bold]Compliance Anti-Riciclaggio (Soglia: 5.000 EUR)[/bold]
cli-lightning-compliance-aml-total = Totale sopra soglia:
cli-lightning-compliance-aml-verified = Verificati:
cli-lightning-compliance-aml-unverified = Non verificati:
cli-lightning-compliance-aml-status-ok = OK
cli-lightning-compliance-aml-status-require = { $count } RICHIEDONO VERIFICA

cli-lightning-compliance-quadro-title = [bold]Dichiarazione Quadro RW (Obbligatoria dal 2025)[/bold]
cli-lightning-compliance-quadro-count = Fatture da dichiarare:
cli-lightning-compliance-action-required = Azione richiesta:
cli-lightning-compliance-quadro-action = [yellow]Dichiarare tutti i possessi crypto nel Quadro RW[/yellow]
cli-lightning-compliance-status = Stato:
cli-lightning-compliance-quadro-status-ok = [green]Nessuna dichiarazione richiesta[/green]

cli-lightning-compliance-data-quality-title = [bold]Qualità Dati[/bold]
cli-lightning-compliance-data-quality-missing = Fatture con dati fiscali mancanti:
cli-lightning-compliance-data-quality-action = [red]Aggiungere tasso BTC/EUR e importo EUR per conformità fiscale[/red]
cli-lightning-compliance-data-quality-status-ok = [green]Tutte le fatture saldate hanno dati fiscali[/green]

cli-lightning-compliance-issue-aml = { $count } pagamento(i) AML non verificato(i)
cli-lightning-compliance-issue-missing-data = { $count } fattura(e) senza dati fiscali
cli-lightning-compliance-issues-found = [bold red]Problemi di Compliance Rilevati: { $issues }[/bold red]

cli-lightning-compliance-passed = [bold green]Tutti i Controlli di Compliance Superati[/bold green]

cli-lightning-compliance-verbose-title = [bold]Pagamenti AML Non Verificati:[/bold]
cli-lightning-compliance-verbose-item =   • { $hash }... - { $amount } EUR - Saldato: { $date }

cli-lightning-compliance-error = [bold red]Errore durante il controllo compliance: { $error }[/bold red]

### Report Commands - Common Options
cli-lightning-report-opt-tax-year = Anno fiscale per il report
cli-lightning-report-opt-format = Formato output: json o csv
cli-lightning-report-opt-output = Percorso file di output (opzionale, stampa su stdout se non fornito)

cli-lightning-report-invalid-format = [bold red]Formato non valido. Usa 'json' o 'csv'[/bold red]
cli-lightning-report-saved = [green]Report salvato in: { $path }[/green]

cli-lightning-report-summary = [cyan]Totale fatture nel report: { $count }[/cyan]

### Quadro RW Report
cli-lightning-report-quadro-title =

    [bold cyan]Generazione Report Quadro RW - { $year } ({ $format })[/bold cyan]

cli-lightning-report-quadro-error = [bold red]Errore nella generazione del report Quadro RW: { $error }[/bold red]

### Capital Gains Report
cli-lightning-report-gains-title =

    [bold cyan]Generazione Report Plusvalenze - { $year } ({ $format })[/bold cyan]

cli-lightning-report-gains-summary-count = [cyan]Totale fatture con plusvalenze: { $count }[/cyan]
cli-lightning-report-gains-summary-total = [yellow]Plusvalenze totali: { $total } EUR[/yellow]
cli-lightning-report-gains-summary-tax = [red]Tasse stimate ({ $rate }%): { $tax } EUR[/red]
cli-lightning-report-gains-error = [bold red]Errore nella generazione del report plusvalenze: { $error }[/bold red]

### AML Report
cli-lightning-aml-opt-threshold = Soglia AML in EUR
cli-lightning-aml-opt-format = Formato output: solo json
cli-lightning-aml-opt-verbose = Mostra informazioni dettagliate

cli-lightning-aml-report-title =

    [bold cyan]Generazione Report Compliance Anti-Riciclaggio (Soglia: { $threshold } EUR)[/bold cyan]

cli-lightning-aml-report-summary-total = [cyan]Totale sopra soglia: { $total }[/cyan]
cli-lightning-aml-report-summary-verified = [green]Verificati: { $verified }[/green]
cli-lightning-aml-report-summary-unverified-ok = Non verificati: 0
cli-lightning-aml-report-summary-unverified-warning = Non verificati: { $count }
cli-lightning-aml-report-summary-rate = [yellow]Tasso di conformità: { $rate }%[/yellow]

cli-lightning-aml-report-action-required =

    [bold yellow]Azione Richiesta: Verificare i pagamenti non verificati con il processo AML[/bold yellow]
cli-lightning-aml-report-action-hint = [dim]Usa: openfatture lightning aml list-unverified per vedere i dettagli[/dim]

cli-lightning-aml-report-error = [bold red]Errore nella generazione del report AML: { $error }[/bold red]

### AML List Unverified Command
cli-lightning-aml-list-title =

    [bold cyan]Pagamenti AML Non Verificati (Soglia: { $threshold } EUR)[/bold cyan]

cli-lightning-aml-list-empty = [green]Nessun pagamento non verificato trovato[/green]

cli-lightning-aml-list-table-title = Pagamenti Non Verificati ({ $count } totali)
cli-lightning-aml-list-col-hash = Hash Pagamento
cli-lightning-aml-list-col-amount = Importo (EUR)
cli-lightning-aml-list-col-settled = Saldato Il
cli-lightning-aml-list-col-fattura = ID Fattura
cli-lightning-aml-list-col-client = ID Cliente
cli-lightning-aml-list-col-description = Descrizione

cli-lightning-aml-list-action-required = [bold yellow]Azione Richiesta: Questi pagamenti richiedono la verifica dell'identità del cliente[/bold yellow]
cli-lightning-aml-list-action-hint = [dim]Usa: openfatture lightning aml verify <payment-hash> --verified-by <email>[/dim]

cli-lightning-aml-list-error = [bold red]Errore nell'elenco dei pagamenti non verificati: { $error }[/bold red]

### AML Verify Command
cli-lightning-aml-verify-arg-hash = Hash del pagamento da verificare
cli-lightning-aml-verify-opt-by = Email della persona che verifica
cli-lightning-aml-verify-opt-notes = Note di verifica (opzionale)
cli-lightning-aml-verify-opt-client = ID Cliente (opzionale)

cli-lightning-aml-verify-title =

    [bold cyan]Verifica Pagamento AML: { $hash }...[/bold cyan]

cli-lightning-aml-verify-not-found = [bold red]Fattura non trovata: { $hash }[/bold red]
cli-lightning-aml-verify-already-verified = [yellow]Pagamento già verificato il { $date }[/yellow]
cli-lightning-aml-verify-below-threshold = [yellow]Il pagamento non supera la soglia AML, ma viene comunque contrassegnato come verificato[/yellow]
cli-lightning-aml-verify-success = [green]Pagamento verificato con successo[/green]

cli-lightning-aml-verify-label-hash = Hash Pagamento:
cli-lightning-aml-verify-label-amount = Importo (EUR):
cli-lightning-aml-verify-label-settled = Saldato Il:
cli-lightning-aml-verify-label-by = Verificato Da:
cli-lightning-aml-verify-label-at = Verificato Il:
cli-lightning-aml-verify-label-notes = Note:

cli-lightning-aml-verify-error = [bold red]Errore nella verifica del pagamento: { $error }[/bold red]

## ============================================================================
## REPORT Commands - Report e Statistiche
## ============================================================================

### Help Texts - Comandi e Opzioni
cli-report-iva-help-anno = Anno
cli-report-iva-help-trimestre = Trimestre (Q1-Q4)
cli-report-clienti-help-anno = Anno
cli-report-scadenze-help-finestra = Numero di giorni considerati "in scadenza" (default: 14)

### Titles and Headers - IVA Report
cli-report-iva-title =

    [bold blue]Report IVA - { $anno }[/bold blue]

cli-report-iva-quarter =

    [cyan]Trimestre: { $trimestre } ({ $mese_inizio }-{ $mese_fine })[/cyan]

cli-report-iva-full-year =

    [cyan]Anno completo[/cyan]

cli-report-iva-summary-title = Riepilogo IVA
cli-report-iva-breakdown-title =

    [bold]Dettaglio per Aliquota IVA:[/bold]

### Titles and Headers - Clienti Report
cli-report-clienti-title =

    [bold blue]Report Fatturato Clienti - { $anno }[/bold blue]

cli-report-clienti-table-title = Top Clienti - { $anno }

### Titles and Headers - Scadenze Report
cli-report-scadenze-title =

    [bold blue]Panoramica Scadenze Pagamenti[/bold blue]

### Table Columns - IVA Report
cli-report-iva-column-metric = Metrica
cli-report-iva-column-amount = Importo
cli-report-iva-column-vat-rate = Aliquota IVA
cli-report-iva-column-imponibile = Imponibile
cli-report-iva-column-vat = IVA

### Table Columns - Clienti Report
cli-report-clienti-column-rank = Pos.
cli-report-clienti-column-client = Cliente
cli-report-clienti-column-invoices = Fatture
cli-report-clienti-column-revenue = Fatturato

### Table Columns - Scadenze Report
cli-report-scadenze-column-invoice = Fattura
cli-report-scadenze-column-client = Cliente
cli-report-scadenze-column-due-date = Scadenza
cli-report-scadenze-column-days-delta = Δ giorni
cli-report-scadenze-column-residual = Residuo
cli-report-scadenze-column-paid = Pagato
cli-report-scadenze-column-total = Totale
cli-report-scadenze-column-status = Stato

### Labels - IVA Report
cli-report-iva-label-num-invoices = Numero di fatture
cli-report-iva-label-imponibile = Totale imponibile
cli-report-iva-label-total-vat = Totale IVA
cli-report-iva-label-total-revenue-bold = [bold]Totale fatturato[/bold]

### Messages - General
cli-report-no-invoices = [yellow]Nessuna fattura trovata per il periodo selezionato[/yellow]
cli-report-no-invoices-year = [yellow]Nessuna fattura trovata per l'anno selezionato[/yellow]

### Messages - IVA Report
cli-report-iva-error-invalid-quarter = [red]Trimestre non valido. Usa Q1, Q2, Q3 o Q4[/red]

### Messages - Clienti Report
cli-report-clienti-total-revenue =

    [bold]Fatturato totale: { $totale }[/bold]

### Messages - Scadenze Report
cli-report-scadenze-no-outstanding =

    [green]Nessun pagamento in sospeso. Tutte le fatture sono state saldate![/green]

cli-report-scadenze-hidden-upcoming =

    [dim]… { $count } ulteriori pagamenti futuri non mostrati. Usa --finestra o esporta dati dal modulo payment per maggiori dettagli.[/dim]

cli-report-scadenze-total-outstanding =

    [bold]Totale residuo complessivo: { $totale }[/bold]

### Section Titles - Scadenze Report
cli-report-scadenze-section-overdue = [red]Scaduti[/red]
cli-report-scadenze-section-due-soon = [yellow]In scadenza (<= { $finestra } giorni)[/yellow]
cli-report-scadenze-section-upcoming = [cyan]Prossimi pagamenti[/cyan]

cli-report-scadenze-section-total = [bold { $color }]Totale residuo: { $totale } • Pagamenti: { $count }[/]

### Payment Status Labels - Scadenze Report
cli-report-scadenze-status-overdue = Scaduto
cli-report-scadenze-status-partial = Parziale
cli-report-scadenze-status-due = Da pagare

## ============================================================================
## PEC Commands - Test e Configurazione PEC
## ============================================================================

### Titles
cli-pec-test-title = [bold blue]Test Configurazione PEC[/bold blue]
cli-pec-info-title = [bold blue]Configurazione PEC[/bold blue]

### Labels
cli-pec-label-address = [cyan]Indirizzo PEC:[/cyan]
cli-pec-label-smtp-server = [cyan]Server SMTP:[/cyan]
cli-pec-label-smtp-port = [cyan]Porta SMTP:[/cyan]
cli-pec-label-template = [cyan]Template:[/cyan] test/test_email.html + .txt
cli-pec-label-locale = [cyan]Lingua:[/cyan]
cli-pec-label-password = Password
cli-pec-label-sdi-pec = PEC SDI

### Table Headers
cli-pec-table-setting = Impostazione
cli-pec-table-value = Valore

### Error Messages
cli-pec-error-no-address = [red]Indirizzo PEC non configurato[/red]
cli-pec-error-no-address-hint = Esegui: [cyan]openfatture init[/cyan] per configurare
cli-pec-error-no-password = [red]Password PEC non configurata[/red]
cli-pec-error-no-password-hint = Impostala nel file .env: PEC_PASSWORD=la_tua_password

### Test Messages
cli-pec-sending-test = Invio email di test con template professionale...
cli-pec-test-success = [bold green]Email di test inviata con successo![/bold green]
cli-pec-test-check-inbox = Controlla la tua casella PEC: { $pec_address }
cli-pec-test-email-includes = [dim]L'email include:[/dim]
cli-pec-test-feature-html = • HTML professionale + testo semplice
cli-pec-test-feature-branding = • Branding aziendale
cli-pec-test-feature-language = • Lingua: { $language }
cli-pec-test-more-testing = [dim]Per ulteriori test email:[/dim]
cli-pec-test-cmd-email-test = [cyan]openfatture email test[/cyan]  - Test email completo
cli-pec-test-cmd-email-preview = [cyan]openfatture email preview[/cyan] - Anteprima template

cli-pec-test-failed =
    [red]Test fallito: { $error }[/red]
cli-pec-test-common-issues = [yellow]Problemi comuni:[/yellow]
cli-pec-issue-credentials = • Credenziali PEC errate
cli-pec-issue-smtp = • Server SMTP non corretto
cli-pec-issue-firewall = • Firewall che blocca porta 465
cli-pec-issue-mailbox = • Casella PEC piena

### Info Messages
cli-pec-not-set = [red]Non impostato[/red]
cli-pec-password-set = [green]Impostata[/green]

## ============================================================================
## NOTIFICHE Commands - Gestione Notifiche SDI
## ============================================================================

### Help Text
cli-notifiche-help-file-path = Percorso al file XML di notifica SDI
cli-notifiche-help-no-email = Salta notifica email automatica
cli-notifiche-help-tipo = Filtra per tipo (AT, RC, NS, MC, NE)
cli-notifiche-help-limit = Numero massimo di risultati
cli-notifiche-help-notification-id = ID Notifica

### Titles
cli-notifiche-process-title = [bold blue]Elaborazione Notifica SDI[/bold blue]
cli-notifiche-list-title = [bold blue]Notifiche SDI[/bold blue]
cli-notifiche-show-title = [bold blue]{ $emoji } Notifica { $id }: { $tipo }[/bold blue]

### Table Headers
cli-notifiche-table-field = Campo
cli-notifiche-table-value = Valore
cli-notifiche-column-id = ID
cli-notifiche-column-type = Tipo
cli-notifiche-column-date = Data
cli-notifiche-column-invoice = Fattura
cli-notifiche-column-client = Cliente
cli-notifiche-column-sdi-id = ID SDI

### Labels
cli-notifiche-label-type = Tipo
cli-notifiche-label-sdi-id = ID SDI
cli-notifiche-label-file = File
cli-notifiche-label-date = Data
cli-notifiche-label-message = Messaggio
cli-notifiche-label-errors = Errori
cli-notifiche-label-invoice = Fattura
cli-notifiche-label-client = Cliente
cli-notifiche-label-invoice-status = Stato Fattura
cli-notifiche-label-received = Ricevuto
cli-notifiche-label-description = Descrizione
cli-notifiche-label-xml-path = Percorso XML

### Messages
cli-notifiche-file-not-found = [red]File non trovato: { $file_path }[/red]
cli-notifiche-file-label = [cyan]File:[/cyan] { $name }
cli-notifiche-size-label = [cyan]Dimensione:[/cyan] { $size } bytes
cli-notifiche-auto-email-enabled =
    [dim]Email automatica abilitata { $email }[/dim]

cli-notifiche-processing = Elaborazione notifica...
cli-notifiche-error =
    [red]Errore: { $error }[/red]
cli-notifiche-success = [bold green]Notifica elaborata con successo![/bold green]
cli-notifiche-errors-count = { $count } errore(i)
cli-notifiche-email-sent =
    [dim]Notifica email inviata a { $email }[/dim]

cli-notifiche-no-notifications = [yellow]Nessuna notifica trovata[/yellow]
cli-notifiche-process-hint = [dim]Elabora notifiche con:[/dim]
cli-notifiche-process-cmd = [cyan]openfatture notifiche process <file.xml>[/cyan]
cli-notifiche-list-table-title = Notifiche ({ $count })

cli-notifiche-not-found = [red]Notifica { $notification_id } non trovata[/red]

## ============================================================================
## CONFIG Commands - Gestione Configurazione
## ============================================================================

### Help Text
cli-config-help-key = Chiave configurazione (es. pec.address)
cli-config-help-value = Valore configurazione

### Titles
cli-config-show-title = Configurazione OpenFatture

### Table Headers
cli-config-column-setting = Impostazione
cli-config-column-value = Valore

### Section Labels - Application
cli-config-label-app-version = Versione App
cli-config-label-debug-mode = Modalità Debug

### Section Labels - Database
cli-config-label-database-url = URL Database

### Section Labels - Paths
cli-config-label-data-dir = Directory Dati
cli-config-label-archive-dir = Directory Archivio
cli-config-label-certificates-dir = Directory Certificati

### Section Labels - Company Data
cli-config-label-company-name = Nome Azienda
cli-config-label-partita-iva = Partita IVA
cli-config-label-codice-fiscale = Codice Fiscale
cli-config-label-tax-regime = Regime Fiscale

### Section Labels - PEC
cli-config-label-pec-address = Indirizzo PEC
cli-config-label-pec-smtp-server = Server SMTP PEC
cli-config-label-sdi-pec-address = Indirizzo PEC SDI

### Section Labels - Email & Notifications
cli-config-label-notification-email = Email Notifiche
cli-config-label-notifications-enabled = Notifiche Abilitate
cli-config-label-locale = Lingua
cli-config-label-email-logo-url = URL Logo Email
cli-config-label-primary-color = Colore Primario
cli-config-label-secondary-color = Colore Secondario
cli-config-label-email-footer = Footer Email

### Section Labels - AI Configuration
cli-config-label-ai-provider = Provider AI
cli-config-label-ai-model = Modello AI
cli-config-label-ai-base-url = URL Base AI
cli-config-label-ai-api-key = Chiave API AI
cli-config-label-chat-enabled = Chat Abilitata
cli-config-label-chat-auto-save = Salvataggio Automatico Chat
cli-config-label-max-messages = Messaggi Massimi/Sessione
cli-config-label-max-tokens = Token Massimi/Sessione
cli-config-label-tools-enabled = Strumenti Abilitati
cli-config-label-enabled-tools = Strumenti Abilitati

### Status Values
cli-config-not-set = [red]Non impostato[/red]
cli-config-not-set-optional = [yellow]Non impostato[/yellow]
cli-config-set = [green]Impostata[/green]
cli-config-yes = [green]Sì[/green]
cli-config-no = [red]No[/red]
cli-config-auto-generated = [dim]Auto-generato[/dim]
cli-config-all-tools = tutti
cli-config-tools-count = { $count } strumenti

### Messages
cli-config-reload-success = [green]Configurazione ricaricata[/green]
cli-config-set-success = [green]Impostato { $key } = { $value }[/green]
cli-config-saved-to = [dim]Salvato in { $path }[/dim]
cli-config-invalid-key = [red]Chiave configurazione non valida: { $key }[/red]
cli-config-error = [red]Errore: { $error }[/red]
