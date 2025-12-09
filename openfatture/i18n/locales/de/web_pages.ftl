# Web Pages translations - German
# Spezifische Übersetzungen für die Seiten der Streamlit-Weboberfläche

## ============================================================================
## HOME PAGE (app.py)
## ============================================================================

page-home-title = 🏠 OpenFatture
page-home-welcome = Willkommen bei OpenFatture
page-home-subtitle = Open-Source-System für Elektronische Rechnungsstellung
page-home-description =
    OpenFatture ist ein vollständiges System für die Verwaltung der italienischen
    elektronischen Rechnungsstellung mit SDI-Integration, KI und Lightning-Zahlungen.

page-home-features-title = ✨ Hauptfunktionen
page-home-feature-invoicing = Vollständige elektronische Rechnungsstellung mit FatturaPA
page-home-feature-sdi = Direkte Integration mit SDI (Austauschsystem)
page-home-feature-ai = KI-Assistent für Beschreibungen und MwSt-Vorschläge
page-home-feature-payments = Automatischer Zahlungsabgleich mit Bankdaten
page-home-feature-lightning = Unterstützung für Lightning Network-Zahlungen
page-home-feature-batch = Stapelverarbeitung für Massen-Import/-Export

## Feature Grid
page-home-feature-grid-invoices-title = 🧾 Rechnungen
page-home-feature-grid-invoices-item-1 = Geführte Erstellung
page-home-feature-grid-invoices-item-2 = Kundenverwaltung
page-home-feature-grid-invoices-item-3 = XML-Generierung
page-home-feature-grid-invoices-item-4 = SDI-Übermittlung via PEC
page-home-feature-grid-invoices-item-5 = Benachrichtigungs-Tracking
page-home-feature-grid-invoices-button = 📝 Zu Rechnungen Gehen

page-home-feature-grid-payments-title = 💰 Zahlungen
page-home-feature-grid-payments-item-1 = Kontoauszüge importieren
page-home-feature-grid-payments-item-2 = Automatischer Abgleich
page-home-feature-grid-payments-item-3 = Abstimmung
page-home-feature-grid-payments-item-4 = Fälligkeitserinnerungen
page-home-feature-grid-payments-item-5 = Prüfpfad
page-home-feature-grid-payments-button = 💳 Zu Zahlungen Gehen

page-home-feature-grid-ai-title = 🤖 KI-Assistent
page-home-feature-grid-ai-item-1 = Interaktiver Chat
page-home-feature-grid-ai-item-2 = Automatische Beschreibungen
page-home-feature-grid-ai-item-3 = Steuerberatung
page-home-feature-grid-ai-item-4 = Cashflow-Prognose
page-home-feature-grid-ai-item-5 = Compliance-Prüfung
page-home-feature-grid-ai-button = 🚀 KI Ausprobieren

## Quick Actions
page-home-quick-actions = ⚡ Schnellaktionen
page-home-action-new-invoice = ➕ Neue Rechnung
page-home-action-new-client = 👤 Neuer Kunde
page-home-action-dashboard = 📊 Dashboard
page-home-action-batch = 📦 Stapelverarbeitung

## Advanced Tools
page-home-advanced-tools = 🔧 Erweiterte Tools
page-home-advanced-reports = 📊 Berichte
page-home-advanced-hooks = 🪝 Hooks
page-home-advanced-events = 📋 Ereignisse

## Getting Started
page-home-getting-started = 🚀 Erste Schritte
page-home-getting-started-title = Erste Schritte

page-home-step-1-title = 1. Umgebung konfigurieren
page-home-step-1-item-1 = Stellen Sie sicher, dass `.env` korrekt konfiguriert ist
page-home-step-1-item-2 = Überprüfen Sie die Unternehmensdaten (USt-IdNr., Steuersystem)
page-home-step-1-item-3 = Konfigurieren Sie PEC-Anmeldeinformationen für SDI-Übermittlung

page-home-step-2-title = 2. Erstellen Sie Ihre ersten Kunden
page-home-step-2-item-1 = Gehen Sie zu "👥 Kunden" → "Kunde Hinzufügen"
page-home-step-2-item-2 = Geben Sie steuerliche Details ein (USt-IdNr., Steuer-ID)
page-home-step-2-item-3 = Geben Sie SDI oder PEC für Rechnungsempfang an

page-home-step-3-title = 3. Erstellen Sie Ihre erste Rechnung
page-home-step-3-item-1 = "🧾 Rechnungen" → "Neue Rechnung"
page-home-step-3-item-2 = Wählen Sie Kunde aus und fügen Sie Positionen hinzu
page-home-step-3-item-3 = Generieren Sie XML und übermitteln Sie an SDI

page-home-step-4-title = 4. Erkunden Sie den KI-Assistenten
page-home-step-4-item-1 = Probieren Sie den Chat für Steuerfragen aus
page-home-step-4-item-2 = Generieren Sie intelligente Beschreibungen
page-home-step-4-item-3 = Erhalten Sie automatische MwSt-Vorschläge

page-home-docs-title = Dokumentation

## Footer
page-home-footer-version = OpenFatture v{ $version }
page-home-footer-license = MIT-Lizenz
page-home-footer-tagline = Mit ❤️ von Freelancern, für Freelancer

page-home-help = 📚 Hilfe und Dokumentation
page-home-github = GitHub-Repository
page-home-report-bug = Fehler Melden
page-home-about = Über

## ============================================================================
## DASHBOARD PAGE (1_📊_Dashboard.py)
## ============================================================================

page-dashboard-title = 📊 Dashboard
page-dashboard-subtitle = Echtzeit-Geschäftsübersicht

### KPI Cards
page-dashboard-kpi-section = 📈 Hauptkennzahlen
page-dashboard-kpi-total-invoices = 📄 Rechnungen Gesamt
page-dashboard-kpi-total-revenue = 💰 Gesamtumsatz
page-dashboard-kpi-total-clients = 👥 Aktive Kunden
page-dashboard-kpi-revenue-month = 📅 Monatsumsatz
page-dashboard-kpi-pending-payments = Ausstehende Zahlungen
page-dashboard-kpi-avg-invoice = Durchschnittlicher Rechnungsbetrag
page-dashboard-kpi-this-month = Dieser Monat
page-dashboard-kpi-this-year = Dieses Jahr
page-dashboard-kpi-growth = Wachstum

### Charts
page-dashboard-chart-invoices-by-status = 📊 Rechnungen nach Status
page-dashboard-chart-revenue-6-months = 📈 Umsatz letzte 6 Monate
page-dashboard-chart-yaxis-revenue = Umsatz (€)
page-dashboard-chart-xaxis-month = Monat
page-dashboard-chart-revenue-title = Umsatzentwicklung
page-dashboard-chart-invoices-title = Rechnungen nach Monat
page-dashboard-chart-clients-title = Top-Kunden
page-dashboard-chart-status-title = Rechnungen nach Status
page-dashboard-chart-payments-title = Zahlungsstatus

### Tables
page-dashboard-top-clients = 👑 Top 5 Kunden
page-dashboard-recent-invoices = 🕐 Letzte 5 Rechnungen
page-dashboard-col-client = Kunde
page-dashboard-col-num-invoices = Anz. Rechnungen
page-dashboard-col-num-invoices-short = Rechnungen
page-dashboard-col-revenue = Umsatz
page-dashboard-col-number = Nummer
page-dashboard-col-date = Datum
page-dashboard-col-total = Gesamt
page-dashboard-col-status = Status
page-dashboard-col-invoice = Rechnung
page-dashboard-col-due-date = Fälligkeit
page-dashboard-col-days = Tage
page-dashboard-col-days-delta = Δ Tage
page-dashboard-col-days-help = Tage bis Fälligkeit
page-dashboard-col-residual = Ausstehend
page-dashboard-col-residual-amount = Ausstehender Betrag
page-dashboard-col-category = Kategorie

### Payment Tracking
page-dashboard-payment-tracking = 💳 Zahlungsverfolgung
page-dashboard-payment-unmatched = 🔍 Nicht Zugeordnet
page-dashboard-payment-matched = ✅ Zugeordnet
page-dashboard-payment-ignored = ⏭️ Ignoriert
page-dashboard-payment-total = 📊 Transaktionen Gesamt
page-dashboard-payment-due-30 = 💰 Zahlungsfälligkeiten (Nächste 30 Tage)
page-dashboard-total-outstanding = 💸 Offene Forderungen Gesamt
page-dashboard-category-overdue = 🔴 Überfällig
page-dashboard-category-due-soon = 🟡 Bald fällig
page-dashboard-category-upcoming = 🟢 Kommend

### Messages
page-dashboard-no-invoices = Keine Rechnungen vorhanden
page-dashboard-no-data = Keine Daten verfügbar
page-dashboard-no-clients = Keine Kunden vorhanden
page-dashboard-no-payments-due = ✅ Keine fälligen Zahlungen
page-dashboard-error-loading = ❌ Fehler beim Laden des Dashboards: { $error }
page-dashboard-refresh-button = 🔄 Daten Aktualisieren

### Recent Activity
page-dashboard-recent-activity = Letzte Aktivitäten

## ============================================================================
## INVOICES PAGE (2_🧾_Fatture.py)
## ============================================================================

page-invoices-title = 🧾 Rechnungsverwaltung
page-invoices-subtitle = Alle Ihre Rechnungen anzeigen und verwalten

### Sidebar Filters
page-invoices-filter-title = 🔍 Filter
page-invoices-filter-year = Jahr
page-invoices-filter-all = Alle
page-invoices-filter-status = Status
page-invoices-filter-max-results = Maximale Ergebnisse
page-invoices-no-invoices-in-db = Keine Rechnungen verfügbar
page-invoices-filter-client = Kunde
page-invoices-filter-date-from = Von Datum
page-invoices-filter-date-to = Bis Datum
page-invoices-filter-amount-min = Mindestbetrag
page-invoices-filter-amount-max = Höchstbetrag
page-invoices-filter-search = Rechnungen suchen...

