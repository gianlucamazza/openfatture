# CLI-Befehle Übersetzungen
# DE (Deutsch)

## HAUPT-CLI

### main - Haupt-CLI
cli-main-title = OpenFatture - Open-Source-System für elektronische Rechnungsstellung
cli-main-description = Vollständiges System zur Verwaltung von FatturaPA-Elektronischemrechnungen
cli-main-version = Version { $version }

### main - Befehlsgruppen
cli-main-group-invoices = Rechnungsverwaltung
cli-main-group-clients = Kundenverwaltung
cli-main-group-products = Produktverwaltung
cli-main-group-pec = PEC & SDI
cli-main-group-batch = Stapelverarbeitung
cli-main-group-ai = KI-Assistent
cli-main-group-payments = Zahlungsverfolgung
cli-main-group-preventivi = Angebote
cli-main-group-events = Ereignissystem
cli-main-group-lightning = Lightning-Netzwerk
cli-main-group-web = Weboberfläche

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
cli-fattura-create-title = [bold blue]Neue Rechnung erstellen[/bold blue]
cli-fattura-select-client-title = [bold cyan]Kundenauswahl[/bold cyan]
cli-fattura-no-clients-error = [red]Keine Kunden gefunden. Fügen Sie zuerst einen mit 'cliente add' hinzu[/red]
cli-fattura-available-clients = [cyan]Verfügbare Kunden:[/cyan]
cli-fattura-client-prompt = Kundennummer
cli-fattura-client-selected = [green]Kunde: { $client_name }[/green]
cli-fattura-invalid-client-error = [red]Ungültige Kundenauswahl[/red]

cli-fattura-add-lines-title = [bold cyan]Rechnungspositionen[/bold cyan]
cli-fattura-line-description-prompt = Beschreibung (Leer zum Beenden)
cli-fattura-line-quantity-prompt = Menge
cli-fattura-line-unit-price-prompt = Einzelpreis (€)
cli-fattura-line-vat-rate-prompt = MwSt-Satz (%)
cli-fattura-line-added = [green]Position hinzugefügt: { $description } - € { $amount }[/green]

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
cli-fattura-created-success = [bold green]Rechnung erfolgreich erstellt![/bold green]
cli-fattura-created-number = [green]Rechnungsnummer: { $numero }/{ $anno }[/green]
cli-fattura-created-xml = [green]XML gespeichert: { $xml_path }[/green]

cli-fattura-list-title = [bold blue]Rechnungsliste[/bold blue]
cli-fattura-list-empty = [yellow]Keine Rechnungen gefunden[/yellow]

cli-fattura-show-title = [bold blue]Rechnung { $numero }/{ $anno }[/bold blue]
cli-fattura-show-not-found = [red]Rechnung nicht gefunden: { $numero }/{ $anno }[/red]

cli-fattura-delete-confirm = [yellow]Rechnung { $numero }/{ $anno } löschen?[/yellow]
cli-fattura-delete-warning = [red]WARNUNG: Diese Operation kann nicht rückgängig gemacht werden[/red]
cli-fattura-delete-status-restriction = [red]Rechnung im Status '{ $status }' kann nicht gelöscht werden[/red]
cli-fattura-delete-success = [green]Rechnung { $numero }/{ $anno } gelöscht[/green]
cli-fattura-delete-cancelled = [yellow]Operation abgebrochen[/yellow]
cli-fattura-delete-cannot-delete-sent = [red]Rechnungen im Status INVIATA oder CONSEGNATA können nicht gelöscht werden[/red]

cli-fattura-validate-success = [green]XML ist gültig[/green]
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
cli-cliente-help-name = Kundenname/Firmenname (weglassen für Aufforderung im --interactive Modus)
cli-cliente-help-denominazione = Unternehmensname oder vollständiger Name
cli-cliente-help-piva = Umsatzsteuer-ID (Partita IVA)
cli-cliente-help-partita-iva = Umsatzsteuer-ID
cli-cliente-help-cf = Steuernummer (Codice Fiscale)
cli-cliente-help-codice-fiscale = Steuernummer
cli-cliente-help-sdi = SDI-Code
cli-cliente-help-pec = PEC-Adresse
cli-cliente-help-codice-destinatario = SDI-Zielcode
cli-cliente-help-interactive = Interaktiver Modus
cli-cliente-help-formato = Ausgabeformat (table, json, yaml)
cli-cliente-help-search = Suchbegriff
cli-cliente-help-limite = Maximale Anzahl der Ergebnisse
cli-cliente-help-limit = Maximale Anzahl der Ergebnisse
cli-cliente-help-cliente-id = Kunden-ID
cli-cliente-help-force = Bestätigung überspringen

### cliente - Konsolenausgabe
cli-cliente-name-required = [red]Fehler: Kundenname ist erforderlich[/red]
cli-cliente-no-clients = [yellow]Keine Kunden gefunden. Fügen Sie einen mit 'cliente add' hinzu[/yellow]
cli-cliente-list-title = Kunden ({ $count })
cli-cliente-list-empty = [yellow]Keine Kunden gefunden[/yellow]
cli-cliente-added-success = [green]Kunde erfolgreich hinzugefügt (ID: { $id })[/green]
cli-cliente-updated-success = [green]Kunde erfolgreich aktualisiert[/green]
cli-cliente-deleted-success = [green]Kunde erfolgreich gelöscht[/green]
cli-cliente-deleted = [green]Kunde '{ $name }' gelöscht[/green]
cli-cliente-cancelled = Abgebrochen.
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

cli-cliente-column-id = ID
cli-cliente-column-name = Name
cli-cliente-column-piva = USt-IdNr.
cli-cliente-column-sdi-pec = SDI/PEC
cli-cliente-column-invoices = Rechnungen

cli-cliente-label-id = ID
cli-cliente-label-name = Name
cli-cliente-label-piva = Umsatzsteuer-ID
cli-cliente-label-cf = Steuernummer
cli-cliente-label-address = Adresse
cli-cliente-label-sdi = SDI-Code
cli-cliente-label-pec = PEC
cli-cliente-label-email = E-Mail
cli-cliente-label-phone = Telefon
cli-cliente-label-total-invoices = Rechnungen insgesamt
cli-cliente-label-created = Erstellt

cli-cliente-show-title = [bold blue]Kundendetails: { $name }[/bold blue]
cli-cliente-prompt-civic-number = Hausnummer (optional)
cli-cliente-prompt-pec-address = PEC-Adresse (falls SDI 0000000 ist)
cli-cliente-confirm-delete = Möchten Sie wirklich löschen?
cli-cliente-confirm-delete-client = Kunde '{ $name }' löschen?

## ============================================================================
## Batch Commands - Stapelverarbeitungsoperationen
## ============================================================================

### batch - Help Text
cli-batch-help-csv-file = Pfad zur CSV-Datei mit Rechnungen
cli-batch-help-dry-run = Validieren ohne Import
cli-batch-help-send-summary = Zusammenfassung per E-Mail senden
cli-batch-help-output-file = Ausgabe-CSV-Dateipfad
cli-batch-help-anno = Nach Jahr filtern
cli-batch-help-stato = Nach Status filtern
cli-batch-help-limit = Maximale Anzahl der Ergebnisse

### batch - Console Output (import)
cli-batch-import-title = [bold blue]Stapel-Rechnungsimport[/bold blue]
cli-batch-file-not-found = [red]Datei nicht gefunden: { $file }[/red]
cli-batch-file-info-name = [cyan]Datei:[/cyan] { $name }
cli-batch-file-info-size = [cyan]Größe:[/cyan] { $size } Bytes
cli-batch-mode-dry-run = [cyan]Modus:[/cyan] Dry run (nur Validierung)
cli-batch-mode-import = [cyan]Modus:[/cyan] Import
cli-batch-dry-run-warning = [yellow]Dry-run-Modus - keine Daten werden gespeichert[/yellow]
cli-batch-warning-dry-run = [yellow]Dry-run-Modus - keine Daten werden gespeichert[/yellow]

