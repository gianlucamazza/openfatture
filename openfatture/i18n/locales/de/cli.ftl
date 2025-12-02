# CLI-Befehle Übersetzungen
# DE (Deutsch)

## HAUPT-CLI

### main - Haupt-CLI
cli-main-title = OpenFatture - Open-Source-System für elektronische Rechnungsstellung
cli-main-description = Vollständiges System zur Verwaltung von FatturaPA-Elektronischemrechnungen
cli-main-version = Version { $version }

### main - Befehlsgruppen
cli-main-group-invoices = 📄 Rechnungsverwaltung
cli-main-group-clients = 👥 Kundenverwaltung
cli-main-group-products = 📦 Produktverwaltung
cli-main-group-pec = 📧 PEC & SDI
cli-main-group-batch = 📊 Stapelverarbeitung
cli-main-group-ai = 🤖 KI-Assistent
cli-main-group-payments = 💰 Zahlungsverfolgung
cli-main-group-preventivi = 📋 Angebote
cli-main-group-events = 📅 Ereignissystem
cli-main-group-lightning = ⚡ Lightning-Netzwerk
cli-main-group-web = 🌐 Weboberfläche

## FATTURA-Befehle

### fattura - Hilfetexte
cli-fattura-help-numero = Rechnungsnummer
cli-fattura-help-cliente-id = Kunden-ID
cli-fattura-help-anno = Jahr (Standard: aktuelles Jahr)
cli-fattura-help-tipo-documento = Dokumenttyp (TD01, TD04, TD06, etc.)
cli-fattura-help-data = Rechnungsdatum (YYYY-MM-DD)
cli-fattura-help-bollo = Stempelgebühr (€ 2,00)
cli-fattura-help-xml-path = Pfad zur XML-Datei
cli-fattura-help-formato = Ausgabeformat (table, json, yaml)
cli-fattura-help-all = Zeige alle Rechnungen, auch alte

### fattura - Konsolenausgabe
cli-fattura-create-title = [bold blue]🧾 Neue Rechnung erstellen[/bold blue]
cli-fattura-select-client-title = [bold cyan]Kundenauswahl[/bold cyan]
cli-fattura-no-clients-error = [red]Keine Kunden gefunden. Fügen Sie zuerst einen mit 'cliente add' hinzu[/red]
cli-fattura-available-clients = [cyan]Verfügbare Kunden:[/cyan]
cli-fattura-client-prompt = Kundennummer
cli-fattura-client-selected = [green]✓ Kunde: { $client_name }[/green]
cli-fattura-invalid-client-error = [red]Ungültige Kundenauswahl[/red]

cli-fattura-add-lines-title = [bold cyan]Rechnungspositionen[/bold cyan]
cli-fattura-line-description-prompt = Beschreibung (Leer zum Beenden)
cli-fattura-line-quantity-prompt = Menge
cli-fattura-line-unit-price-prompt = Einzelpreis (€)
cli-fattura-line-vat-rate-prompt = MwSt-Satz (%)
cli-fattura-line-added = [green]✓ Position hinzugefügt: { $description } - € { $amount }[/green]

cli-fattura-payment-terms-title = [bold cyan]Zahlungsbedingungen[/bold cyan]
cli-fattura-payment-condition-prompt = Zahlungsbedingung (TP01=Zahlung fällig, TP02=Bezahlt)
cli-fattura-payment-method-prompt = Zahlungsmethode (MP05=Banküberweisung, MP01=Bargeld, MP08=Kreditkarte)
cli-fattura-payment-days-prompt = Zahlungsfrist (Tage)
cli-fattura-payment-date-prompt = Zahlungsdatum (YYYY-MM-DD, Leer=automatisch)
cli-fattura-payment-iban-prompt = IBAN (optional)

cli-fattura-summary-title = [bold yellow]Rechnungszusammenfassung[/bold yellow]
cli-fattura-summary-client = Kunde: { $client_name }
cli-fattura-summary-lines = { $count } { $count ->
    [one] Position
   *[other] Positionen
}
cli-fattura-summary-subtotal = Gesamtsumme: € { $subtotal }
cli-fattura-summary-vat = MwSt: € { $vat }
cli-fattura-summary-total = [bold]Gesamtbetrag: € { $total }[/bold]
cli-fattura-summary-stamp = Stempelgebühr: € { $stamp }

