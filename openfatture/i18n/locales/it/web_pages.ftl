# Web Pages translations - Italian
# Traduzioni specifiche per le pagine dell'interfaccia web Streamlit

## ============================================================================
## HOME PAGE (app.py)
## ============================================================================

page-home-title = 🏠 OpenFatture
page-home-welcome = Benvenuto in OpenFatture
page-home-subtitle = Sistema di Fatturazione Elettronica Open Source
page-home-description =
    OpenFatture è un sistema completo per la gestione della fatturazione elettronica
    italiana, con integrazione SDI, AI e pagamenti Lightning.

page-home-features-title = ✨ Caratteristiche Principali
page-home-feature-invoicing = Fatturazione Elettronica completa con FatturaPA
page-home-feature-sdi = Integrazione diretta con SDI (Sistema di Interscambio)
page-home-feature-ai = Assistente AI per descrizioni e suggerimenti IVA
page-home-feature-payments = Riconciliazione pagamenti bancari automatica
page-home-feature-lightning = Supporto pagamenti Lightning Network
page-home-feature-batch = Operazioni batch per import/export massivi

## Feature Grid
page-home-feature-grid-invoices-title = 🧾 Fatture
page-home-feature-grid-invoices-item-1 = Creazione guidata
page-home-feature-grid-invoices-item-2 = Gestione clienti
page-home-feature-grid-invoices-item-3 = Generazione XML
page-home-feature-grid-invoices-item-4 = Invio SDI via PEC
page-home-feature-grid-invoices-item-5 = Tracking notifiche
page-home-feature-grid-invoices-button = 📝 Vai alle Fatture

page-home-feature-grid-payments-title = 💰 Pagamenti
page-home-feature-grid-payments-item-1 = Import estratti conto
page-home-feature-grid-payments-item-2 = Matching automatico
page-home-feature-grid-payments-item-3 = Riconciliazione
page-home-feature-grid-payments-item-4 = Reminder scadenze
page-home-feature-grid-payments-item-5 = Audit trail
page-home-feature-grid-payments-button = 💳 Vai ai Pagamenti

page-home-feature-grid-ai-title = 🤖 AI Assistant
page-home-feature-grid-ai-item-1 = Chat interattivo
page-home-feature-grid-ai-item-2 = Descrizioni automatiche
page-home-feature-grid-ai-item-3 = Consulenza fiscale
page-home-feature-grid-ai-item-4 = Cash flow forecast
page-home-feature-grid-ai-item-5 = Compliance check
page-home-feature-grid-ai-button = 🚀 Prova l'AI

## Quick Actions
page-home-quick-actions = ⚡ Azioni Rapide
page-home-action-new-invoice = ➕ Nuova Fattura
page-home-action-new-client = 👤 Nuovo Cliente
page-home-action-dashboard = 📊 Dashboard
page-home-action-batch = 📦 Batch Operations

## Advanced Tools
page-home-advanced-tools = 🔧 Strumenti Avanzati
page-home-advanced-reports = 📊 Reports
page-home-advanced-hooks = 🪝 Hooks
page-home-advanced-events = 📋 Events

## Getting Started
page-home-getting-started = 🚀 Getting Started
page-home-getting-started-title = Primi Passi

page-home-step-1-title = 1. Configura l'ambiente
page-home-step-1-item-1 = Assicurati che `.env` sia configurato correttamente
page-home-step-1-item-2 = Verifica i dati aziendali (P.IVA, regime fiscale)
page-home-step-1-item-3 = Configura credenziali PEC per invio SDI

page-home-step-2-title = 2. Crea i primi clienti
page-home-step-2-item-1 = Vai su "👥 Clienti" → "Aggiungi Cliente"
page-home-step-2-item-2 = Inserisci i dati fiscali (P.IVA, codice fiscale)
page-home-step-2-item-3 = Specifica SDI o PEC per ricezione fatture

page-home-step-3-title = 3. Emetti la prima fattura
page-home-step-3-item-1 = "🧾 Fatture" → "Nuova Fattura"
page-home-step-3-item-2 = Seleziona cliente e aggiungi righe
page-home-step-3-item-3 = Genera XML e invia a SDI

page-home-step-4-title = 4. Esplora l'AI Assistant
page-home-step-4-item-1 = Prova la chat per domande fiscali
page-home-step-4-item-2 = Genera descrizioni intelligenti
page-home-step-4-item-3 = Ottieni suggerimenti IVA automatici

page-home-docs-title = Documentazione

## Footer
page-home-footer-version = OpenFatture v{ $version }
page-home-footer-license = MIT License
page-home-footer-tagline = Made with ❤️ by freelancers, for freelancers

page-home-help = 📚 Aiuto e Documentazione
page-home-github = Repository GitHub
page-home-report-bug = Segnala un Bug
page-home-about = Informazioni

## ============================================================================
## DASHBOARD PAGE (1_📊_Dashboard.py)
## ============================================================================

page-dashboard-title = 📊 Dashboard
page-dashboard-subtitle = Panoramica Business Real-Time

### KPI Cards
page-dashboard-kpi-section = 📈 Metriche Principali
page-dashboard-kpi-total-invoices = 📄 Totale Fatture
page-dashboard-kpi-total-revenue = 💰 Fatturato Totale
page-dashboard-kpi-total-clients = 👥 Clienti Attivi
page-dashboard-kpi-revenue-month = 📅 Fatturato Mese
page-dashboard-kpi-pending-payments = Pagamenti Pendenti
page-dashboard-kpi-avg-invoice = Importo Medio Fattura
page-dashboard-kpi-this-month = Questo Mese
page-dashboard-kpi-this-year = Quest'Anno
page-dashboard-kpi-growth = Crescita

### Charts
page-dashboard-chart-invoices-by-status = 📊 Fatture per Stato
page-dashboard-chart-revenue-6-months = 📈 Fatturato Ultimi 6 Mesi
page-dashboard-chart-yaxis-revenue = Fatturato (€)
page-dashboard-chart-xaxis-month = Mese
page-dashboard-chart-revenue-title = Andamento Fatturato
page-dashboard-chart-invoices-title = Fatture per Mese
page-dashboard-chart-clients-title = Top Clienti
page-dashboard-chart-status-title = Fatture per Stato
page-dashboard-chart-payments-title = Stato Pagamenti

### Tables
page-dashboard-top-clients = 👑 Top 5 Clienti
page-dashboard-recent-invoices = 🕐 Ultime 5 Fatture
page-dashboard-col-client = Cliente
page-dashboard-col-num-invoices = N. Fatture
page-dashboard-col-num-invoices-short = Fatture
page-dashboard-col-revenue = Fatturato
page-dashboard-col-number = Numero
page-dashboard-col-date = Data
page-dashboard-col-total = Totale
page-dashboard-col-status = Stato
page-dashboard-col-invoice = Fattura
page-dashboard-col-due-date = Scadenza
page-dashboard-col-days = Giorni
page-dashboard-col-days-delta = Δ Giorni
page-dashboard-col-days-help = Giorni alla scadenza
page-dashboard-col-residual = Residuo
page-dashboard-col-residual-amount = Importo Residuo
page-dashboard-col-category = Categoria

### Payment Tracking
page-dashboard-payment-tracking = 💳 Tracking Pagamenti
page-dashboard-payment-unmatched = 🔍 Non Abbinati
page-dashboard-payment-matched = ✅ Abbinati
page-dashboard-payment-ignored = ⏭️ Ignorati
page-dashboard-payment-total = 📊 Totale Transazioni
page-dashboard-payment-due-30 = 💰 Scadenze Pagamenti (Prossimi 30 gg)
page-dashboard-total-outstanding = 💸 Totale Residuo da Incassare
page-dashboard-category-overdue = 🔴 Scaduto
page-dashboard-category-due-soon = 🟡 In scadenza
page-dashboard-category-upcoming = 🟢 Prossimo

### Messages
page-dashboard-no-invoices = Nessuna fattura presente
page-dashboard-no-data = Nessun dato disponibile
page-dashboard-no-clients = Nessun cliente presente
page-dashboard-no-payments-due = ✅ Nessun pagamento in scadenza
page-dashboard-error-loading = ❌ Errore caricamento dashboard: { $error }
page-dashboard-refresh-button = 🔄 Aggiorna Dati

### Recent Activity
page-dashboard-recent-activity = Attività Recenti
page-dashboard-recent-payments = Ultimi Pagamenti
page-dashboard-pending-invoices = Fatture in Attesa
page-dashboard-overdue-payments = Pagamenti Scaduti

### Alerts
page-dashboard-alerts-title = 🔔 Avvisi
page-dashboard-alert-sdi-pending = Fatture in attesa di invio a SDI
page-dashboard-alert-overdue = Pagamenti scaduti
page-dashboard-alert-expiring = Preventivi in scadenza

### Quick Stats
page-dashboard-stats-today = Oggi
page-dashboard-stats-week = Questa Settimana
page-dashboard-stats-month = Questo Mese
page-dashboard-stats-year = Quest'Anno

## ============================================================================
## INVOICES PAGE (2_🧾_Fatture.py)
## ============================================================================

page-invoices-title = 🧾 Gestione Fatture
page-invoices-subtitle = Visualizza e gestisci tutte le tue fatture

### Sidebar Filters
page-invoices-filter-title = 🔍 Filtri
page-invoices-filter-year = Anno
page-invoices-filter-all = Tutti
page-invoices-filter-status = Stato
page-invoices-filter-max-results = Risultati massimi
page-invoices-no-invoices-in-db = Nessuna fattura presente
page-invoices-filter-client = Cliente
page-invoices-filter-date-from = Da Data
page-invoices-filter-date-to = A Data
page-invoices-filter-amount-min = Importo Min
page-invoices-filter-amount-max = Importo Max
page-invoices-filter-search = Cerca fatture...

### Quick Actions
page-invoices-action-quick-title = ⚡ Azioni Rapide
page-invoices-action-new-invoice = ➕ Nuova Fattura
page-invoices-action-new-invoice-info =
    **Feature in sviluppo**

    Per ora, crea fatture tramite CLI:
    ```bash
    uv run openfatture fattura crea
    ```

    La creazione guidata Web UI sarà disponibile a breve!
page-invoices-action-refresh = 🔄 Aggiorna Lista

### Main Content
page-invoices-list-title = ### 📋 Lista Fatture
page-invoices-no-invoices-found = 📭 Nessuna fattura trovata con i filtri selezionati

### Stats Metrics
page-invoices-stats-count = 📊 Fatture Trovate
page-invoices-stats-total = 💰 Totale
page-invoices-stats-statuses = 📋 Stati Diversi
page-invoices-stats-average = 📈 Importo Medio

### Table
page-invoices-table-title = #### 📋 Tabella Fatture
page-invoices-col-id = ID
page-invoices-col-number = Numero
page-invoices-col-date = Data
page-invoices-col-client = Cliente
page-invoices-col-total-eur = Totale €
page-invoices-col-status = Stato
page-invoices-col-lines = Righe
page-invoices-col-amount = Importo
page-invoices-col-payment = Pagamento
page-invoices-col-actions = Azioni

### Invoice Detail Section
page-invoices-detail-title = ### 🔍 Dettaglio Fattura
page-invoices-detail-input-id = Inserisci ID fattura da visualizzare
page-invoices-detail-show-button = 📄 Mostra Dettaglio
page-invoices-detail-error-not-found = ❌ Fattura con ID { $id } non trovata
page-invoices-detail-success = ✅ Fattura { $number }/{ $year }

### Detail Header Metrics
page-invoices-detail-number = Numero
page-invoices-detail-date = Data Emissione
page-invoices-detail-client = Cliente
page-invoices-detail-type = Tipo
page-invoices-detail-status = Stato
page-invoices-detail-sdi-number = Numero SDI