cli-batch-results-title = [bold]Importergebnisse:[/bold]
cli-batch-metric-total = Zeilen insgesamt
cli-batch-metric-processed = Verarbeitet
cli-batch-metric-succeeded = Erfolgreich
cli-batch-metric-failed = Fehlgeschlagen
cli-batch-metric-success-rate = Erfolgsquote
cli-batch-metric-duration = Dauer
cli-batch-metric-label = Metrik
cli-batch-metric-value = Wert

cli-batch-errors-title = [bold red]Fehler:[/bold red]
cli-batch-errors-more = [dim]... und { $count } weitere Fehler[/dim]

cli-batch-success-all = [bold green]Alle Rechnungen erfolgreich importiert![/bold green]
cli-batch-warning-failed = [yellow]{ $count } Rechnungen nicht importiert[/yellow]

cli-batch-email-not-configured = [yellow]E-Mail-Benachrichtigung nicht konfiguriert.[/yellow]
cli-batch-sending-email = [dim]Zusammenfassung per E-Mail wird gesendet...[/dim]
cli-batch-email-sending = [dim]Zusammenfassung per E-Mail wird gesendet...[/dim]
cli-batch-email-sent = [dim]Zusammenfassung gesendet an { $email }[/dim]
cli-batch-email-failed = [yellow]Fehler beim Senden der Zusammenfassung: { $error }[/yellow]

cli-batch-error-general = [red]Fehler: { $error }[/red]

### batch - Console Output (export)
cli-batch-export-title = [bold blue]Stapel-Rechnungsexport[/bold blue]
cli-batch-filter-year = [cyan]Filter:[/cyan] Jahr = { $anno }
cli-batch-filter-status = [cyan]Filter:[/cyan] Status = { $stato }
cli-batch-invalid-status = [red]Ungültiger Status: { $stato }[/red]
cli-batch-no-invoices = [yellow]Keine Rechnungen gefunden[/yellow]
cli-batch-invoices-count = [cyan]Rechnungen:[/cyan] { $count }

cli-batch-export-success = [bold green]{ $count } Rechnungen exportiert![/bold green]
cli-batch-export-file-path = [cyan]Datei:[/cyan] { $path }
cli-batch-export-file = [cyan]Datei:[/cyan] { $path }
cli-batch-export-file-size = [cyan]Größe:[/cyan] { $size } Bytes
cli-batch-export-size = [cyan]Größe:[/cyan] { $size } Bytes
cli-batch-export-failed = [red]Export fehlgeschlagen[/red]

### batch - Console Output (history)
cli-batch-history-title = [bold blue]Stapelverarbeitungs-Verlauf[/bold blue]
cli-batch-history-not-implemented = [yellow]Verlaufsverfolgung noch nicht vollständig implementiert[/yellow]
cli-batch-history-future-features = [dim]In Produktion wird angezeigt:[/dim]
cli-batch-history-will-show = [dim]In Produktion wird angezeigt:[/dim]
cli-batch-history-feature-datetime = • Datum/Uhrzeit der Operation
cli-batch-history-feature-type = • Typ (import/export)
cli-batch-history-feature-records = • Verarbeitete Datensätze
cli-batch-history-feature-counts = • Erfolgs-/Fehleranzahl
cli-batch-history-feature-errors = • Fehlerzusammenfassungen

cli-batch-history-example-title = [bold]Beispiel-Verlauf:[/bold]
cli-batch-history-example = [bold]Beispiel-Verlauf:[/bold]
cli-batch-history-column-date = Datum
cli-batch-history-col-date = Datum
cli-batch-history-column-type = Typ
cli-batch-history-col-type = Typ
cli-batch-history-column-records = Datensätze
cli-batch-history-col-records = Datensätze
cli-batch-history-column-success = Erfolgreich
cli-batch-history-col-success = Erfolgreich
cli-batch-history-column-failed = Fehlgeschlagen
cli-batch-history-col-failed = Fehlgeschlagen

cli-batch-history-todo = [dim]TODO: BatchOperation-Modell zur Datenbank hinzufügen[/dim]

## ============================================================================
## Preventivo Commands - Kostenvoranschlagsverwaltung
## ============================================================================

### preventivo - Help Text
cli-preventivo-help-cliente-id = Kunden-ID
cli-preventivo-help-validita = Gültigkeitszeitraum in Tagen
cli-preventivo-help-stato = Nach Status filtern
cli-preventivo-help-anno = Nach Jahr filtern
cli-preventivo-help-cliente = Nach Kunden-ID filtern
cli-preventivo-help-limit = Maximale Anzahl der Ergebnisse
cli-preventivo-help-preventivo-id = Kostenvoranschlags-ID
cli-preventivo-help-force = Bestätigung überspringen
cli-preventivo-help-tipo-documento = Rechnungsdokumenttyp (TD01, TD06, usw.)
cli-preventivo-help-new-stato = Neuer Status (entwurf, gesendet, akzeptiert, abgelehnt, abgelaufen)

### preventivo - Console Output (crea)
cli-preventivo-create-title = [bold blue]Neuen Kostenvoranschlag Erstellen[/bold blue]
cli-preventivo-no-clients = [red]Keine Kunden gefunden. Fügen Sie zuerst einen Kunden mit 'openfatture cliente add' hinzu[/red]
cli-preventivo-select-client = [cyan]Verfügbare Kunden:[/cyan]
cli-preventivo-client-id-prompt = Kunden-ID auswählen
cli-preventivo-client-not-found = [red]Kunde { $id } nicht gefunden[/red]
cli-preventivo-client-selected = [green]Kunde: { $name }[/green]
cli-preventivo-validity-info = [dim]Gültigkeit: { $days } Tage (Ablauf: { $date })[/dim]

cli-preventivo-add-items-title = [bold]Positionen hinzufügen[/bold]
cli-preventivo-add-items-hint = [dim]Leere Beschreibung eingeben, um zu beenden[/dim]
cli-preventivo-item-description-prompt = Artikelbeschreibung { $num }
cli-preventivo-item-quantity-prompt = Menge
cli-preventivo-item-price-prompt = Stückpreis (€)
cli-preventivo-item-vat-prompt = MwSt.-Satz (%)
cli-preventivo-item-unit-prompt = Maßeinheit
cli-preventivo-item-added = [green]Hinzugefügt: { $desc } - €{ $total }[/green]

cli-preventivo-no-items = [yellow]Keine Positionen hinzugefügt. Erstellung des Kostenvoranschlags abgebrochen.[/yellow]
cli-preventivo-add-notes-prompt = Notizen hinzufügen?
cli-preventivo-notes-prompt = Notizen
cli-preventivo-add-conditions-prompt = Geschäftsbedingungen hinzufügen?
cli-preventivo-conditions-prompt = Geschäftsbedingungen

cli-preventivo-error-general = [red]Fehler: { $error }[/red]
cli-preventivo-created-success = [bold green]Kostenvoranschlag erfolgreich erstellt![/bold green]
cli-preventivo-next-convert = [dim]Weiter: openfatture preventivo converti { $id } (um Rechnung zu erstellen)[/dim]

### preventivo - Console Output (lista)
cli-preventivo-invalid-status = [red]Ungültiger Status: { $stato }[/red]
cli-preventivo-valid-statuses = Gültig: { $statuses }
cli-preventivo-no-preventivi = [yellow]Keine Kostenvoranschläge gefunden[/yellow]
cli-preventivo-list-title = Kostenvoranschläge ({ $count })