cli-fattura-confirm-prompt = [yellow]Erstellung bestätigen?[/yellow]
cli-fattura-created-success = [bold green]✓ Rechnung erfolgreich erstellt![/bold green]
cli-fattura-created-number = [green]Rechnungsnummer: { $numero }/{ $anno }[/green]
cli-fattura-created-xml = [green]XML gespeichert: { $xml_path }[/green]

cli-fattura-list-title = [bold blue]Rechnungsliste[/bold blue]
cli-fattura-list-empty = [yellow]Keine Rechnungen gefunden[/yellow]

cli-fattura-show-title = [bold blue]Rechnung { $numero }/{ $anno }[/bold blue]
cli-fattura-show-not-found = [red]Rechnung nicht gefunden: { $numero }/{ $anno }[/red]

cli-fattura-delete-confirm = [yellow]Rechnung { $numero }/{ $anno } löschen?[/yellow]
cli-fattura-delete-warning = [red]WARNUNG: Diese Operation kann nicht rückgängig gemacht werden[/red]
cli-fattura-delete-status-restriction = [red]Rechnung im Status '{ $status }' kann nicht gelöscht werden[/red]
cli-fattura-delete-success = [green]✓ Rechnung { $numero }/{ $anno } gelöscht[/green]
cli-fattura-delete-cancelled = [yellow]Operation abgebrochen[/yellow]
cli-fattura-delete-cannot-delete-sent = [red]Rechnungen im Status INVIATA oder CONSEGNATA können nicht gelöscht werden[/red]

cli-fattura-validate-success = [green]✓ XML ist gültig[/green]
cli-fattura-validate-error = [red]Validierungsfehler gefunden:[/red]

cli-fattura-table-numero = Nr.
cli-fattura-table-data = Datum
cli-fattura-table-cliente = Kunde
cli-fattura-table-importo = Betrag
cli-fattura-table-stato = Status
cli-fattura-table-tipo = Typ
cli-fattura-table-pagamento = Zahlung
cli-fattura-table-iva = MwSt
cli-fattura-table-totale = Gesamtbetrag
cli-fattura-table-bollo = Stempel
cli-fattura-table-descrizione = Beschreibung
cli-fattura-table-quantita = Menge
cli-fattura-table-prezzo = Preis
cli-fattura-table-aliquota = Satz
cli-fattura-table-importo-riga = Zeilenbetrag

## CLIENTE-Befehle

### cliente - Hilfetexte
cli-cliente-help-id = Kunden-ID
cli-cliente-help-denominazione = Unternehmensname oder vollständiger Name
cli-cliente-help-partita-iva = Umsatzsteuer-ID
cli-cliente-help-codice-fiscale = Steuernummer
cli-cliente-help-pec = PEC-Adresse
cli-cliente-help-codice-destinatario = SDI-Zielcode
cli-cliente-help-formato = Ausgabeformat (table, json, yaml)
cli-cliente-help-search = Suchbegriff
cli-cliente-help-limit = Maximale Anzahl der Ergebnisse

### cliente - Konsolenausgabe
cli-cliente-list-title = Kunden ({ $count })
cli-cliente-list-empty = [yellow]Keine Kunden gefunden[/yellow]
cli-cliente-added-success = [green]✓ Kunde erfolgreich hinzugefügt (ID: { $id })[/green]
cli-cliente-updated-success = [green]✓ Kunde erfolgreich aktualisiert[/green]
cli-cliente-deleted-success = [green]✓ Kunde erfolgreich gelöscht[/green]
cli-cliente-not-found = [red]Kunde nicht gefunden: { $id }[/red]
cli-cliente-has-invoices = [yellow]Warnung: Dieser Kunde hat { $count } { $count ->
    [one] Rechnung
   *[other] Rechnungen
}[/yellow]
cli-cliente-cannot-delete = [red]Kunde mit Rechnungen kann nicht gelöscht werden[/red]
cli-cliente-delete-confirm = [yellow]Kunde { $denominazione } löschen?[/yellow]