### Detail Line Items
page-invoices-detail-lines-title = #### 📦 Righe Fattura
page-invoices-detail-lines-col-num = #
page-invoices-detail-lines-col-desc = Descrizione
page-invoices-detail-lines-col-qty = Quantità
page-invoices-detail-lines-col-price = Prezzo €
page-invoices-detail-lines-col-vat = IVA %
page-invoices-detail-lines-col-total = Totale €
page-invoices-detail-lines-empty = Nessuna riga presente

### Detail Totals
page-invoices-detail-totals-title = #### 💰 Totali
page-invoices-detail-totals-taxable = Imponibile
page-invoices-detail-totals-vat = IVA
page-invoices-detail-totals-withholding = Ritenuta
page-invoices-detail-totals-stamp = Bollo
page-invoices-detail-totals-total = **TOTALE**

### Detail Files
page-invoices-detail-files-title = #### 📁 File
page-invoices-detail-files-xml-exists = ✅ XML: `{ $path }`
page-invoices-detail-files-xml-missing = 📄 XML non ancora generato
page-invoices-detail-files-pdf-exists = ✅ PDF: `{ $path }`
page-invoices-detail-files-pdf-missing = 📄 PDF non ancora generato

### Detail Actions
page-invoices-detail-actions-title = #### ⚡ Azioni
page-invoices-detail-actions-generate-xml = 📝 Genera XML
page-invoices-detail-actions-generating-xml = Generando XML...
page-invoices-detail-actions-error = ❌ Errore: { $error }
page-invoices-detail-actions-xml-success = ✅ XML generato con successo!
page-invoices-detail-actions-send-sdi = 📤 Invia SDI
page-invoices-detail-actions-generate-pdf = 📄 Genera PDF
page-invoices-detail-actions-cli-feature = Feature CLI

### Error Messages
page-invoices-error-loading = ❌ Errore caricamento fatture: { $error }

### Legacy (kept for compatibility)
page-invoices-action-view = Visualizza
page-invoices-action-edit = Modifica
page-invoices-action-delete = Elimina
page-invoices-action-send = Invia a SDI
page-invoices-action-download-xml = Scarica XML
page-invoices-action-download-pdf = Scarica PDF
page-invoices-action-duplicate = Duplica
page-invoices-no-invoices = Nessuna fattura trovata
page-invoices-create-first = Crea la tua prima fattura
page-invoices-total-found = { $count } fatture trovate
page-invoices-selected = { $count } selezionate

## ============================================================================
## INVOICE CREATION PAGE (13_✏️_Crea_Fattura.py)
## ============================================================================

### Page Configuration
page-invoice-create-page-title = Crea Fattura - OpenFatture
page-invoice-create-title = ✏️ Creazione Fattura Guidata

### Wizard Progress
page-invoice-create-wizard-title = 📋 Creazione Fattura - Passo { $step }/{ $total }

### Step Labels
page-invoice-create-step-1-label = 👥 Seleziona Cliente
page-invoice-create-step-2-label = 📝 Dettagli Fattura
page-invoice-create-step-3-label = 🛒 Aggiungi Prodotti
page-invoice-create-step-4-label = 🤖 AI Assistenza
page-invoice-create-step-5-label = ✅ Riepilogo & Crea

### Step 1: Select Client
page-invoice-create-step-1-header = 👥 Seleziona Cliente
page-invoice-create-client-search-label = Cerca cliente esistente
page-invoice-create-client-search-placeholder = Nome azienda, P.IVA...
page-invoice-create-client-search-help = Lascia vuoto per vedere tutti i clienti
page-invoice-create-client-existing-title = Clienti esistenti
page-invoice-create-client-vat-label = P.IVA
page-invoice-create-client-select-label = Seleziona cliente
page-invoice-create-client-select-help = Scegli un cliente esistente o creane uno nuovo
page-invoice-create-client-create-title = ➕ Oppure crea nuovo cliente
page-invoice-create-client-create-expander = Crea nuovo cliente
page-invoice-create-client-name-label = Denominazione *
page-invoice-create-client-name-placeholder = Nome azienda o persona
page-invoice-create-client-vat-input-label = Partita IVA
page-invoice-create-client-vat-placeholder = 12345678901
page-invoice-create-client-fiscal-code-label = Codice Fiscale
page-invoice-create-client-fiscal-code-placeholder = Codice fiscale (se persona fisica)
page-invoice-create-client-address-label = Indirizzo
page-invoice-create-client-address-placeholder = Via Roma 123, 00100 Roma
page-invoice-create-client-email-label = Email
page-invoice-create-client-email-placeholder = cliente@email.com
page-invoice-create-client-phone-label = Telefono
page-invoice-create-client-phone-placeholder = +39 123 456 7890
page-invoice-create-client-regime-label = Regime Fiscale
page-invoice-create-client-regime-ordinary = RF01 - Ordinario
page-invoice-create-client-regime-flat = RF19 - Forfettario
page-invoice-create-client-create-button = Crea Cliente
page-invoice-create-client-name-required = Denominazione è obbligatoria
page-invoice-create-client-create-success = Cliente '{ $name }' creato con successo!
page-invoice-create-client-create-error = Errore nella creazione del cliente: { $error }

### Step 2: Invoice Details
page-invoice-create-step-2-header = 📝 Dettagli Fattura
page-invoice-create-details-client-selected = Cliente selezionato: **{ $name }**
page-invoice-create-details-regime = Regime fiscale: { $regime }
page-invoice-create-details-number-label = Numero Fattura
page-invoice-create-details-number-help = Numero progressivo della fattura
page-invoice-create-details-year-label = Anno
page-invoice-create-details-year-help = Anno fiscale della fattura
page-invoice-create-details-date-label = Data Emissione
page-invoice-create-details-date-help = Data di emissione della fattura
page-invoice-create-details-due-date-label = Data Scadenza
page-invoice-create-details-due-date-help = Data di scadenza del pagamento
page-invoice-create-details-additional-title = 📋 Dettagli aggiuntivi
page-invoice-create-details-subject-label = Oggetto/Descrizione
page-invoice-create-details-subject-placeholder = Descrizione generale della fattura...
page-invoice-create-details-subject-help = Descrizione generale dei servizi/prodotti fatturati
page-invoice-create-details-notes-label = Note
page-invoice-create-details-notes-placeholder = Eventuali note aggiuntive...
page-invoice-create-details-notes-help = Note interne o da mostrare in fattura

### Step 3: Invoice Lines
page-invoice-create-step-3-header = 🛒 Prodotti e Servizi
page-invoice-create-lines-title = Righe fattura
page-invoice-create-lines-description-label = Descrizione
page-invoice-create-lines-quantity-label = Quantità
page-invoice-create-lines-price-label = Prezzo Unitario (€)
page-invoice-create-lines-row-total = Totale riga: { $total }
page-invoice-create-lines-remove-button = 🗑️ Rimuovi
page-invoice-create-lines-add-title = ➕ Aggiungi nuova riga
page-invoice-create-lines-description-input-label = Descrizione *
page-invoice-create-lines-description-placeholder = Descrizione del prodotto/servizio...
page-invoice-create-lines-quantity-input-label = Quantità
page-invoice-create-lines-quantity-help = Quantità del prodotto/servizio
page-invoice-create-lines-price-input-label = Prezzo Unitario (€)
page-invoice-create-lines-price-help = Prezzo unitario IVA esclusa
page-invoice-create-lines-vat-label = Aliquota IVA
page-invoice-create-lines-vat-help = Aliquota IVA applicabile
page-invoice-create-lines-add-button = Aggiungi Riga
page-invoice-create-lines-description-required = Descrizione è obbligatoria
page-invoice-create-lines-add-success = Riga aggiunta!
page-invoice-create-lines-totals-title = 💰 Totali
page-invoice-create-lines-subtotal-label = Imponibile
page-invoice-create-lines-vat-amount-label = IVA
page-invoice-create-lines-total-label = Totale

### Step 4: AI Assistance
page-invoice-create-step-4-header = 🤖 Assistenza AI
page-invoice-create-ai-description-title = 📝 Genera Descrizioni con AI
page-invoice-create-ai-description-button = 🎯 Suggerisci descrizioni per le righe
page-invoice-create-ai-description-no-lines = Aggiungi prima delle righe alla fattura
page-invoice-create-ai-description-generating = Generando descrizioni...
page-invoice-create-ai-description-improved = Descrizione riga { $row } migliorata!
page-invoice-create-ai-description-error = Errore generazione descrizione riga { $row }: { $error }
page-invoice-create-ai-vat-title = 💼 Consigli IVA
page-invoice-create-ai-vat-button = 🧾 Verifica aliquote IVA
page-invoice-create-ai-vat-no-lines = Aggiungi prima delle righe alla fattura
page-invoice-create-ai-vat-checking = Verificando aliquote IVA...
page-invoice-create-ai-vat-suggestion = 💡 Riga { $row }: Suggerita aliquota IVA { $suggested }% invece di { $current }%
page-invoice-create-ai-vat-apply = Applica { $rate }% alla riga { $row }
page-invoice-create-ai-vat-updated = Aliquota IVA aggiornata!
page-invoice-create-ai-vat-info = Riga { $row }: { $info }
page-invoice-create-ai-vat-error = Errore verifica IVA riga { $row }: { $error }
page-invoice-create-ai-compliance-title = ⚖️ Controllo Conformità
page-invoice-create-ai-compliance-button = 🔍 Verifica conformità fattura
page-invoice-create-ai-compliance-no-number = Numero fattura mancante
page-invoice-create-ai-compliance-no-lines = Nessuna riga fattura presente
page-invoice-create-ai-compliance-line-no-desc = Riga { $row }: descrizione mancante
page-invoice-create-ai-compliance-line-qty-invalid = Riga { $row }: quantità deve essere > 0
page-invoice-create-ai-compliance-line-price-invalid = Riga { $row }: prezzo unitario deve essere > 0
page-invoice-create-ai-compliance-issues-found = Problemi trovati
page-invoice-create-ai-compliance-success = ✅ Fattura conforme ai requisiti di base!

### Step 5: Summary
page-invoice-create-step-5-header = ✅ Riepilogo e Creazione
page-invoice-create-summary-client-title = 👥 Cliente
page-invoice-create-summary-client-vat = P.IVA: { $vat }
page-invoice-create-summary-client-regime = Regime: { $regime }
page-invoice-create-summary-invoice-title = 📄 Fattura
page-invoice-create-summary-invoice-date = Emissione: { $date }
page-invoice-create-summary-invoice-due = Scadenza: { $date }
page-invoice-create-summary-lines-title = 🛒 Righe Fattura
page-invoice-create-summary-table-description = Descrizione
page-invoice-create-summary-table-quantity = Q.tà
page-invoice-create-summary-table-price = Prezzo
page-invoice-create-summary-table-vat = IVA
page-invoice-create-summary-table-total = Totale
page-invoice-create-summary-totals-title = 💰 Totali
page-invoice-create-summary-totals-subtotal = Imponibile
page-invoice-create-summary-totals-vat = IVA
page-invoice-create-summary-totals-total = Totale Fattura
page-invoice-create-summary-create-button = 🚀 Crea Fattura
page-invoice-create-summary-creating = Creando fattura...
page-invoice-create-summary-error-create-failed = Impossibile creare la fattura
page-invoice-create-summary-success = ✅ Fattura { $number }/{ $year } creata con successo!
page-invoice-create-summary-next-steps =
    **Prossimi passi:**
    1. **Valida** la fattura: `openfatture fattura valida { $number }`
    2. **Invia** alla SDI: `openfatture pec invia { $number }`
    3. **Monitora** lo stato nella pagina Fatture