### Quick Actions
page-invoices-action-quick-title = ⚡ Schnellaktionen
page-invoices-action-new-invoice = ➕ Neue Rechnung
page-invoices-action-new-invoice-info =
    **Funktion in Entwicklung**

    Erstellen Sie vorerst Rechnungen über CLI:
    ```bash
    uv run openfatture fattura crea
    ```

    Die geführte Erstellung über die Weboberfläche wird bald verfügbar sein!
page-invoices-action-refresh = 🔄 Liste Aktualisieren

### Main Content
page-invoices-list-title = ### 📋 Rechnungsliste
page-invoices-no-invoices-found = 📭 Keine Rechnungen mit den ausgewählten Filtern gefunden

### Stats Metrics
page-invoices-stats-count = 📊 Gefundene Rechnungen
page-invoices-stats-total = 💰 Gesamt
page-invoices-stats-statuses = 📋 Verschiedene Status
page-invoices-stats-average = 📈 Durchschnittsbetrag

### Table
page-invoices-table-title = #### 📋 Rechnungstabelle
page-invoices-col-id = ID
page-invoices-col-number = Nummer
page-invoices-col-date = Datum
page-invoices-col-client = Kunde
page-invoices-col-total-eur = Gesamt €
page-invoices-col-status = Status
page-invoices-col-lines = Zeilen
page-invoices-col-amount = Betrag
page-invoices-col-payment = Zahlung
page-invoices-col-actions = Aktionen

### Invoice Detail Section
page-invoices-detail-title = ### 🔍 Rechnungsdetails
page-invoices-detail-input-id = Rechnungs-ID zur Anzeige eingeben
page-invoices-detail-show-button = 📄 Details Anzeigen
page-invoices-detail-error-not-found = ❌ Rechnung mit ID { $id } nicht gefunden
page-invoices-detail-success = ✅ Rechnung { $number }/{ $year }

### Detail Header Metrics
page-invoices-detail-number = Nummer
page-invoices-detail-date = Ausstellungsdatum
page-invoices-detail-client = Kunde
page-invoices-detail-type = Typ
page-invoices-detail-status = Status
page-invoices-detail-sdi-number = SDI-Nummer

### Detail Line Items
page-invoices-detail-lines-title = #### 📦 Rechnungszeilen
page-invoices-detail-lines-col-num = #
page-invoices-detail-lines-col-desc = Beschreibung
page-invoices-detail-lines-col-qty = Menge
page-invoices-detail-lines-col-price = Preis €
page-invoices-detail-lines-col-vat = MwSt. %
page-invoices-detail-lines-col-total = Gesamt €
page-invoices-detail-lines-empty = Keine Zeilen verfügbar

### Detail Totals
page-invoices-detail-totals-title = #### 💰 Summen
page-invoices-detail-totals-taxable = Steuerpflichtig
page-invoices-detail-totals-vat = MwSt.
page-invoices-detail-totals-withholding = Quellensteuer
page-invoices-detail-totals-stamp = Stempel
page-invoices-detail-totals-total = **GESAMT**

### Detail Files
page-invoices-detail-files-title = #### 📁 Dateien
page-invoices-detail-files-xml-exists = ✅ XML: `{ $path }`
page-invoices-detail-files-xml-missing = 📄 XML noch nicht erstellt
page-invoices-detail-files-pdf-exists = ✅ PDF: `{ $path }`
page-invoices-detail-files-pdf-missing = 📄 PDF noch nicht erstellt

### Detail Actions
page-invoices-detail-actions-title = #### ⚡ Aktionen
page-invoices-detail-actions-generate-xml = 📝 XML Erstellen
page-invoices-detail-actions-generating-xml = XML wird erstellt...
page-invoices-detail-actions-error = ❌ Fehler: { $error }
page-invoices-detail-actions-xml-success = ✅ XML erfolgreich erstellt!
page-invoices-detail-actions-send-sdi = 📤 An SDI Senden
page-invoices-detail-actions-generate-pdf = 📄 PDF Erstellen
page-invoices-detail-actions-cli-feature = CLI-Funktion

### Error Messages
page-invoices-error-loading = ❌ Fehler beim Laden der Rechnungen: { $error }

### Legacy (kept for compatibility)
page-invoices-action-view = Anzeigen
page-invoices-action-edit = Bearbeiten
page-invoices-action-delete = Löschen
page-invoices-action-send = An SDI Senden
page-invoices-action-download-xml = XML Herunterladen
page-invoices-action-download-pdf = PDF Herunterladen
page-invoices-action-duplicate = Duplizieren
page-invoices-no-invoices = Keine Rechnungen gefunden
page-invoices-create-first = Erstellen Sie Ihre erste Rechnung
page-invoices-total-found = { $count } Rechnungen gefunden
page-invoices-selected = { $count } ausgewählt

## ============================================================================
## INVOICE CREATION PAGE (13_✏️_Crea_Fattura.py)
## ============================================================================

### Page Configuration
page-invoice-create-page-title = Rechnung Erstellen - OpenFatture
page-invoice-create-title = ✏️ Geführte Rechnungserstellung

### Wizard Progress
page-invoice-create-wizard-title = 📋 Rechnungserstellung - Schritt { $step }/{ $total }

### Step Labels
page-invoice-create-step-1-label = 👥 Kunde Auswählen
page-invoice-create-step-2-label = 📝 Rechnungsdetails
page-invoice-create-step-3-label = 🛒 Produkte Hinzufügen
page-invoice-create-step-4-label = 🤖 KI-Assistenz
page-invoice-create-step-5-label = ✅ Zusammenfassung & Erstellen

### Step 1: Select Client
page-invoice-create-step-1-header = 👥 Kunde Auswählen
page-invoice-create-client-search-label = Bestehenden Kunden suchen
page-invoice-create-client-search-placeholder = Firmenname, USt-IdNr...
page-invoice-create-client-search-help = Leer lassen, um alle Kunden zu sehen
page-invoice-create-client-existing-title = Bestehende Kunden
page-invoice-create-client-vat-label = USt-IdNr
page-invoice-create-client-select-label = Kunde auswählen
page-invoice-create-client-select-help = Wählen Sie einen bestehenden Kunden oder erstellen Sie einen neuen
page-invoice-create-client-create-title = ➕ Oder neuen Kunden erstellen
page-invoice-create-client-create-expander = Neuen Kunden erstellen
page-invoice-create-client-name-label = Firmenname *
page-invoice-create-client-name-placeholder = Firmen- oder Personenname
page-invoice-create-client-vat-input-label = USt-IdNr
page-invoice-create-client-vat-placeholder = 12345678901
page-invoice-create-client-fiscal-code-label = Steuernummer
page-invoice-create-client-fiscal-code-placeholder = Steuernummer (falls Privatperson)
page-invoice-create-client-address-label = Adresse
page-invoice-create-client-address-placeholder = Römerstraße 123, 00100 Rom
page-invoice-create-client-email-label = E-Mail
page-invoice-create-client-email-placeholder = kunde@email.com
page-invoice-create-client-phone-label = Telefon
page-invoice-create-client-phone-placeholder = +49 123 456 7890
page-invoice-create-client-regime-label = Steuerregime
page-invoice-create-client-regime-ordinary = RF01 - Regelbesteuerung
page-invoice-create-client-regime-flat = RF19 - Pauschalsteuer
page-invoice-create-client-create-button = Kunde Erstellen
page-invoice-create-client-name-required = Firmenname ist erforderlich
page-invoice-create-client-create-success = Kunde '{ $name }' erfolgreich erstellt!
page-invoice-create-client-create-error = Fehler beim Erstellen des Kunden: { $error }

### Step 2: Invoice Details
page-invoice-create-step-2-header = 📝 Rechnungsdetails
page-invoice-create-details-client-selected = Ausgewählter Kunde: **{ $name }**
page-invoice-create-details-regime = Steuerregime: { $regime }
page-invoice-create-details-number-label = Rechnungsnummer
page-invoice-create-details-number-help = Fortlaufende Rechnungsnummer
page-invoice-create-details-year-label = Jahr
page-invoice-create-details-year-help = Steuerjahr
page-invoice-create-details-date-label = Ausstellungsdatum
page-invoice-create-details-date-help = Rechnungsausstellungsdatum
page-invoice-create-details-due-date-label = Fälligkeitsdatum
page-invoice-create-details-due-date-help = Zahlungsfälligkeitsdatum
page-invoice-create-details-additional-title = 📋 Zusätzliche Details
page-invoice-create-details-subject-label = Betreff/Beschreibung
page-invoice-create-details-subject-placeholder = Allgemeine Rechnungsbeschreibung...
page-invoice-create-details-subject-help = Allgemeine Beschreibung der Dienstleistungen/Produkte
page-invoice-create-details-notes-label = Notizen
page-invoice-create-details-notes-placeholder = Zusätzliche Notizen...
page-invoice-create-details-notes-help = Interne oder Rechnungsnotizen

