### Help Text - Opzioni e Argomenti

## CONFIG Commands - Gestione Configurazione
cli-config-help-key = Chiave configurazione (es. pec.address)
cli-config-help-value = Valore configurazione
cli-config-show-title = Configurazione OpenFatture
cli-config-column-setting = Impostazione
cli-config-column-value = Valore
cli-config-label-app-version = Versione App
cli-config-label-debug-mode = Modalità Debug
cli-config-label-database-url = URL Database
cli-config-label-data-dir = Directory Dati
cli-config-label-archive-dir = Directory Archivio
cli-config-label-certificates-dir = Directory Certificati
cli-config-label-company-name = Nome Azienda
cli-config-label-partita-iva = Partita IVA
cli-config-label-codice-fiscale = Codice Fiscale
cli-config-label-tax-regime = Regime Fiscale
cli-config-label-pec-address = Indirizzo PEC
cli-config-label-pec-smtp-server = Server SMTP PEC
cli-config-label-sdi-pec-address = Indirizzo PEC SDI
cli-config-label-notification-email = Email Notifiche
cli-config-label-notifications-enabled = Notifiche Abilitate
cli-config-label-locale = Lingua
cli-config-label-email-logo-url = URL Logo Email
cli-config-label-primary-color = Colore Primario
cli-config-label-secondary-color = Colore Secondario
cli-config-label-email-footer = Footer Email
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
cli-config-not-set = [red]Non impostato[/red]
cli-config-not-set-optional = [yellow]Non impostato[/yellow]
cli-config-set = [green]Impostata[/green]
cli-config-yes = [green]Sì[/green]
cli-config-no = [red]No[/red]
cli-config-auto-generated = [dim]Auto-generato[/dim]
cli-config-all-tools = tutti
cli-config-tools-count = { $count } strumenti
cli-config-reload-success = [green]Configurazione ricaricata[/green]
cli-config-set-success = [green]Impostato { $key } = { $value }[/green]
cli-config-saved-to = [dim]Salvato in { $path }[/dim]
cli-config-invalid-key = [red]Chiave configurazione non valida: { $key }[/red]
cli-config-error = [red]Errore: { $error }[/red]
cli-config-column-source = Origine
cli-config-source-env = ambiente
cli-config-source-keyring = portachiavi
cli-config-source-file = file credenziali
cli-config-source-config = config.toml
cli-config-source-default = predefinito
cli-config-file-path = [dim]File di configurazione: { $path }[/dim]
cli-config-secret-backend = [dim]Segreti: { $backend }[/dim]
cli-config-secret-saved = [green]{ $key } salvato in: { $backend }[/green]
cli-config-env-override = [yellow]{ $key } è impostato da una variabile d'ambiente: il valore salvato non sarà usato finché resta impostata.[/yellow]
cli-config-unset-success = [green]Rimosso { $key }[/green]
cli-config-unset-missing = [yellow]{ $key } non era impostato[/yellow]
cli-config-invalid-value = [red]Valore non valido per { $key }: { $error }[/red]
cli-config-migrate-moved = [green]Spostati in { $backend }: { $keys }[/green]
cli-config-migrate-imported = [green]Importati in config.toml: { $keys }[/green]
cli-config-migrate-conflicts = [yellow]Già impostati, non sovrascritti: { $keys }[/yellow]
cli-config-migrate-nothing = Nessuna impostazione da migrare.
cli-config-migrate-source-kept = [dim]{ $path } non è stato modificato: eliminalo dopo aver verificato.[/dim]
assistant-describe-what-you-need = Descrivi cosa ti serve. /help per i comandi · /exit per uscire
assistant-thinking = Elaborazione…
assistant-request-error = Richiesta non riuscita. Usa --debug per i dettagli.
assistant-confirm-operation = Confermi questa operazione? [s/N]
assistant-help = Comandi
    /help     Mostra questo aiuto
    /exit     Esci (anche: exit, quit, q)
    /session  Mostra ID sessione
    /clear    Cancella i messaggi della sessione