### cliente - Eingabeaufforderungen
cli-cliente-prompt-denominazione = Unternehmensname
cli-cliente-prompt-partita-iva = Umsatzsteuer-ID
cli-cliente-prompt-codice-fiscale = Steuernummer
cli-cliente-prompt-indirizzo = Adresse
cli-cliente-prompt-cap = Postleitzahl
cli-cliente-prompt-comune = Stadt
cli-cliente-prompt-provincia = Provinz
cli-cliente-prompt-nazione = Land
cli-cliente-prompt-pec = PEC-Adresse
cli-cliente-prompt-codice-destinatario = SDI-Zielcode
cli-cliente-prompt-email = E-Mail
cli-cliente-prompt-telefono = Telefon
cli-cliente-prompt-regime-fiscale = Steuerregime (RF01, RF19, etc.)

### cliente - Tabellenbeschriftungen
cli-cliente-table-id = ID
cli-cliente-table-denominazione = Name
cli-cliente-table-partita-iva = MwSt-ID
cli-cliente-table-codice-fiscale = Steuernummer
cli-cliente-table-comune = Stadt
cli-cliente-table-provincia = Provinz
cli-cliente-table-pec = PEC
cli-cliente-table-codice-destinatario = SDI-Code
cli-cliente-table-fatture = Rechnungen
cli-cliente-table-indirizzo = Adresse
cli-cliente-table-cap = PLZ
cli-cliente-table-nazione = Land
cli-cliente-table-email = E-Mail

## KI-Befehle

### ai - Hilfetexte
cli-ai-help-text = Zu verarbeitender Text
cli-ai-help-invoice-id = Rechnungs-ID
cli-ai-help-provider = KI-Anbieter (openai, anthropic, ollama)
cli-ai-help-model = KI-Modellname
cli-ai-help-temperature = Temperatur (0,0-2,0)
cli-ai-help-max-tokens = Maximale Token
cli-ai-help-interactive = Interaktiver Modus
cli-ai-help-session-id = Chat-Sitzungs-ID
cli-ai-help-stream = Streaming aktivieren
cli-ai-help-save-session = Sitzung nach Chat speichern
cli-ai-help-list-sessions = Verfügbare Sitzungen auflisten
cli-ai-help-months = Anzahl der Monate für Vorhersage
cli-ai-help-confidence = Konfidenzlevel (0,0-1,0)
cli-ai-help-retrain = Modell mit neuesten Daten umtrainieren
cli-ai-help-show-metrics = Modellmetriken anzeigen
cli-ai-help-invoice-numero = Rechnungsnummer
cli-ai-help-year = Rechnungsjahr
cli-ai-help-context = Zusätzlicher Kontext
cli-ai-help-language = Sprachcode
cli-ai-help-format = Ausgabeformat
cli-ai-help-embedding-model = Embedding-Modell
cli-ai-help-chunk-size = Chunk-Größe für Dokumente
cli-ai-help-collection = RAG-Sammlungsname
cli-ai-help-query = Suchanfrage
cli-ai-help-top-k = Anzahl der Ergebnisse
cli-ai-help-rating = Bewertung (1-5)
cli-ai-help-comment = Kommentartext
cli-ai-help-duration = Aufnahmedauer in Sekunden
cli-ai-help-save-audio = Audiodateien zum Debuggen speichern
cli-ai-help-no-playback = Audiowiedergabe deaktivieren
cli-ai-help-sample-rate = Audio-Abtastrate

### ai - Konsolenausgabe (describe)
cli-ai-describe-title = [bold cyan]🤖 KI-Generierung von Rechnungsbeschreibungen[/bold cyan]
cli-ai-describe-input-prompt = [cyan]Geben Sie kurze Beschreibung ein:[/cyan]
cli-ai-describe-processing = [yellow]Wird mit KI verarbeitet...[/yellow]
cli-ai-describe-result-title = [bold green]Generierte Beschreibung:[/bold green]
cli-ai-describe-result-text = [white]{ $text }[/white]
cli-ai-describe-copy-hint = [dim]Sie können diese Beschreibung beim Erstellen einer Rechnung kopieren[/dim]
cli-ai-describe-error = [red]Fehler beim Generieren der Beschreibung: { $error }[/red]