### Step 3: Invoice Lines
page-invoice-create-step-3-header = 🛒 Produkte und Dienstleistungen
page-invoice-create-lines-title = Rechnungspositionen
page-invoice-create-lines-description-label = Beschreibung
page-invoice-create-lines-quantity-label = Menge
page-invoice-create-lines-price-label = Einzelpreis (€)
page-invoice-create-lines-row-total = Positionssumme: { $total }
page-invoice-create-lines-remove-button = 🗑️ Entfernen
page-invoice-create-lines-add-title = ➕ Neue Position hinzufügen
page-invoice-create-lines-description-input-label = Beschreibung *
page-invoice-create-lines-description-placeholder = Produkt-/Dienstleistungsbeschreibung...
page-invoice-create-lines-quantity-input-label = Menge
page-invoice-create-lines-quantity-help = Produkt-/Dienstleistungsmenge
page-invoice-create-lines-price-input-label = Einzelpreis (€)
page-invoice-create-lines-price-help = Einzelpreis ohne MwSt
page-invoice-create-lines-vat-label = MwSt-Satz
page-invoice-create-lines-vat-help = Anwendbarer MwSt-Satz
page-invoice-create-lines-add-button = Position Hinzufügen
page-invoice-create-lines-description-required = Beschreibung ist erforderlich
page-invoice-create-lines-add-success = Position hinzugefügt!
page-invoice-create-lines-totals-title = 💰 Summen
page-invoice-create-lines-subtotal-label = Nettobetrag
page-invoice-create-lines-vat-amount-label = MwSt
page-invoice-create-lines-total-label = Gesamt

### Step 4: AI Assistance
page-invoice-create-step-4-header = 🤖 KI-Assistenz
page-invoice-create-ai-description-title = 📝 Beschreibungen mit KI Generieren
page-invoice-create-ai-description-button = 🎯 Beschreibungen für Positionen vorschlagen
page-invoice-create-ai-description-no-lines = Fügen Sie zuerst Positionen zur Rechnung hinzu
page-invoice-create-ai-description-generating = Beschreibungen werden generiert...
page-invoice-create-ai-description-improved = Beschreibung für Position { $row } verbessert!
page-invoice-create-ai-description-error = Fehler beim Generieren der Beschreibung für Position { $row }: { $error }
page-invoice-create-ai-vat-title = 💼 MwSt-Beratung
page-invoice-create-ai-vat-button = 🧾 MwSt-Sätze prüfen
page-invoice-create-ai-vat-no-lines = Fügen Sie zuerst Positionen zur Rechnung hinzu
page-invoice-create-ai-vat-checking = MwSt-Sätze werden geprüft...
page-invoice-create-ai-vat-suggestion = 💡 Position { $row }: Vorgeschlagener MwSt-Satz { $suggested }% statt { $current }%
page-invoice-create-ai-vat-apply = { $rate }% auf Position { $row } anwenden
page-invoice-create-ai-vat-updated = MwSt-Satz aktualisiert!
page-invoice-create-ai-vat-info = Position { $row }: { $info }
page-invoice-create-ai-vat-error = Fehler beim Prüfen der MwSt für Position { $row }: { $error }
page-invoice-create-ai-compliance-title = ⚖️ Konformitätsprüfung
page-invoice-create-ai-compliance-button = 🔍 Rechnungskonformität prüfen
page-invoice-create-ai-compliance-no-number = Rechnungsnummer fehlt
page-invoice-create-ai-compliance-no-lines = Keine Rechnungspositionen vorhanden
page-invoice-create-ai-compliance-line-no-desc = Position { $row }: Beschreibung fehlt
page-invoice-create-ai-compliance-line-qty-invalid = Position { $row }: Menge muss > 0 sein
page-invoice-create-ai-compliance-line-price-invalid = Position { $row }: Einzelpreis muss > 0 sein
page-invoice-create-ai-compliance-issues-found = Probleme gefunden
page-invoice-create-ai-compliance-success = ✅ Rechnung erfüllt die grundlegenden Anforderungen!

### Step 5: Summary
page-invoice-create-step-5-header = ✅ Zusammenfassung und Erstellung
page-invoice-create-summary-client-title = 👥 Kunde
page-invoice-create-summary-client-vat = USt-IdNr: { $vat }
page-invoice-create-summary-client-regime = Regime: { $regime }
page-invoice-create-summary-invoice-title = 📄 Rechnung
page-invoice-create-summary-invoice-date = Ausstellung: { $date }
page-invoice-create-summary-invoice-due = Fälligkeit: { $date }
page-invoice-create-summary-lines-title = 🛒 Rechnungspositionen
page-invoice-create-summary-table-description = Beschreibung
page-invoice-create-summary-table-quantity = Menge
page-invoice-create-summary-table-price = Preis
page-invoice-create-summary-table-vat = MwSt
page-invoice-create-summary-table-total = Gesamt
page-invoice-create-summary-totals-title = 💰 Summen
page-invoice-create-summary-totals-subtotal = Nettobetrag
page-invoice-create-summary-totals-vat = MwSt
page-invoice-create-summary-totals-total = Rechnungssumme
page-invoice-create-summary-create-button = 🚀 Rechnung Erstellen
page-invoice-create-summary-creating = Rechnung wird erstellt...
page-invoice-create-summary-error-create-failed = Rechnung kann nicht erstellt werden
page-invoice-create-summary-success = ✅ Rechnung { $number }/{ $year } erfolgreich erstellt!
page-invoice-create-summary-next-steps =
    **Nächste Schritte:**
    1. **Validieren** Sie die Rechnung: `openfatture fattura valida { $number }`
    2. **Senden** Sie an SDI: `openfatture pec invia { $number }`
    3. **Überwachen** Sie den Status auf der Rechnungsseite
page-invoice-create-summary-error = Fehler beim Erstellen der Rechnung: { $error }

### Navigation
page-invoice-create-nav-back = ⬅️ Zurück
page-invoice-create-nav-next = Weiter ➡️
page-invoice-create-nav-success = 🎉 Rechnung erfolgreich erstellt!
page-invoice-create-nav-create-another = 🔄 Weitere Rechnung erstellen

## ============================================================================
## CLIENTS PAGE (3_👥_Clienti.py)
## ============================================================================

page-clients-title = 👥 Kundenverwaltung
page-clients-subtitle = Ihre Kunden anzeigen und verwalten

### Filters
page-clients-search = Kunden suchen...
page-clients-filter-type = Typ
page-clients-filter-country = Land

### Table Headers
page-clients-col-name = Name/Firmenname
page-clients-col-vat = USt-IdNr.
page-clients-col-email = E-Mail
page-clients-col-phone = Telefon
page-clients-col-invoices = Rechnungen
page-clients-col-revenue = Umsatz
page-clients-col-actions = Aktionen

### Actions
page-clients-action-add = Kunde Hinzufügen
page-clients-action-view = Anzeigen
page-clients-action-edit = Bearbeiten
page-clients-action-delete = Löschen
page-clients-action-create-invoice = Rechnung Erstellen

### Messages
page-clients-no-clients = Keine Kunden gefunden
page-clients-add-first = Fügen Sie Ihren ersten Kunden hinzu
page-clients-total-found = { $count } Kunden gefunden

## ============================================================================
## ============================================================================
## PAYMENTS PAGE (4_💰_Pagamenti.py)
## ============================================================================

### Page Config
page-payments-page-title = Zahlungen - OpenFatture
page-payments-title = 💰 Zahlungsverfolgung & Abgleich

### Sidebar Filters
page-payments-filter-title = 🔍 Filter
page-payments-filter-bank-account = Bankkonto
page-payments-filter-all-accounts = Alle
page-payments-filter-status = Status
page-payments-no-accounts-configured = Keine Bankkonten konfiguriert

### Status Labels
page-payments-status-all = Alle
page-payments-status-unmatched = Abzugleichen
page-payments-status-matched = Abgeglichen
page-payments-status-ignored = Ignoriert
page-payments-status-paired = Zugeordnet

### Sidebar Actions
page-payments-action-import = 📥 Importieren
page-payments-action-import-help = Kontoauszug importieren
page-payments-action-refresh = 🔄 Aktualisieren

### Import Form
page-payments-import-title = 📥 Kontoauszug Importieren
page-payments-import-select-account = Bankkonto auswählen *
page-payments-import-select-account-help = Wählen Sie das Konto zum Importieren der Transaktionen
page-payments-import-no-account-error = Kein Bankkonto konfiguriert. Erstellen Sie eines vor dem Import.
page-payments-import-file-label = Kontoauszugsdatei auswählen
page-payments-import-file-help = Unterstützt Formate: OFX, QFX, CSV, QIF
page-payments-import-bank-preset = Bank (für CSV)
page-payments-import-bank-preset-help = Wählen Sie die Bank für korrekte CSV-Analyse
page-payments-import-auto-match = Auto-Zuordnung von Zahlungen
page-payments-import-auto-match-help = Versuchen Sie automatisch, Transaktionen mit Rechnungen abzugleichen
page-payments-import-confidence = Vertrauensschwelle
page-payments-import-confidence-help = Minimales Vertrauen für Auto-Zuordnung
page-payments-import-button = 🚀 Transaktionen Importieren
page-payments-import-error-no-account = Wählen Sie ein Bankkonto
page-payments-import-error-no-file = Wählen Sie eine zu importierende Datei
page-payments-import-importing = Transaktionen werden importiert...
page-payments-import-metric-imported = Importierte Transaktionen
page-payments-import-metric-errors = Fehler
page-payments-import-metric-duplicates = Duplikate
page-payments-import-format-detected = 📄 Format erkannt: { $format }
page-payments-import-errors-title = ⚠️ Importfehler
page-payments-import-success-refresh = 🔄 Daten aktualisiert!
page-payments-import-close = ❌ Schließen

### Bank Accounts Overview
page-payments-accounts-title = 🏦 Bankkonten
page-payments-accounts-current-balance = Aktueller Saldo
page-payments-accounts-iban = IBAN: ...{ $last4 }
page-payments-accounts-bank = Bank: { $name }

### Payment Statistics
page-payments-stats-title = 📊 Zahlungsstatistiken
page-payments-stats-accounts = Bankkonten
page-payments-stats-transactions = Gesamttransaktionen
page-payments-stats-balance = Gesamtsaldo
page-payments-stats-reconciled = Abgeglichen
page-payments-stats-distribution-title = 📈 Verteilung nach Status
page-payments-stats-distribution-status = Status
page-payments-stats-distribution-transactions = Transaktionen