cli-preventivo-column-id = ID
cli-preventivo-column-number = Nummer
cli-preventivo-column-date = Datum
cli-preventivo-column-expiration = Ablauf
cli-preventivo-column-client = Kunde
cli-preventivo-column-total = Gesamt
cli-preventivo-column-status = Status

### preventivo - Console Output (show)
cli-preventivo-not-found = [red]Kostenvoranschlag { $id } nicht gefunden[/red]
cli-preventivo-show-title = [bold blue]Kostenvoranschlag { $numero }/{ $anno }[/bold blue]

cli-preventivo-field-client = Kunde
cli-preventivo-field-issue-date = Ausstellungsdatum
cli-preventivo-field-expiration = Ablaufdatum
cli-preventivo-field-validity = Gültigkeit
cli-preventivo-field-validity-days = { $days } Tage
cli-preventivo-field-status = Status
cli-preventivo-warning-expired = [red]WARNUNG[/red]
cli-preventivo-expired = [red]Abgelaufen![/red]

cli-preventivo-line-items-title = [bold]Positionen:[/bold]
cli-preventivo-line-item-number = #
cli-preventivo-line-item-description = Beschreibung
cli-preventivo-line-item-quantity = Menge
cli-preventivo-line-item-price = Preis
cli-preventivo-line-item-vat = MwSt%
cli-preventivo-line-item-total = Gesamt

cli-preventivo-totals-title = [bold]Summen:[/bold]
cli-preventivo-total-imponibile = Nettobetrag
cli-preventivo-total-iva = MwSt
cli-preventivo-total-total = [bold]GESAMT[/bold]

cli-preventivo-notes-title = [bold]Notizen:[/bold]
cli-preventivo-conditions-title = [bold]Geschäftsbedingungen:[/bold]

### preventivo - Console Output (delete)
cli-preventivo-confirm-delete = Kostenvoranschlag { $numero }/{ $anno } löschen?
cli-preventivo-cancelled = Abgebrochen.
cli-preventivo-deleted = [green]Kostenvoranschlag { $numero }/{ $anno } gelöscht[/green]

### preventivo - Console Output (converti)
cli-preventivo-convert-title = [bold blue]Kostenvoranschlag in Rechnung Umwandeln[/bold blue]
cli-preventivo-convert-summary-numero = [cyan]Kostenvoranschlag: { $numero }/{ $anno }[/cyan]
cli-preventivo-convert-summary-client = [cyan]Kunde: { $name }[/cyan]
cli-preventivo-convert-summary-total = [cyan]Gesamt: €{ $total }[/cyan]
cli-preventivo-invalid-doc-type = [red]Ungültiger Dokumenttyp: { $tipo }[/red]
cli-preventivo-valid-doc-types = Gültig: TD01, TD06, usw.
cli-preventivo-confirm-convert = In Rechnung umwandeln?
cli-preventivo-convert-cancelled = [yellow]Abgebrochen.[/yellow]
cli-preventivo-converted-success = [bold green]Kostenvoranschlag erfolgreich umgewandelt![/bold green]

cli-preventivo-invoice-title = Rechnung { $numero }/{ $anno }
cli-preventivo-invoice-field-client = Kunde
cli-preventivo-invoice-field-date = Datum
cli-preventivo-invoice-field-doc-type = Dokumenttyp
cli-preventivo-invoice-field-items = Positionen
cli-preventivo-invoice-field-imponibile = Nettobetrag
cli-preventivo-invoice-field-iva = MwSt
cli-preventivo-invoice-field-total = [bold]GESAMT[/bold]

cli-preventivo-invoice-id-info = [dim]Rechnungs-ID: { $id }[/dim]
cli-preventivo-original-preventivo-info = [dim]Original-Kostenvoranschlag: { $numero }/{ $anno } (ID: { $id })[/dim]
cli-preventivo-next-send = [dim]Weiter: openfatture fattura invia { $id } --pec[/dim]

### preventivo - Console Output (aggiorna-stato)
cli-preventivo-status-updated = [green]Kostenvoranschlagsstatus aktualisiert: { $stato }[/green]

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
cli-ai-help-service-description = Beschreibung der zu erweiternden Dienstleistung
cli-ai-help-hours-worked = Geleistete Arbeitsstunden
cli-ai-help-hourly-rate = Stundensatz (€)
cli-ai-help-project-name = Projektname
cli-ai-help-technologies = Verwendete Technologien (durch Komma getrennt)
cli-ai-help-json-output = Ausgabe im JSON-Format
cli-ai-help-stream = Echtzeit-Antwort-Streaming
cli-ai-help-client-pa = Kunde ist öffentliche Verwaltung
cli-ai-help-client-foreign = Ausländischer Kunde (außerhalb Italiens)
cli-ai-help-country-code = Ländercode des Kunden (IT, FR, DE, etc.)
cli-ai-help-service-category = Dienstleistungskategorie
cli-ai-help-amount-eur = Betrag in Euro
cli-ai-help-ateco-code = ATECO-Code
cli-ai-help-chat-message = Nachricht zum Senden an den Chat

### ai - Konsolenausgabe (describe)
cli-ai-describe-title = [bold cyan]KI-Generierung von Rechnungsbeschreibungen[/bold cyan]
cli-ai-describe-input-prompt = [cyan]Geben Sie kurze Beschreibung ein:[/cyan]
cli-ai-describe-processing = [yellow]Wird mit KI verarbeitet...[/yellow]
cli-ai-describe-result-title = [bold green]Generierte Beschreibung:[/bold green]
cli-ai-describe-result-text = [white]{ $text }[/white]
cli-ai-describe-copy-hint = [dim]Sie können diese Beschreibung beim Erstellen einer Rechnung kopieren[/dim]
cli-ai-describe-error = [red]Fehler beim Generieren der Beschreibung: { $error }[/red]
cli-ai-describe-activity = Aktivität: [yellow]{ $activity }[/yellow]
cli-ai-describe-generating = Detaillierte Beschreibung wird generiert...
cli-ai-describe-input-service = Dienstleistung
cli-ai-describe-input-hours = Geleistete Stunden
cli-ai-describe-input-rate = Stundensatz
cli-ai-describe-input-project = Projekt
cli-ai-describe-input-technologies = Technologien
cli-ai-describe-input-client-pa = PA-Kunde
cli-ai-describe-input-client-foreign = Ausländischer Kunde
cli-ai-describe-input-country = Land
cli-ai-describe-input-category = Kategorie
cli-ai-describe-input-amount = Betrag
cli-ai-describe-input-ateco = ATECO-Code

### ai - Konsolenausgabe (suggest-vat)
cli-ai-vat-title = [bold cyan]MwSt-Satzerkennung mit KI[/bold cyan]
cli-ai-vat-input-prompt = [cyan]Beschreibung der Dienstleistung/des Produkts:[/cyan]
cli-ai-vat-processing = [yellow]Wird mit KI analysiert...[/yellow]
cli-ai-vat-result-title = [bold green]Vorgeschlagener MwSt-Satz:[/bold green]
cli-ai-vat-rate = [white]{ $rate }%[/white]
cli-ai-vat-reasoning-title = [bold yellow]Begründung:[/bold yellow]
cli-ai-vat-reasoning-text = [white]{ $reasoning }[/white]
cli-ai-vat-warning = [yellow]Überprüfen Sie immer mit einem Steuerberater für komplexe Fälle[/yellow]
cli-ai-vat-error = [red]Fehler bei MwSt-Satzerkennung: { $error }[/red]
cli-ai-vat-query = Anfrage: [yellow]{ $query }[/yellow]
cli-ai-vat-analyzing = Analyse der MwSt-Vorschriften...
cli-ai-vat-disclaimer = [yellow]Dies ist ein Vorschlag. Konsultieren Sie immer einen Steuerberater.[/yellow]
cli-ai-vat-processing = Verarbeitung des MwSt-Vorschlags...
cli-ai-vat-input-service = Dienstleistung
cli-ai-vat-input-client-pa = PA-Kunde
cli-ai-vat-input-client-foreign = Ausländischer Kunde
cli-ai-input-country = Land
cli-ai-vat-input-category = Kategorie
cli-ai-vat-input-amount = Betrag
cli-ai-vat-input-ateco = ATECO-Code
cli-ai-vat-result-rate = Empfohlener MwSt-Satz
cli-ai-vat-result-nature = Art (falls zutreffend)
cli-ai-vat-result-reasoning = Begründung
cli-ai-vat-result-legal-ref = Gesetzliche Grundlage
cli-ai-vat-result-confidence = Konfidenzniveau
cli-ai-vat-result-warnings = Warnungen
cli-ai-vat-result-note = Zusätzlicher Hinweis

