### main - Haupt-CLI

## CONFIG Commands - Konfigurationsverwaltung
cli-config-help-key = Konfigurationsschlüssel (z.B. pec.address)
cli-config-help-value = Konfigurationswert
cli-config-show-title = OpenFatture Konfiguration
cli-config-column-setting = Einstellung
cli-config-column-value = Wert
cli-config-label-app-version = App-Version
cli-config-label-debug-mode = Debug-Modus
cli-config-label-database-url = Datenbank-URL
cli-config-label-data-dir = Datenverzeichnis
cli-config-label-archive-dir = Archivverzeichnis
cli-config-label-certificates-dir = Zertifikatsverzeichnis
cli-config-label-company-name = Firmenname
cli-config-label-partita-iva = Partita IVA
cli-config-label-codice-fiscale = Codice Fiscale
cli-config-label-tax-regime = Steuerregime
cli-config-label-pec-address = PEC-Adresse
cli-config-label-pec-smtp-server = PEC-SMTP-Server
cli-config-label-sdi-pec-address = SDI-PEC-Adresse
cli-config-label-notification-email = Benachrichtigungs-E-Mail
cli-config-label-notifications-enabled = Benachrichtigungen aktiviert
cli-config-label-locale = Sprache
cli-config-label-email-logo-url = E-Mail-Logo-URL
cli-config-label-primary-color = Primärfarbe
cli-config-label-secondary-color = Sekundärfarbe
cli-config-label-email-footer = E-Mail-Fußzeile
cli-config-label-ai-provider = KI-Anbieter
cli-config-label-ai-model = KI-Modell
cli-config-label-ai-base-url = KI-Basis-URL
cli-config-label-ai-api-key = KI-API-Schlüssel
cli-config-label-chat-enabled = Chat aktiviert
cli-config-label-chat-auto-save = Chat-Auto-Speicherung
cli-config-label-max-messages = Max. Nachrichten/Sitzung
cli-config-label-max-tokens = Max. Tokens/Sitzung
cli-config-label-tools-enabled = Werkzeuge aktiviert
cli-config-label-tool-access = KI-Werkzeugzugriff
cli-config-label-extra-tools = Zusätzliche Werkzeuge
cli-config-not-set = [red]Nicht festgelegt[/red]
cli-config-not-set-optional = [yellow]Nicht festgelegt[/yellow]
cli-config-set = [green]Festgelegt[/green]
cli-config-yes = [green]Ja[/green]
cli-config-no = [red]Nein[/red]
cli-config-auto-generated = [dim]Automatisch generiert[/dim]
cli-config-reload-success = [green]Konfiguration neu geladen[/green]
cli-config-set-success = [green]{ $key } = { $value } festgelegt[/green]
cli-config-saved-to = [dim]Gespeichert in { $path }[/dim]
cli-config-invalid-key = [red]Ungültiger Konfigurationsschlüssel: { $key }[/red]
cli-config-error = [red]Fehler: { $error }[/red]
cli-config-column-source = Quelle
cli-config-source-env = Umgebung
cli-config-source-keyring = Schlüsselbund
cli-config-source-file = Anmeldedatei
cli-config-source-config = config.toml
cli-config-source-default = Standard
cli-config-file-path = [dim]Konfigurationsdatei: { $path }[/dim]
cli-config-secret-backend = [dim]Geheimnisse: { $backend }[/dim]
cli-config-secret-saved = [green]{ $key } gespeichert in: { $backend }[/green]
cli-config-env-override = [yellow]{ $key } wird durch eine Umgebungsvariable gesetzt: der gespeicherte Wert wird ignoriert, solange sie gesetzt ist.[/yellow]
cli-config-unset-success = [green]{ $key } entfernt[/green]
cli-config-unset-missing = [yellow]{ $key } war nicht gesetzt[/yellow]
cli-config-invalid-value = [red]Ungültiger Wert für { $key }: { $error }[/red]
cli-config-migrate-moved = [green]Verschoben nach { $backend }: { $keys }[/green]
cli-config-migrate-imported = [green]In config.toml importiert: { $keys }[/green]
cli-config-migrate-conflicts = [yellow]Bereits gesetzt, nicht überschrieben: { $keys }[/yellow]
cli-config-migrate-nothing = Nichts zu migrieren.
cli-config-migrate-source-kept = [dim]{ $path } wurde nicht geändert: nach Prüfung löschen.[/dim]
## Assistant and status
assistant-describe-what-you-need = Beschreibe, was du brauchst. /help für Befehle · /exit zum Beenden
assistant-thinking = Denke nach…
assistant-request-error = Anfrage fehlgeschlagen. Mit --debug erhältst du Details.
assistant-confirm-operation = Diesen Vorgang bestätigen? [y/N]
assistant-help = Slash-Befehle
    /help     Diese Hilfe anzeigen
    /exit     Beenden (auch: exit, quit, q)
    /session  Sitzungs-ID anzeigen
    /clear    Sitzungsnachrichten löschen