page-invoice-create-summary-error = Errore nella creazione della fattura: { $error }

### Navigation
page-invoice-create-nav-back = ⬅️ Indietro
page-invoice-create-nav-next = Avanti ➡️
page-invoice-create-nav-success = 🎉 Fattura creata con successo!
page-invoice-create-nav-create-another = 🔄 Crea un'altra fattura

## ============================================================================
## CLIENTS PAGE (3_👥_Clienti.py)
## ============================================================================

page-clients-title = 👥 Gestione Clienti
page-clients-subtitle = Visualizza e gestisci i tuoi clienti

### Sidebar Filters
page-clients-filter-title = 🔍 Filtri
page-clients-filter-search = Cerca
page-clients-filter-search-placeholder = Denominazione, P.IVA, Codice Fiscale...
page-clients-filter-search-help = Cerca per denominazione, partita IVA o codice fiscale

### Actions
page-clients-action-new = ➕ Nuovo Cliente
page-clients-action-refresh = 🔄 Aggiorna
page-clients-action-view = Visualizza dettagli
page-clients-action-edit = Modifica
page-clients-action-delete = Elimina

### Add Client Form
page-clients-form-add-title = ➕ Nuovo Cliente
page-clients-form-denominazione = Denominazione *
page-clients-form-denominazione-placeholder = Nome azienda o persona
page-clients-form-piva = Partita IVA
page-clients-form-piva-placeholder = 12345678901
page-clients-form-cf = Codice Fiscale
page-clients-form-cf-placeholder = RSSMRA80A01H501U
page-clients-form-sdi = Codice SDI
page-clients-form-sdi-placeholder = ABC1234
page-clients-form-pec = PEC
page-clients-form-pec-placeholder = cliente@pec.it
page-clients-form-address = Indirizzo
page-clients-form-address-placeholder = Via Roma 123
page-clients-form-zip = CAP
page-clients-form-zip-placeholder = 00100
page-clients-form-phone = Telefono
page-clients-form-phone-placeholder = +39 123 456 7890
page-clients-form-city = Comune
page-clients-form-city-placeholder = Roma
page-clients-form-province = Provincia
page-clients-form-province-placeholder = RM
page-clients-form-email = Email
page-clients-form-email-placeholder = cliente@email.com
page-clients-form-notes = Note
page-clients-form-notes-placeholder = Note aggiuntive...
page-clients-form-save = 💾 Salva Cliente
page-clients-form-cancel = ❌ Annulla

### Statistics
page-clients-stats-title = 📊 Statistiche
page-clients-stats-total = Totale Clienti
page-clients-stats-with-pec = Con PEC
page-clients-stats-with-sdi = Con SDI
page-clients-stats-with-piva = Con P.IVA

### Client List
page-clients-list-title = 📋 Lista Clienti

### Table Columns
page-clients-table-col-id = ID
page-clients-table-col-denominazione = Denominazione
page-clients-table-col-piva = P.IVA
page-clients-table-col-cf = Codice Fiscale
page-clients-table-col-sdi = SDI
page-clients-table-col-pec = PEC
page-clients-table-col-comune = Comune
page-clients-table-col-provincia = Prov.
page-clients-table-col-created = Creato il
page-clients-table-col-actions = Azioni

### Empty State
page-clients-no-results = 🔍 Nessun cliente trovato per '{ $term }'
page-clients-empty-state = 📝 Nessun cliente presente. Crea il primo cliente!

### Quick Add Form
page-clients-quick-add-title = 🚀 Crea il primo cliente
page-clients-quick-add-description = Compila i dati essenziali:
page-clients-quick-add-pec-optional = PEC (opzionale)
page-clients-quick-add-button = ➕ Crea Cliente

### Client Detail
page-clients-detail-title = 👁️ Dettagli Cliente: { $name }
page-clients-detail-id = ID
page-clients-detail-denominazione = Denominazione
page-clients-detail-piva = P.IVA
page-clients-detail-cf = Codice Fiscale
page-clients-detail-sdi = SDI
page-clients-detail-pec = PEC
page-clients-detail-phone = Telefono
page-clients-detail-email = Email
page-clients-detail-address = Indirizzo
page-clients-detail-city = Città
page-clients-detail-notes = Note
page-clients-detail-na = N/A
page-clients-detail-close = ❌ Chiudi

### Edit Client
page-clients-edit-title = ✏️ Modifica Cliente: { $name }
page-clients-edit-save = 💾 Salva Modifiche

### Delete Client
page-clients-delete-title = 🗑️ Elimina Cliente: { $name }
page-clients-delete-confirm = ⚠️ Sei sicuro di voler eliminare il cliente '{ $name }'?
page-clients-delete-warning = Questa azione non può essere annullata.
page-clients-delete-yes = 🗑️ Sì, Elimina
page-clients-delete-no = ❌ Annulla

### Quick Preview
page-clients-preview-title = 📊 Anteprima Rapida
page-clients-preview-total = 👥 Totale Clienti
page-clients-preview-invoices = 📄 Totale Fatture
page-clients-preview-top5 = 👑 Top 5 Clienti
page-clients-preview-col-client = Cliente
page-clients-preview-col-invoices = N. Fatture
page-clients-preview-col-revenue = Fatturato Totale

### Success Messages
page-clients-success-created = ✅ Cliente '{ $name }' creato con successo!
page-clients-success-updated = ✅ Cliente '{ $name }' aggiornato!
page-clients-success-deleted = ✅ Cliente '{ $name }' eliminato!
page-clients-success-quick-created = ✅ Cliente '{ $name }' creato!

### Error Messages
page-clients-error-denominazione-required = La denominazione è obbligatoria
page-clients-error-create = ❌ Errore nella creazione del cliente: { $error }
page-clients-error-update = ❌ Errore nell'aggiornamento: { $error }
page-clients-error-delete = ❌ Errore nell'eliminazione: { $error }
page-clients-error-not-found = Cliente non trovato
page-clients-error-loading = ❌ Errore nel caricamento dei clienti: { $error }
page-clients-error-loading-hint = 💡 Verifica che il database sia inizializzato correttamente
page-clients-error-quick-create = ❌ Errore: { $error }
page-clients-preview-error = Errore caricamento dati: { $error }

### Legacy (kept for compatibility)
page-clients-search = Cerca clienti...
page-clients-filter-type = Tipo
page-clients-filter-country = Paese
page-clients-col-name = Nome/Ragione Sociale
page-clients-col-vat = Partita IVA
page-clients-col-email = Email
page-clients-col-phone = Telefono
page-clients-col-invoices = Fatture
page-clients-col-revenue = Fatturato
page-clients-col-actions = Azioni
page-clients-action-add = Aggiungi Cliente
page-clients-action-create-invoice = Crea Fattura
page-clients-no-clients = Nessun cliente trovato
page-clients-add-first = Aggiungi il tuo primo cliente
page-clients-total-found = { $count } clienti trovati

## ============================================================================
## PAYMENTS PAGE (4_💰_Pagamenti.py)
## ============================================================================

### Page Config
page-payments-page-title = Pagamenti - OpenFatture
page-payments-title = 💰 Tracking & Riconciliazione Pagamenti

### Sidebar Filters
page-payments-filter-title = 🔍 Filtri
page-payments-filter-bank-account = Conto Bancario
page-payments-filter-all-accounts = Tutti
page-payments-filter-status = Stato
page-payments-no-accounts-configured = Nessun conto bancario configurato

### Status Labels
page-payments-status-all = Tutti
page-payments-status-unmatched = Da Riconciliare
page-payments-status-matched = Riconciliati
page-payments-status-ignored = Ignorati
page-payments-status-paired = Abbinati

### Sidebar Actions
page-payments-action-import = 📥 Import
page-payments-action-import-help = Importa estratto conto
page-payments-action-refresh = 🔄 Aggiorna

### Import Form
page-payments-import-title = 📥 Importa Estratto Conto
page-payments-import-select-account = Seleziona conto bancario *
page-payments-import-select-account-help = Scegli il conto dove importare le transazioni
page-payments-import-no-account-error = Nessun conto bancario configurato. Creane uno prima di importare.
page-payments-import-file-label = Seleziona file estratto conto
page-payments-import-file-help = Supporta formati: OFX, QFX, CSV, QIF
page-payments-import-bank-preset = Banca (per CSV)
page-payments-import-bank-preset-help = Seleziona la banca per il parsing corretto del CSV
page-payments-import-auto-match = Auto-match pagamenti
page-payments-import-auto-match-help = Tenta automaticamente di abbinare le transazioni alle fatture
page-payments-import-confidence = Soglia confidenza
page-payments-import-confidence-help = Minima confidenza per auto-matching
page-payments-import-button = 🚀 Importa Transazioni
page-payments-import-error-no-account = Seleziona un conto bancario
page-payments-import-error-no-file = Seleziona un file da importare
page-payments-import-importing = Importando transazioni...
page-payments-import-metric-imported = Transazioni Importate
page-payments-import-metric-errors = Errori
page-payments-import-metric-duplicates = Duplicati
page-payments-import-format-detected = 📄 Formato rilevato: { $format }
page-payments-import-errors-title = ⚠️ Errori durante l'import
page-payments-import-success-refresh = 🔄 Dati aggiornati!
page-payments-import-close = ❌ Chiudi

### Bank Accounts Overview
page-payments-accounts-title = 🏦 Conti Bancari
page-payments-accounts-current-balance = Saldo Attuale
page-payments-accounts-iban = IBAN: ...{ $last4 }
page-payments-accounts-bank = Banca: { $name }

### Payment Statistics
page-payments-stats-title = 📊 Statistiche Pagamenti
page-payments-stats-accounts = Conti Bancari
page-payments-stats-transactions = Transazioni Totali
page-payments-stats-balance = Saldo Totale
page-payments-stats-reconciled = Riconciliati
page-payments-stats-distribution-title = 📈 Distribuzione per Stato
page-payments-stats-distribution-status = Stato
page-payments-stats-distribution-transactions = Transazioni

### Transactions List
page-payments-transactions-title = 📋 Transazioni
page-payments-table-col-id = ID
page-payments-table-col-date = Data
page-payments-table-col-amount = Importo
page-payments-table-col-description = Descrizione
page-payments-table-col-reference = Riferimento
page-payments-table-col-status = Stato
page-payments-table-col-invoice = Fattura
page-payments-table-col-actions = Azioni
page-payments-action-view-details = Visualizza dettagli
page-payments-action-match = Riconcilia
page-payments-transactions-summary = 📊 **Totale visualizzato:** { $total } su { $count } transazioni
page-payments-no-transactions-filtered = 🔍 Nessuna transazione trovata con i filtri selezionati
page-payments-no-transactions = 📭 Nessuna transazione presente

### Quick Start Guide
page-payments-quickstart-title = 🚀 Come iniziare con i pagamenti
page-payments-quickstart-content =
    ### Primi Passi

    1. **Aggiungi un conto bancario**
       ```bash
       uv run openfatture payment account add "Conto Business" --iban IT123...
       ```

    2. **Importa un estratto conto**
       ```bash
       uv run openfatture payment import estratto.ofx --account 1
       ```

    3. **Riconcilia automaticamente**
       ```bash
       uv run openfatture payment match --auto-apply
       ```

    4. **Verifica riconciliazioni**
       ```bash
       uv run openfatture payment status
       ```

### Error Messages
page-payments-error-loading = ❌ Errore nel caricamento dei pagamenti: { $error }
page-payments-error-loading-hint = 💡 Verifica che il database sia inizializzato correttamente