### Transactions List
page-payments-transactions-title = 📋 Transaktionen
page-payments-table-col-id = ID
page-payments-table-col-date = Datum
page-payments-table-col-amount = Betrag
page-payments-table-col-description = Beschreibung
page-payments-table-col-reference = Referenz
page-payments-table-col-status = Status
page-payments-table-col-invoice = Rechnung
page-payments-table-col-actions = Aktionen
page-payments-action-view-details = Details anzeigen
page-payments-action-match = Abgleichen
page-payments-transactions-summary = 📊 **Angezeigt insgesamt:** { $total } von { $count } Transaktionen
page-payments-no-transactions-filtered = 🔍 Keine Transaktionen mit ausgewählten Filtern gefunden
page-payments-no-transactions = 📭 Keine Transaktionen vorhanden

### Quick Start Guide
page-payments-quickstart-title = 🚀 Erste Schritte mit Zahlungen
page-payments-quickstart-content =
    ### Erste Schritte

    1. **Bankkonto hinzufügen**
       ```bash
       uv run openfatture payment account add "Geschäftskonto" --iban IT123...
       ```

    2. **Kontoauszug importieren**
       ```bash
       uv run openfatture payment import auszug.ofx --account 1
       ```

    3. **Automatisch abgleichen**
       ```bash
       uv run openfatture payment match --auto-apply
       ```

    4. **Abgleiche überprüfen**
       ```bash
       uv run openfatture payment status
       ```

### Error Messages
page-payments-error-loading = ❌ Fehler beim Laden der Zahlungen: { $error }
page-payments-error-loading-hint = 💡 Überprüfen Sie, ob die Datenbank korrekt initialisiert ist

### Transaction Detail Modal
page-payments-detail-title = 👁️ Transaktionsdetails { $id }...
page-payments-detail-id = ID
page-payments-detail-date = Datum
page-payments-detail-amount = Betrag
page-payments-detail-description = Beschreibung
page-payments-detail-reference = Referenz
page-payments-detail-counterparty = Gegenpartei
page-payments-detail-status = Status
page-payments-detail-confidence = Zuordnungsvertrauen
page-payments-detail-linked-invoice = Verknüpfte Rechnung
page-payments-detail-close = ❌ Schließen
page-payments-detail-not-found = Transaktion nicht gefunden

### Match Transaction Modal
page-payments-match-title = 🔗 Transaktion Abgleichen { $amount }
page-payments-match-date = Datum
page-payments-match-amount = Betrag
page-payments-match-description = Beschreibung
page-payments-match-reference = Referenz
page-payments-match-counterparty = Gegenpartei
page-payments-match-status = Status
page-payments-match-suggestions-title = 🎯 Vorgeschlagene Zuordnungen
page-payments-match-client = Kunde: { $client }
page-payments-match-confidence = Vertrauen
page-payments-match-days-diff = ±{ $days } Tage
page-payments-match-button = ✅ Zuordnen
page-payments-match-matching = Transaktion wird zugeordnet...
page-payments-match-success = ✅ Transaktion mit Rechnung { $number } zugeordnet
page-payments-match-error = ❌ Fehler: { $error }
page-payments-match-no-suggestions = 🔍 Keine automatischen Zuordnungen gefunden
page-payments-match-manual-title = 🔍 Manuelle Suche
page-payments-match-manual-search = Rechnung suchen
page-payments-match-manual-placeholder = Rechnungsnummer, Kunde...
page-payments-match-manual-help = Rechnungsnummer oder Kundenname eingeben
page-payments-match-manual-results = Suchergebnisse:
page-payments-match-manual-button = Zuordnen
page-payments-match-manual-success = ✅ Zugeordnet!
page-payments-match-manual-no-results = Keine Rechnungen gefunden
page-payments-match-close = ❌ Schließen

### Quick Stats Section
page-payments-quick-stats-title = ### 📊 Zahlungsstatistiken
page-payments-quick-stats-unmatched = 🔍 Nicht Zugeordnet
page-payments-quick-stats-matched = ✅ Zugeordnet
page-payments-quick-stats-ignored = ⏭️ Ignoriert
page-payments-quick-stats-total = 📊 Gesamt
page-payments-quick-stats-error = Fehler beim Laden der Daten: { $error }

### Payment Due Section
page-payments-due-title = ### 💳 Fälligkeiten Nächste 30 Tage
page-payments-due-col-invoice = Rechnung
page-payments-due-col-client = Kunde
page-payments-due-col-due-date = Fälligkeit
page-payments-due-col-residual = Ausstehend
page-payments-due-col-status = Status
page-payments-due-total-residual = 💸 Gesamt Ausstehend
page-payments-due-no-payments = ✅ Keine ausstehenden Zahlungen

### Legacy (kept for compatibility)
page-payments-tab-overview = Übersicht
page-payments-tab-reconciliation = Abgleich
page-payments-tab-history = Verlauf
page-payments-total-received = Erhalten
page-payments-total-pending = Ausstehend
page-payments-total-overdue = Überfällig
page-payments-reconciliation-rate = Abgleichsrate
page-payments-import-bank = Kontoauszug Importieren
page-payments-match-automatic = Automatischer Abgleich
page-payments-match-manual = Manueller Abgleich
page-payments-unmatched = Nicht Abgeglichene Transaktionen
page-payments-matched = Abgeglichene Transaktionen
page-payments-col-invoice = Rechnung
page-payments-col-client = Kunde
page-payments-col-amount = Betrag
page-payments-col-due-date = Fälligkeit
page-payments-col-paid-date = Zahlungsdatum
page-payments-col-status = Status
page-payments-col-method = Methode

## ============================================================================
## AI ASSISTANT PAGE (5_🤖_AI_Assistant.py)
## ============================================================================

### Page Config
page-ai-page-title = KI-Assistent - OpenFatture
page-ai-title = 🤖 KI-Assistent
page-ai-subtitle = Intelligenter Assistent für Rechnungsstellung und Steuern
page-ai-not-configured =
    ⚠️ **KI nicht konfiguriert**

    Um den KI-Assistenten zu aktivieren:
    1. Konfigurieren Sie die Anmeldedaten in der `.env`-Datei
    2. Setzen Sie `AI_PROVIDER` (openai/anthropic/ollama)
    3. Setzen Sie `AI_API_KEY` (falls erforderlich)
    4. Starten Sie die Anwendung neu

    Siehe `docs/CONFIGURATION.md` für Details.

### Tabs
page-ai-tab-chat = Chat-Assistent
page-ai-tab-description = Beschreibung Generieren
page-ai-tab-vat = MwSt-Vorschlag
page-ai-tab-voice = Sprach-Chat

### General
page-ai-yes = ✓ JA
page-ai-no = ✗ NEIN

### Retry Logic
page-ai-retry-message = 🔄 Versuch { $attempt }/{ $max_retries } fehlgeschlagen. Wiederholung in { $delay }s...

### Error Messages
page-ai-error-connection = 🌐 Verbindungsfehler. Überprüfen Sie Ihre Internetverbindung und versuchen Sie es erneut.
page-ai-error-auth = 🔐 Authentifizierungsfehler. Überprüfen Sie Ihre KI-Anmeldedaten.
page-ai-error-rate-limit = ⏱️ Ratenlimit erreicht. Versuchen Sie es in ein paar Minuten erneut.
page-ai-error-service-unavailable = 🚫 Dienst vorübergehend nicht verfügbar. Versuchen Sie es später erneut.
page-ai-error-generic = ❌ Unerwarteter Fehler: { $error }...
page-ai-error-hint-connection = 💡 Hinweis: Überprüfen Sie Ihre Internetverbindung
page-ai-error-hint-auth = 💡 Hinweis: Überprüfen Sie die KI-Einstellungen in den Präferenzen

### Slash Commands
page-ai-command-help-feedback =
    **🤖 Verfügbare Befehle:**

    **Integriert:**
    - `/help` - Diese Nachricht anzeigen
    - `/tools` - Verfügbare KI-Tools auflisten
    - `/stats` - Aktuelle Gesprächsstatistiken
    - `/custom` - Benutzerdefinierte Befehle auflisten
    - `/reload` - Befehle von der Festplatte neu laden
    - `/clear` - Chat-Verlauf löschen

    **Benutzerdefiniert:**
    Erstellen Sie Befehle in `~/.openfatture/commands/*.yaml`

    **Beispiele:**
    - "Wie erstelle ich eine Rechnung?"
    - "Was ist der MwSt-Satz für Webdesign?"
    - "Zeige mir die Rechnungen dieses Monats"

page-ai-command-tools-feedback =
    **🔧 Verfügbare KI-Tools:**

    **Suche und Beratung:**
    - Rechnungen nach Kunde, Datum, Betrag suchen
    - Umsatz- und Zahlungsstatistiken
    - Steuerrechtliche Beratung

    **Verfügbare Aktionen:**
    - Professionelle Rechnungsbeschreibungen erstellen
    - Korrekte MwSt-Sätze vorschlagen
    - Rechnungs-Compliance-Analyse

    **Datenintegration:**
    - Zugriff auf Kunden- und Produktdatenbank
    - Zahlungshistorie und Fälligkeiten
    - Geschäftsberichte und Analytics

page-ai-command-stats-feedback =
    **📊 Gesprächsstatistiken:**

    - **Nachrichten gesamt:** { $total_messages }
    - **Ihre Nachrichten:** { $user_messages }
    - **KI-Antworten:** { $assistant_messages }
    - **Zeichen gesamt:** { NUMBER($total_chars) }
    - **Geschätzte Tokens:** { NUMBER($estimated_tokens) }

    **💡 Hinweise:**
    - Verwenden Sie `/clear`, um neu zu beginnen
    - Speichern Sie wichtige Gespräche mit 💾 Speichern