assistant-input = Du ›
assistant-operation = Vorgang: { $name }
assistant-tool-running = Läuft · { $name }
assistant-incomplete = Unvollständige Antwort.
assistant-session = Sitzung: { $session }
assistant-not-persisted = nicht gespeichert
assistant-cleared = Sitzungsnachrichten gelöscht.
assistant-no-session = Keine gespeicherte Sitzung zum Löschen.
assistant-unknown-command = Unbekannter Befehl: { $command }. Versuche /help.
assistant-turn-failed = Anfrage nicht abgeschlossen. Mit --debug erhältst du Details.
assistant-interrupted = Anfrage unterbrochen. Bereits gestartete Vorgänge können wirksam geworden sein: prüfe ihren Status, bevor du es erneut versuchst.
assistant-missing-extra = KI-Abhängigkeiten fehlen: installiere OpenFatture mit dem Extra ai neu.
assistant-tool-completed = Abgeschlossen · { $name }
assistant-tool-failed = Nicht abgeschlossen · { $name }
status-blocking-fields = Felder, die die Rechnungsstellung blockieren
status-field = Feld
status-problem = Problem
status-missing = Fehlt
status-invalid = Ungültig
status-local-only = Die Prüfungen beschreiben die lokale Konfiguration. KI-Authentifizierung und SDI-Zustellung werden von diesem Befehl nicht geprüft.
cli-database-unavailable = Datenbank nicht verfügbar. Prüfe DATABASE_URL und Berechtigungen; mit --debug erhältst du Details.
assistant-reconciled = Geprüftes Ergebnis gespeichert. Mit /resume fortfahren.
assistant-reconcile-invalid = Ungültiger Abgleich: call_id, result und evidence sind erforderlich.
assistant-resolve-pending-first = Schließe den offenen Durchlauf mit /resume ab, bevor du den Verlauf löschst.
assistant-resuming = Unterbrochener Durchlauf wird fortgesetzt…
assistant-uncertain-tool = Unsicheres Tool-Ergebnis: /pending und /reconcile vor /resume verwenden.
assistant-no-pending = Kein offener Durchlauf.

## Shared command output
cli-common-error = [red]Fehler:[/red] { $error }
## FATTURA Commands
cli-fattura-xml-generated = [green]✓[/green] XML erfolgreich erstellt
cli-fattura-xml-generated-dry-run = [green]✓[/green] XML erfolgreich erstellt (Probelauf, keine Datei geschrieben)
cli-fattura-xml-content = [bold]XML-Inhalt:[/bold]
cli-fattura-output = Ausgabe: [cyan]{ $path }[/cyan]
cli-fattura-size = Größe: { $size } Byte
cli-fattura-journal-submission = Versand Nr. { $id } · Rechnung { $invoice } · { $filename } · { $outcome }
cli-fattura-journal-receipt = Empfangsbestätigung Nr. { $id } · Rechnung { $invoice } · { $outcome } · Quelle { $source }
cli-fattura-journal-empty = Keine SDI-Übermittlungen oder Empfangsbestätigungen erfasst.
cli-fattura-associate-confirm = Empfangsbestätigung { $receipt } der Rechnung { $invoice } zuordnen?
cli-fattura-receipt-associated = Empfangsbestätigung zugeordnet
cli-fattura-resolve-confirm = Bestätigen, dass Versand { $attempt } { $sent ->
        [yes] übermittelt wurde
       *[no] nicht übermittelt wurde
    }?