### ai - Konsolenausgabe (chat)
cli-ai-chat-title = [bold cyan]KI-Chat[/bold cyan]
cli-ai-chat-welcome = [cyan]Willkommen zum OpenFatture KI-Assistenten![/cyan]
cli-ai-chat-welcome-help = [dim]Geben Sie Ihre Fragen ein oder 'exit' zum Beenden[/dim]
cli-ai-chat-session-loaded = [green]Sitzung geladen: { $session_id }[/green]
cli-ai-chat-session-created = [green]Neue Sitzung erstellt: { $session_id }[/green]
cli-ai-chat-prompt = [bold cyan]Sie:[/bold cyan]
cli-ai-chat-assistant-prefix = [bold green]Assistent:[/bold green]
cli-ai-chat-thinking = [yellow]Nachdenken...[/yellow]
cli-ai-chat-tool-calling = [yellow]Werkzeug wird ausgeführt: { $tool_name }[/yellow]
cli-ai-chat-tool-result = [dim]Werkzeugergebnis: { $result }[/dim]
cli-ai-chat-session-saved = [green]Sitzung gespeichert[/green]
cli-ai-chat-goodbye = [cyan]Auf Wiedersehen! Sitzung gespeichert.[/cyan]
cli-ai-chat-error = [red]Fehler: { $error }[/red]
cli-ai-chat-cost-info = [dim]Token: { $tokens } | Kosten: €{ $cost }[/dim]
cli-ai-chat-assistant-response = [bold cyan]Assistent:[/bold cyan]
cli-ai-chat-you = [bold green]Sie:[/bold green]
cli-ai-chat-instructions = Anweisungen: Stellen Sie Fragen zu Rechnungen, Kunden, MwSt oder Steuerverwaltung
cli-ai-chat-invalid-session = [red]Sitzung nicht gefunden: { $session_id }[/red]
cli-ai-chat-no-sessions = [yellow]Keine Sitzungen verfügbar[/yellow]
cli-ai-chat-exported = [green]Konversation exportiert: { $path }[/green]
cli-ai-chat-export-error = [red]Exportfehler: { $error }[/red]

### KI-Metriken
cli-ai-metrics-provider = Anbieter
cli-ai-metrics-model = Modell
cli-ai-metrics-tokens = Verwendete Token
cli-ai-metrics-cost = Geschätzte Kosten
cli-ai-metrics-latency = Latenz

### Allgemeine KI-Fehler
cli-ai-error-unknown = Unbekannter Fehler bei der Ausführung des KI-Befehls
cli-ai-error-provider-init = KI-Anbieter-Initialisierungsfehler: { $error }
cli-ai-error-context-load = Fehler beim Laden des Geschäftskontexts: { $error }

### ai - Konsolenausgabe (voice-chat)
cli-ai-voice-title = [bold cyan]KI-Sprachchat[/bold cyan]
cli-ai-voice-welcome = [cyan]Willkommen zum Sprachchat![/cyan]
cli-ai-voice-recording-prompt = [yellow]Drücken Sie ENTER zum Starten der Aufnahme ({ $duration }s)...[/yellow]
cli-ai-voice-recording = [bold yellow]Wird aufgezeichnet...[/bold yellow]
cli-ai-voice-processing = [yellow]Audio wird verarbeitet...[/yellow]
cli-ai-voice-transcription-title = [bold green]Sie sagten:[/bold green]
cli-ai-voice-transcription-text = [white]{ $text }[/white]
cli-ai-voice-language-detected = [dim]Sprache: { $language }[/dim]
cli-ai-voice-thinking = [yellow]Assistent denkt nach...[/yellow]
cli-ai-voice-response-title = [bold green]Assistent:[/bold green]
cli-ai-voice-response-text = [white]{ $text }[/white]
cli-ai-voice-playing = [cyan]Antwort wird abgespielt...[/cyan]
cli-ai-voice-audio-saved = [dim]Audio gespeichert: { $path }[/dim]
cli-ai-voice-goodbye = [cyan]Auf Wiedersehen![/cyan]
cli-ai-voice-error = [red]Fehler: { $error }[/red]