page-ai-command-custom-no-commands = 📝 **Keine benutzerdefinierten Befehle gefunden**\n\nErstellen Sie Befehle in `~/.openfatture/commands/*.yaml`
page-ai-command-custom-header = 📝 **Benutzerdefinierte Befehle ({ $count }):**
page-ai-command-custom-footer = 💡 Verwenden Sie `/help`, um alle Befehle zu sehen
page-ai-command-reload-success = 🔄 **Befehle neu geladen:** { $old_count } → { $new_count } ({ $added } hinzugefügt, { $removed } entfernt)
page-ai-command-reload-error = ❌ **Fehler beim Neuladen:** { $error }
page-ai-command-clear-feedback = 🗑️ **Verlauf gelöscht**\n\nDas Gespräch wurde zurückgesetzt.
page-ai-command-custom-expanded = 🔧 **Befehl erweitert:** `/{ $command }` → { $length } Zeichen
page-ai-command-custom-error = ❌ **Befehlsfehler:** { $error }
page-ai-command-unknown = ❓ **Unbekannter Befehl:** `{ $command }`\n\nVerwenden Sie `/help`, um verfügbare Befehle zu sehen

### Tab 1: Chat Assistant
page-ai-chat-title = Interaktiver Chat
page-ai-chat-description =
    Chatten Sie mit dem KI-Assistenten für:
    - Fragen zur Rechnungsstellung und Vorschriften
    - Steuer- und MwSt-Beratung
    - Zahlungs- und Fristenmanagement
    - Allgemeine Geschäftsberatung

page-ai-chat-save = Speichern
page-ai-chat-save-help = Gespräch speichern
page-ai-chat-session-title = Chat { $count } Nachrichten
page-ai-chat-saved = ✅ Gespeichert: { $session_id }...
page-ai-chat-save-error = ❌ Speicherfehler
page-ai-chat-reload = Neu laden
page-ai-chat-reload-help = Benutzerdefinierte Befehle neu laden
page-ai-chat-reloaded = ✅ Neu geladen: { $count } Befehle
page-ai-chat-clear = Löschen

### Chat File Upload
page-ai-chat-file-upload-title = 📎 Datei Anhängen (Optional)
page-ai-chat-file-upload-label = Laden Sie ein Dokument hoch, um es mit der KI zu besprechen
page-ai-chat-file-upload-help = Unterstützt PDF, Text, Bilder und andere Dokumente
page-ai-chat-file-uploaded = 📄 Datei hochgeladen: { $name } ({ $size } Bytes)
page-ai-chat-files-attached = Angehängte Dateien
page-ai-chat-files-clear-all = Alle Löschen
page-ai-chat-files-cleared = Dateien gelöscht!

### Chat File Types
page-ai-chat-file-text-preview = - **{ $name }** (Text): { $preview }
page-ai-chat-file-text = - **{ $name }** (Text, { $size } Bytes)
page-ai-chat-file-pdf = - **{ $name }** (PDF, { $size } Bytes) - Zu analysierender Inhalt
page-ai-chat-file-image = - **{ $name }** (Bild { $format }, { $size } Bytes) - Text über OCR zu extrahieren
page-ai-chat-file-other = - **{ $name }** ({ $type }, { $size } Bytes)
page-ai-chat-file-analysis-hint = Die KI wird diese Dateien analysieren, um eine genauere Antwort zu geben.

### Custom Commands
page-ai-chat-custom-commands-title = 📝 Benutzerdefinierte Befehle
page-ai-chat-custom-commands-empty = Keine benutzerdefinierten Befehle gefunden. Erstellen Sie Befehle in `~/.openfatture/commands/*.yaml`
page-ai-chat-custom-commands-count = **{ $count } Befehle verfügbar:**
page-ai-chat-custom-commands-description = **Beschreibung:** { $desc }
page-ai-chat-custom-commands-examples = Beispiele
page-ai-chat-custom-commands-author = **Autor:** { $author }
page-ai-chat-custom-commands-version = **Version:** { $version }

### Chat Sessions
page-ai-chat-sessions-title = 💾 Gespeicherte Sitzungen
page-ai-chat-sessions-empty = Keine gespeicherten Sitzungen. Verwenden Sie die 💾 Speichern-Schaltfläche, um das aktuelle Gespräch zu speichern.
page-ai-chat-sessions-count = **{ $count } Sitzungen verfügbar:**
page-ai-chat-sessions-load = Laden
page-ai-chat-sessions-loaded = ✅ Sitzung geladen: { $title }
page-ai-chat-sessions-load-error-empty = ❌ Leere oder beschädigte Sitzung
page-ai-chat-sessions-load-error = ❌ Ladefehler: { $error }
page-ai-chat-sessions-rename = Umbenennen
page-ai-chat-sessions-rename-todo = Umbenennungsfunktion noch zu implementieren
page-ai-chat-sessions-delete = Löschen
page-ai-chat-sessions-deleted = ✅ Sitzung gelöscht
page-ai-chat-sessions-delete-error = ❌ Löschfehler

### Chat Input & Messages
page-ai-chat-input-placeholder = Geben Sie Ihre Nachricht ein oder verwenden Sie /befehl...
page-ai-chat-attachments = Anhänge
page-ai-chat-thinking = Denkt nach...

### Chat Feedback
page-ai-chat-feedback-good = Gut
page-ai-chat-feedback-good-comment = Gute Antwort
page-ai-chat-feedback-bad = Schlecht
page-ai-chat-feedback-bad-comment = Unbefriedigende Antwort
page-ai-chat-feedback-comment = Kommentar
page-ai-chat-feedback-comment-label = Hinterlassen Sie einen Kommentar zur Antwort:
page-ai-chat-feedback-submit = Kommentar Absenden
page-ai-chat-feedback-comment-sent = ✅ Kommentar gesendet!
page-ai-chat-feedback-comment-empty = Geben Sie einen Kommentar ein
page-ai-chat-feedback-thanks = ✅ Vielen Dank für Ihr Feedback!
page-ai-chat-feedback-error = ❌ Fehler beim Senden des Feedbacks

### Tab 2: Description Generator
page-ai-desc-title = Rechnungsbeschreibung Generieren
page-ai-desc-description =
    Generieren Sie professionelle Beschreibungen für Ihre Rechnungen mit KI.
    Geben Sie Informationen über die Dienstleistung an und erhalten Sie eine detaillierte Beschreibung.

page-ai-desc-service-label = Erbrachte Dienstleistung *
page-ai-desc-service-placeholder = z.B., E-Commerce-Webanwendungs-Entwicklungsberatung
page-ai-desc-service-help = Beschreiben Sie kurz die Dienstleistung/das Produkt
page-ai-desc-hours-label = Geleistete Stunden
page-ai-desc-hours-help = Anzahl der Stunden (optional)
page-ai-desc-project-label = Projektname
page-ai-desc-project-placeholder = z.B., XYZ E-Commerce Projekt
page-ai-desc-project-help = Projektname (optional)
page-ai-desc-rate-label = Stundensatz (€)
page-ai-desc-rate-help = Stundensatz in Euro (optional)
page-ai-desc-tech-label = Technologien
page-ai-desc-tech-placeholder = Python, FastAPI, PostgreSQL
page-ai-desc-tech-help = Verwendete Technologien, durch Komma getrennt (optional)
page-ai-desc-generate = Beschreibung Generieren
page-ai-desc-error-empty = ⚠️ Geben Sie eine Dienstleistungsbeschreibung ein
page-ai-desc-generating = 🤖 Generiere professionelle Beschreibung...
page-ai-desc-success = ✅ Beschreibung erfolgreich generiert!
page-ai-desc-result-title = Professionelle Beschreibung
page-ai-desc-deliverables = Ergebnisse
page-ai-desc-skills = Technische Fähigkeiten
page-ai-desc-duration = **⏱️ Dauer:** { $hours } Stunden
page-ai-desc-notes = **📌 Notizen:** { $notes }
page-ai-desc-result-generated = Generierte Beschreibung

### Tab 3: VAT Suggestion
page-ai-vat-title = MwSt-Satz-Vorschlag
page-ai-vat-description =
    Erhalten Sie KI-Vorschläge zum korrekten MwSt-Satz und zur steuerlichen Behandlung
    basierend auf Dienstleistungs-/Produkttyp und Kunde.

page-ai-vat-service-label = Dienstleistungs-/Produktbeschreibung *
page-ai-vat-service-placeholder = z.B., IT-Beratung für Management-Software-Entwicklung
page-ai-vat-service-help = Beschreiben Sie die zu berechnende Dienstleistung oder das Produkt
page-ai-vat-client-pa-label = Kunde ist Öffentliche Verwaltung
page-ai-vat-client-pa-help = Markieren Sie, wenn der Kunde PA ist
page-ai-vat-amount-label = Betrag (€)
page-ai-vat-amount-help = Betrag in Euro (optional)
page-ai-vat-client-foreign-label = Ausländischer Kunde
page-ai-vat-client-foreign-help = Markieren Sie, wenn der Kunde nicht in Italien ansässig ist
page-ai-vat-country-label = Kundenland
page-ai-vat-country-placeholder = IT, FR, US...
page-ai-vat-country-help = 2-stelliger ISO-Ländercode
page-ai-vat-category-label = Dienstleistungskategorie
page-ai-vat-category-help = Dienstleistungskategorie (optional)
page-ai-vat-category-consulting = Beratung
page-ai-vat-category-software = Softwareentwicklung
page-ai-vat-category-training = Schulung
page-ai-vat-category-design = Design/Grafik
page-ai-vat-category-marketing = Marketing
page-ai-vat-category-maintenance = Wartung
page-ai-vat-category-other = Sonstiges
page-ai-vat-suggest = MwSt-Vorschlag Erhalten
page-ai-vat-error-empty = ⚠️ Geben Sie eine Dienstleistungs-/Produktbeschreibung ein
page-ai-vat-analyzing = 🤖 Analysiere steuerliche Behandlung...
page-ai-vat-success = ✅ Analyse abgeschlossen!
page-ai-vat-treatment-title = Steuerliche Behandlung
page-ai-vat-rate-metric = MwSt-Satz
page-ai-vat-reverse-charge-metric = Reverse Charge
page-ai-vat-confidence-metric = Vertrauen
page-ai-vat-nature-code = **MwSt-Naturcode:** { $code }
page-ai-vat-split-payment = ⚠️ **Geteilte Zahlung** anwendbar
page-ai-vat-special-regime = **Sonderregelung:** { $regime }
page-ai-vat-explanation-title = Erklärung
page-ai-vat-legal-reference-title = Rechtliche Referenz
page-ai-vat-invoice-note-title = Rechnungshinweis
page-ai-vat-recommendations-title = Empfehlungen
page-ai-vat-suggestion-title = Vorschlag
page-ai-vat-error = ❌ Fehler: { $error }
page-ai-vat-error-generic = ❌ Analysefehler: { $error }