cli-fattura-submission-resolved = Prüfung erfasst

## CLIENTE Commands
## PAGAMENTO Commands
## INIT Command
cli-init-title = [bold blue]OpenFatture-Einrichtung[/bold blue]
cli-init-structured-needs-no-interactive = Verwende --no-interactive mit einem strukturierten Ausgabeformat
cli-init-creating-dirs = [cyan]Verzeichnisse werden erstellt...[/cyan]
cli-init-dirs-created = Datenverzeichnisse erstellt
cli-init-initializing-db = [cyan]Datenbank wird initialisiert...[/cyan]
cli-init-backup = Sicherung vor dem Upgrade: { $path }
cli-init-database = Datenbank { $state ->
        [empty] erstellt
        [current] aktuell
        [outdated] aktualisiert
        [unversioned] übernommen und aktualisiert
       *[other] { $state }
    }: { $url }
cli-init-configure-company = [bold yellow]Konfigurieren wir deine Unternehmensdaten[/bold yellow]
cli-init-overwrite-confirm = [yellow]Ein OpenFatture-Profil existiert bereits. Unternehmens- und KI-Einstellungen überschreiben?[/yellow]
cli-init-config-preserved = [green]Bestehende Konfiguration beibehalten.[/green] Verzeichnisse und Datenbank wurden trotzdem sichergestellt.
cli-init-company-section = [bold]Unternehmensdaten (Cedente Prestatore)[/bold]
cli-init-prompt-name = Firma oder dein Name
cli-init-prompt-partita-iva = Partita IVA (11 Ziffern)
cli-init-invalid-partita-iva = [red]Ungültige Partita IVA. Bitte erneut versuchen.[/red]
cli-init-prompt-codice-fiscale = Codice fiscale (16 Zeichen)
cli-init-invalid-codice-fiscale = [red]Ungültiger Codice fiscale. Bitte erneut versuchen.[/red]
cli-init-prompt-regime = Steuerregime (verwende deinen tatsächlichen RF-Code)
cli-init-invalid-regime = [red]Gib ein von FatturaPA unterstütztes Steuerregime ein.[/red]
cli-init-prompt-address = Adresse (Straße)
cli-init-prompt-cap = Postleitzahl (CAP)
cli-init-prompt-city = Ort (Comune)
cli-init-prompt-province = Provinz (2 Buchstaben, z. B. RM)
cli-init-pec-section = [bold]PEC-Konfiguration[/bold]
cli-init-prompt-pec-address = Deine PEC-Adresse
cli-init-prompt-pec-password = PEC-Passwort
cli-init-prompt-pec-smtp = PEC-SMTP-Server
cli-init-notifications-section = [bold]E-Mail-Benachrichtigungen[/bold]
cli-init-prompt-notification-email = E-Mail für Benachrichtigungen (SDI-Meldungen, Zusammenfassungen)
cli-init-prompt-locale = Sprache (it/en/de/es/fr)
cli-init-ai-section = [bold]KI-Konfiguration (optional)[/bold]
cli-init-ai-description = [dim]KI-Funktionen konfigurieren: Rechnungsbeschreibungen, Steuervorschläge und Chat-Assistent.[/dim]
cli-init-ai-confirm = KI-Funktionen jetzt konfigurieren? (Das geht auch später mit openfatture config)
cli-init-ai-provider = KI-Anbieter
cli-init-ai-skip = Vorerst überspringen
cli-init-api-key-from = [cyan]{ $provider } ausgewählt - API-Schlüssel erhältst du hier:[/cyan]
cli-init-ollama-selected = [cyan]Ollama ausgewählt - kostenloses lokales Modell![/cyan]
cli-init-ollama-install = Installieren: [bold]ollama pull { $model }[/bold]
cli-init-ollama-start = Starten: [bold]ollama serve[/bold]
cli-init-prompt-api-key = API-Schlüssel (leer lassen, um ihn später festzulegen)
cli-init-config-saved = Konfiguration gespeichert in: { $path }
cli-init-secrets-saved = Geheimnisse gespeichert { $backend ->
        [keyring] im System-Schlüsselbund
       *[file] in der privaten Zugangsdatendatei
    }