### Transaction Detail Modal
page-payments-detail-title = 👁️ Dettagli Transazione { $id }...
page-payments-detail-id = ID
page-payments-detail-date = Data
page-payments-detail-amount = Importo
page-payments-detail-description = Descrizione
page-payments-detail-reference = Riferimento
page-payments-detail-counterparty = Controparte
page-payments-detail-status = Stato
page-payments-detail-confidence = Confidenza Match
page-payments-detail-linked-invoice = Fattura Collegata
page-payments-detail-close = ❌ Chiudi
page-payments-detail-not-found = Transazione non trovata

### Match Transaction Modal
page-payments-match-title = 🔗 Riconcilia Transazione { $amount }
page-payments-match-date = Data
page-payments-match-amount = Importo
page-payments-match-description = Descrizione
page-payments-match-reference = Riferimento
page-payments-match-counterparty = Controparte
page-payments-match-status = Stato
page-payments-match-suggestions-title = 🎯 Abbinamenti Suggeriti
page-payments-match-client = Cliente: { $client }
page-payments-match-confidence = Confidenza
page-payments-match-days-diff = ±{ $days } giorni
page-payments-match-button = ✅ Abbina
page-payments-match-matching = Abbinando transazione...
page-payments-match-success = ✅ Transazione abbinata a fattura { $number }
page-payments-match-error = ❌ Errore: { $error }
page-payments-match-no-suggestions = 🔍 Nessun abbinamento automatico trovato
page-payments-match-manual-title = 🔍 Ricerca Manuale
page-payments-match-manual-search = Cerca fattura
page-payments-match-manual-placeholder = Numero fattura, cliente...
page-payments-match-manual-help = Inserisci numero fattura o nome cliente
page-payments-match-manual-results = Risultati ricerca:
page-payments-match-manual-button = Abbina
page-payments-match-manual-success = ✅ Abbinata!
page-payments-match-manual-no-results = Nessuna fattura trovata
page-payments-match-close = ❌ Chiudi

### Quick Stats Section
page-payments-quick-stats-title = ### 📊 Statistiche Pagamenti
page-payments-quick-stats-unmatched = 🔍 Non Abbinati
page-payments-quick-stats-matched = ✅ Abbinati
page-payments-quick-stats-ignored = ⏭️ Ignorati
page-payments-quick-stats-total = 📊 Totale
page-payments-quick-stats-error = Errore caricamento dati: { $error }

### Payment Due Section
page-payments-due-title = ### 💳 Scadenze Prossimi 30 Giorni
page-payments-due-col-invoice = Fattura
page-payments-due-col-client = Cliente
page-payments-due-col-due-date = Scadenza
page-payments-due-col-residual = Residuo
page-payments-due-col-status = Stato
page-payments-due-total-residual = 💸 Totale Residuo
page-payments-due-no-payments = ✅ Nessun pagamento in scadenza

### Legacy (kept for compatibility)
page-payments-tab-overview = Panoramica
page-payments-tab-reconciliation = Riconciliazione
page-payments-tab-history = Storico
page-payments-total-received = Incassato
page-payments-total-pending = Da Incassare
page-payments-total-overdue = Scaduto
page-payments-reconciliation-rate = Tasso Riconciliazione
page-payments-import-bank = Importa Estratto Conto
page-payments-match-automatic = Abbinamento Automatico
page-payments-match-manual = Abbinamento Manuale
page-payments-unmatched = Movimenti Non Abbinati
page-payments-matched = Movimenti Abbinati
page-payments-col-invoice = Fattura
page-payments-col-client = Cliente
page-payments-col-amount = Importo
page-payments-col-due-date = Scadenza
page-payments-col-paid-date = Data Pagamento
page-payments-col-status = Stato
page-payments-col-method = Metodo

## ============================================================================
## AI ASSISTANT PAGE (5_🤖_AI_Assistant.py)
## ============================================================================

### Page Config
page-ai-page-title = AI Assistant - OpenFatture
page-ai-title = 🤖 AI Assistant
page-ai-subtitle = Assistente Intelligente per Fatturazione e Fisco
page-ai-not-configured =
    ⚠️ **AI non configurato**

    Per abilitare l'AI Assistant:
    1. Configura le credenziali nel file `.env`
    2. Imposta `AI_PROVIDER` (openai/anthropic/ollama)
    3. Imposta `AI_API_KEY` (se necessario)
    4. Riavvia l'applicazione

    Consulta `docs/CONFIGURATION.md` per i dettagli.

### Tabs
page-ai-tab-chat = Chat Assistente
page-ai-tab-description = Genera Descrizione
page-ai-tab-vat = Suggerimento IVA
page-ai-tab-voice = Voice Chat

### General
page-ai-yes = ✓ SI
page-ai-no = ✗ NO

### Retry Logic
page-ai-retry-message = 🔄 Tentativo { $attempt }/{ $max_retries } fallito. Riprovo tra { $delay }s...

### Error Messages
page-ai-error-connection = 🌐 Errore di connessione. Verifica la tua connessione internet e riprova.
page-ai-error-auth = 🔐 Errore di autenticazione. Verifica le tue credenziali AI.
page-ai-error-rate-limit = ⏱️ Limite di richieste raggiunto. Riprova tra qualche minuto.
page-ai-error-service-unavailable = 🚫 Servizio temporaneamente non disponibile. Riprova più tardi.
page-ai-error-generic = ❌ Errore imprevisto: { $error }...
page-ai-error-hint-connection = 💡 Suggerimento: Controlla la tua connessione internet
page-ai-error-hint-auth = 💡 Suggerimento: Verifica le impostazioni AI nelle preferenze

### Slash Commands
page-ai-command-help-feedback =
    **🤖 Comandi Disponibili:**

    **Built-in:**
    - `/help` - Mostra questo messaggio
    - `/tools` - Lista strumenti AI disponibili
    - `/stats` - Statistiche conversazione corrente
    - `/custom` - Lista comandi personalizzati
    - `/reload` - Ricarica comandi da disco
    - `/clear` - Cancella cronologia chat

    **Personalizzati:**
    Crea comandi in `~/.openfatture/commands/*.yaml`

    **Esempi:**
    - "Come creo una fattura?"
    - "Qual è l'aliquota IVA per il web design?"
    - "Mostra le fatture di questo mese"

page-ai-command-tools-feedback =
    **🔧 Strumenti AI Disponibili:**

    **Ricerca e Consultazione:**
    - Ricerca fatture per cliente, data, importo
    - Statistiche fatturato e pagamenti
    - Consultazione normativa fiscale

    **Azioni Disponibili:**
    - Creazione descrizioni fatture professionali
    - Suggerimento aliquote IVA corrette
    - Analisi compliance fatturazione

    **Integrazione Dati:**
    - Accesso database clienti e prodotti
    - Cronologia pagamenti e scadenze
    - Report e analytics business

page-ai-command-stats-feedback =
    **📊 Statistiche Conversazione:**

    - **Messaggi totali:** { $total_messages }
    - **Tuoi messaggi:** { $user_messages }
    - **Risposte AI:** { $assistant_messages }
    - **Caratteri totali:** { NUMBER($total_chars) }
    - **Token stimati:** { NUMBER($estimated_tokens) }

    **💡 Suggerimenti:**
    - Usa `/clear` per ricominciare da capo
    - Salva conversazioni importanti con 💾 Salva

page-ai-command-custom-no-commands = 📝 **Nessun comando personalizzato trovato**\n\nCrea comandi in `~/.openfatture/commands/*.yaml`
page-ai-command-custom-header = 📝 **Comandi Personalizzati ({ $count }):**
page-ai-command-custom-footer = 💡 Usa `/help` per vedere tutti i comandi
page-ai-command-reload-success = 🔄 **Comandi ricaricati:** { $old_count } → { $new_count } ({ $added } aggiunti, { $removed } rimossi)
page-ai-command-reload-error = ❌ **Errore ricarica:** { $error }
page-ai-command-clear-feedback = 🗑️ **Cronologia cancellata**\n\nLa conversazione è stata azzerata.
page-ai-command-custom-expanded = 🔧 **Comando espanso:** `/{ $command }` → { $length } caratteri
page-ai-command-custom-error = ❌ **Errore comando:** { $error }
page-ai-command-unknown = ❓ **Comando sconosciuto:** `{ $command }`\n\nUsa `/help` per vedere i comandi disponibili

### Tab 1: Chat Assistant
page-ai-chat-title = Chat Interattivo
page-ai-chat-description =
    Chatta con l'assistente AI per:
    - Domande su fatturazione e normativa
    - Consigli fiscali e IVA
    - Gestione pagamenti e scadenze
    - Consulenza generale business

page-ai-chat-save = Salva
page-ai-chat-save-help = Salva conversazione
page-ai-chat-session-title = Chat { $count } messaggi
page-ai-chat-saved = ✅ Salvata: { $session_id }...
page-ai-chat-save-error = ❌ Errore salvataggio
page-ai-chat-reload = Reload
page-ai-chat-reload-help = Ricarica comandi personalizzati
page-ai-chat-reloaded = ✅ Ricaricati: { $count } comandi
page-ai-chat-clear = Cancella

### Chat File Upload
page-ai-chat-file-upload-title = 📎 Allega File (Opzionale)
page-ai-chat-file-upload-label = Carica un documento per discuterne con l'AI
page-ai-chat-file-upload-help = Supporta PDF, testo, immagini e altri documenti
page-ai-chat-file-uploaded = 📄 File caricato: { $name } ({ $size } bytes)
page-ai-chat-files-attached = File Allegati
page-ai-chat-files-clear-all = Cancella Tutti
page-ai-chat-files-cleared = File cancellati!

### Chat File Types
page-ai-chat-file-text-preview = - **{ $name }** (testo): { $preview }
page-ai-chat-file-text = - **{ $name }** (testo, { $size } bytes)
page-ai-chat-file-pdf = - **{ $name }** (PDF, { $size } bytes) - Contenuto da analizzare
page-ai-chat-file-image = - **{ $name }** (immagine { $format }, { $size } bytes) - Testo da estrarre via OCR
page-ai-chat-file-other = - **{ $name }** ({ $type }, { $size } bytes)
page-ai-chat-file-analysis-hint = L'AI analizzerà questi file per fornire una risposta più precisa.

### Custom Commands
page-ai-chat-custom-commands-title = 📝 Comandi Personalizzati
page-ai-chat-custom-commands-empty = Nessun comando personalizzato trovato. Crea comandi in `~/.openfatture/commands/*.yaml`
page-ai-chat-custom-commands-count = **{ $count } comandi disponibili:**
page-ai-chat-custom-commands-description = **Descrizione:** { $desc }
page-ai-chat-custom-commands-examples = Esempi
page-ai-chat-custom-commands-author = **Autore:** { $author }
page-ai-chat-custom-commands-version = **Versione:** { $version }

### Chat Sessions
page-ai-chat-sessions-title = 💾 Sessioni Salvate
page-ai-chat-sessions-empty = Nessuna sessione salvata. Usa il pulsante 💾 Salva per salvare la conversazione corrente.
page-ai-chat-sessions-count = **{ $count } sessioni disponibili:**
page-ai-chat-sessions-load = Carica
page-ai-chat-sessions-loaded = ✅ Caricata sessione: { $title }
page-ai-chat-sessions-load-error-empty = ❌ Sessione vuota o corrotta
page-ai-chat-sessions-load-error = ❌ Errore caricamento: { $error }
page-ai-chat-sessions-rename = Rinomina
page-ai-chat-sessions-rename-todo = Funzionalità rinomina da implementare
page-ai-chat-sessions-delete = Elimina
page-ai-chat-sessions-deleted = ✅ Sessione eliminata
page-ai-chat-sessions-delete-error = ❌ Errore eliminazione