### Tab 4: Voice Chat
page-ai-voice-title = Sprach-Chat mit KI
page-ai-voice-not-configured =
    ⚠️ **Sprach-Chat nicht konfiguriert**

    Um Sprach-Chat zu aktivieren:
    1. Konfigurieren Sie `OPENAI_API_KEY` in der `.env`-Datei
    2. Setzen Sie `OPENFATTURE_VOICE_ENABLED=true`
    3. Starten Sie die Anwendung neu

    Siehe Dokumentation für Details.

page-ai-voice-description =
    Sprechen Sie mit dem KI-Assistenten über Ihre Stimme:
    - 🎤 Nehmen Sie Ihre Frage auf
    - 🤖 KI transkribiert und antwortet
    - 🔊 Hören Sie die Sprachantwort
    - 💬 Unterstützt Kontextgespräche

### Voice Configuration
page-ai-voice-config-title = ⚙️ Sprachkonfiguration
page-ai-voice-config-provider = Anbieter
page-ai-voice-config-stt = STT-Modell
page-ai-voice-config-tts-voice = TTS-Stimme
page-ai-voice-config-tts-model = **TTS-Modell:** { $model }
page-ai-voice-config-tts-speed = **TTS-Geschwindigkeit:** { $speed }x
page-ai-voice-config-tts-format = **TTS-Format:** { $format }
page-ai-voice-config-streaming = **Streaming:** { $enabled }

### Voice History
page-ai-voice-clear = Sprache Löschen
page-ai-voice-history-title = Gesprächsverlauf
page-ai-voice-user-message = **Sie:** { $text }
page-ai-voice-assistant-message = **Assistent:** { $text }
page-ai-voice-language-detected = Sprache erkannt: { $lang }
page-ai-voice-language = Sprache: { $lang }
page-ai-voice-metric-stt = STT: { $ms }ms
page-ai-voice-metric-llm = LLM: { $ms }ms
page-ai-voice-metric-tts = TTS: { $ms }ms
page-ai-voice-metric-total = Gesamt: { $ms }ms
page-ai-voice-metric-total-label = Gesamt
page-ai-voice-history-empty = 👋 Noch keine Sprachgespräche. Nehmen Sie Ihre erste Frage auf!

### Voice Input
page-ai-voice-record-title = Nehmen Sie Ihre Stimme auf
page-ai-voice-record-label = Drücken Sie die Taste zum Aufnehmen
page-ai-voice-record-help = Sprechen Sie deutlich ins Mikrofon. Die Aufnahme stoppt automatisch nach Stille.
page-ai-voice-recorded = ✅ Audio aufgenommen: { $size } Bytes
page-ai-voice-process = Senden und Verarbeiten
page-ai-voice-processing = 🤖 Verarbeite Ihre Sprachnachricht...
page-ai-voice-success = ✅ Sprachnachricht erfolgreich verarbeitet!
page-ai-voice-transcription-title = Transkription
page-ai-voice-response-title = KI-Antwort
page-ai-voice-audio-response-title = Sprachantwort
page-ai-voice-metrics-title = Metriken
page-ai-voice-tech-details = ℹ️ Technische Details
page-ai-voice-error = ❌ Verarbeitungsfehler: { $error }
page-ai-voice-error-hint-connection = 💡 Hinweis: Überprüfen Sie Ihre Internetverbindung
page-ai-voice-error-hint-auth = 💡 Hinweis: Überprüfen Sie die API-Einstellungen in der Konfiguration
page-ai-voice-error-hint-rate = 💡 Hinweis: Ratenlimit erreicht. Versuchen Sie es in ein paar Minuten erneut

### Voice Help
page-ai-voice-help-title = ❓ Wie es funktioniert
page-ai-voice-help-content =
    **Sprach-Chat-Workflow:**

    1. **🎤 Aufnahme**: Drücken Sie die Taste und sprechen Sie ins Mikrofon
    2. **📝 Transkription (STT)**: OpenAI Whisper wandelt Sprache in Text um
    3. **🤖 Verarbeitung (LLM)**: KI versteht und generiert eine Antwort
    4. **🔊 Synthese (TTS)**: OpenAI TTS wandelt Antwort in Audio um
    5. **▶️ Wiedergabe**: Hören Sie die Sprachantwort

    **Sprachunterstützung:**
    - Automatische Erkennung aus über 100 Sprachen
    - Italienisch, Englisch, Französisch, Deutsch, Spanisch und viele mehr

    **Geschätzte Kosten:**
    - STT (Whisper): ~0,006 $ pro Minute Audio
    - TTS: ~0,015 $ pro 1.000 Zeichen (tts-1) oder ~0,030 $ (tts-1-hd)
    - LLM: Standardpreise des konfigurierten Modells

    **Anforderungen:**
    - Funktionierendes Mikrofon
    - Moderner Browser (Chrome, Firefox, Safari, Edge)
    - Stabile Internetverbindung

### Metrics (shared across tabs)
page-ai-metric-provider = Anbieter
page-ai-metric-tokens = Tokens
page-ai-metric-cost = Kosten

### Footer
page-ai-footer-disclaimer =
    **💡 Hinweis:** Der KI-Assistent ist ein Unterstützungswerkzeug. Die bereitgestellten Informationen
    sollten immer mit einem Buchhalter oder Steuerberater überprüft werden, um die Einhaltung
    der geltenden Vorschriften sicherzustellen.

## ============================================================================
## CLIENTS PAGE (3_👥_Clienti.py)
## ============================================================================

page-clients-title = 👥 Kundenverwaltung
page-clients-subtitle = Kunden anzeigen und verwalten

### Sidebar Filters
page-clients-filter-title = 🔍 Filter
page-clients-filter-search = Suchen
page-clients-filter-search-placeholder = Firmenname, USt-IdNr., Steuernummer...
page-clients-filter-search-help = Nach Firmenname, Umsatzsteuer-ID oder Steuernummer suchen

### Actions
page-clients-action-new = ➕ Neuer Kunde
page-clients-action-refresh = 🔄 Aktualisieren
page-clients-action-view = Details anzeigen
page-clients-action-edit = Bearbeiten
page-clients-action-delete = Löschen

### Add Client Form
page-clients-form-add-title = ➕ Neuer Kunde
page-clients-form-denominazione = Firmenname *
page-clients-form-denominazione-placeholder = Firmen- oder Personenname
page-clients-form-piva = USt-IdNr.
page-clients-form-piva-placeholder = 12345678901
page-clients-form-cf = Steuernummer
page-clients-form-cf-placeholder = RSSMRA80A01H501U
page-clients-form-sdi = SDI-Code
page-clients-form-sdi-placeholder = ABC1234
page-clients-form-pec = PEC
page-clients-form-pec-placeholder = kunde@pec.it
page-clients-form-address = Adresse
page-clients-form-address-placeholder = Römerstraße 123
page-clients-form-zip = Postleitzahl
page-clients-form-zip-placeholder = 10115
page-clients-form-phone = Telefon
page-clients-form-phone-placeholder = +49 30 1234567
page-clients-form-city = Stadt
page-clients-form-city-placeholder = Berlin
page-clients-form-province = Bundesland
page-clients-form-province-placeholder = BE
page-clients-form-email = E-Mail
page-clients-form-email-placeholder = kunde@email.com
page-clients-form-notes = Notizen
page-clients-form-notes-placeholder = Zusätzliche Notizen...
page-clients-form-save = 💾 Kunde Speichern
page-clients-form-cancel = ❌ Abbrechen

### Statistics
page-clients-stats-title = 📊 Statistiken
page-clients-stats-total = Kunden Gesamt
page-clients-stats-with-pec = Mit PEC
page-clients-stats-with-sdi = Mit SDI
page-clients-stats-with-piva = Mit USt-IdNr.

### Client List
page-clients-list-title = 📋 Kundenliste

### Table Columns
page-clients-table-col-id = ID
page-clients-table-col-denominazione = Firmenname
page-clients-table-col-piva = USt-IdNr.
page-clients-table-col-cf = Steuernummer
page-clients-table-col-sdi = SDI
page-clients-table-col-pec = PEC
page-clients-table-col-comune = Stadt
page-clients-table-col-provincia = BL
page-clients-table-col-created = Erstellt
page-clients-table-col-actions = Aktionen

### Empty State
page-clients-no-results = 🔍 Keine Kunden für '{ $term }' gefunden
page-clients-empty-state = 📝 Keine Kunden vorhanden. Erstellen Sie Ihren ersten Kunden!

### Quick Add Form
page-clients-quick-add-title = 🚀 Ersten Kunden erstellen
page-clients-quick-add-description = Füllen Sie die wichtigsten Angaben aus:
page-clients-quick-add-pec-optional = PEC (optional)
page-clients-quick-add-button = ➕ Kunde Erstellen