cli-init-complete-title = Einrichtung abgeschlossen
cli-init-complete-body = [bold green]Einrichtung beendet[/bold green]

    Nächste Schritte:
      • Bereitschaft prüfen: [cyan]openfatture status[/cyan]
      • Einstellungen prüfen: [cyan]openfatture config show[/cyan]
      • Assistent (benötigt [cyan]uv sync --extra ai[/cyan]): [cyan]openfatture assistant "Zeige die offenen Rechnungen"[/cyan]
      • Hilfe: [cyan]openfatture --help[/cyan]

## STATUS Command
cli-status-readiness = [bold]Bereitschaft[/bold]  Kern: [cyan]{ $core ->
        [yes] bereit
       *[no] nicht bereit
    }[/cyan]  Assistent: [cyan]{ $assistant ->
        [yes] konfiguriert
       *[no] nicht konfiguriert
    }[/cyan]
cli-status-title = OpenFatture-Status
cli-status-label-ai-api-key-configured = KI-API-Schlüssel konfiguriert
cli-status-label-assistant-backend = Assistent-Backend
cli-status-label-assistant-backend-id = Assistent-Backend-ID
cli-status-label-config-file = Konfigurationsdatei
cli-status-label-secret-backend = Geheimnisspeicher
cli-status-checks-title = Bereitschaftsprüfungen
cli-status-column-check = Prüfung
cli-status-yes = ja
cli-status-no = nein
cli-status-next-steps = [bold]Nächste Schritte[/bold]
cli-status-extras-title = Optionale Extras (Funktionsmodule)
cli-status-column-extra = Extra
cli-status-column-installed = Installiert
cli-status-extensions-title = Erweiterungen
cli-status-column-mechanism = Mechanismus
cli-status-column-detail = Detail
cli-status-hooks = Hooks (unterstützt)
cli-status-hooks-detail = { $path } ({ $count ->
        [one] 1 Skript
       *[other] { $count } Skripte
    })
cli-status-plugins = In-Process-Plugins

## Global
cli-main-version = [bold blue]OpenFatture[/bold blue] Version { $version }
cli-output-unsupported-format = Unterstützte Formate: { $formats }

## Rich formatter
cli-formatter-error = [bold red]Fehler:[/bold red] { $error }
cli-formatter-unknown-error = Unbekannter Fehler
cli-formatter-ai-response = [bold]KI-Antwort[/bold]
cli-formatter-unknown = unbekannt
cli-formatter-provider = Anbieter: { $provider }
cli-formatter-model = Modell: { $model }
cli-formatter-tokens = Tokens: { $tokens }
cli-formatter-cost = Kosten: { $cost }
cli-formatter-latency = Latenz: { $latency } ms

## Localized refusals of application services (error_code)
cli-error-invoice-not-found = Rechnung nicht gefunden.
cli-error-invoice-issued-elsewhere = Die Rechnung wurde anderswo ausgestellt und dient nur als Referenz: Es wird kein XML erzeugt, um eine doppelte SDI-Übermittlung zu vermeiden.
cli-error-xml-invalid = Das XML ist ungültig: { $detail }
cli-error-xml-failed = XML kann nicht erzeugt werden: { $detail }
cli-error-receipt-not-associable = Die Empfangsbestätigung existiert nicht oder ist bereits zugeordnet.
cli-error-evidence-required = Ein geprüfter Nachweis ist erforderlich (--evidence).
cli-error-submission-not-found = Übermittlungsversuch nicht gefunden.
cli-error-submission-already-resolved = Der Übermittlungsversuch ist bereits geklärt.
cli-error-sdi-evidence-contradicts = Erfasste SDI-Nachweise widersprechen dem Ergebnis „nicht gesendet“.
cli-error-submission-concurrent-update = Der Versuch wurde inzwischen geklärt: neu laden und erneut versuchen.