### Chat Input & Messages
page-ai-chat-input-placeholder = Scrivi il tuo messaggio o usa /comando...
page-ai-chat-attachments = Allegati
page-ai-chat-thinking = Pensando...

### Chat Feedback
page-ai-chat-feedback-good = Buono
page-ai-chat-feedback-good-comment = Buona risposta
page-ai-chat-feedback-bad = Scarso
page-ai-chat-feedback-bad-comment = Risposta insoddisfacente
page-ai-chat-feedback-comment = Commento
page-ai-chat-feedback-comment-label = Lascia un commento sulla risposta:
page-ai-chat-feedback-submit = Invia Commento
page-ai-chat-feedback-comment-sent = ✅ Commento inviato!
page-ai-chat-feedback-comment-empty = Inserisci un commento
page-ai-chat-feedback-thanks = ✅ Grazie per il feedback!
page-ai-chat-feedback-error = ❌ Errore nell'invio del feedback

### Tab 2: Description Generator
page-ai-desc-title = Genera Descrizione Fattura
page-ai-desc-description =
    Genera descrizioni professionali per le tue fatture usando l'AI.
    Fornisci informazioni sul servizio e ottieni una descrizione dettagliata.

page-ai-desc-service-label = Servizio Fornito *
page-ai-desc-service-placeholder = es. Consulenza sviluppo web app e-commerce
page-ai-desc-service-help = Descrivi brevemente il servizio/prodotto
page-ai-desc-hours-label = Ore Lavorate
page-ai-desc-hours-help = Numero ore (opzionale)
page-ai-desc-project-label = Nome Progetto
page-ai-desc-project-placeholder = es. Progetto E-Commerce XYZ
page-ai-desc-project-help = Nome del progetto (opzionale)
page-ai-desc-rate-label = Tariffa Oraria (€)
page-ai-desc-rate-help = Tariffa oraria in euro (opzionale)
page-ai-desc-tech-label = Tecnologie
page-ai-desc-tech-placeholder = Python, FastAPI, PostgreSQL
page-ai-desc-tech-help = Tecnologie usate, separate da virgola (opzionale)
page-ai-desc-generate = Genera Descrizione
page-ai-desc-error-empty = ⚠️ Inserisci una descrizione del servizio
page-ai-desc-generating = 🤖 Generando descrizione professionale...
page-ai-desc-success = ✅ Descrizione generata con successo!
page-ai-desc-result-title = Descrizione Professionale
page-ai-desc-deliverables = Deliverables
page-ai-desc-skills = Competenze Tecniche
page-ai-desc-duration = **⏱️ Durata:** { $hours } ore
page-ai-desc-notes = **📌 Note:** { $notes }
page-ai-desc-result-generated = Descrizione Generata

### Tab 3: VAT Suggestion
page-ai-vat-title = Suggerimento Aliquota IVA
page-ai-vat-description =
    Ottieni suggerimenti AI sull'aliquota IVA corretta e il trattamento fiscale
    in base al tipo di servizio/prodotto e al cliente.

page-ai-vat-service-label = Descrizione Servizio/Prodotto *
page-ai-vat-service-placeholder = es. Consulenza informatica per sviluppo software gestionale
page-ai-vat-service-help = Descrivi il servizio o prodotto da fatturare
page-ai-vat-client-pa-label = Cliente è Pubblica Amministrazione
page-ai-vat-client-pa-help = Spunta se il cliente è PA
page-ai-vat-amount-label = Importo (€)
page-ai-vat-amount-help = Importo in euro (opzionale)
page-ai-vat-client-foreign-label = Cliente Estero
page-ai-vat-client-foreign-help = Spunta se il cliente non è residente in Italia
page-ai-vat-country-label = Paese Cliente
page-ai-vat-country-placeholder = IT, FR, US...
page-ai-vat-country-help = Codice ISO paese a 2 lettere
page-ai-vat-category-label = Categoria Servizio
page-ai-vat-category-help = Categoria del servizio (opzionale)
page-ai-vat-category-consulting = Consulenza
page-ai-vat-category-software = Sviluppo Software
page-ai-vat-category-training = Formazione
page-ai-vat-category-design = Design/Grafica
page-ai-vat-category-marketing = Marketing
page-ai-vat-category-maintenance = Manutenzione
page-ai-vat-category-other = Altro
page-ai-vat-suggest = Ottieni Suggerimento IVA
page-ai-vat-error-empty = ⚠️ Inserisci una descrizione del servizio/prodotto
page-ai-vat-analyzing = 🤖 Analizzando trattamento fiscale...
page-ai-vat-success = ✅ Analisi completata!
page-ai-vat-treatment-title = Trattamento Fiscale
page-ai-vat-rate-metric = Aliquota IVA
page-ai-vat-reverse-charge-metric = Reverse Charge
page-ai-vat-confidence-metric = Confidence
page-ai-vat-nature-code = **Codice Natura IVA:** { $code }
page-ai-vat-split-payment = ⚠️ **Split Payment** applicabile
page-ai-vat-special-regime = **Regime Speciale:** { $regime }
page-ai-vat-explanation-title = Spiegazione
page-ai-vat-legal-reference-title = Riferimento Normativo
page-ai-vat-invoice-note-title = Nota per Fattura
page-ai-vat-recommendations-title = Raccomandazioni
page-ai-vat-suggestion-title = Suggerimento
page-ai-vat-error = ❌ Errore: { $error }
page-ai-vat-error-generic = ❌ Errore durante analisi: { $error }

### Tab 4: Voice Chat
page-ai-voice-title = Chat Vocale con AI
page-ai-voice-not-configured =
    ⚠️ **Voice Chat non configurato**

    Per abilitare il Voice Chat:
    1. Configura `OPENAI_API_KEY` nel file `.env`
    2. Imposta `OPENFATTURE_VOICE_ENABLED=true`
    3. Riavvia l'applicazione

    Consulta la documentazione per i dettagli.

page-ai-voice-description =
    Parla con l'assistente AI usando la tua voce:
    - 🎤 Registra la tua domanda
    - 🤖 L'AI la trascrive e risponde
    - 🔊 Ascolta la risposta vocale
    - 💬 Supporta conversazioni con contesto

### Voice Configuration
page-ai-voice-config-title = ⚙️ Configurazione Voice
page-ai-voice-config-provider = Provider
page-ai-voice-config-stt = STT Model
page-ai-voice-config-tts-voice = TTS Voice
page-ai-voice-config-tts-model = **TTS Model:** { $model }
page-ai-voice-config-tts-speed = **TTS Speed:** { $speed }x
page-ai-voice-config-tts-format = **TTS Format:** { $format }
page-ai-voice-config-streaming = **Streaming:** { $enabled }

### Voice History
page-ai-voice-clear = Cancella Voice
page-ai-voice-history-title = Cronologia Conversazione
page-ai-voice-user-message = **Tu:** { $text }
page-ai-voice-assistant-message = **Assistente:** { $text }
page-ai-voice-language-detected = Lingua rilevata: { $lang }
page-ai-voice-language = Lingua: { $lang }
page-ai-voice-metric-stt = STT: { $ms }ms
page-ai-voice-metric-llm = LLM: { $ms }ms
page-ai-voice-metric-tts = TTS: { $ms }ms
page-ai-voice-metric-total = Totale: { $ms }ms
page-ai-voice-metric-total-label = Totale
page-ai-voice-history-empty = 👋 Nessuna conversazione vocale ancora. Registra la tua prima domanda!

### Voice Input
page-ai-voice-record-title = Registra la tua voce
page-ai-voice-record-label = Premi il pulsante per registrare
page-ai-voice-record-help = Parla chiaramente nel microfono. La registrazione si ferma automaticamente dopo il silenzio.
page-ai-voice-recorded = ✅ Audio registrato: { $size } bytes
page-ai-voice-process = Invia e Processa
page-ai-voice-processing = 🤖 Processando il tuo messaggio vocale...
page-ai-voice-success = ✅ Messaggio vocale processato con successo!
page-ai-voice-transcription-title = Trascrizione
page-ai-voice-response-title = Risposta AI
page-ai-voice-audio-response-title = Risposta Vocale
page-ai-voice-metrics-title = Metriche
page-ai-voice-tech-details = ℹ️ Dettagli Tecnici
page-ai-voice-error = ❌ Errore durante il processamento: { $error }
page-ai-voice-error-hint-connection = 💡 Suggerimento: Verifica la tua connessione internet
page-ai-voice-error-hint-auth = 💡 Suggerimento: Verifica le impostazioni API nelle configurazioni
page-ai-voice-error-hint-rate = 💡 Suggerimento: Limite di richieste raggiunto. Riprova tra qualche minuto

### Voice Help
page-ai-voice-help-title = ❓ Come funziona
page-ai-voice-help-content =
    **Workflow Voice Chat:**

    1. **🎤 Registrazione**: Premi il pulsante e parla nel microfono
    2. **📝 Trascrizione (STT)**: OpenAI Whisper converte la voce in testo
    3. **🤖 Elaborazione (LLM)**: L'AI comprende e genera una risposta
    4. **🔊 Sintesi (TTS)**: OpenAI TTS converte la risposta in audio
    5. **▶️ Riproduzione**: Ascolta la risposta vocale

    **Supporto Lingue:**
    - Rilevamento automatico tra 100+ lingue
    - Italiano, Inglese, Francese, Tedesco, Spagnolo e molte altre

    **Costi Stimati:**
    - STT (Whisper): ~$0.006 per minuto di audio
    - TTS: ~$0.015 per 1.000 caratteri (tts-1) o ~$0.030 (tts-1-hd)
    - LLM: Prezzo standard del modello configurato

    **Requisiti:**
    - Microfono funzionante
    - Browser moderno (Chrome, Firefox, Safari, Edge)
    - Connessione internet stabile

### Metrics (shared across tabs)
page-ai-metric-provider = Provider
page-ai-metric-tokens = Tokens
page-ai-metric-cost = Costo

### Footer
page-ai-footer-disclaimer =
    **💡 Suggerimento:** L'AI Assistant è uno strumento di supporto. Le informazioni fornite
    dovrebbero essere sempre verificate con un commercialista o consulente fiscale per garantire
    la conformità alle normative vigenti.

## ============================================================================
## SETTINGS PAGE (6_⚙️_Impostazioni.py)
## ============================================================================

### Page Config
page-settings-page-title = Impostazioni - OpenFatture
page-settings-title = ⚙️ Impostazioni & Configurazione
page-settings-not-configured = Non configurato

### Company Section
page-settings-company-title = 🏢 Dati Azienda
page-settings-company-name = Denominazione
page-settings-company-vat = Partita IVA
page-settings-company-fiscal-code = Codice Fiscale
page-settings-company-regime = Regime Fiscale
page-settings-company-address = Indirizzo
page-settings-company-zip-city = CAP - Comune

### PEC Section
page-settings-pec-title = 📧 Configurazione PEC (SDI)
page-settings-pec-address = PEC Address
page-settings-pec-smtp-server = SMTP Server
page-settings-pec-from = PEC From
page-settings-pec-smtp-port = SMTP Port

### AI Section
page-settings-ai-title = 🤖 Configurazione AI
page-settings-ai-enabled = ✅ AI Abilitato
page-settings-ai-not-configured = ⚠️ AI Non Configurato
page-settings-ai-provider = Provider
page-settings-ai-model = Model

### Database Section
page-settings-database-title = 💾 Database
page-settings-database-url = Database URL

### Paths Section
page-settings-paths-title = 📁 Percorsi
page-settings-paths-data-dir = Data Directory
page-settings-paths-archivio-dir = Archivio Directory