### Client Detail
page-clients-detail-title = 👁️ Kundendetails: { $name }
page-clients-detail-id = ID
page-clients-detail-denominazione = Firmenname
page-clients-detail-piva = USt-IdNr.
page-clients-detail-cf = Steuernummer
page-clients-detail-sdi = SDI
page-clients-detail-pec = PEC
page-clients-detail-phone = Telefon
page-clients-detail-email = E-Mail
page-clients-detail-address = Adresse
page-clients-detail-city = Stadt
page-clients-detail-notes = Notizen
page-clients-detail-na = N/V
page-clients-detail-close = ❌ Schließen

### Edit Client
page-clients-edit-title = ✏️ Kunde Bearbeiten: { $name }
page-clients-edit-save = 💾 Änderungen Speichern

### Delete Client
page-clients-delete-title = 🗑️ Kunde Löschen: { $name }
page-clients-delete-confirm = ⚠️ Sind Sie sicher, dass Sie den Kunden '{ $name }' löschen möchten?
page-clients-delete-warning = Diese Aktion kann nicht rückgängig gemacht werden.
page-clients-delete-yes = 🗑️ Ja, Löschen
page-clients-delete-no = ❌ Abbrechen

### Quick Preview
page-clients-preview-title = 📊 Schnellansicht
page-clients-preview-total = 👥 Kunden Gesamt
page-clients-preview-invoices = 📄 Rechnungen Gesamt
page-clients-preview-top5 = 👑 Top 5 Kunden
page-clients-preview-col-client = Kunde
page-clients-preview-col-invoices = Anz. Rechnungen
page-clients-preview-col-revenue = Gesamtumsatz

### Success Messages
page-clients-success-created = ✅ Kunde '{ $name }' erfolgreich erstellt!
page-clients-success-updated = ✅ Kunde '{ $name }' aktualisiert!
page-clients-success-deleted = ✅ Kunde '{ $name }' gelöscht!
page-clients-success-quick-created = ✅ Kunde '{ $name }' erstellt!

### Error Messages
page-clients-error-denominazione-required = Firmenname ist erforderlich
page-clients-error-create = ❌ Fehler beim Erstellen des Kunden: { $error }
page-clients-error-update = ❌ Fehler beim Aktualisieren: { $error }
page-clients-error-delete = ❌ Fehler beim Löschen: { $error }
page-clients-error-not-found = Kunde nicht gefunden
page-clients-error-loading = ❌ Fehler beim Laden der Kunden: { $error }
page-clients-error-loading-hint = 💡 Stellen Sie sicher, dass die Datenbank korrekt initialisiert ist
page-clients-error-quick-create = ❌ Fehler: { $error }
page-clients-preview-error = Fehler beim Laden der Daten: { $error }

### Legacy (kept for compatibility)
page-clients-search = Kunden suchen...
page-clients-filter-type = Typ
page-clients-filter-country = Land
page-clients-col-name = Name/Firmenname
page-clients-col-vat = USt-IdNr.
page-clients-col-email = E-Mail
page-clients-col-phone = Telefon
page-clients-col-invoices = Rechnungen
page-clients-col-revenue = Umsatz
page-clients-col-actions = Aktionen
page-clients-action-add = Kunde Hinzufügen
page-clients-action-create-invoice = Rechnung Erstellen
page-clients-no-clients = Keine Kunden gefunden
page-clients-add-first = Fügen Sie Ihren ersten Kunden hinzu
page-clients-total-found = { $count } Kunden gefunden

## ============================================================================
## BERICHTE-SEITE (9_📊_Reports.py)
## ============================================================================

page-reports-page-title = Berichte - OpenFatture
page-reports-title = 📊 Berichte & Analysen
page-reports-subtitle = Unternehmensberichte und erweiterte Analysen
page-reports-no-data = ⚠️ Keine Daten für Berichte verfügbar
page-reports-no-data-info = Erstellen Sie einige Rechnungen, um Berichte zu sehen

### Seitenleiste
page-reports-filter-title = 🔍 Berichtsparameter
page-reports-filter-year = Jahr
page-reports-filter-quarter = Quartal (optional)
page-reports-filter-quarter-all = Alle
page-reports-filter-quarter-q1 = Q1
page-reports-filter-quarter-q2 = Q2
page-reports-filter-quarter-q3 = Q3
page-reports-filter-quarter-q4 = Q4

### Registerkarten
page-reports-tab-revenue = 💰 Umsatz
page-reports-tab-vat = 📋 MwSt.
page-reports-tab-clients = 👥 Kunden

### Umsatz-Registerkarte
page-reports-revenue-title = 💰 Umsatzbericht
page-reports-revenue-total = Gesamtumsatz
page-reports-revenue-total-help = Zeitraum: { $period }
page-reports-revenue-vat-total = MwSt. Gesamt
page-reports-revenue-invoices = Ausgestellte Rechnungen
page-reports-revenue-avg = Durchschnittlicher Rechnungswert
page-reports-revenue-monthly = 📈 Monatlicher Trend
page-reports-revenue-chart-title = Monatlicher Umsatz
page-reports-revenue-chart-xaxis = Monat
page-reports-revenue-chart-yaxis = Umsatz (€)
page-reports-revenue-count-chart = Monatliche Rechnungsanzahl
page-reports-revenue-count-yaxis = Rechnungsanzahl

### MwSt.-Registerkarte
page-reports-vat-title = 📋 MwSt.-Bericht
page-reports-vat-taxable = Steuerpflichtige Gesamtsumme
page-reports-vat-total = MwSt. Gesamt
page-reports-vat-revenue-total = Gesamtumsatz
page-reports-vat-breakdown-title = 📊 Aufschlüsselung nach MwSt.-Satz
page-reports-vat-pie-title = Verteilung der steuerpflichtigen Summe nach MwSt.-Satz
page-reports-vat-detail-title = 📋 Details nach Satz
page-reports-vat-table-rate = MwSt.-Satz
page-reports-vat-table-taxable = Steuerpflichtige Summe
page-reports-vat-table-vat = MwSt.
page-reports-vat-table-total = Gesamt

### Kunden-Registerkarte
page-reports-clients-title = 👥 Kundenbericht
page-reports-clients-active = Aktive Kunden
page-reports-clients-active-help = Kunden mit ausgestellten Rechnungen in { $year }
page-reports-clients-top-title = 🏆 Top-Kunden nach Umsatz
page-reports-clients-table-client = Kunde
page-reports-clients-table-invoices = Rechnungen
page-reports-clients-table-total = Gesamt
page-reports-clients-table-last = Letzte Rechnung
page-reports-clients-chart-title = Top 10 Kunden nach Umsatz
page-reports-clients-chart-xaxis = Kunde
page-reports-clients-chart-yaxis = Umsatz (€)

### Export
page-reports-export-title = 📤 Berichte Exportieren
page-reports-export-revenue = 📊 Umsatz Exportieren (CSV)
page-reports-export-vat = 📋 MwSt. Exportieren (CSV)
page-reports-export-clients = 👥 Kunden Exportieren (CSV)
page-reports-export-download = CSV Herunterladen

page-reports-footer = 📊 <strong>Automatisch aktualisierte Berichte</strong> • Daten basierend auf gelieferten oder akzeptierten Rechnungen

## ============================================================================
## HOOKS-SEITE (10_🪝_Hooks.py)
## ============================================================================

page-hooks-page-title = Hooks & Automatisierung - OpenFatture
page-hooks-title = 🪝 Hooks & Automatisierung
page-hooks-subtitle = Verwaltung automatisierter Workflows und Trigger

### Zusammenfassungsmetriken
page-hooks-metric-total = Hooks Gesamt
page-hooks-metric-enabled = Aktive Hooks
page-hooks-metric-pre = Pre-Hooks
page-hooks-metric-post = Post-Hooks

### Registerkarten
page-hooks-tab-overview = 📊 Übersicht
page-hooks-tab-manage = ⚙️ Verwalten
page-hooks-tab-create = ➕ Hook Erstellen
page-hooks-tab-test = 🧪 Testen

### Übersichts-Registerkarte
page-hooks-overview-title = 📊 Hooks-Übersicht
page-hooks-overview-group-pre = 🎯
page-hooks-overview-group-post = ✅
page-hooks-overview-group-on = 👀
page-hooks-overview-status-active = ✅ Aktiv
page-hooks-overview-status-inactive = ⏸️ Inaktiv
page-hooks-overview-timeout = ⏱️ { $timeout }s
page-hooks-overview-empty = 🎣 Keine Hooks gefunden. Erstellen Sie Ihren ersten Hook in der Registerkarte 'Hook Erstellen'!

### Verwaltungs-Registerkarte
page-hooks-manage-title = ⚙️ Hooks Verwalten
page-hooks-manage-toggle-title = Hook-Status Umschalten
page-hooks-manage-toggle-label = { $name } Aktivieren
page-hooks-manage-toggle-help = Hook { $name } aktivieren/deaktivieren
page-hooks-manage-toggle-enabled = ✅ Hook '{ $name }' aktiviert
page-hooks-manage-toggle-disabled = ⏸️ Hook '{ $name }' deaktiviert
page-hooks-manage-toggle-error = ❌ Fehler beim Aktualisieren des Hook-Status
page-hooks-manage-details-button = 👁️ Details
page-hooks-manage-details-help = Hook-Details anzeigen
page-hooks-manage-details-title = Details { $name }
page-hooks-manage-empty = 🎣 Keine Hooks zu verwalten