### ai - Konsolenausgabe (suggest-vat)
cli-ai-vat-title = [bold cyan]🧾 MwSt-Satzerkennung mit KI[/bold cyan]
cli-ai-vat-input-prompt = [cyan]Beschreibung der Dienstleistung/des Produkts:[/cyan]
cli-ai-vat-processing = [yellow]Wird mit KI analysiert...[/yellow]
cli-ai-vat-result-title = [bold green]Vorgeschlagener MwSt-Satz:[/bold green]
cli-ai-vat-rate = [white]{ $rate }%[/white]
cli-ai-vat-reasoning-title = [bold yellow]Begründung:[/bold yellow]
cli-ai-vat-reasoning-text = [white]{ $reasoning }[/white]
cli-ai-vat-warning = [yellow]⚠️  Überprüfen Sie immer mit einem Steuerberater für komplexe Fälle[/yellow]
cli-ai-vat-error = [red]Fehler bei MwSt-Satzerkennung: { $error }[/red]

### ai - Konsolenausgabe (chat)
cli-ai-chat-title = [bold cyan]🎤 KI-Chat[/bold cyan]
cli-ai-chat-welcome = [cyan]Willkommen zum OpenFatture KI-Assistenten![/cyan]
cli-ai-chat-welcome-help = [dim]Geben Sie Ihre Fragen ein oder 'exit' zum Beenden[/dim]
cli-ai-chat-session-loaded = [green]✓ Sitzung geladen: { $session_id }[/green]
cli-ai-chat-session-created = [green]✓ Neue Sitzung erstellt: { $session_id }[/green]
cli-ai-chat-prompt = [bold cyan]Sie:[/bold cyan]
cli-ai-chat-assistant-prefix = [bold green]Assistent:[/bold green]
cli-ai-chat-thinking = [yellow]Nachdenken...[/yellow]
cli-ai-chat-tool-calling = [yellow]Werkzeug wird ausgeführt: { $tool_name }[/yellow]
cli-ai-chat-tool-result = [dim]Werkzeugergebnis: { $result }[/dim]
cli-ai-chat-session-saved = [green]✓ Sitzung gespeichert[/green]
cli-ai-chat-goodbye = [cyan]Auf Wiedersehen! Sitzung gespeichert.[/cyan]
cli-ai-chat-error = [red]Fehler: { $error }[/red]
cli-ai-chat-cost-info = [dim]Token: { $tokens } | Kosten: €{ $cost }[/dim]

### ai - Konsolenausgabe (voice-chat)
cli-ai-voice-title = [bold cyan]🎤 KI-Sprachchat[/bold cyan]
cli-ai-voice-welcome = [cyan]Willkommen zum Sprachchat![/cyan]
cli-ai-voice-recording-prompt = [yellow]Drücken Sie ENTER zum Starten der Aufnahme ({ $duration }s)...[/yellow]
cli-ai-voice-recording = [bold yellow]🔴 Wird aufgezeichnet...[/bold yellow]
cli-ai-voice-processing = [yellow]Audio wird verarbeitet...[/yellow]
cli-ai-voice-transcription-title = [bold green]Sie sagten:[/bold green]
cli-ai-voice-transcription-text = [white]{ $text }[/white]
cli-ai-voice-language-detected = [dim]Sprache: { $language }[/dim]
cli-ai-voice-thinking = [yellow]Assistent denkt nach...[/yellow]
cli-ai-voice-response-title = [bold green]Assistent:[/bold green]
cli-ai-voice-response-text = [white]{ $text }[/white]
cli-ai-voice-playing = [cyan]🔊 Antwort wird abgespielt...[/cyan]
cli-ai-voice-audio-saved = [dim]Audio gespeichert: { $path }[/dim]
cli-ai-voice-goodbye = [cyan]Auf Wiedersehen![/cyan]
cli-ai-voice-error = [red]Fehler: { $error }[/red]