### Configuration Guide
page-settings-guide-title = 📖 Guida Configurazione
page-settings-guide-content =
    **Modificare la configurazione:**

    1. Edita il file `.env` nella root del progetto
    2. Usa `.env.example` come template
    3. Riavvia l'applicazione per applicare le modifiche

    **Documentazione completa:**
    - `docs/CONFIGURATION.md` - Reference completo variabili
    - `docs/QUICKSTART.md` - Setup iniziale
    - `.env.example` - Template configurazione

### Quick Links
page-settings-links-title = 🔗 Link Utili
page-settings-link-docs = 📚 Documentazione
page-settings-link-bug = 🐛 Report Bug
page-settings-link-discussions = 💬 Discussions

### System Info
page-settings-system-title = ℹ️ Informazioni Sistema
page-settings-system-python = Python Version
page-settings-system-platform = Platform
page-settings-system-version = App Version

## ============================================================================
## LIGHTNING PAGE (7_⚡_Lightning.py)
## ============================================================================

page-lightning-page-title = Lightning - OpenFatture
page-lightning-title = ⚡ Lightning Network Pagamenti
page-lightning-not-enabled =
    ⚠️ **Lightning Network non abilitato**

    Per utilizzare i pagamenti Lightning:

    1. Abilita Lightning nelle impostazioni:
       ```bash
       uv run openfatture config set lightning_enabled true
       ```

    2. Configura la connessione LND:
       ```bash
       uv run openfatture config set lightning_host "localhost:10009"
       uv run openfatture config set lightning_cert_path "/path/to/tls.cert"
       uv run openfatture config set lightning_macaroon_path "/path/to/admin.macaroon"
       ```

    3. Riavvia l'applicazione

page-lightning-invoices-title = 📋 Gestione Fatture Lightning
page-lightning-invoices-info =
    **🚧 Feature in sviluppo**

    La gestione fatture Lightning via Web UI sarà disponibile a breve!

    Per ora, crea fatture Lightning tramite CLI:

    ```bash
    # Crea fattura da fattura esistente
    uv run openfatture lightning invoice create --fattura-id 123

    # Crea fattura zero-amount
    uv run openfatture lightning invoice create --amount 0 --description "Donazione"

    # Lista fatture Lightning
    uv run openfatture lightning invoice list
    ```

page-lightning-channels-title = 📊 Stato Canali
page-lightning-channels-info =
    **Monitoraggio Canali**

    ```bash
    # Stato canali
    uv run openfatture lightning channels status

    # Report liquidità
    uv run openfatture lightning liquidity report

    # Monitoraggio automatico
    uv run openfatture lightning liquidity monitor --start
    ```

page-lightning-recent-title = 🕒 Fatture Lightning Recenti
page-lightning-recent-info = Le fatture Lightning recenti verranno mostrate qui una volta implementata l'integrazione completa.
page-lightning-status-title = 🔗 Stato Canali Lightning
page-lightning-metric-active = Canali Attivi
page-lightning-metric-active-help = Canali Lightning attivi
page-lightning-metric-capacity = Capacità Totale
page-lightning-metric-capacity-help = Capacità totale canali
page-lightning-metric-inbound = Liquidità Inbound
page-lightning-metric-inbound-help = Percentuale liquidità inbound
page-lightning-technical-notes =
    **Note tecniche:**

    - **LND**: Lightning Network Daemon connection required
    - **Rate Provider**: BTC/EUR conversion via CoinGecko/CoinMarketCap
    - **Sicurezza**: TLS + Macaroon authentication
    - **Webhook**: Real-time payment notifications support

page-lightning-config-title = ⚙️ Configurazione Lightning
page-lightning-config-info =
    **Modifica configurazione:**

    ```bash
    uv run openfatture config set lightning_host "your-lnd-host:10009"
    uv run openfatture config set lightning_cert_path "/path/to/tls.cert"
    uv run openfatture config set lightning_macaroon_path "/path/to/admin.macaroon"
    ```

## ============================================================================
## BATCH PAGE (8_📦_Batch.py)
## ============================================================================

page-batch-page-title = Batch Operations - OpenFatture
page-batch-title = 📦 Operazioni Batch
page-batch-subtitle = Import/Export massivi di dati
page-batch-tab-import = 📥 Import
page-batch-tab-export = 📤 Export
page-batch-tab-history = 📋 Cronologia

### Import Tab
page-batch-import-title = 📥 Import Dati
page-batch-import-type-label = Tipo di dati da importare:
page-batch-import-type-clients = Clienti
page-batch-import-type-invoices = Fatture
page-batch-import-type-help = Seleziona il tipo di dati da importare
page-batch-import-upload-label = Carica file CSV per { $type }
page-batch-import-upload-help = Il file CSV deve contenere i dati dei { $type }
page-batch-import-valid-file = ✅ File valido! { $count } righe rilevate
page-batch-import-preview = 👁️ Anteprima dati
page-batch-import-validate-only = 🔍 Convalida Solo
page-batch-import-validate-complete = ✅ Convalida completata senza errori
page-batch-import-validate-errors = ❌ Errori di convalida:
page-batch-import-button = 📥 Importa { $type }
page-batch-import-importing = Importando { $type }...
page-batch-import-success = ✅ Import completato con successo!
page-batch-import-metric-processed = Processati
page-batch-import-metric-created = Creati
page-batch-import-metric-updated = Aggiornati
page-batch-import-minor-errors = ⚠️ Errori minori
page-batch-import-failed = ❌ Import fallito
page-batch-import-invalid-file = ❌ File CSV non valido:
page-batch-import-template-title = 📋 Template CSV
page-batch-import-template-clients = 📥 Scarica Template Clienti
page-batch-import-template-invoices = 📥 Scarica Template Fatture
page-batch-import-download-csv = Scarica CSV

### Export Tab
page-batch-export-title = 📤 Export Dati
page-batch-export-type-label = Tipo di dati da esportare:
page-batch-export-year-label = Anno (opzionale)
page-batch-export-year-all = Tutti
page-batch-export-include-lines = Includi righe fattura
page-batch-export-include-lines-help = Esporta ogni riga fattura separatamente
page-batch-export-button = 📤 Esporta { $type }
page-batch-export-exporting = Esportando { $type }...
page-batch-export-success = ✅ Export completato!
page-batch-export-preview = 👁️ Anteprima
page-batch-export-download = 📥 Scarica { $type }.csv
page-batch-export-failed = ❌ Export fallito: { $error }

### History Tab
page-batch-history-title = 📋 Cronologia Operazioni Batch
page-batch-history-operation = { $operation }
page-batch-history-records = 📊 { $count } record
page-batch-history-status-success = ✅ Successo
page-batch-history-status-partial = ⚠️ Parziale
page-batch-history-status-failed = ❌ Fallito
page-batch-history-details = 👁️
page-batch-history-details-title = Dettagli operazione:
page-batch-history-empty = 📭 Nessuna operazione batch registrata
page-batch-history-cli-title = 💡 Operazioni Batch Avanzate
page-batch-history-cli-info =
    Per operazioni batch avanzate, utilizza la CLI:

    **Import:**
    ```bash
    # Import clienti
    uv run openfatture batch import-clients clienti.csv

    # Import fatture
    uv run openfatture batch import-invoices fatture.csv
    ```

    **Export:**
    ```bash
    # Export fatture per anno
    uv run openfatture batch export-invoices --year 2024

    # Export clienti
    uv run openfatture batch export-clients
    ```

    **Validazione:**
    ```bash
    # Valida fatture senza salvare
    uv run openfatture batch validate-invoices fatture.csv
    ```

page-batch-footer-tip = 💡 <strong>Suggerimento:</strong> Per operazioni batch molto grandi, usa la CLI per prestazioni ottimali

## ============================================================================
## REPORTS PAGE (9_📊_Reports.py)
## ============================================================================

page-reports-page-title = Reports - OpenFatture
page-reports-title = 📊 Reports & Analytics
page-reports-subtitle = Report aziendali e analisi avanzate
page-reports-no-data = ⚠️ Nessun dato disponibile per i report
page-reports-no-data-info = Crea alcune fatture per vedere i report

### Sidebar
page-reports-filter-title = 🔍 Parametri Report
page-reports-filter-year = Anno
page-reports-filter-quarter = Trimestre (opzionale)
page-reports-filter-quarter-all = Tutti
page-reports-filter-quarter-q1 = Q1
page-reports-filter-quarter-q2 = Q2
page-reports-filter-quarter-q3 = Q3
page-reports-filter-quarter-q4 = Q4

### Tabs
page-reports-tab-revenue = 💰 Fatturato
page-reports-tab-vat = 📋 IVA
page-reports-tab-clients = 👥 Clienti

### Revenue Tab
page-reports-revenue-title = 💰 Report Fatturato
page-reports-revenue-total = Fatturato Totale
page-reports-revenue-total-help = Periodo: { $period }
page-reports-revenue-vat-total = IVA Totale
page-reports-revenue-invoices = Fatture Emesse
page-reports-revenue-avg = Valore Medio Fattura
page-reports-revenue-monthly = 📈 Andamento Mensile
page-reports-revenue-chart-title = Fatturato Mensile
page-reports-revenue-chart-xaxis = Mese
page-reports-revenue-chart-yaxis = Fatturato (€)
page-reports-revenue-count-chart = Numero Fatture Mensili
page-reports-revenue-count-yaxis = Numero Fatture

### VAT Tab
page-reports-vat-title = 📋 Report IVA
page-reports-vat-taxable = Imponibile Totale
page-reports-vat-total = IVA Totale
page-reports-vat-revenue-total = Fatturato Totale
page-reports-vat-breakdown-title = 📊 Ripartizione per Aliquota IVA
page-reports-vat-pie-title = Riparto Imponibile per Aliquota IVA
page-reports-vat-detail-title = 📋 Dettaglio per Aliquota
page-reports-vat-table-rate = Aliquota IVA
page-reports-vat-table-taxable = Imponibile
page-reports-vat-table-vat = IVA
page-reports-vat-table-total = Totale

### Clients Tab
page-reports-clients-title = 👥 Report Clienti
page-reports-clients-active = Clienti Attivi
page-reports-clients-active-help = Clienti con fatture emesse nel { $year }
page-reports-clients-top-title = 🏆 Top Clienti per Fatturato
page-reports-clients-table-client = Cliente
page-reports-clients-table-invoices = Fatture
page-reports-clients-table-total = Totale
page-reports-clients-table-last = Ultima Fattura
page-reports-clients-chart-title = Top 10 Clienti per Fatturato
page-reports-clients-chart-xaxis = Cliente
page-reports-clients-chart-yaxis = Fatturato (€)

### Export
page-reports-export-title = 📤 Export Report
page-reports-export-revenue = 📊 Export Fatturato (CSV)
page-reports-export-vat = 📋 Export IVA (CSV)
page-reports-export-clients = 👥 Export Clienti (CSV)
page-reports-export-download = Scarica CSV

page-reports-footer = 📊 <strong>Report aggiornati automaticamente</strong> • Dati basati su fatture consegnate o accettate

## ============================================================================
## HOOKS PAGE (10_🪝_Hooks.py)
## ============================================================================

page-hooks-page-title = Hooks & Automation - OpenFatture
page-hooks-title = 🪝 Hooks & Automation
page-hooks-subtitle = Gestione workflow automatizzati e trigger

### Summary Metrics
page-hooks-metric-total = Hooks Totali
page-hooks-metric-enabled = Hooks Attivi
page-hooks-metric-pre = Pre-hooks
page-hooks-metric-post = Post-hooks

