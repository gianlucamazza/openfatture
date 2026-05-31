# Web UI translations - German
# Vollständige Übersetzungen für die Streamlit-Weboberfläche von OpenFatture

## ============================================================================
## COMMON - Allgemeine Web-UI-Zeichenketten
## ============================================================================

### Application
web-app-title = OpenFatture - Elektronische Rechnungsstellung
web-app-tagline = Open-Source-System für italienische elektronische Rechnungsstellung
web-app-version = Version { $version }
web-app-license = MIT-Lizenz

### Navigation
web-nav-home = Startseite
web-nav-dashboard = Dashboard
web-nav-invoices = Rechnungen
web-nav-clients = Kunden
web-nav-payments = Zahlungen
web-nav-ai-assistant = KI-Assistent
web-nav-settings = Einstellungen
web-nav-batch = Stapelverarbeitung
web-nav-reports = Berichte
web-nav-events = Ereignisse
web-nav-health = Systemstatus
web-nav-lightning = Lightning
web-nav-hooks = Hooks

### Common Buttons
web-button-save = Speichern
web-button-cancel = Abbrechen
web-button-delete = Löschen
web-button-edit = Bearbeiten
web-button-create = Erstellen
web-button-update = Aktualisieren
web-button-search = Suchen
web-button-filter = Filtern
web-button-export = Exportieren
web-button-import = Importieren
web-button-refresh = Aktualisieren
web-button-close = Schließen
web-button-submit = Absenden
web-button-reset = Zurücksetzen
web-button-back = Zurück
web-button-next = Weiter
web-button-finish = Fertig
web-button-download = Herunterladen
web-button-upload = Hochladen
web-button-view = Anzeigen
web-button-send = Senden

### Common Labels
web-label-name = Name
web-label-description = Beschreibung
web-label-date = Datum
web-label-amount = Betrag
web-label-status = Status
web-label-type = Typ
web-label-total = Gesamt
web-label-subtotal = Zwischensumme
web-label-tax = MwSt
web-label-quantity = Menge
web-label-price = Preis
web-label-client = Kunde
web-label-invoice = Rechnung
web-label-payment = Zahlung
web-label-notes = Notizen
web-label-actions = Aktionen
web-label-created = Erstellt
web-label-updated = Aktualisiert
web-label-email = E-Mail
web-label-phone = Telefon
web-label-address = Adresse
web-label-city = Stadt
web-label-country = Land
web-label-search = Suchen
web-label-filter = Filtern
web-label-all = Alle
web-label-none = Keine
web-label-yes = Ja
web-label-no = Nein

### Common Messages
web-message-success = Vorgang erfolgreich abgeschlossen
web-message-error = Ein Fehler ist aufgetreten
web-message-warning = Warnung
web-message-info = Information
web-message-loading = Wird geladen...
web-message-no-data = Keine Daten verfügbar
web-message-no-results = Keine Ergebnisse gefunden
web-message-confirm-delete = Sind Sie sicher, dass Sie dieses Element löschen möchten?
web-message-unsaved-changes = Es gibt ungespeicherte Änderungen
web-message-saved = Gespeichert
web-message-deleted = Gelöscht
web-message-updated = Aktualisiert
web-message-created = Erstellt

### Validation Messages
web-validation-required = Dieses Feld ist erforderlich
web-validation-invalid = Ungültiger Wert
web-validation-email-invalid = Ungültige E-Mail
web-validation-number-invalid = Ungültige Nummer
web-validation-date-invalid = Ungültiges Datum
web-validation-min-length = Mindestlänge: { $length } Zeichen
web-validation-max-length = Maximale Länge: { $length } Zeichen
web-validation-min-value = Mindestwert: { $value }
web-validation-max-value = Maximalwert: { $value }

### Error Messages
web-error-generic = Ein unerwarteter Fehler ist aufgetreten
web-error-unexpected = Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.
web-error-reload-page = Seite Neu Laden
web-error-goto-health = Zum Gesundheits-Dashboard Gehen
web-error-network = Verbindungsfehler
web-error-timeout = Zeitüberschreitung der Anfrage
web-error-unauthorized = Nicht autorisiert
web-error-forbidden = Zugriff verweigert
web-error-not-found = Ressource nicht gefunden
web-error-server = Serverfehler
web-error-database = Datenbankfehler
web-error-loading = Fehler beim Laden
web-error-saving = Fehler beim Speichern
web-error-deleting = Fehler beim Löschen

### Sidebar
web-sidebar-quick-stats = Schnellstatistiken
web-sidebar-invoices = Rechnungen
web-sidebar-clients = Kunden
web-sidebar-revenue = Umsatz
web-sidebar-pending = Ausstehend
web-sidebar-configuration = Konfiguration
web-sidebar-company = Unternehmen
web-sidebar-vat-number = USt-IdNr.
web-sidebar-tax-regime = Steuersystem
web-sidebar-ai-enabled = KI Aktiviert
web-sidebar-ai-disabled = KI Nicht Konfiguriert
web-sidebar-ai-provider = Anbieter
web-sidebar-advanced-ops = Erweiterte Funktionen
web-sidebar-error-loading-stats = Fehler beim Laden der Statistiken: { $error }

### Language Selector
web-lang-selector-title = Sprache
web-lang-selector-italian = Italiano
web-lang-selector-english = English
web-lang-selector-spanish = Español
web-lang-selector-french = Français
web-lang-selector-german = Deutsch
web-lang-selector-changed = Sprache geändert zu { $language }

### Status Values
web-status-active = Aktiv
web-status-inactive = Inaktiv
web-status-pending = Ausstehend
web-status-completed = Abgeschlossen
web-status-failed = Fehlgeschlagen
web-status-draft = Entwurf
web-status-sent = Gesendet
web-status-paid = Bezahlt
web-status-unpaid = Unbezahlt
web-status-overdue = Überfällig
web-status-cancelled = Storniert

### Time & Date
web-time-today = Heute
web-time-yesterday = Gestern
web-time-this-week = Diese Woche
web-time-this-month = Dieser Monat
web-time-this-year = Dieses Jahr
web-time-last-week = Letzte Woche
web-time-last-month = Letzter Monat
web-time-last-year = Letztes Jahr
web-time-custom = Benutzerdefiniert

### Pagination
web-pagination-showing = Zeige { $start }-{ $end } von { $total }
web-pagination-per-page = Pro Seite
web-pagination-first = Erste
web-pagination-last = Letzte
web-pagination-previous = Vorherige
web-pagination-next = Nächste

### File Upload
web-upload-drag-drop = Dateien hier ablegen
web-upload-or = oder
web-upload-browse = Durchsuchen
web-upload-max-size = Maximale Größe: { $size }
web-upload-accepted-formats = Akzeptierte Formate: { $formats }
web-upload-uploading = Wird hochgeladen...
web-upload-success = Datei erfolgreich hochgeladen
web-upload-error = Fehler beim Hochladen der Datei