## Command-line help
cli-help-app = Elektronische Rechnungsstellung mit Assistent. Starte openfatture für ein Gespräch.
cli-help-epilog = Beispiele: openfatture · openfatture assistant "Zeige unbezahlte Rechnungen"
cli-help-version = Version anzeigen und beenden.
cli-help-debug = Diagnoseprotokolle und Tracebacks anzeigen.
cli-help-format = Ausgabeformat: rich, json, markdown, stream-json, html
cli-help-panel-assistant = Assistent
cli-help-panel-setup = Einrichtung und Diagnose
cli-help-panel-tools = Werkzeuge
cli-help-assistant = Anfrage senden oder Sitzung fortsetzen
cli-help-init = OpenFatture initialisieren
cli-help-config = Konfiguration verwalten
cli-help-status = Konfiguration und Bereitschaft prüfen
cli-help-fattura = FatturaPA-XML und SDI-Journal
cli-help-pagamento = Wartung des Zahlungseingangsjournals
cli-help-assistant-message = Anfrage an den Assistenten.
cli-help-assistant-stream = Antwort während der Erzeugung anzeigen.
cli-help-assistant-json = Antwort als JSON ausgeben.
cli-help-assistant-session = Gespeicherte Sitzung über ihre ID fortsetzen (aktiviert die Speicherung).
cli-help-init-interactive = Interaktiver Einrichtungsassistent
cli-help-status-json = Status als JSON ausgeben.
cli-help-config-show =
    Wirksame Konfiguration anzeigen.

    Für jeden Wert wird die Quelle angezeigt: Umgebung, Schlüsselbund oder Anmeldedatei, config.toml, Standard.
cli-help-config-reload = Konfiguration aus Umgebung, Geheimnisspeicher und config.toml neu laden.
cli-help-config-set =
    Einen Konfigurationswert setzen.

    Nur KEY wird geschrieben. Geheimnisse (API-Schlüssel, Passwörter) kommen in den Schlüsselbund des Systems oder, ohne Schlüsselbund, in die private Anmeldedatei; andere Werte in config.toml. Verschachtelte Schlüssel verwenden Punkte, z. B. debug_config.enable_debug_logging.
cli-help-config-unset = KEY aus config.toml oder dem Geheimnisspeicher entfernen und den Standard wiederherstellen.
cli-help-config-migrate =
    Klartext-Geheimnisse aus config.toml verschieben und optional eine .env-Datei importieren.

    Geheimnisse kommen in den Schlüsselbund (oder die private Anmeldedatei); andere Werte aus --env-file werden nur dann in config.toml übernommen, wenn sie noch nicht gesetzt sind. Die Quelldatei wird nie verändert.
cli-help-config-env-file = Einstellungen aus einer dotenv-Datei importieren (vorhandene Werte bleiben).
cli-help-xml = FatturaPA-XML einer Rechnung erzeugen (ohne XSD-Validierung, ohne Übermittlung).
cli-help-invoice-id = Rechnungs-ID
cli-help-xml-output = Pfad der XML-Datei
cli-help-xml-dry-run = XML anzeigen, ohne die Datei zu schreiben
cli-help-sdi-journal = Erfasste PEC-Übermittlungen und SDI-Empfangsbestätigungen anzeigen, ohne etwas zu senden.
cli-help-associate-receipt = Eine ungeklärte Empfangsbestätigung nach manueller Prüfung einer Rechnung zuordnen.
cli-help-receipt-id = ID der SDI-Empfangsbestätigung
cli-help-receipt-evidence = Geprüfter Nachweis (z. B. eine Referenz)
cli-help-resolve-submission = Eine unsichere PEC-Übermittlung klären, nachdem das Transportergebnis geprüft wurde.
cli-help-attempt-id = ID des Übermittlungsversuchs
cli-help-resolve-sent = Geprüftes Ergebnis: gesendet oder nicht gesendet
cli-help-resolve-evidence = Geprüfter Nachweis (z. B. die Referenz des Anbieters)
cli-help-collections-migrate = Historische Zahlungseingangsdaten aktualisieren, ohne Beträge zu ändern.
cli-help-install-completion = Vervollständigung für die aktuelle Shell installieren.
cli-help-show-completion = Vervollständigung für die aktuelle Shell anzeigen, zum Kopieren oder Anpassen.
cli-help-help-option = Diese Hilfe anzeigen und beenden.