### Tabs
page-hooks-tab-overview = 📊 Panoramica
page-hooks-tab-manage = ⚙️ Gestione
page-hooks-tab-create = ➕ Crea Hook
page-hooks-tab-test = 🧪 Test

### Overview Tab
page-hooks-overview-title = 📊 Panoramica Hooks
page-hooks-overview-group-pre = 🎯
page-hooks-overview-group-post = ✅
page-hooks-overview-group-on = 👀
page-hooks-overview-status-active = ✅ Attivo
page-hooks-overview-status-inactive = ⏸️ Disattivo
page-hooks-overview-timeout = ⏱️ { $timeout }s
page-hooks-overview-empty = 🎣 Nessun hook trovato. Crea il tuo primo hook nella tab 'Crea Hook'!

### Manage Tab
page-hooks-manage-title = ⚙️ Gestione Hooks
page-hooks-manage-toggle-title = Toggle Stato Hooks
page-hooks-manage-toggle-label = Attiva { $name }
page-hooks-manage-toggle-help = Abilita/disabilita l'hook { $name }
page-hooks-manage-toggle-enabled = ✅ Hook '{ $name }' attivato
page-hooks-manage-toggle-disabled = ⏸️ Hook '{ $name }' disattivato
page-hooks-manage-toggle-error = ❌ Errore nell'aggiornamento dello stato del hook
page-hooks-manage-details-button = 👁️ Dettagli
page-hooks-manage-details-help = Mostra dettagli hook
page-hooks-manage-details-title = Dettagli { $name }
page-hooks-manage-empty = 🎣 Nessun hook da gestire

### Create Tab
page-hooks-create-title = ➕ Crea Nuovo Hook
page-hooks-create-name-label = Nome Hook
page-hooks-create-name-placeholder = es: post-invoice-send
page-hooks-create-name-help = Nome del hook (usa prefissi pre-, post-, on-)
page-hooks-create-type-label = Tipo Script
page-hooks-create-type-help = Tipo di script per l'hook
page-hooks-create-type-bash = bash
page-hooks-create-type-python = python
page-hooks-create-desc-label = Descrizione
page-hooks-create-desc-placeholder = Cosa fa questo hook...
page-hooks-create-desc-help = Breve descrizione del hook
page-hooks-create-event-label = Tipo Evento
page-hooks-create-event-help = Quando viene eseguito l'hook
page-hooks-create-event-pre = pre
page-hooks-create-event-post = post
page-hooks-create-event-on = on
page-hooks-create-preview-title = 📋 Anteprima Template
page-hooks-create-preview-code = 👁️ Codice Template
page-hooks-create-button = 🚀 Crea Hook
page-hooks-create-error-name = ❌ Inserisci un nome per l'hook
page-hooks-create-warning-prefix = 💡 Suggerimento: il nome dovrebbe iniziare con '{ $prefix }-'
page-hooks-create-success = ✅ { $message }
page-hooks-create-reload = 🔄 Ricarica la pagina per vedere il nuovo hook
page-hooks-create-error = ❌ { $message }

### Test Tab
page-hooks-test-title = 🧪 Test Hooks
page-hooks-test-select-label = Seleziona Hook da Testare
page-hooks-test-select-help = Scegli l'hook da validare
page-hooks-test-info-title = 📋 Informazioni Hook
page-hooks-test-metric-type = Tipo Evento
page-hooks-test-metric-status = Stato
page-hooks-test-metric-timeout = Timeout
page-hooks-test-metric-status-active = Attivo
page-hooks-test-metric-status-inactive = Disattivo
page-hooks-test-validate-button = 🧪 Valida Hook
page-hooks-test-validating = Validando hook...
page-hooks-test-success = ✅ Hook validato con successo!
page-hooks-test-metric-lines = Righe Codice
page-hooks-test-metric-size = Dimensione
page-hooks-test-metric-size-value = { $size } bytes
page-hooks-test-metric-executable = Eseguibile
page-hooks-test-metric-executable-yes = Sì
page-hooks-test-metric-executable-no = No
page-hooks-test-result-message = 💡 { $message }
page-hooks-test-error = ❌ Errore validazione: { $error }
page-hooks-test-show-code = 📄 Mostra Codice
page-hooks-test-code-error = ❌ File hook non trovato
page-hooks-test-read-error = ❌ Errore lettura file: { $error }
page-hooks-test-empty = 🎣 Nessun hook disponibile per il test

page-hooks-footer =
    🪝 <strong>Hooks System:</strong> Automazione workflow basata su eventi •
    📍 <strong>Directory:</strong> ~/.openfatture/hooks/ •
    📚 <strong>Documentazione:</strong> Vedi CLI per esempi avanzati

## ============================================================================
## EVENTS PAGE (11_📋_Events.py)
## ============================================================================

page-events-page-title = Events & Audit Trail - OpenFatture
page-events-title = 📋 Events & Audit Trail
page-events-subtitle = Tracciamento eventi e audit trail di sistema

### Summary Metrics
page-events-metric-total = Eventi Totali
page-events-metric-total-help = Ultimi { $days } giorni
page-events-metric-daily-avg = Eventi Giornalieri
page-events-metric-types = Tipi Evento
page-events-metric-entities = Entità Tracciate

### Sidebar Filters
page-events-filter-title = 🔍 Filtri Eventi
page-events-filter-period = Periodo (giorni)
page-events-filter-period-help = Numero di giorni da analizzare
page-events-filter-type = Tipo Evento
page-events-filter-type-all = Tutti
page-events-filter-type-help = Filtra per tipo di evento
page-events-filter-entity-type = Tipo Entità
page-events-filter-entity-type-help = Filtra per tipo di entità
page-events-filter-search = 🔎 Cerca
page-events-filter-search-placeholder = Cerca negli eventi...
page-events-filter-search-help = Cerca per tipo evento o entità

### Tabs
page-events-tab-recent = 🕐 Recenti
page-events-tab-filtered = 🔍 Filtrati
page-events-tab-stats = 📊 Statistiche
page-events-tab-timeline = ⏰ Timeline

### Recent Tab
page-events-recent-title = 🕐 Eventi Recenti
page-events-table-timestamp = Timestamp
page-events-table-type = Tipo Evento
page-events-table-entity = Entità
page-events-table-description = Descrizione
page-events-table-user = Utente
page-events-table-user-system = Sistema
page-events-details-button = 👁️ Mostra Dettagli
page-events-details-help = Mostra dettagli completi degli eventi
page-events-details-title = Evento { $num }: { $desc }
page-events-empty = 📭 Nessun evento trovato nel database

### Filtered Tab
page-events-filtered-title = 🔍 Eventi Filtrati
page-events-filtered-found = ✅ Trovati { $count } eventi
page-events-export-button = 📤 Esporta CSV
page-events-export-help = Esporta risultati filtrati come CSV
page-events-export-download = Scarica CSV
page-events-filtered-empty = 🔍 Nessun evento trovato con i filtri selezionati

### Stats Tab
page-events-stats-title = 📊 Statistiche Eventi
page-events-stats-by-type = 📈 Eventi per Tipo
page-events-stats-type-col = Tipo Evento
page-events-stats-count-col = Conteggio
page-events-stats-by-entity = 🏢 Eventi per Entità
page-events-stats-entity-col = Tipo Entità
page-events-stats-daily = 📅 Attività Giornaliera (Ultimi 7 Giorni)

### Timeline Tab
page-events-timeline-title = ⏰ Timeline Entità
page-events-timeline-entity-type = Tipo Entità
page-events-timeline-entity-type-help = Seleziona il tipo di entità
page-events-timeline-entity-id = ID Entità
page-events-timeline-entity-id-placeholder = es: INV-001, CLI-001
page-events-timeline-entity-id-help = Inserisci l'ID dell'entità da tracciare
page-events-timeline-found = ✅ Trovati { $count } eventi per { $type } { $id }
page-events-timeline-event-time = 🕐 **{ $time }**
page-events-timeline-event-type = 📋 { $type }
page-events-timeline-event-details = 📄 Dettagli
page-events-timeline-empty = 📭 Nessun evento trovato per { $type } { $id }
page-events-timeline-info = 💡 Seleziona un tipo entità e inserisci un ID per vedere la timeline

page-events-footer =
    📋 <strong>Event System:</strong> Audit trail completo per compliance e debugging •
    🔍 <strong>Ricerca:</strong> Filtra per tipo, entità e periodo •
    📊 <strong>Analytics:</strong> Statistiche attività e timeline entità

## ============================================================================
## HEALTH PAGE (12_🏥_Health.py)
## ============================================================================

page-health-page-title = System Health - OpenFatture
page-health-title = 🏥 System Health Dashboard
page-health-subtitle = Monitoring e diagnostica real-time

### Usage Metrics
page-health-usage-title = 📊 Usage Metrics
page-health-metric-visits = Total Page Visits
page-health-metric-unique = Unique Pages
page-health-metric-session = Session Start

### Cache Statistics
page-health-cache-title = 💾 Cache Statistics
page-health-cache-cleanup = 🧹 Cleaned up { $count } expired cache entries
page-health-metric-entries = Total Cache Entries
page-health-metric-functions = Cached Functions
page-health-clear-all = 🗑️ Clear All Caches
page-health-clear-success = ✅ All caches cleared!
page-health-cache-breakdown = Cache Breakdown by Function
page-health-table-function = Function
page-health-table-entries = Entries
page-health-cache-management = Selective Cache Management
page-health-clear-invoices = 🧾 Clear Invoice Caches
page-health-clear-clients = 👥 Clear Client Caches
page-health-clear-payments = 💰 Clear Payment Caches
page-health-cleared-category = ✅ Cleared { $count } { $category } caches

### Page Visits
page-health-visits-breakdown = Page Visit Breakdown
page-health-table-page = Page
page-health-table-visits = Visits

### API Health
page-health-api-title = 🔌 API Health Endpoint
page-health-api-info =
    For external monitoring, use the `quick_health_check()` function:

    ```python
    from openfatture.web.utils.health import quick_health_check

    health = quick_health_check()
    # Returns: {"status": "healthy|degraded|unhealthy", "checks": [...]}
    ```

    This can be exposed via an API endpoint for monitoring tools like:
    - Prometheus
    - Datadog
    - New Relic
    - Custom monitoring dashboards

page-health-api-sample = 🔍 Show Sample Health Check JSON
page-health-best-practice =
    **💡 Best Practice:** Monitor this dashboard regularly to catch issues early.
    Set up alerts for "unhealthy" or "degraded" statuses in production.

################################################################################
# Reports Page (9_📊_Reports.py)
################################################################################

### Page Configuration
page-reports-page-title = Report e Analisi - OpenFatture
page-reports-title = 📊 Report e Analisi
page-reports-subtitle = Genera report aziendali e analisi dettagliate

### Data Status
page-reports-no-data-warning = ⚠️ Nessun dato disponibile per i report
page-reports-no-data-info = Crea alcune fatture per vedere i report

### Sidebar
page-reports-sidebar-title = 🔍 Parametri Report
page-reports-year-label = Anno
page-reports-quarter-label = Trimestre (opzionale)
page-reports-all-label = Tutti

### Tabs
page-reports-tab-revenue = 💰 Fatturato
page-reports-tab-vat = 📋 IVA
page-reports-tab-clients = 👥 Clienti

### Revenue Tab
page-reports-revenue-title = 💰 Report Fatturato
page-reports-total-revenue = Fatturato Totale
page-reports-total-vat = IVA Totale
page-reports-invoices-issued = Fatture Emesse
page-reports-avg-invoice-value = Valore Medio Fattura
page-reports-period-label = Periodo
page-reports-monthly-trend = 📈 Andamento Mensile
page-reports-monthly-revenue-chart = Fatturato Mensile
page-reports-monthly-invoices-chart = Numero Fatture Mensili
page-reports-month-label = Mese
page-reports-revenue-label = Fatturato (€)
page-reports-invoice-count-label = Numero Fatture