### ai - Konsolenausgabe (forecast)
cli-ai-forecast-title = [bold cyan]📊 Cashflow-Prognose mit KI[/bold cyan]
cli-ai-forecast-loading-data = [yellow]Historische Daten werden geladen...[/yellow]
cli-ai-forecast-data-stats = [cyan]Rechnungen: { $invoices } | Zahlungen: { $payments }[/cyan]
cli-ai-forecast-training = [yellow]ML-Modelle werden trainiert...[/yellow]
cli-ai-forecast-training-progress = [yellow]{ $progress }%[/yellow]
cli-ai-forecast-predicting = [yellow]Prognose wird erstellt...[/yellow]
cli-ai-forecast-results-title = [bold green]📊 Cashflow-Prognose - Nächste { $months } { $months ->
    [one] Monat
   *[other] Monate
}[/bold green]
cli-ai-forecast-month = [cyan]{ $month }[/cyan]
cli-ai-forecast-predicted = Prognose: € { $amount }
cli-ai-forecast-confidence = Konfidenz: { $confidence }%
cli-ai-forecast-lower-bound = Untere Grenze: € { $lower }
cli-ai-forecast-upper-bound = Obere Grenze: € { $upper }
cli-ai-forecast-metrics-title = [bold yellow]Modellmetriken:[/bold yellow]
cli-ai-forecast-mae = MAE: { $mae }
cli-ai-forecast-rmse = RMSE: { $rmse }
cli-ai-forecast-mape = MAPE: { $mape }%
cli-ai-forecast-insufficient-data = [yellow]Unzureichende Daten. Benötigt mindestens { $required } Rechnungen/Zahlungen zum Trainieren.[/yellow]
cli-ai-forecast-error = [red]Prognosefehler: { $error }[/red]

### ai - Konsolenausgabe (intelligence)
cli-ai-intelligence-title = [bold cyan]🧠 Geschäftsintelligenzanalyse[/bold cyan]
cli-ai-intelligence-analyzing = [yellow]Geschäftsdaten werden analysiert...[/yellow]
cli-ai-intelligence-report-title = [bold green]Geschäftserkenntnisse:[/bold green]
cli-ai-intelligence-section = [bold yellow]{ $section }[/bold yellow]
cli-ai-intelligence-insight = • { $insight }
cli-ai-intelligence-error = [red]Analysefehler: { $error }[/red]

### ai - Konsolenausgabe (compliance)
cli-ai-compliance-title = [bold cyan]✅ Compliance-Überprüfung[/bold cyan]
cli-ai-compliance-checking = [yellow]Prüfe Rechnung { $numero }/{ $anno }...[/yellow]
cli-ai-compliance-passed = [bold green]✓ Alle Compliance-Überprüfungen bestanden[/bold green]
cli-ai-compliance-warnings = [yellow]⚠️  { $count } { $count ->
    [one] Warnung gefunden
   *[other] Warnungen gefunden
}[/yellow]
cli-ai-compliance-errors = [red]❌ { $count } { $count ->
    [one] Fehler gefunden
   *[other] Fehler gefunden
}[/red]
cli-ai-compliance-check-item = [{ $status }] { $message }
cli-ai-compliance-error = [red]Compliance-Überprüfungsfehler: { $error }[/red]

### ai - Konsolenausgabe (rag)
cli-ai-rag-title = [bold cyan]📚 RAG-Dokumentsuche[/bold cyan]
cli-ai-rag-indexing = [yellow]Dokumente werden indexiert...[/yellow]
cli-ai-rag-indexed = [green]✓ { $count } { $count ->
    [one] Dokument indexiert
   *[other] Dokumente indexiert
}[/green]
cli-ai-rag-searching = [yellow]Wissensdatenbank wird durchsucht...[/yellow]
cli-ai-rag-results-title = [bold green]Suchergebnisse:[/bold green]
cli-ai-rag-result-item = { $rank }. [bold]{ $title }[/bold] (Bewertung: { $score })
cli-ai-rag-result-text = { $text }
cli-ai-rag-no-results = [yellow]Keine Ergebnisse gefunden[/yellow]
cli-ai-rag-error = [red]RAG-Fehler: { $error }[/red]

### ai - Konsolenausgabe (feedback)
cli-ai-feedback-title = [bold cyan]📝 KI-Feedback[/bold cyan]
cli-ai-feedback-prompt-rating = [cyan]Antwort bewerten (1-5):[/cyan]
cli-ai-feedback-prompt-comment = [cyan]Kommentar (optional):[/cyan]
cli-ai-feedback-thanks = [green]✓ Vielen Dank für Ihr Feedback![/green]
cli-ai-feedback-saved = [green]Feedback in Sitzung { $session_id } gespeichert[/green]
cli-ai-feedback-error = [red]Feedback-Fehler: { $error }[/red]