assistant-input = Tu ›
assistant-operation = Operazione: { $name }
assistant-tool-running = Esecuzione · { $name }
assistant-incomplete = Risposta incompleta.
assistant-session = Sessione: { $session }
assistant-not-persisted = non salvata
assistant-cleared = Messaggi della sessione cancellati.
assistant-no-session = Nessuna sessione salvata da cancellare.
assistant-unknown-command = Comando sconosciuto: { $command }. Usa /help.
assistant-turn-failed = Richiesta non completata. Usa --debug per i dettagli.
assistant-interrupted = Richiesta interrotta. Le operazioni già avviate potrebbero avere avuto effetto: verificane lo stato prima di riprovare.
assistant-missing-extra = Dipendenze AI mancanti: reinstalla OpenFatture con l’extra ai.
assistant-tool-completed = Completato · { $name }
assistant-tool-failed = Non completato · { $name }
status-blocking-fields = Campi che impediscono la fatturazione
status-field = Campo
status-problem = Problema
status-missing = Da completare
status-invalid = Da correggere
status-local-only = I controlli descrivono la configurazione locale. Autenticazione AI e invio SDI non vengono verificati da questo comando.
cli-database-unavailable = Database non accessibile. Controlla DATABASE_URL e i permessi; usa --debug per i dettagli.
cli-invoice-collected = Incassato
cli-invoice-residual = Residuo
cli-invoice-collection = Incasso
cli-invoice-document = Documento
cli-invoice-historical = Storica
cli-invoice-unpaid = Non pagato
cli-invoice-historical-note = Documento emesso altrove; invio bloccato. Stato SDI non verificato.
cli-invoice-total = Totale
assistant-reconciled = Esito verificato registrato. Usa /resume per continuare.
assistant-reconcile-invalid = Riconciliazione non valida: servono call_id, result ed evidence.
assistant-resolve-pending-first = Risolvi il turno pendente con /resume prima di cancellare lo storico.
assistant-resuming = Ripresa del turno interrotto…
assistant-uncertain-tool = Esito tool incerto: usa /pending e /reconcile prima di /resume.
assistant-no-pending = Nessun turno pendente.

## Shared command output
cli-common-error = [red]Errore:[/red] { $error }
cli-common-more-results = [dim]... e altri risultati. Usa --limit per vederne di più.[/dim]
cli-common-not-available = N/D
cli-common-number = Numero
cli-common-date = Data
cli-common-status = Stato
cli-common-client = Cliente
cli-common-amount = Importo
cli-common-name = Denominazione
cli-common-notes = Note
cli-common-vat-number = P.IVA
cli-common-tax-code = Codice fiscale

## FATTURA Commands
cli-fattura-none-found = [yellow]Nessuna fattura trovata.[/yellow]
cli-fattura-list-title = Fatture ({ $count })
cli-fattura-pec-to-verify = PEC: da verificare
cli-fattura-statement = Dichiarazione: { $value } · fonte: { $source }
cli-fattura-show-title = [bold cyan]Fattura n. { $id }[/bold cyan]
cli-fattura-submission-unverified = Esito invio da verificare; non ripetere automaticamente la trasmissione.
cli-fattura-amounts = Importi
cli-fattura-taxable = Imponibile
cli-fattura-vat = IVA
cli-fattura-line-items = [bold]Righe:[/bold] { $count } in totale
cli-fattura-column-description = Descrizione
cli-fattura-column-quantity = Q.tà
cli-fattura-column-unit-price = Prezzo unitario
cli-fattura-column-vat-rate = IVA %
cli-fattura-created-id = ID fattura: [cyan]{ $id }[/cyan]
cli-fattura-line = Riga n. { $numero }: { $descrizione }
cli-fattura-invoice-total = Totale fattura
cli-fattura-pdf-generated = [green]✓[/green] PDF generato correttamente
cli-fattura-xml-generated = [green]✓[/green] XML generato correttamente
cli-fattura-xml-generated-dry-run = [green]✓[/green] XML generato correttamente (simulazione, nessun file scritto)
cli-fattura-xml-content = [bold]Contenuto XML:[/bold]
cli-fattura-output = File: [cyan]{ $path }[/cyan]
cli-fattura-size = Dimensione: { $size } byte
cli-fattura-status-change = Stato: { $old } → { $new }
cli-fattura-credit-note-id = ID nota di credito: [cyan]{ $id }[/cyan]
cli-fattura-document-type = Tipo documento
cli-fattura-source-invoice = [dim]Fattura di origine:[/dim]
cli-fattura-journal-submission = Invio n. { $id } · fattura { $invoice } · { $filename } · { $outcome }
cli-fattura-journal-receipt = Ricevuta n. { $id } · fattura { $invoice } · { $outcome } · origine { $source }
cli-fattura-associate-confirm = Associare la ricevuta { $receipt } alla fattura { $invoice }?
cli-fattura-receipt-associated = Ricevuta associata
cli-fattura-resolve-confirm = Confermi che l'invio { $attempt } { $sent ->
        [yes] è stato trasmesso
       *[no] non è stato trasmesso
    }?