### VAT Tab
page-reports-vat-title = 📋 Report IVA
page-reports-total-taxable = Imponibile Totale
page-reports-vat-breakdown-title = 📊 Ripartizione per Aliquota IVA
page-reports-vat-distribution-chart = Riparto Imponibile per Aliquota IVA
page-reports-vat-detail-title = 📋 Dettaglio per Aliquota
page-reports-vat-rate-label = Aliquota IVA
page-reports-taxable-label = Imponibile
page-reports-vat-label = IVA
page-reports-total-label = Totale

### Clients Tab
page-reports-clients-title = 👥 Report Clienti
page-reports-active-clients = Clienti Attivi
page-reports-clients-with-invoices = Clienti con fatture emesse nel
page-reports-top-clients-title = 🏆 Top Clienti per Fatturato
page-reports-client-label = Cliente
page-reports-invoices-label = Fatture
page-reports-last-invoice-label = Ultima Fattura
page-reports-top-10-clients-chart = Top 10 Clienti per Fatturato

### Export
page-reports-export-title = 📤 Export Report
page-reports-export-revenue-btn = 📊 Export Fatturato (CSV)
page-reports-export-vat-btn = 📋 Export IVA (CSV)
page-reports-export-clients-btn = 👥 Export Clienti (CSV)
page-reports-download-csv = Scarica CSV

### Footer
page-reports-footer-info = 📊 <strong>Report aggiornati automaticamente</strong> • Dati basati su fatture consegnate o accettate

################################################################################
# Hooks Page (10_🪝_Hooks.py)
################################################################################

### Page Configuration
page-hooks-page-title = Hooks & Automation - OpenFatture
page-hooks-title = 🪝 Hooks & Automation
page-hooks-subtitle = Gestione workflow automatizzati e trigger

### Metrics
page-hooks-total-hooks = Hooks Totali
page-hooks-enabled-hooks = Hooks Attivi
page-hooks-pre-hooks = Pre-hooks
page-hooks-post-hooks = Post-hooks

### Tabs
page-hooks-tab-overview = 📊 Panoramica
page-hooks-tab-manage = ⚙️ Gestione
page-hooks-tab-create = ➕ Crea Hook
page-hooks-tab-test = 🧪 Test

### Overview Tab
page-hooks-overview-title = 📊 Panoramica Hooks
page-hooks-active = Attivo
page-hooks-inactive = Disattivo
page-hooks-no-hooks-info = 🎣 Nessun hook trovato. Crea il tuo primo hook nella tab 'Crea Hook'!

### Manage Tab
page-hooks-manage-title = ⚙️ Gestione Hooks
page-hooks-toggle-state-title = Toggle Stato Hooks
page-hooks-activate-label = Attiva { $name }
page-hooks-toggle-help = Abilita/disabilita l'hook { $name }
page-hooks-activated-success = ✅ Hook '{ $name }' attivato
page-hooks-deactivated-success = ⏸️ Hook '{ $name }' disattivato
page-hooks-update-error = ❌ Errore nell'aggiornamento dello stato del hook
page-hooks-details-btn = 👁️ Dettagli
page-hooks-show-details-help = Mostra dettagli hook
page-hooks-details-title = Dettagli { $name }
page-hooks-no-hooks-manage = 🎣 Nessun hook da gestire

### Create Tab
page-hooks-create-title = ➕ Crea Nuovo Hook
page-hooks-hook-name-label = Nome Hook
page-hooks-hook-name-placeholder = es: post-invoice-send
page-hooks-hook-name-help = Nome del hook (usa prefissi pre-, post-, on-)
page-hooks-script-type-label = Tipo Script
page-hooks-script-type-help = Tipo di script per l'hook
page-hooks-description-label = Descrizione
page-hooks-description-placeholder = Cosa fa questo hook...
page-hooks-description-help = Breve descrizione del hook
page-hooks-event-type-label = Tipo Evento
page-hooks-event-type-help = Quando viene eseguito l'hook
page-hooks-template-preview = 📋 Anteprima Template
page-hooks-template-code = 👁️ Codice Template
page-hooks-create-hook-btn = 🚀 Crea Hook
page-hooks-name-required-error = ❌ Inserisci un nome per l'hook
page-hooks-name-prefix-warning = 💡 Suggerimento: il nome dovrebbe iniziare con '{ $prefix }-'
page-hooks-reload-page-info = 🔄 Ricarica la pagina per vedere il nuovo hook

### Test Tab
page-hooks-test-title = 🧪 Test Hooks
page-hooks-select-hook-label = Seleziona Hook da Testare
page-hooks-select-hook-help = Scegli l'hook da validare
page-hooks-hook-info-title = 📋 Informazioni Hook
page-hooks-event-type-metric = Tipo Evento
page-hooks-status-metric = Stato
page-hooks-timeout-metric = Timeout
page-hooks-validate-hook-btn = 🧪 Valida Hook
page-hooks-validating-spinner = Validando hook...
page-hooks-validation-success = ✅ Hook validato con successo!
page-hooks-code-lines-metric = Righe Codice
page-hooks-size-metric = Dimensione
page-hooks-executable-metric = Eseguibile
page-hooks-yes = Sì
page-hooks-no = No
page-hooks-validation-error = ❌ Errore validazione: { $error }
page-hooks-show-code-btn = 📄 Mostra Codice
page-hooks-file-not-found-error = ❌ File hook non trovato
page-hooks-file-read-error = ❌ Errore lettura file: { $error }
page-hooks-no-hooks-test = 🎣 Nessun hook disponibile per il test

### Footer
page-hooks-footer-info = 🪝 <strong>Hooks System:</strong> Automazione workflow basata su eventi • 📍 <strong>Directory:</strong> ~/.openfatture/hooks/ • 📚 <strong>Documentazione:</strong> Vedi CLI per esempi avanzati

################################################################################
# Events Page (11_📋_Events.py)
################################################################################

### Page Configuration
page-events-page-title = Events & Audit Trail - OpenFatture
page-events-title = 📋 Events & Audit Trail
page-events-subtitle = Tracciamento eventi e audit trail di sistema

### Metrics
page-events-total-events = Eventi Totali
page-events-last-days = Ultimi { $days } giorni
page-events-daily-events = Eventi Giornalieri
page-events-event-types = Tipi Evento
page-events-tracked-entities = Entità Tracciate

### Sidebar Filters
page-events-filters-title = 🔍 Filtri Eventi
page-events-period-label = Periodo (giorni)
page-events-period-help = Numero di giorni da analizzare
page-events-event-type-label = Tipo Evento
page-events-event-type-help = Filtra per tipo di evento
page-events-entity-type-label = Tipo Entità
page-events-entity-type-help = Filtra per tipo di entità
page-events-all-label = Tutti
page-events-search-label = 🔎 Cerca
page-events-search-placeholder = Cerca negli eventi...
page-events-search-help = Cerca per tipo evento o entità

### Tabs
page-events-tab-recent = 🕐 Recenti
page-events-tab-filtered = 🔍 Filtrati
page-events-tab-stats = 📊 Statistiche
page-events-tab-timeline = ⏰ Timeline

### Recent Tab
page-events-recent-title = 🕐 Eventi Recenti
page-events-timestamp-col = Timestamp
page-events-event-type-col = Tipo Evento
page-events-entity-col = Entità
page-events-description-col = Descrizione
page-events-user-col = Utente
page-events-system-label = Sistema
page-events-show-details-btn = 👁️ Mostra Dettagli
page-events-show-details-help = Mostra dettagli completi degli eventi
page-events-event-detail-title = Evento { $num }: { $desc }
page-events-no-events-found = 📭 Nessun evento trovato nel database

### Filtered Tab
page-events-filtered-title = 🔍 Eventi Filtrati
page-events-found-count = ✅ Trovati { $count } eventi
page-events-export-csv-btn = 📤 Esporta CSV
page-events-export-csv-help = Esporta risultati filtrati come CSV
page-events-download-csv = Scarica CSV
page-events-no-filtered-events = 🔍 Nessun evento trovato con i filtri selezionati

### Stats Tab
page-events-stats-title = 📊 Statistiche Eventi
page-events-by-type-title = 📈 Eventi per Tipo
page-events-count-col = Conteggio
page-events-by-entity-title = 🏢 Eventi per Entità
page-events-entity-type-col = Tipo Entità
page-events-daily-activity-title = 📅 Attività Giornaliera (Ultimi 7 Giorni)

### Timeline Tab
page-events-timeline-title = ⏰ Timeline Entità
page-events-timeline-entity-help = Seleziona il tipo di entità
page-events-entity-id-label = ID Entità
page-events-entity-id-placeholder = es: INV-001, CLI-001
page-events-entity-id-help = Inserisci l'ID dell'entità da tracciare
page-events-timeline-found = ✅ Trovati { $count } eventi per { $entity_type } { $entity_id }
page-events-details-label = 📄 Dettagli
page-events-no-timeline-events = 📭 Nessun evento trovato per { $entity_type } { $entity_id }
page-events-timeline-instruction = 💡 Seleziona un tipo entità e inserisci un ID per vedere la timeline

### Footer
page-events-footer-info = 📋 <strong>Event System:</strong> Audit trail completo per compliance e debugging • 🔍 <strong>Ricerca:</strong> Filtra per tipo, entità e periodo • 📊 <strong>Analytics:</strong> Statistiche attività e timeline entità

################################################################################
# Health Page (12_🏥_Health.py)
################################################################################

### Page Configuration
page-health-page-title = System Health - OpenFatture

### Usage Metrics
page-health-usage-metrics-title = 📊 Usage Metrics
page-health-total-visits = Total Page Visits
page-health-unique-pages = Unique Pages
page-health-session-start = Session Start

### Cache Statistics
page-health-cache-stats-title = 💾 Cache Statistics
page-health-cleaned-caches = 🧹 Cleaned up { $count } expired cache entries
page-health-total-cache-entries = Total Cache Entries
page-health-cached-functions = Cached Functions
page-health-clear-all-caches-btn = 🗑️ Clear All Caches
page-health-all-caches-cleared = ✅ All caches cleared!
page-health-cache-breakdown-title = Cache Breakdown by Function
page-health-selective-cache-title = Selective Cache Management
page-health-clear-invoice-caches = 🧾 Clear Invoice Caches
page-health-clear-client-caches = 👥 Clear Client Caches
page-health-clear-payment-caches = 💰 Clear Payment Caches
page-health-cleared-count = ✅ Cleared { $count } { $category } caches
page-health-invoice-category = invoice
page-health-client-category = client
page-health-payment-category = payment

### Page Visits
page-health-visit-breakdown-title = Page Visit Breakdown

### API Health
page-health-api-endpoint-title = 🔌 API Health Endpoint
page-health-api-endpoint-desc =
    For external monitoring, use the `quick_health_check()` function:

    ```python
    from openfatture.web.utils.health import quick_health_check

    health = quick_health_check()
    # Returns: {"status": "healthy|degraded|unhealthy", "checks": [...]}
    ```

    This can be exposed via an API endpoint for monitoring tools like:
    - Prometheus
    - Datadog
    - New Relic
    - Custom monitoring dashboards

page-health-show-sample-json-btn = 🔍 Show Sample Health Check JSON
page-health-best-practice-info =
    **💡 Best Practice:** Monitor this dashboard regularly to catch issues early.
    Set up alerts for "unhealthy" or "degraded" statuses in production.
