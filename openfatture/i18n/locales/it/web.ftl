# Web UI translations - Italian
# Traduzioni complete per l'interfaccia web Streamlit di OpenFatture

## ============================================================================
## COMMON - Stringhe Comuni Web UI
## ============================================================================

### Application
web-app-title = OpenFatture - Fatturazione Elettronica
web-app-tagline = Sistema open-source per fatturazione elettronica italiana
web-app-version = Versione { $version }
web-app-license = Licenza MIT

### Navigation
web-nav-home = Home
web-nav-dashboard = Dashboard
web-nav-invoices = Fatture
web-nav-clients = Clienti
web-nav-payments = Pagamenti
web-nav-ai-assistant = Assistente AI
web-nav-settings = Impostazioni
web-nav-batch = Operazioni Batch
web-nav-reports = Report
web-nav-events = Eventi
web-nav-health = Stato Sistema
web-nav-lightning = Lightning
web-nav-hooks = Hooks

### Common Buttons
web-button-save = Salva
web-button-cancel = Annulla
web-button-delete = Elimina
web-button-edit = Modifica
web-button-create = Crea
web-button-update = Aggiorna
web-button-search = Cerca
web-button-filter = Filtra
web-button-export = Esporta
web-button-import = Importa
web-button-refresh = Aggiorna
web-button-close = Chiudi
web-button-submit = Invia
web-button-reset = Reimposta
web-button-back = Indietro
web-button-next = Avanti
web-button-finish = Termina
web-button-download = Scarica
web-button-upload = Carica
web-button-view = Visualizza
web-button-send = Invia

### Common Labels
web-label-name = Nome
web-label-description = Descrizione
web-label-date = Data
web-label-amount = Importo
web-label-status = Stato
web-label-type = Tipo
web-label-total = Totale
web-label-subtotal = Subtotale
web-label-tax = IVA
web-label-quantity = Quantità
web-label-price = Prezzo
web-label-client = Cliente
web-label-invoice = Fattura
web-label-payment = Pagamento
web-label-notes = Note
web-label-actions = Azioni
web-label-created = Creato
web-label-updated = Aggiornato
web-label-email = Email
web-label-phone = Telefono
web-label-address = Indirizzo
web-label-city = Città
web-label-country = Paese
web-label-search = Cerca
web-label-filter = Filtra
web-label-all = Tutti
web-label-none = Nessuno
web-label-yes = Sì
web-label-no = No

### Common Messages
web-message-success = Operazione completata con successo
web-message-error = Si è verificato un errore
web-message-warning = Attenzione
web-message-info = Informazione
web-message-loading = Caricamento in corso...
web-message-no-data = Nessun dato disponibile
web-message-no-results = Nessun risultato trovato
web-message-confirm-delete = Sei sicuro di voler eliminare questo elemento?
web-message-unsaved-changes = Ci sono modifiche non salvate
web-message-saved = Salvato
web-message-deleted = Eliminato
web-message-updated = Aggiornato
web-message-created = Creato

### Validation Messages
web-validation-required = Questo campo è obbligatorio
web-validation-invalid = Valore non valido
web-validation-email-invalid = Email non valida
web-validation-number-invalid = Numero non valido
web-validation-date-invalid = Data non valida
web-validation-min-length = Lunghezza minima: { $length } caratteri
web-validation-max-length = Lunghezza massima: { $length } caratteri
web-validation-min-value = Valore minimo: { $value }
web-validation-max-value = Valore massimo: { $value }

### Error Messages
web-error-generic = Si è verificato un errore inaspettato
web-error-unexpected = 🚨 Si è verificato un errore imprevisto. Riprova più tardi.
web-error-reload-page = 🔄 Ricarica Pagina
web-error-goto-health = 🏥 Vai alla Dashboard Salute
web-error-network = Errore di connessione
web-error-timeout = Timeout della richiesta
web-error-unauthorized = Non autorizzato
web-error-forbidden = Accesso negato
web-error-not-found = Risorsa non trovata
web-error-server = Errore del server
web-error-database = Errore del database
web-error-loading = Errore durante il caricamento
web-error-saving = Errore durante il salvataggio
web-error-deleting = Errore durante l'eliminazione

### Sidebar
web-sidebar-quick-stats = 📊 Statistiche Rapide
web-sidebar-invoices = Fatture
web-sidebar-clients = Clienti
web-sidebar-revenue = Fatturato
web-sidebar-pending = In Sospeso
web-sidebar-configuration = ⚙️ Configurazione
web-sidebar-company = Azienda
web-sidebar-vat-number = P.IVA
web-sidebar-tax-regime = Regime
web-sidebar-ai-enabled = 🤖 AI Abilitato
web-sidebar-ai-disabled = AI Non Configurato
web-sidebar-ai-provider = Provider
web-sidebar-advanced-ops = 🔧 Operazioni Avanzate
web-sidebar-error-loading-stats = Errore caricamento stats: { $error }

### Language Selector
web-lang-selector-title = 🌍 Lingua
web-lang-selector-italian = Italiano
web-lang-selector-english = English
web-lang-selector-spanish = Español
web-lang-selector-french = Français
web-lang-selector-german = Deutsch
web-lang-selector-changed = Lingua cambiata in { $language }

### Status Values
web-status-active = Attivo
web-status-inactive = Inattivo
web-status-pending = In Attesa
web-status-completed = Completato
web-status-failed = Fallito
web-status-draft = Bozza
web-status-sent = Inviato
web-status-paid = Pagato
web-status-unpaid = Non Pagato
web-status-overdue = Scaduto
web-status-cancelled = Annullato

### Time & Date
web-time-today = Oggi
web-time-yesterday = Ieri
web-time-this-week = Questa settimana
web-time-this-month = Questo mese
web-time-this-year = Quest'anno
web-time-last-week = Settimana scorsa
web-time-last-month = Mese scorso
web-time-last-year = Anno scorso
web-time-custom = Personalizzato

### Pagination
web-pagination-showing = Visualizzati { $start }-{ $end } di { $total }
web-pagination-per-page = Per pagina
web-pagination-first = Prima
web-pagination-last = Ultima
web-pagination-previous = Precedente
web-pagination-next = Successiva

### File Upload
web-upload-drag-drop = Trascina e rilascia i file qui
web-upload-or = oppure
web-upload-browse = Sfoglia
web-upload-max-size = Dimensione massima: { $size }
web-upload-accepted-formats = Formati accettati: { $formats }
web-upload-uploading = Caricamento...
web-upload-success = File caricato con successo
web-upload-error = Errore durante il caricamento del file