cli-fattura-submission-resolved = Verifica registrata

## CLIENTE Commands
cli-cliente-none-found = [yellow]Nessun cliente trovato.[/yellow]
cli-cliente-list-title = Clienti ({ $count })
cli-cliente-column-invoices = Fatture
cli-cliente-show-title = [bold cyan]Cliente n. { $id }[/bold cyan]
cli-cliente-address = Indirizzo
cli-cliente-contacts = Contatti
cli-cliente-phone = Tel.
cli-cliente-invoices-total = [bold]Fatture:[/bold] { $count } in totale
cli-cliente-recent-invoices = Fatture recenti
cli-cliente-created-id = ID cliente: [cyan]{ $id }[/cyan]

## PAGAMENTO Commands
cli-pagamento-reverse-confirm = Stornare { $amount } dalla registrazione { $entry }?

## INIT Command
cli-init-title = [bold blue]Configurazione di OpenFatture[/bold blue]
cli-init-structured-needs-no-interactive = Usa --no-interactive con un formato di output strutturato
cli-init-creating-dirs = [cyan]Creazione delle directory...[/cyan]
cli-init-dirs-created = Directory dei dati create
cli-init-initializing-db = [cyan]Inizializzazione del database...[/cyan]
cli-init-backup = Backup prima dell'aggiornamento: { $path }
cli-init-database = Database { $state ->
        [empty] creato
        [current] già aggiornato
        [outdated] aggiornato
        [unversioned] adottato e aggiornato
       *[other] { $state }
    }: { $url }