### ai - Konsolenausgabe (forecast)
cli-ai-forecast-title = [bold cyan]Cashflow-Prognose mit KI[/bold cyan]
cli-ai-forecast-loading-data = [yellow]Historische Daten werden geladen...[/yellow]
cli-ai-forecast-data-stats = [cyan]Rechnungen: { $invoices } | Zahlungen: { $payments }[/cyan]
cli-ai-forecast-training = [yellow]ML-Modelle werden trainiert...[/yellow]
cli-ai-forecast-training-progress = [yellow]{ $progress }%[/yellow]
cli-ai-forecast-predicting = [yellow]Prognose wird erstellt...[/yellow]
cli-ai-forecast-results-title = [bold green]Cashflow-Prognose - Nächste { $months } { $months ->
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
cli-ai-intelligence-title = [bold cyan]Geschäftsintelligenzanalyse[/bold cyan]
cli-ai-intelligence-analyzing = [yellow]Geschäftsdaten werden analysiert...[/yellow]
cli-ai-intelligence-report-title = [bold green]Geschäftserkenntnisse:[/bold green]
cli-ai-intelligence-section = [bold yellow]{ $section }[/bold yellow]
cli-ai-intelligence-insight = • { $insight }
cli-ai-intelligence-error = [red]Analysefehler: { $error }[/red]

### ai - Konsolenausgabe (compliance)
cli-ai-compliance-title = [bold cyan]Compliance-Überprüfung[/bold cyan]
cli-ai-compliance-checking = [yellow]Prüfe Rechnung { $numero }/{ $anno }...[/yellow]
cli-ai-compliance-passed = [bold green]Alle Compliance-Überprüfungen bestanden[/bold green]
cli-ai-compliance-warnings = [yellow]{ $count } { $count ->
    [one] Warnung gefunden
   *[other] Warnungen gefunden
}[/yellow]
cli-ai-compliance-errors = [red]{ $count } { $count ->
    [one] Fehler gefunden
   *[other] Fehler gefunden
}[/red]
cli-ai-compliance-check-item = [{ $status }] { $message }
cli-ai-compliance-error = [red]Compliance-Überprüfungsfehler: { $error }[/red]

### ai - Konsolenausgabe (rag)
cli-ai-rag-title = [bold cyan]RAG-Dokumentsuche[/bold cyan]
cli-ai-rag-indexing = [yellow]Dokumente werden indexiert...[/yellow]
cli-ai-rag-indexed = [green]{ $count } { $count ->
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
cli-ai-feedback-title = [bold cyan]KI-Feedback[/bold cyan]
cli-ai-feedback-prompt-rating = [cyan]Antwort bewerten (1-5):[/cyan]
cli-ai-feedback-prompt-comment = [cyan]Kommentar (optional):[/cyan]
cli-ai-feedback-thanks = [green]Vielen Dank für Ihr Feedback![/green]
cli-ai-feedback-saved = [green]Feedback in Sitzung { $session_id } gespeichert[/green]
cli-ai-feedback-error = [red]Feedback-Fehler: { $error }[/red]

## ============================================================================
## EVENTS Commands - Ereignisverlauf und Audit-Trail
## ============================================================================

### Help Texts - Befehle und Optionen
cli-events-help = Ereignisverlauf anzeigen und analysieren

# list command
cli-events-list-help-type = Nach Ereignistyp filtern
cli-events-list-help-entity = Nach Entitätstyp filtern (Rechnung, Kunde, Zahlung, etc.)
cli-events-list-help-entity-id = Nach Entitäts-ID filtern
cli-events-list-help-last-hours = Ereignisse der letzten N Stunden anzeigen
cli-events-list-help-last-days = Ereignisse der letzten N Tage anzeigen
cli-events-list-help-limit = Maximale Anzahl anzuzeigender Ereignisse

# show command
cli-events-show-help-event-id = Ereignis-ID (UUID)

# stats command
cli-events-stats-help-last-hours = Statistiken der letzten N Stunden
cli-events-stats-help-last-days = Statistiken der letzten N Tage

# timeline command
cli-events-timeline-help-entity-type = Entitätstyp (invoice, client, etc.)
cli-events-timeline-help-entity-id = Entitäts-ID

# search command
cli-events-search-help-query = Suchzeichenfolge
cli-events-search-help-limit = Maximale Anzahl der Ergebnisse

# dashboard command
cli-events-dashboard-help-days = Anzahl der zu analysierenden Tage

# trends command
cli-events-trends-help-days = Anzahl der zu analysierenden Tage
cli-events-trends-help-type = Nach Ereignistyp filtern

### Table Columns - Spaltenüberschriften
cli-events-column-timestamp = Zeitstempel
cli-events-column-event-type = Ereignistyp
cli-events-column-entity = Entität
cli-events-column-entity-type = Entitätstyp
cli-events-column-summary = Zusammenfassung
cli-events-column-count = Anzahl
cli-events-column-percentage = Prozentsatz
cli-events-column-match = Übereinstimmung

### Titles and Headers - Titel und Überschriften
cli-events-list-title = Ereignisverlauf ({ $count } Ereignisse)
cli-events-show-panel-title = [bold]Ereignisdetails: { $event_type }[/bold]
cli-events-stats-table-by-type = Ereignisse nach Typ
cli-events-stats-table-by-entity = Ereignisse nach Entitätstyp
cli-events-stats-panel-title = [bold]Ereignisstatistiken - { $range }[/bold]
cli-events-timeline-panel-title = [bold]Ereignis-Zeitlinie: { $entity_type } #{ $entity_id }[/bold]
cli-events-search-results-title = Suchergebnisse: '{ $query }' ({ $count } Ereignisse)
cli-events-types-table-title = Verfügbare Ereignistypen
cli-events-dashboard-panel-title = [bold]Ereignis-Analyse-Dashboard - Letzte { $days } Tage[/bold]
cli-events-dashboard-table-entity-activity = Aktivität nach Entität
cli-events-trends-panel-title = [bold]Ereignistrends - Letzte { $days } Tage[/bold]
cli-events-trends-panel-title-filtered = [bold]Ereignistrends - Letzte { $days } Tage ({ $event_type })[/bold]

### Labels - Feldbezeichnungen
cli-events-show-label-event-id = Ereignis-ID
cli-events-show-label-event-type = Ereignistyp
cli-events-show-label-occurred-at = Aufgetreten am
cli-events-show-label-published-at = Veröffentlicht am
cli-events-show-label-entity-type = Entitätstyp
cli-events-show-label-entity-id = Entitäts-ID
cli-events-show-label-user-id = Benutzer-ID
cli-events-show-label-event-data = Ereignisdaten
cli-events-show-label-metadata = Metadaten

### Dashboard Metrics - Dashboard-Metriken
cli-events-dashboard-metric-total = Ereignisse Gesamt
cli-events-dashboard-metric-types = Ereignistypen
cli-events-dashboard-metric-velocity = Ereignisse/Stunde (24h)
cli-events-dashboard-metric-trend = Trend
cli-events-dashboard-section-top-types = [bold]Wichtigste Ereignistypen[/bold]
cli-events-dashboard-column-events = Ereignisse

### Messages - Ausgabemeldungen
cli-events-no-events = [yellow]Keine Ereignisse gefunden, die den Kriterien entsprechen[/yellow]
cli-events-show-not-found = [red]Ereignis mit ID '{ $event_id }' nicht gefunden[/red]
cli-events-filters-applied = [dim]Filter: { $filters }[/dim]
cli-events-stats-all-time = Alle Zeit
cli-events-stats-last-hours = Letzte { $hours } Stunden
cli-events-stats-last-days = Letzte { $days } Tage
cli-events-stats-total = [bold]Ereignisse Gesamt:[/bold] { $total }

cli-events-stats-most-recent = [bold]Neuestes Ereignis:[/bold] { $event_type } am { $timestamp }
cli-events-stats-oldest = [bold]Ältestes Ereignis:[/bold] { $event_type } am { $timestamp }
cli-events-timeline-no-events = [yellow]Keine Ereignisse für { $entity_type } mit ID { $entity_id } gefunden[/yellow]
cli-events-timeline-total = [dim]Ereignisse gesamt: { $total }[/dim]
cli-events-search-no-results = [yellow]Keine Ereignisse gefunden, die '{ $query }' entsprechen[/yellow]
cli-events-types-no-events = [yellow]Noch keine Ereignisse aufgezeichnet[/yellow]
cli-events-dashboard-most-recent = [dim]Neuestes: { $event_type } am { $timestamp }[/dim]
cli-events-trends-no-events = [yellow]Keine Ereignisse für den angegebenen Zeitraum gefunden[/yellow]
cli-events-trends-summary = [dim]Gesamt: { $total } Ereignisse | Durchschnitt: { $avg } Ereignisse/Tag[/dim]

## ============================================================================
## LIGHTNING Commands - Lightning Network und Compliance
## ============================================================================

### Help Texts - Befehle und Optionen
cli-lightning-help = Lightning Network Zahlungsverwaltung
cli-lightning-report-help = Compliance-Berichte erstellen
cli-lightning-aml-help = Geldwäsche-Compliance-Verwaltung

### Status Command
cli-lightning-status-title = Lightning Network Status
cli-lightning-status-disabled = Status: Deaktiviert
cli-lightning-status-disabled-hint-env = Setzen Sie lightning_enabled=true in .env um Lightning-Zahlungen zu aktivieren
cli-lightning-status-disabled-hint-cmd = Verwenden Sie 'openfatture config set lightning_enabled true' zum Aktivieren
cli-lightning-status-enabled = Status: Aktiviert
cli-lightning-status-host = Host: { $host }
cli-lightning-status-timeout = Zeitüberschreitung: { $timeout }s
cli-lightning-status-max-retries = Max. Versuche: { $max_retries }
cli-lightning-status-btc-provider = BTC-Anbieter: { $provider }
cli-lightning-status-liquidity = Liquiditätsüberwachung: { $status }

cli-lightning-btc-provider-coingecko = CoinGecko
cli-lightning-btc-provider-cmc = CoinMarketCap
cli-lightning-btc-provider-fallback = Fallback
cli-lightning-liquidity-enabled = Aktiviert
cli-lightning-liquidity-disabled = Deaktiviert

### Invoice Command
cli-lightning-disabled-error = Lightning ist deaktiviert. Aktivieren Sie mit: openfatture config set lightning_enabled true
cli-lightning-invoice-title = Lightning-Rechnung Erstellen
cli-lightning-invoice-not-available = Funktion noch nicht verfügbar - Lightning-Integration in Entwicklung

### Channels Command
cli-lightning-channels-title = Lightning-Kanäle
cli-lightning-channels-not-available = Keine Kanäle konfiguriert - Lightning-Integration in Entwicklung

### Liquidity Command
cli-lightning-liquidity-title = Kanal-Liquidität
cli-lightning-liquidity-not-available = Liquiditätsüberwachung nicht verfügbar - Lightning-Integration in Entwicklung

### Compliance Check Command
cli-lightning-compliance-opt-tax-year = Zu prüfendes Steuerjahr (Standard: aktuelles Jahr)
cli-lightning-compliance-opt-verbose = Detaillierte Informationen anzeigen

cli-lightning-compliance-title = [bold cyan]Lightning Compliance-Prüfung - { $year }[/bold cyan]

cli-lightning-compliance-summary-title = [bold]Steuerjahr Zusammenfassung[/bold]
cli-lightning-compliance-summary-payments = Anzahl der Zahlungen:
cli-lightning-compliance-summary-revenue = Gesamteinnahmen (EUR):
cli-lightning-compliance-summary-gains = Gesamtkapitalgewinne (EUR):
cli-lightning-compliance-summary-tax = Geschätzte Steuern (EUR):

cli-lightning-compliance-aml-title = [bold]GW-Compliance (Schwelle: 5.000 EUR)[/bold]
cli-lightning-compliance-aml-total = Gesamt über Schwelle:
cli-lightning-compliance-aml-verified = Verifiziert:
cli-lightning-compliance-aml-unverified = Nicht verifiziert:
cli-lightning-compliance-aml-status-ok = OK
cli-lightning-compliance-aml-status-require = { $count } BENÖTIGEN VERIFIZIERUNG

cli-lightning-compliance-quadro-title = [bold]Quadro RW Erklärung (Obligatorisch ab 2025)[/bold]
cli-lightning-compliance-quadro-count = Rechnungen die Erklärung benötigen:
cli-lightning-compliance-action-required = Erforderliche Aktion:
cli-lightning-compliance-quadro-action = [yellow]Alle Krypto-Bestände in Quadro RW erklären[/yellow]
cli-lightning-compliance-status = Status:
cli-lightning-compliance-quadro-status-ok = [green]Keine Erklärungen erforderlich[/green]

cli-lightning-compliance-data-quality-title = [bold]Datenqualität[/bold]
cli-lightning-compliance-data-quality-missing = Rechnungen mit fehlenden Steuerdaten:
cli-lightning-compliance-data-quality-action = [red]BTC/EUR-Kurs und EUR-Betrag für Steuer-Compliance hinzufügen[/red]
cli-lightning-compliance-data-quality-status-ok = [green]Alle abgerechneten Rechnungen haben Steuerdaten[/green]

cli-lightning-compliance-issue-aml = { $count } nicht verifizierte GW-Zahlung(en)
cli-lightning-compliance-issue-missing-data = { $count } Rechnung(en) ohne Steuerdaten
cli-lightning-compliance-issues-found = [bold red]Compliance-Probleme Gefunden: { $issues }[/bold red]

cli-lightning-compliance-passed = [bold green]Alle Compliance-Prüfungen Bestanden[/bold green]

cli-lightning-compliance-verbose-title = [bold]Nicht Verifizierte GW-Zahlungen:[/bold]
cli-lightning-compliance-verbose-item =   • { $hash }... - { $amount } EUR - Abgerechnet: { $date }

cli-lightning-compliance-error = [bold red]Fehler bei Compliance-Prüfung: { $error }[/bold red]

### Report Commands - Common Options
cli-lightning-report-opt-tax-year = Steuerjahr für Bericht
cli-lightning-report-opt-format = Ausgabeformat: json oder csv
cli-lightning-report-opt-output = Ausgabedateipfad (optional, gibt auf stdout aus wenn nicht angegeben)

cli-lightning-report-invalid-format = [bold red]Ungültiges Format. Verwenden Sie 'json' oder 'csv'[/bold red]
cli-lightning-report-saved = [green]Bericht gespeichert in: { $path }[/green]

cli-lightning-report-summary = [cyan]Gesamtrechnungen im Bericht: { $count }[/cyan]

### Quadro RW Report
cli-lightning-report-quadro-title = [bold cyan]Erstelle Quadro RW Bericht - { $year } ({ $format })[/bold cyan]

cli-lightning-report-quadro-error = [bold red]Fehler beim Erstellen des Quadro RW Berichts: { $error }[/bold red]

### Capital Gains Report
cli-lightning-report-gains-title = [bold cyan]Erstelle Kapitalgewinne-Bericht - { $year } ({ $format })[/bold cyan]

cli-lightning-report-gains-summary-count = [cyan]Gesamtrechnungen mit Gewinnen: { $count }[/cyan]
cli-lightning-report-gains-summary-total = [yellow]Gesamtkapitalgewinne: { $total } EUR[/yellow]
cli-lightning-report-gains-summary-tax = [red]Geschätzte Steuern ({ $rate }%): { $tax } EUR[/red]
cli-lightning-report-gains-error = [bold red]Fehler beim Erstellen des Kapitalgewinne-Berichts: { $error }[/bold red]

### AML Report
cli-lightning-aml-opt-threshold = GW-Schwelle in EUR
cli-lightning-aml-opt-format = Ausgabeformat: nur json
cli-lightning-aml-opt-verbose = Detaillierte Informationen anzeigen

cli-lightning-aml-report-title = [bold cyan]Erstelle GW-Compliance-Bericht (Schwelle: { $threshold } EUR)[/bold cyan]

cli-lightning-aml-report-summary-total = [cyan]Gesamt über Schwelle: { $total }[/cyan]
cli-lightning-aml-report-summary-verified = [green]Verifiziert: { $verified }[/green]
cli-lightning-aml-report-summary-unverified-ok = Nicht verifiziert: 0
cli-lightning-aml-report-summary-unverified-warning = Nicht verifiziert: { $count }
cli-lightning-aml-report-summary-rate = [yellow]Compliance-Rate: { $rate }%[/yellow]

cli-lightning-aml-report-action-required = [bold yellow]Erforderliche Aktion: Nicht verifizierte Zahlungen mit GW-Prozess verifizieren[/bold yellow]
cli-lightning-aml-report-action-hint = [dim]Verwenden Sie: openfatture lightning aml list-unverified für Details[/dim]

cli-lightning-aml-report-error = [bold red]Fehler beim Erstellen des GW-Berichts: { $error }[/bold red]

### AML List Unverified Command
cli-lightning-aml-list-title = [bold cyan]Nicht Verifizierte GW-Zahlungen (Schwelle: { $threshold } EUR)[/bold cyan]

cli-lightning-aml-list-empty = [green]Keine nicht verifizierten Zahlungen gefunden[/green]

cli-lightning-aml-list-table-title = Nicht Verifizierte Zahlungen ({ $count } gesamt)
cli-lightning-aml-list-col-hash = Zahlungs-Hash
cli-lightning-aml-list-col-amount = Betrag (EUR)
cli-lightning-aml-list-col-settled = Abgerechnet Am
cli-lightning-aml-list-col-fattura = Rechnungs-ID
cli-lightning-aml-list-col-client = Kunden-ID
cli-lightning-aml-list-col-description = Beschreibung

cli-lightning-aml-list-action-required = [bold yellow]Erforderliche Aktion: Diese Zahlungen benötigen Kundenidentitätsprüfung[/bold yellow]
cli-lightning-aml-list-action-hint = [dim]Verwenden Sie: openfatture lightning aml verify <payment-hash> --verified-by <email>[/dim]

cli-lightning-aml-list-error = [bold red]Fehler beim Auflisten nicht verifizierter Zahlungen: { $error }[/bold red]

### AML Verify Command
cli-lightning-aml-verify-arg-hash = Zu verifizierender Zahlungs-Hash
cli-lightning-aml-verify-opt-by = E-Mail der verifizierenden Person
cli-lightning-aml-verify-opt-notes = Verifizierungsnotizen (optional)
cli-lightning-aml-verify-opt-client = Kunden-ID (optional)

cli-lightning-aml-verify-title = [bold cyan]Verifiziere GW-Zahlung: { $hash }...[/bold cyan]

cli-lightning-aml-verify-not-found = [bold red]Rechnung nicht gefunden: { $hash }[/bold red]
cli-lightning-aml-verify-already-verified = [yellow]Zahlung bereits verifiziert am { $date }[/yellow]
cli-lightning-aml-verify-below-threshold = [yellow]Zahlung überschreitet GW-Schwelle nicht, wird aber trotzdem als verifiziert markiert[/yellow]
cli-lightning-aml-verify-success = [green]Zahlung erfolgreich verifiziert[/green]

cli-lightning-aml-verify-label-hash = Zahlungs-Hash:
cli-lightning-aml-verify-label-amount = Betrag (EUR):
cli-lightning-aml-verify-label-settled = Abgerechnet Am:
cli-lightning-aml-verify-label-by = Verifiziert Von:
cli-lightning-aml-verify-label-at = Verifiziert Am:
cli-lightning-aml-verify-label-notes = Notizen:

cli-lightning-aml-verify-error = [bold red]Fehler beim Verifizieren der Zahlung: { $error }[/bold red]

## ============================================================================
## REPORT Commands - Berichte und Statistiken
## ============================================================================

### Help Texts - Befehle und Optionen
cli-report-iva-help-anno = Jahr
cli-report-iva-help-trimestre = Quartal (Q1-Q4)
cli-report-clienti-help-anno = Jahr
cli-report-scadenze-help-finestra = Anzahl der Tage, die als "bald fällig" betrachtet werden (Standard: 14)

### Titles and Headers - MwSt Report
cli-report-iva-title = [bold blue]MwSt-Bericht - { $anno }[/bold blue]

cli-report-iva-quarter = [cyan]Quartal: { $trimestre } ({ $mese_inizio }-{ $mese_fine })[/cyan]

cli-report-iva-full-year = [cyan]Gesamtes Jahr[/cyan]

cli-report-iva-summary-title = MwSt-Zusammenfassung
cli-report-iva-breakdown-title = [bold]Aufschlüsselung nach MwSt-Satz:[/bold]

### Titles and Headers - Client Report
cli-report-clienti-title = [bold blue]Kunden-Umsatzbericht - { $anno }[/bold blue]

cli-report-clienti-table-title = Top-Kunden - { $anno }

### Titles and Headers - Due Dates Report
cli-report-scadenze-title = [bold blue]Übersicht der Fälligkeitstermine[/bold blue]

### Table Columns - MwSt Report
cli-report-iva-column-metric = Metrik
cli-report-iva-column-amount = Betrag
cli-report-iva-column-vat-rate = MwSt-Satz
cli-report-iva-column-imponibile = Steuerbemessungsgrundlage
cli-report-iva-column-vat = MwSt

### Table Columns - Client Report
cli-report-clienti-column-rank = Rang
cli-report-clienti-column-client = Kunde
cli-report-clienti-column-invoices = Rechnungen
cli-report-clienti-column-revenue = Umsatz

### Table Columns - Due Dates Report
cli-report-scadenze-column-invoice = Rechnung
cli-report-scadenze-column-client = Kunde
cli-report-scadenze-column-due-date = Fälligkeitsdatum
cli-report-scadenze-column-days-delta = Δ Tage
cli-report-scadenze-column-residual = Ausstehend
cli-report-scadenze-column-paid = Bezahlt
cli-report-scadenze-column-total = Gesamt
cli-report-scadenze-column-status = Status

### Labels - MwSt Report
cli-report-iva-label-num-invoices = Anzahl der Rechnungen
cli-report-iva-label-imponibile = Gesamt-Steuerbemessungsgrundlage
cli-report-iva-label-total-vat = Gesamt-MwSt
cli-report-iva-label-total-revenue-bold = [bold]Gesamtumsatz[/bold]

### Messages - General
cli-report-no-invoices = [yellow]Keine Rechnungen für den ausgewählten Zeitraum gefunden[/yellow]
cli-report-no-invoices-year = [yellow]Keine Rechnungen für das ausgewählte Jahr gefunden[/yellow]

### Messages - MwSt Report
cli-report-iva-error-invalid-quarter = [red]Ungültiges Quartal. Verwenden Sie Q1, Q2, Q3 oder Q4[/red]

### Messages - Client Report
cli-report-clienti-total-revenue = [bold]Gesamtumsatz: { $totale }[/bold]

### Messages - Due Dates Report
cli-report-scadenze-no-outstanding = [green]Keine ausstehenden Zahlungen. Alle Rechnungen sind beglichen![/green]

cli-report-scadenze-hidden-upcoming = [dim]… { $count } weitere zukünftige Zahlungen nicht angezeigt. Verwenden Sie --finestra oder exportieren Sie Daten aus dem Zahlungsmodul für weitere Details.[/dim]

cli-report-scadenze-total-outstanding = [bold]Gesamter ausstehender Saldo: { $totale }[/bold]

### Section Titles - Due Dates Report
cli-report-scadenze-section-overdue = [red]Überfällig[/red]
cli-report-scadenze-section-due-soon = [yellow]Bald fällig (<= { $finestra } Tage)[/yellow]
cli-report-scadenze-section-upcoming = [cyan]Kommende Zahlungen[/cyan]

cli-report-scadenze-section-total = [bold { $color }]Gesamt ausstehend: { $totale } • Zahlungen: { $count }[/]

### Payment Status Labels - Due Dates Report
cli-report-scadenze-status-overdue = Überfällig
cli-report-scadenze-status-partial = Teilweise
cli-report-scadenze-status-due = Fällig

## ============================================================================
## PEC Commands - PEC-Tests und Konfiguration
## ============================================================================

### Titles
cli-pec-test-title = [bold blue]PEC-Konfiguration testen[/bold blue]
cli-pec-info-title = [bold blue]PEC-Konfiguration[/bold blue]

### Labels
cli-pec-label-address = [cyan]PEC-Adresse:[/cyan]
cli-pec-label-smtp-server = [cyan]SMTP-Server:[/cyan]
cli-pec-label-smtp-port = [cyan]SMTP-Port:[/cyan]
cli-pec-label-template = [cyan]Vorlage:[/cyan] test/test_email.html + .txt
cli-pec-label-locale = [cyan]Sprache:[/cyan]
cli-pec-label-password = Passwort
cli-pec-label-sdi-pec = SDI PEC

### Table Headers
cli-pec-table-setting = Einstellung
cli-pec-table-value = Wert

### Error Messages
cli-pec-error-no-address = [red]PEC-Adresse nicht konfiguriert[/red]
cli-pec-error-no-address-hint = Ausführen: [cyan]openfatture init[/cyan] zum Konfigurieren
cli-pec-error-no-password = [red]PEC-Passwort nicht konfiguriert[/red]
cli-pec-error-no-password-hint = Setzen Sie es in Ihrer .env-Datei: PEC_PASSWORD=ihr_passwort

### Test Messages
cli-pec-sending-test = Sende Test-E-Mail mit professioneller Vorlage...
cli-pec-test-success = [bold green]Test-E-Mail erfolgreich gesendet![/bold green]
cli-pec-test-check-inbox = Überprüfen Sie Ihr PEC-Postfach: { $pec_address }
cli-pec-test-email-includes = [dim]Die E-Mail enthält:[/dim]
cli-pec-test-feature-html = • Professionelles HTML + Klartext
cli-pec-test-feature-branding = • Ihr Firmen-Branding
cli-pec-test-feature-language = • Sprache: { $language }
cli-pec-test-more-testing = [dim]Für weitere E-Mail-Tests:[/dim]
cli-pec-test-cmd-email-test = [cyan]openfatture email test[/cyan]  - Vollständiger E-Mail-Test
cli-pec-test-cmd-email-preview = [cyan]openfatture email preview[/cyan] - Vorlagenvorschau

cli-pec-test-failed = [red]Test fehlgeschlagen: { $error }[/red]
cli-pec-test-common-issues = [yellow]Häufige Probleme:[/yellow]
cli-pec-issue-credentials = • Falsche PEC-Anmeldedaten
cli-pec-issue-smtp = • Falscher SMTP-Server
cli-pec-issue-firewall = • Firewall blockiert Port 465
cli-pec-issue-mailbox = • PEC-Postfach voll

### Info Messages
cli-pec-not-set = [red]Nicht festgelegt[/red]
cli-pec-password-set = [green]Festgelegt[/green]

## ============================================================================
## NOTIFICHE Commands - SDI-Benachrichtigungsverwaltung
## ============================================================================

### Help Text
cli-notifiche-help-file-path = Pfad zur SDI-Benachrichtigungs-XML-Datei
cli-notifiche-help-no-email = Automatische E-Mail-Benachrichtigung überspringen
cli-notifiche-help-tipo = Nach Typ filtern (AT, RC, NS, MC, NE)
cli-notifiche-help-limit = Maximale Anzahl der Ergebnisse
cli-notifiche-help-notification-id = Benachrichtigungs-ID

### Titles
cli-notifiche-process-title = [bold blue]SDI-Benachrichtigung verarbeiten[/bold blue]
cli-notifiche-list-title = [bold blue]SDI-Benachrichtigungen[/bold blue]
cli-notifiche-show-title = [bold blue]{ $emoji } Benachrichtigung { $id }: { $tipo }[/bold blue]

### Table Headers
cli-notifiche-table-field = Feld
cli-notifiche-table-value = Wert
cli-notifiche-column-id = ID
cli-notifiche-column-type = Typ
cli-notifiche-column-date = Datum
cli-notifiche-column-invoice = Rechnung
cli-notifiche-column-client = Kunde
cli-notifiche-column-sdi-id = SDI-ID

### Labels
cli-notifiche-label-type = Typ
cli-notifiche-label-sdi-id = SDI-ID
cli-notifiche-label-file = Datei
cli-notifiche-label-date = Datum
cli-notifiche-label-message = Nachricht
cli-notifiche-label-errors = Fehler
cli-notifiche-label-invoice = Rechnung
cli-notifiche-label-client = Kunde
cli-notifiche-label-invoice-status = Rechnungsstatus
cli-notifiche-label-received = Empfangen
cli-notifiche-label-description = Beschreibung
cli-notifiche-label-xml-path = XML-Pfad

### Messages
cli-notifiche-file-not-found = [red]Datei nicht gefunden: { $file_path }[/red]
cli-notifiche-file-label = [cyan]Datei:[/cyan] { $name }
cli-notifiche-size-label = [cyan]Größe:[/cyan] { $size } Bytes
cli-notifiche-auto-email-enabled = [dim]Automatische E-Mail aktiviert { $email }[/dim]

cli-notifiche-processing = Verarbeite Benachrichtigung...
cli-notifiche-error = [red]Fehler: { $error }[/red]
cli-notifiche-success = [bold green]Benachrichtigung erfolgreich verarbeitet![/bold green]
cli-notifiche-errors-count = { $count } Fehler
cli-notifiche-email-sent = [dim]E-Mail-Benachrichtigung gesendet an { $email }[/dim]

cli-notifiche-no-notifications = [yellow]Keine Benachrichtigungen gefunden[/yellow]
cli-notifiche-process-hint = [dim]Benachrichtigungen verarbeiten mit:[/dim]
cli-notifiche-process-cmd = [cyan]openfatture notifiche process <datei.xml>[/cyan]
cli-notifiche-list-table-title = Benachrichtigungen ({ $count })

cli-notifiche-not-found = [red]Benachrichtigung { $notification_id } nicht gefunden[/red]

## ============================================================================
## CONFIG Commands - Konfigurationsverwaltung
## ============================================================================

### Help Text
cli-config-help-key = Konfigurationsschlüssel (z.B. pec.address)
cli-config-help-value = Konfigurationswert

### Titles
cli-config-show-title = OpenFatture Konfiguration

### Table Headers
cli-config-column-setting = Einstellung
cli-config-column-value = Wert

### Section Labels - Application
cli-config-label-app-version = App-Version
cli-config-label-debug-mode = Debug-Modus

### Section Labels - Database
cli-config-label-database-url = Datenbank-URL

### Section Labels - Paths
cli-config-label-data-dir = Datenverzeichnis
cli-config-label-archive-dir = Archivverzeichnis
cli-config-label-certificates-dir = Zertifikatsverzeichnis

### Section Labels - Company Data
cli-config-label-company-name = Firmenname
cli-config-label-partita-iva = Partita IVA
cli-config-label-codice-fiscale = Codice Fiscale
cli-config-label-tax-regime = Steuerregime

### Section Labels - PEC
cli-config-label-pec-address = PEC-Adresse
cli-config-label-pec-smtp-server = PEC-SMTP-Server
cli-config-label-sdi-pec-address = SDI-PEC-Adresse

### Section Labels - Email & Notifications
cli-config-label-notification-email = Benachrichtigungs-E-Mail
cli-config-label-notifications-enabled = Benachrichtigungen aktiviert
cli-config-label-locale = Sprache
cli-config-label-email-logo-url = E-Mail-Logo-URL
cli-config-label-primary-color = Primärfarbe
cli-config-label-secondary-color = Sekundärfarbe
cli-config-label-email-footer = E-Mail-Fußzeile

### Section Labels - AI Configuration
cli-config-label-ai-provider = KI-Anbieter
cli-config-label-ai-model = KI-Modell
cli-config-label-ai-base-url = KI-Basis-URL
cli-config-label-ai-api-key = KI-API-Schlüssel
cli-config-label-chat-enabled = Chat aktiviert
cli-config-label-chat-auto-save = Chat-Auto-Speicherung
cli-config-label-max-messages = Max. Nachrichten/Sitzung
cli-config-label-max-tokens = Max. Tokens/Sitzung
cli-config-label-tools-enabled = Werkzeuge aktiviert
cli-config-label-enabled-tools = Aktivierte Werkzeuge

### Status Values
cli-config-not-set = [red]Nicht festgelegt[/red]
cli-config-not-set-optional = [yellow]Nicht festgelegt[/yellow]
cli-config-set = [green]Festgelegt[/green]
cli-config-yes = [green]Ja[/green]
cli-config-no = [red]Nein[/red]
cli-config-auto-generated = [dim]Automatisch generiert[/dim]
cli-config-all-tools = alle
cli-config-tools-count = { $count } Werkzeuge

### Messages
cli-config-reload-success = [green]Konfiguration neu geladen[/green]
cli-config-set-success = [green]{ $key } = { $value } festgelegt[/green]
cli-config-saved-to = [dim]Gespeichert in { $path }[/dim]
cli-config-invalid-key = [red]Ungültiger Konfigurationsschlüssel: { $key }[/red]
cli-config-error = [red]Fehler: { $error }[/red]

# Added: chat labels / DB-error messages
cli-ai-chat-assistant-title = [bold cyan]KI-Assistent[/bold cyan]
cli-ai-chat-exit-message = [yellow]Auf Wiedersehen![/yellow]
cli-cliente-add-error = [red]Fehler beim Speichern des Kunden: { $error }[/red]
cli-fattura-create-error = [red]Fehler beim Erstellen der Rechnung: { $error }[/red]