### Erstellungs-Registerkarte
page-hooks-create-title = ➕ Neuen Hook Erstellen
page-hooks-create-name-label = Hook-Name
page-hooks-create-name-placeholder = z.B.: post-invoice-send
page-hooks-create-name-help = Hook-Name (verwenden Sie Präfixe pre-, post-, on-)
page-hooks-create-type-label = Skripttyp
page-hooks-create-type-help = Skripttyp für den Hook
page-hooks-create-type-bash = bash
page-hooks-create-type-python = python
page-hooks-create-desc-label = Beschreibung
page-hooks-create-desc-placeholder = Was macht dieser Hook...
page-hooks-create-desc-help = Kurze Beschreibung des Hooks
page-hooks-create-event-label = Ereignistyp
page-hooks-create-event-help = Wann der Hook ausgeführt wird
page-hooks-create-event-pre = pre
page-hooks-create-event-post = post
page-hooks-create-event-on = on
page-hooks-create-preview-title = 📋 Vorlagenvorschau
page-hooks-create-preview-code = 👁️ Vorlagencode
page-hooks-create-button = 🚀 Hook Erstellen
page-hooks-create-error-name = ❌ Geben Sie einen Namen für den Hook ein
page-hooks-create-warning-prefix = 💡 Tipp: Name sollte mit '{ $prefix }-' beginnen
page-hooks-create-success = ✅ { $message }
page-hooks-create-reload = 🔄 Seite neu laden, um den neuen Hook zu sehen
page-hooks-create-error = ❌ { $message }

### Test-Registerkarte
page-hooks-test-title = 🧪 Hooks Testen
page-hooks-test-select-label = Hook zum Testen Auswählen
page-hooks-test-select-help = Wählen Sie den zu validierenden Hook
page-hooks-test-info-title = 📋 Hook-Informationen
page-hooks-test-metric-type = Ereignistyp
page-hooks-test-metric-status = Status
page-hooks-test-metric-timeout = Timeout
page-hooks-test-metric-status-active = Aktiv
page-hooks-test-metric-status-inactive = Inaktiv
page-hooks-test-validate-button = 🧪 Hook Validieren
page-hooks-test-validating = Hook wird validiert...
page-hooks-test-success = ✅ Hook erfolgreich validiert!
page-hooks-test-metric-lines = Code-Zeilen
page-hooks-test-metric-size = Größe
page-hooks-test-metric-size-value = { $size } Bytes
page-hooks-test-metric-executable = Ausführbar
page-hooks-test-metric-executable-yes = Ja
page-hooks-test-metric-executable-no = Nein
page-hooks-test-result-message = 💡 { $message }
page-hooks-test-error = ❌ Validierungsfehler: { $error }
page-hooks-test-show-code = 📄 Code Anzeigen
page-hooks-test-code-error = ❌ Hook-Datei nicht gefunden
page-hooks-test-read-error = ❌ Dateifehler beim Lesen: { $error }
page-hooks-test-empty = 🎣 Keine Hooks zum Testen verfügbar

page-hooks-footer =
    🪝 <strong>Hooks-System:</strong> Ereignisbasierte Workflow-Automatisierung •
    📍 <strong>Verzeichnis:</strong> ~/.openfatture/hooks/ •
    📚 <strong>Dokumentation:</strong> Siehe CLI für erweiterte Beispiele

## ============================================================================
## EREIGNISSE-SEITE (11_📋_Events.py)
## ============================================================================

page-events-page-title = Ereignisse & Audit-Trail - OpenFatture
page-events-title = 📋 Ereignisse & Audit-Trail
page-events-subtitle = Systemereignisverfolgung und Audit-Trail

### Zusammenfassungsmetriken
page-events-metric-total = Ereignisse Gesamt
page-events-metric-total-help = Letzte { $days } Tage
page-events-metric-daily-avg = Tägliche Ereignisse
page-events-metric-types = Ereignistypen
page-events-metric-entities = Verfolgte Entitäten

### Seitenleisten-Filter
page-events-filter-title = 🔍 Ereignisfilter
page-events-filter-period = Zeitraum (Tage)
page-events-filter-period-help = Anzahl der zu analysierenden Tage
page-events-filter-type = Ereignistyp
page-events-filter-type-all = Alle
page-events-filter-type-help = Nach Ereignistyp filtern
page-events-filter-entity-type = Entitätstyp
page-events-filter-entity-type-help = Nach Entitätstyp filtern
page-events-filter-search = 🔎 Suchen
page-events-filter-search-placeholder = In Ereignissen suchen...
page-events-filter-search-help = Nach Ereignistyp oder Entität suchen

### Registerkarten
page-events-tab-recent = 🕐 Neueste
page-events-tab-filtered = 🔍 Gefiltert
page-events-tab-stats = 📊 Statistiken
page-events-tab-timeline = ⏰ Zeitleiste

### Neueste-Registerkarte
page-events-recent-title = 🕐 Neueste Ereignisse
page-events-table-timestamp = Zeitstempel
page-events-table-type = Ereignistyp
page-events-table-entity = Entität
page-events-table-description = Beschreibung
page-events-table-user = Benutzer
page-events-table-user-system = System
page-events-details-button = 👁️ Details Anzeigen
page-events-details-help = Vollständige Ereignisdetails anzeigen
page-events-details-title = Ereignis { $num }: { $desc }
page-events-empty = 📭 Keine Ereignisse in der Datenbank gefunden

### Gefiltert-Registerkarte
page-events-filtered-title = 🔍 Gefilterte Ereignisse
page-events-filtered-found = ✅ { $count } Ereignisse gefunden
page-events-export-button = 📤 CSV Exportieren
page-events-export-help = Gefilterte Ergebnisse als CSV exportieren
page-events-export-download = CSV Herunterladen
page-events-filtered-empty = 🔍 Keine Ereignisse mit den ausgewählten Filtern gefunden

### Statistik-Registerkarte
page-events-stats-title = 📊 Ereignisstatistiken
page-events-stats-by-type = 📈 Ereignisse nach Typ
page-events-stats-type-col = Ereignistyp
page-events-stats-count-col = Anzahl
page-events-stats-by-entity = 🏢 Ereignisse nach Entität
page-events-stats-entity-col = Entitätstyp
page-events-stats-daily = 📅 Tägliche Aktivität (Letzte 7 Tage)

### Zeitleisten-Registerkarte
page-events-timeline-title = ⏰ Entitäts-Zeitleiste
page-events-timeline-entity-type = Entitätstyp
page-events-timeline-entity-type-help = Entitätstyp auswählen
page-events-timeline-entity-id = Entitäts-ID
page-events-timeline-entity-id-placeholder = z.B.: INV-001, CLI-001
page-events-timeline-entity-id-help = Geben Sie die zu verfolgende Entitäts-ID ein
page-events-timeline-found = ✅ { $count } Ereignisse für { $type } { $id } gefunden
page-events-timeline-event-time = 🕐 **{ $time }**
page-events-timeline-event-type = 📋 { $type }
page-events-timeline-event-details = 📄 Details
page-events-timeline-empty = 📭 Keine Ereignisse für { $type } { $id } gefunden
page-events-timeline-info = 💡 Wählen Sie einen Entitätstyp aus und geben Sie eine ID ein, um die Zeitleiste zu sehen

page-events-footer =
    📋 <strong>Ereignissystem:</strong> Vollständiger Audit-Trail für Compliance und Debugging •
    🔍 <strong>Suche:</strong> Nach Typ, Entität und Zeitraum filtern •
    📊 <strong>Analysen:</strong> Aktivitätsstatistiken und Entitäts-Zeitleiste

## ============================================================================
## SYSTEMZUSTAND-SEITE (12_🏥_Health.py)
## ============================================================================

page-health-page-title = Systemzustand - OpenFatture
page-health-title = 🏥 Systemzustand-Dashboard
page-health-subtitle = Echtzeit-Überwachung und Diagnose

### Nutzungsmetriken
page-health-usage-title = 📊 Nutzungsmetriken
page-health-metric-visits = Seitenaufrufe Gesamt
page-health-metric-unique = Eindeutige Seiten
page-health-metric-session = Sitzungsstart

### Cache-Statistiken
page-health-cache-title = 💾 Cache-Statistiken
page-health-cache-cleanup = 🧹 { $count } abgelaufene Cache-Einträge bereinigt
page-health-metric-entries = Cache-Einträge Gesamt
page-health-metric-functions = Gecachte Funktionen
page-health-clear-all = 🗑️ Alle Caches Leeren
page-health-clear-success = ✅ Alle Caches geleert!
page-health-cache-breakdown = Cache-Aufschlüsselung nach Funktion
page-health-table-function = Funktion
page-health-table-entries = Einträge
page-health-cache-management = Selektive Cache-Verwaltung
page-health-clear-invoices = 🧾 Rechnungs-Caches Leeren
page-health-clear-clients = 👥 Kunden-Caches Leeren
page-health-clear-payments = 💰 Zahlungs-Caches Leeren
page-health-cleared-category = ✅ { $count } { $category }-Caches geleert

### Seitenaufrufe
page-health-visits-breakdown = Aufschlüsselung der Seitenaufrufe
page-health-table-page = Seite
page-health-table-visits = Aufrufe

### API-Systemzustand
page-health-api-title = 🔌 API-Systemzustand-Endpunkt
page-health-api-info =
    Für externe Überwachung verwenden Sie die Funktion `quick_health_check()`:

    ```python
    from openfatture.web.utils.health import quick_health_check

    health = quick_health_check()
    # Gibt zurück: {"status": "healthy|degraded|unhealthy", "checks": [...]}
    ```

    Dies kann über einen API-Endpunkt für Überwachungstools bereitgestellt werden wie:
    - Prometheus
    - Datadog
    - New Relic
    - Benutzerdefinierte Überwachungs-Dashboards

page-health-api-sample = 🔍 Beispiel-Systemzustand-JSON Anzeigen
page-health-best-practice =
    **💡 Best Practice:** Überwachen Sie dieses Dashboard regelmäßig, um Probleme frühzeitig zu erkennen.
    Richten Sie Alarme für "unhealthy"- oder "degraded"-Status in der Produktion ein.