cli-init-configure-company = [bold yellow]Configuriamo i dati della tua azienda[/bold yellow]
cli-init-overwrite-confirm = [yellow]Esiste già un profilo OpenFatture. Sovrascrivere le impostazioni aziendali e AI?[/yellow]
cli-init-config-preserved = [green]Configurazione esistente mantenuta.[/green] Directory e database sono stati comunque verificati.
cli-init-company-section = [bold]Dati aziendali (Cedente Prestatore)[/bold]
cli-init-prompt-name = Ragione sociale o nome
cli-init-prompt-partita-iva = Partita IVA (11 cifre)
cli-init-invalid-partita-iva = [red]Partita IVA non valida. Riprova.[/red]
cli-init-prompt-codice-fiscale = Codice fiscale (16 caratteri)
cli-init-invalid-codice-fiscale = [red]Codice fiscale non valido. Riprova.[/red]
cli-init-prompt-regime = Regime fiscale (usa il tuo codice RF effettivo)
cli-init-invalid-regime = [red]Inserisci un regime fiscale supportato da FatturaPA.[/red]
cli-init-prompt-address = Indirizzo (via/piazza)
cli-init-prompt-cap = CAP
cli-init-prompt-city = Comune
cli-init-prompt-province = Provincia (2 lettere, es. RM)
cli-init-pec-section = [bold]Configurazione PEC[/bold]
cli-init-prompt-pec-address = Il tuo indirizzo PEC
cli-init-prompt-pec-password = Password PEC
cli-init-prompt-pec-smtp = Server SMTP PEC
cli-init-notifications-section = [bold]Notifiche email[/bold]
cli-init-prompt-notification-email = Email per le notifiche (avvisi SDI, riepiloghi)
cli-init-prompt-locale = Lingua (it/en/de/es/fr)
cli-init-ai-section = [bold]Configurazione AI (facoltativa)[/bold]
cli-init-ai-description = [dim]Configura le funzioni AI: descrizioni delle fatture, suggerimenti fiscali e assistente conversazionale.[/dim]
cli-init-ai-confirm = Configurare ora le funzioni AI? (Puoi farlo anche in seguito con openfatture config)
cli-init-ai-provider = Provider AI
cli-init-ai-skip = Salta per ora
cli-init-api-key-from = [cyan]{ $provider } selezionato: ottieni la chiave API da:[/cyan]
cli-init-ollama-selected = [cyan]Ollama selezionato: modello locale gratuito![/cyan]
cli-init-ollama-install = Installa: [bold]ollama pull { $model }[/bold]
cli-init-ollama-start = Avvia: [bold]ollama serve[/bold]
cli-init-prompt-api-key = Chiave API (lascia vuoto per impostarla in seguito)
cli-init-config-saved = Configurazione salvata in: { $path }
cli-init-secrets-saved = Segreti salvati { $backend ->
        [keyring] nel portachiavi di sistema
       *[file] nel file privato delle credenziali
    }
cli-init-complete-title = Configurazione completata
cli-init-complete-body = [bold green]Configurazione terminata[/bold green]

    Prossimi passi:
      • Verifica lo stato: [cyan]openfatture status[/cyan]
      • Rivedi le impostazioni: [cyan]openfatture config show[/cyan]
      • Assistente (richiede [cyan]uv sync --extra ai[/cyan]): [cyan]openfatture assistant "Elenca le fatture aperte"[/cyan]
      • Aiuto: [cyan]openfatture --help[/cyan]

## STATUS Command
cli-status-readiness = [bold]Prontezza[/bold]  base: [cyan]{ $core ->
        [yes] pronta
       *[no] non pronta
    }[/cyan]  assistente: [cyan]{ $assistant ->
        [yes] configurato
       *[no] non configurato
    }[/cyan]
cli-status-title = Stato di OpenFatture
cli-status-label-ai-api-key-configured = Chiave API AI configurata
cli-status-label-assistant-backend = Backend assistente
cli-status-label-assistant-backend-id = ID backend assistente
cli-status-label-config-file = File di configurazione
cli-status-label-secret-backend = Archivio segreti
cli-status-checks-title = Controlli di prontezza
cli-status-column-check = Controllo
cli-status-yes = sì
cli-status-no = no
cli-status-next-steps = [bold]Prossimi passi[/bold]
cli-status-extras-title = Extra opzionali (moduli funzionali)
cli-status-column-extra = Extra
cli-status-column-installed = Installato
cli-status-extensions-title = Estensioni
cli-status-column-mechanism = Meccanismo
cli-status-column-detail = Dettaglio
cli-status-hooks = hook (supportati)
cli-status-hooks-detail = { $path } ({ $count } script)
cli-status-plugins = plugin in-process

## Global
cli-main-version = [bold blue]OpenFatture[/bold blue] versione { $version }
cli-output-unsupported-format = Formati supportati: { $formats }

## Rich formatter
cli-formatter-error = [bold red]Errore:[/bold red] { $error }
cli-formatter-unknown-error = Errore sconosciuto
cli-formatter-ai-response = [bold]Risposta AI[/bold]
cli-formatter-unknown = sconosciuto
cli-formatter-provider = Provider: { $provider }
cli-formatter-model = Modello: { $model }
cli-formatter-tokens = Token: { $tokens }
cli-formatter-cost = Costo: { $cost }
cli-formatter-latency = Latenza: { $latency } ms
