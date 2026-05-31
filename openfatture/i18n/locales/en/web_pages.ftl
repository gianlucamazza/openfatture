# Web Pages translations - English
# Specific translations for Streamlit web interface pages

## ============================================================================
## HOME PAGE (app.py)
## ============================================================================

page-home-title = OpenFatture
page-home-welcome = Welcome to OpenFatture
page-home-subtitle = Open Source Electronic Invoicing System
page-home-description =
    OpenFatture is a complete system for managing Italian electronic invoicing,
    with SDI integration, AI, and Lightning payments.

page-home-features-title = Key Features
page-home-feature-invoicing = Complete electronic invoicing with FatturaPA
page-home-feature-sdi = Direct integration with SDI (Exchange System)
page-home-feature-ai = AI assistant for descriptions and VAT suggestions
page-home-feature-payments = Automatic bank payment reconciliation
page-home-feature-lightning = Lightning Network payment support
page-home-feature-batch = Batch operations for bulk import/export

## Feature Grid
page-home-feature-grid-invoices-title = Invoices
page-home-feature-grid-invoices-item-1 = Guided creation
page-home-feature-grid-invoices-item-2 = Client management
page-home-feature-grid-invoices-item-3 = XML generation
page-home-feature-grid-invoices-item-4 = SDI submission via PEC
page-home-feature-grid-invoices-item-5 = Notification tracking
page-home-feature-grid-invoices-button = Go to Invoices

page-home-feature-grid-payments-title = Payments
page-home-feature-grid-payments-item-1 = Import bank statements
page-home-feature-grid-payments-item-2 = Automatic matching
page-home-feature-grid-payments-item-3 = Reconciliation
page-home-feature-grid-payments-item-4 = Due date reminders
page-home-feature-grid-payments-item-5 = Audit trail
page-home-feature-grid-payments-button = Go to Payments

page-home-feature-grid-ai-title = AI Assistant
page-home-feature-grid-ai-item-1 = Interactive chat
page-home-feature-grid-ai-item-2 = Automatic descriptions
page-home-feature-grid-ai-item-3 = Tax consulting
page-home-feature-grid-ai-item-4 = Cash flow forecast
page-home-feature-grid-ai-item-5 = Compliance check
page-home-feature-grid-ai-button = Try the AI

## Quick Actions
page-home-quick-actions = Quick Actions
page-home-action-new-invoice = New Invoice
page-home-action-new-client = New Client
page-home-action-dashboard = Dashboard
page-home-action-batch = Batch Operations

## Advanced Tools
page-home-advanced-tools = Advanced Tools
page-home-advanced-reports = Reports
page-home-advanced-hooks = Hooks
page-home-advanced-events = Events

## Getting Started
page-home-getting-started = Getting Started
page-home-getting-started-title = First Steps

page-home-step-1-title = 1. Configure the environment
page-home-step-1-item-1 = Ensure `.env` is properly configured
page-home-step-1-item-2 = Verify company data (VAT number, tax regime)
page-home-step-1-item-3 = Configure PEC credentials for SDI submission

page-home-step-2-title = 2. Create your first clients
page-home-step-2-item-1 = Go to "Clients" "Add Client"
page-home-step-2-item-2 = Enter tax details (VAT number, tax code)
page-home-step-2-item-3 = Specify SDI or PEC for invoice receipt

page-home-step-3-title = 3. Issue your first invoice
page-home-step-3-item-1 = "Invoices" "New Invoice"
page-home-step-3-item-2 = Select client and add line items
page-home-step-3-item-3 = Generate XML and submit to SDI

page-home-step-4-title = 4. Explore the AI Assistant
page-home-step-4-item-1 = Try the chat for tax questions
page-home-step-4-item-2 = Generate intelligent descriptions
page-home-step-4-item-3 = Get automatic VAT suggestions

page-home-docs-title = Documentation

## Footer
page-home-footer-version = OpenFatture v{ $version }
page-home-footer-license = MIT License
page-home-footer-tagline = Made with by freelancers, for freelancers

page-home-help = Help and Documentation
page-home-github = GitHub Repository
page-home-report-bug = Report a Bug
page-home-about = About

## ============================================================================
## DASHBOARD PAGE (1__Dashboard.py)
## ============================================================================

page-dashboard-title = Dashboard
page-dashboard-subtitle = Real-Time Business Overview

### KPI Cards
page-dashboard-kpi-section = Key Metrics
page-dashboard-kpi-total-invoices = Total Invoices
page-dashboard-kpi-total-revenue = Total Revenue
page-dashboard-kpi-total-clients = Active Clients
page-dashboard-kpi-revenue-month = Monthly Revenue
page-dashboard-kpi-pending-payments = Pending Payments
page-dashboard-kpi-avg-invoice = Average Invoice Amount
page-dashboard-kpi-this-month = This Month
page-dashboard-kpi-this-year = This Year
page-dashboard-kpi-growth = Growth

### Charts
page-dashboard-chart-invoices-by-status = Invoices by Status
page-dashboard-chart-revenue-6-months = Revenue Last 6 Months
page-dashboard-chart-yaxis-revenue = Revenue (€)
page-dashboard-chart-xaxis-month = Month
page-dashboard-chart-revenue-title = Revenue Trend
page-dashboard-chart-invoices-title = Invoices by Month
page-dashboard-chart-clients-title = Top Clients
page-dashboard-chart-status-title = Invoices by Status
page-dashboard-chart-payments-title = Payment Status

### Tables
page-dashboard-top-clients = Top 5 Clients
page-dashboard-recent-invoices = Last 5 Invoices
page-dashboard-col-client = Client
page-dashboard-col-num-invoices = No. Invoices
page-dashboard-col-num-invoices-short = Invoices
page-dashboard-col-revenue = Revenue
page-dashboard-col-number = Number
page-dashboard-col-date = Date
page-dashboard-col-total = Total
page-dashboard-col-status = Status
page-dashboard-col-invoice = Invoice
page-dashboard-col-due-date = Due Date
page-dashboard-col-days = Days
page-dashboard-col-days-delta = Δ Days
page-dashboard-col-days-help = Days to due date
page-dashboard-col-residual = Outstanding
page-dashboard-col-residual-amount = Outstanding Amount
page-dashboard-col-category = Category

### Payment Tracking
page-dashboard-payment-tracking = Payment Tracking
page-dashboard-payment-unmatched = Unmatched
page-dashboard-payment-matched = Matched
page-dashboard-payment-ignored = Ignored
page-dashboard-payment-total = Total Transactions
page-dashboard-payment-due-30 = Payment Due Dates (Next 30 days)
page-dashboard-total-outstanding = Total Outstanding Receivables
page-dashboard-category-overdue = Overdue
page-dashboard-category-due-soon = Due Soon
page-dashboard-category-upcoming = Upcoming

### Messages
page-dashboard-no-invoices = No invoices available
page-dashboard-no-data = No data available
page-dashboard-no-clients = No clients available
page-dashboard-no-payments-due = No payments due
page-dashboard-error-loading = Error loading dashboard: { $error }
page-dashboard-refresh-button = Refresh Data

### Recent Activity
page-dashboard-recent-activity = Recent Activity

## ============================================================================
## INVOICES PAGE (2__Fatture.py)
## ============================================================================

page-invoices-title = Invoice Management
page-invoices-subtitle = View and manage all your invoices

### Sidebar Filters
page-invoices-filter-title = Filters
page-invoices-filter-year = Year
page-invoices-filter-all = All
page-invoices-filter-status = Status
page-invoices-filter-max-results = Maximum results
page-invoices-no-invoices-in-db = No invoices available
page-invoices-filter-client = Client
page-invoices-filter-date-from = From Date
page-invoices-filter-date-to = To Date
page-invoices-filter-amount-min = Min Amount
page-invoices-filter-amount-max = Max Amount
page-invoices-filter-search = Search invoices...

### Quick Actions
page-invoices-action-quick-title = Quick Actions
page-invoices-action-new-invoice = New Invoice
page-invoices-action-new-invoice-info =
    **Feature in development**

    For now, create invoices via CLI:
    ```bash
    uv run openfatture fattura crea
    ```

    The guided Web UI creation will be available soon!
page-invoices-action-refresh = Refresh List

### Main Content
page-invoices-list-title = ### Invoice List
page-invoices-no-invoices-found = No invoices found with the selected filters

### Stats Metrics
page-invoices-stats-count = Invoices Found
page-invoices-stats-total = Total
page-invoices-stats-statuses = Different Statuses
page-invoices-stats-average = Average Amount

### Table
page-invoices-table-title = #### Invoice Table
page-invoices-col-id = ID
page-invoices-col-number = Number
page-invoices-col-date = Date
page-invoices-col-client = Client
page-invoices-col-total-eur = Total €
page-invoices-col-status = Status
page-invoices-col-lines = Lines
page-invoices-col-amount = Amount
page-invoices-col-payment = Payment
page-invoices-col-actions = Actions

### Invoice Detail Section
page-invoices-detail-title = ### Invoice Detail
page-invoices-detail-input-id = Enter invoice ID to view
page-invoices-detail-show-button = Show Detail
page-invoices-detail-error-not-found = Invoice with ID { $id } not found
page-invoices-detail-success = Invoice { $number }/{ $year }

### Detail Header Metrics
page-invoices-detail-number = Number
page-invoices-detail-date = Issue Date
page-invoices-detail-client = Client
page-invoices-detail-type = Type
page-invoices-detail-status = Status
page-invoices-detail-sdi-number = SDI Number

### Detail Line Items
page-invoices-detail-lines-title = #### Invoice Lines
page-invoices-detail-lines-col-num = #
page-invoices-detail-lines-col-desc = Description
page-invoices-detail-lines-col-qty = Quantity
page-invoices-detail-lines-col-price = Price €
page-invoices-detail-lines-col-vat = VAT %
page-invoices-detail-lines-col-total = Total €
page-invoices-detail-lines-empty = No lines available

### Detail Totals
page-invoices-detail-totals-title = #### Totals
page-invoices-detail-totals-taxable = Taxable
page-invoices-detail-totals-vat = VAT
page-invoices-detail-totals-withholding = Withholding
page-invoices-detail-totals-stamp = Stamp
page-invoices-detail-totals-total = **TOTAL**

### Detail Files
page-invoices-detail-files-title = #### Files
page-invoices-detail-files-xml-exists = XML: `{ $path }`
page-invoices-detail-files-xml-missing = XML not yet generated
page-invoices-detail-files-pdf-exists = PDF: `{ $path }`
page-invoices-detail-files-pdf-missing = PDF not yet generated

### Detail Actions
page-invoices-detail-actions-title = #### Actions
page-invoices-detail-actions-generate-xml = Generate XML
page-invoices-detail-actions-generating-xml = Generating XML...
page-invoices-detail-actions-error = Error: { $error }
page-invoices-detail-actions-xml-success = XML generated successfully!
page-invoices-detail-actions-send-sdi = Send to SDI
page-invoices-detail-actions-generate-pdf = Generate PDF
page-invoices-detail-actions-cli-feature = CLI Feature

### Error Messages
page-invoices-error-loading = Error loading invoices: { $error }

### Legacy (kept for compatibility)
page-invoices-action-view = View
page-invoices-action-edit = Edit
page-invoices-action-delete = Delete
page-invoices-action-send = Send to SDI
page-invoices-action-download-xml = Download XML
page-invoices-action-download-pdf = Download PDF
page-invoices-action-duplicate = Duplicate
page-invoices-no-invoices = No invoices found
page-invoices-create-first = Create your first invoice
page-invoices-total-found = { $count } invoices found
page-invoices-selected = { $count } selected

## ============================================================================
## INVOICE CREATION PAGE (13__Crea_Fattura.py)
## ============================================================================

### Page Configuration
page-invoice-create-page-title = Create Invoice - OpenFatture
page-invoice-create-title = Guided Invoice Creation

### Wizard Progress
page-invoice-create-wizard-title = Invoice Creation - Step { $step }/{ $total }

### Step Labels
page-invoice-create-step-1-label = Select Client
page-invoice-create-step-2-label = Invoice Details
page-invoice-create-step-3-label = Add Products
page-invoice-create-step-4-label = AI Assistance
page-invoice-create-step-5-label = Summary & Create

### Step 1: Select Client
page-invoice-create-step-1-header = Select Client
page-invoice-create-client-search-label = Search existing client
page-invoice-create-client-search-placeholder = Company name, VAT number...
page-invoice-create-client-search-help = Leave empty to see all clients
page-invoice-create-client-existing-title = Existing clients
page-invoice-create-client-vat-label = VAT
page-invoice-create-client-select-label = Select client
page-invoice-create-client-select-help = Choose an existing client or create a new one
page-invoice-create-client-create-title = Or create new client
page-invoice-create-client-create-expander = Create new client
page-invoice-create-client-name-label = Company Name *
page-invoice-create-client-name-placeholder = Company or person name
page-invoice-create-client-vat-input-label = VAT Number
page-invoice-create-client-vat-placeholder = 12345678901
page-invoice-create-client-fiscal-code-label = Tax ID
page-invoice-create-client-fiscal-code-placeholder = Tax ID (if individual)
page-invoice-create-client-address-label = Address
page-invoice-create-client-address-placeholder = 123 Main St, 00100 Rome
page-invoice-create-client-email-label = Email
page-invoice-create-client-email-placeholder = client@email.com
page-invoice-create-client-phone-label = Phone
page-invoice-create-client-phone-placeholder = +39 123 456 7890
page-invoice-create-client-regime-label = Tax Regime
page-invoice-create-client-regime-ordinary = RF01 - Standard
page-invoice-create-client-regime-flat = RF19 - Flat Rate
page-invoice-create-client-create-button = Create Client
page-invoice-create-client-name-required = Company name is required
page-invoice-create-client-create-success = Client '{ $name }' created successfully!
page-invoice-create-client-create-error = Error creating client: { $error }

### Step 2: Invoice Details
page-invoice-create-step-2-header = Invoice Details
page-invoice-create-details-client-selected = Selected client: **{ $name }**
page-invoice-create-details-regime = Tax regime: { $regime }
page-invoice-create-details-number-label = Invoice Number
page-invoice-create-details-number-help = Sequential invoice number
page-invoice-create-details-year-label = Year
page-invoice-create-details-year-help = Fiscal year
page-invoice-create-details-date-label = Issue Date
page-invoice-create-details-date-help = Invoice issue date
page-invoice-create-details-due-date-label = Due Date
page-invoice-create-details-due-date-help = Payment due date
page-invoice-create-details-additional-title = Additional Details
page-invoice-create-details-subject-label = Subject/Description
page-invoice-create-details-subject-placeholder = General invoice description...
page-invoice-create-details-subject-help = General description of services/products
page-invoice-create-details-notes-label = Notes
page-invoice-create-details-notes-placeholder = Additional notes...
page-invoice-create-details-notes-help = Internal or invoice notes

### Step 3: Invoice Lines
page-invoice-create-step-3-header = Products and Services
page-invoice-create-lines-title = Invoice lines
page-invoice-create-lines-description-label = Description
page-invoice-create-lines-quantity-label = Quantity
page-invoice-create-lines-price-label = Unit Price (€)
page-invoice-create-lines-row-total = Line total: { $total }
page-invoice-create-lines-remove-button = Remove
page-invoice-create-lines-add-title = Add new line
page-invoice-create-lines-description-input-label = Description *
page-invoice-create-lines-description-placeholder = Product/service description...
page-invoice-create-lines-quantity-input-label = Quantity
page-invoice-create-lines-quantity-help = Product/service quantity
page-invoice-create-lines-price-input-label = Unit Price (€)
page-invoice-create-lines-price-help = Unit price excluding VAT
page-invoice-create-lines-vat-label = VAT Rate
page-invoice-create-lines-vat-help = Applicable VAT rate
page-invoice-create-lines-add-button = Add Line
page-invoice-create-lines-description-required = Description is required
page-invoice-create-lines-add-success = Line added!
page-invoice-create-lines-totals-title = Totals
page-invoice-create-lines-subtotal-label = Subtotal
page-invoice-create-lines-vat-amount-label = VAT
page-invoice-create-lines-total-label = Total

### Step 4: AI Assistance
page-invoice-create-step-4-header = AI Assistance
page-invoice-create-ai-description-title = Generate Descriptions with AI
page-invoice-create-ai-description-button = Suggest descriptions for lines
page-invoice-create-ai-description-no-lines = Add lines to the invoice first
page-invoice-create-ai-description-generating = Generating descriptions...
page-invoice-create-ai-description-improved = Description for line { $row } improved!
page-invoice-create-ai-description-error = Error generating description for line { $row }: { $error }
page-invoice-create-ai-vat-title = VAT Advice
page-invoice-create-ai-vat-button = Check VAT rates
page-invoice-create-ai-vat-no-lines = Add lines to the invoice first
page-invoice-create-ai-vat-checking = Checking VAT rates...
page-invoice-create-ai-vat-suggestion = Line { $row }: Suggested VAT rate { $suggested }% instead of { $current }%
page-invoice-create-ai-vat-apply = Apply { $rate }% to line { $row }
page-invoice-create-ai-vat-updated = VAT rate updated!
page-invoice-create-ai-vat-info = Line { $row }: { $info }
page-invoice-create-ai-vat-error = Error checking VAT for line { $row }: { $error }
page-invoice-create-ai-compliance-title = Compliance Check
page-invoice-create-ai-compliance-button = Check invoice compliance
page-invoice-create-ai-compliance-no-number = Invoice number missing
page-invoice-create-ai-compliance-no-lines = No invoice lines present
page-invoice-create-ai-compliance-line-no-desc = Line { $row }: description missing
page-invoice-create-ai-compliance-line-qty-invalid = Line { $row }: quantity must be > 0
page-invoice-create-ai-compliance-line-price-invalid = Line { $row }: unit price must be > 0
page-invoice-create-ai-compliance-issues-found = Issues found
page-invoice-create-ai-compliance-success = Invoice complies with basic requirements!

### Step 5: Summary
page-invoice-create-step-5-header = Summary and Creation
page-invoice-create-summary-client-title = Client
page-invoice-create-summary-client-vat = VAT: { $vat }
page-invoice-create-summary-client-regime = Regime: { $regime }
page-invoice-create-summary-invoice-title = Invoice
page-invoice-create-summary-invoice-date = Issue: { $date }
page-invoice-create-summary-invoice-due = Due: { $date }
page-invoice-create-summary-lines-title = Invoice Lines
page-invoice-create-summary-table-description = Description
page-invoice-create-summary-table-quantity = Qty
page-invoice-create-summary-table-price = Price
page-invoice-create-summary-table-vat = VAT
page-invoice-create-summary-table-total = Total
page-invoice-create-summary-totals-title = Totals
page-invoice-create-summary-totals-subtotal = Subtotal
page-invoice-create-summary-totals-vat = VAT
page-invoice-create-summary-totals-total = Total Invoice
page-invoice-create-summary-create-button = Create Invoice
page-invoice-create-summary-creating = Creating invoice...
page-invoice-create-summary-error-create-failed = Unable to create invoice
page-invoice-create-summary-success = Invoice { $number }/{ $year } created successfully!
page-invoice-create-summary-next-steps =
    **Next steps:**
    1. **Validate** the invoice: `openfatture fattura valida { $number }`
    2. **Send** to SDI: `openfatture pec invia { $number }`
    3. **Monitor** status in the Invoices page
page-invoice-create-summary-error = Error creating invoice: { $error }

### Navigation
page-invoice-create-nav-back = Back
page-invoice-create-nav-next = Next
page-invoice-create-nav-success = Invoice created successfully!
page-invoice-create-nav-create-another = Create another invoice

## ============================================================================
## CLIENTS PAGE (3__Clienti.py)
## ============================================================================

page-clients-title = Client Management
page-clients-subtitle = View and manage your clients

### Filters
page-clients-search = Search clients...
page-clients-filter-type = Type
page-clients-filter-country = Country

### Table Headers
page-clients-col-name = Name/Company Name
page-clients-col-vat = VAT Number
page-clients-col-email = Email
page-clients-col-phone = Phone
page-clients-col-invoices = Invoices
page-clients-col-revenue = Revenue
page-clients-col-actions = Actions

### Actions
page-clients-action-add = Add Client
page-clients-action-view = View
page-clients-action-edit = Edit
page-clients-action-delete = Delete
page-clients-action-create-invoice = Create Invoice

### Messages
page-clients-no-clients = No clients found
page-clients-add-first = Add your first client
page-clients-total-found = { $count } clients found

## ============================================================================
## PAYMENTS PAGE (4__Pagamenti.py)
## ============================================================================

### Page Config
page-payments-page-title = Payments - OpenFatture
page-payments-title = Payment Tracking & Reconciliation

### Sidebar Filters
page-payments-filter-title = Filters
page-payments-filter-bank-account = Bank Account
page-payments-filter-all-accounts = All
page-payments-filter-status = Status
page-payments-no-accounts-configured = No bank accounts configured

### Status Labels
page-payments-status-all = All
page-payments-status-unmatched = To Reconcile
page-payments-status-matched = Reconciled
page-payments-status-ignored = Ignored
page-payments-status-paired = Paired

### Sidebar Actions
page-payments-action-import = Import
page-payments-action-import-help = Import bank statement
page-payments-action-refresh = Refresh

### Import Form
page-payments-import-title = Import Bank Statement
page-payments-import-select-account = Select bank account *
page-payments-import-select-account-help = Choose the account to import transactions into
page-payments-import-no-account-error = No bank account configured. Create one before importing.
page-payments-import-file-label = Select bank statement file
page-payments-import-file-help = Supports formats: OFX, QFX, CSV, QIF
page-payments-import-bank-preset = Bank (for CSV)
page-payments-import-bank-preset-help = Select the bank for proper CSV parsing
page-payments-import-auto-match = Auto-match payments
page-payments-import-auto-match-help = Automatically attempt to match transactions to invoices
page-payments-import-confidence = Confidence threshold
page-payments-import-confidence-help = Minimum confidence for auto-matching
page-payments-import-button = Import Transactions
page-payments-import-error-no-account = Select a bank account
page-payments-import-error-no-file = Select a file to import
page-payments-import-importing = Importing transactions...
page-payments-import-metric-imported = Imported Transactions
page-payments-import-metric-errors = Errors
page-payments-import-metric-duplicates = Duplicates
page-payments-import-format-detected = Format detected: { $format }
page-payments-import-errors-title = Import errors
page-payments-import-success-refresh = Data refreshed!
page-payments-import-close = Close

### Bank Accounts Overview
page-payments-accounts-title = Bank Accounts
page-payments-accounts-current-balance = Current Balance
page-payments-accounts-iban = IBAN: ...{ $last4 }
page-payments-accounts-bank = Bank: { $name }

### Payment Statistics
page-payments-stats-title = Payment Statistics
page-payments-stats-accounts = Bank Accounts
page-payments-stats-transactions = Total Transactions
page-payments-stats-balance = Total Balance
page-payments-stats-reconciled = Reconciled
page-payments-stats-distribution-title = Distribution by Status
page-payments-stats-distribution-status = Status
page-payments-stats-distribution-transactions = Transactions

### Transactions List
page-payments-transactions-title = Transactions
page-payments-table-col-id = ID
page-payments-table-col-date = Date
page-payments-table-col-amount = Amount
page-payments-table-col-description = Description
page-payments-table-col-reference = Reference
page-payments-table-col-status = Status
page-payments-table-col-invoice = Invoice
page-payments-table-col-actions = Actions
page-payments-action-view-details = View details
page-payments-action-match = Reconcile
page-payments-transactions-summary = **Total displayed:** { $total } of { $count } transactions
page-payments-no-transactions-filtered = No transactions found with selected filters
page-payments-no-transactions = No transactions present

### Quick Start Guide
page-payments-quickstart-title = Getting Started with Payments
page-payments-quickstart-content =
    ### First Steps

    1. **Add a bank account**
       ```bash
       uv run openfatture payment account add "Business Account" --iban IT123...
       ```

    2. **Import a bank statement**
       ```bash
       uv run openfatture payment import statement.ofx --account 1
       ```

    3. **Automatically reconcile**
       ```bash
       uv run openfatture payment match --auto-apply
       ```

    4. **Verify reconciliations**
       ```bash
       uv run openfatture payment status
       ```

### Error Messages
page-payments-error-loading = Error loading payments: { $error }
page-payments-error-loading-hint = Make sure the database is initialized correctly

### Transaction Detail Modal
page-payments-detail-title = Transaction Details { $id }...
page-payments-detail-id = ID
page-payments-detail-date = Date
page-payments-detail-amount = Amount
page-payments-detail-description = Description
page-payments-detail-reference = Reference
page-payments-detail-counterparty = Counterparty
page-payments-detail-status = Status
page-payments-detail-confidence = Match Confidence
page-payments-detail-linked-invoice = Linked Invoice
page-payments-detail-close = Close
page-payments-detail-not-found = Transaction not found

### Match Transaction Modal
page-payments-match-title = Reconcile Transaction { $amount }
page-payments-match-date = Date
page-payments-match-amount = Amount
page-payments-match-description = Description
page-payments-match-reference = Reference
page-payments-match-counterparty = Counterparty
page-payments-match-status = Status
page-payments-match-suggestions-title = Suggested Matches
page-payments-match-client = Client: { $client }
page-payments-match-confidence = Confidence
page-payments-match-days-diff = ±{ $days } days
page-payments-match-button = Match
page-payments-match-matching = Matching transaction...
page-payments-match-success = Transaction matched to invoice { $number }
page-payments-match-error = Error: { $error }
page-payments-match-no-suggestions = No automatic matches found
page-payments-match-manual-title = Manual Search
page-payments-match-manual-search = Search invoice
page-payments-match-manual-placeholder = Invoice number, client...
page-payments-match-manual-help = Enter invoice number or client name
page-payments-match-manual-results = Search results:
page-payments-match-manual-button = Match
page-payments-match-manual-success = Matched!
page-payments-match-manual-no-results = No invoices found
page-payments-match-close = Close

### Quick Stats Section
page-payments-quick-stats-title = ### Payment Statistics
page-payments-quick-stats-unmatched = Unmatched
page-payments-quick-stats-matched = Matched
page-payments-quick-stats-ignored = Ignored
page-payments-quick-stats-total = Total
page-payments-quick-stats-error = Error loading data: { $error }

### Payment Due Section
page-payments-due-title = ### Due Next 30 Days
page-payments-due-col-invoice = Invoice
page-payments-due-col-client = Client
page-payments-due-col-due-date = Due Date
page-payments-due-col-residual = Outstanding
page-payments-due-col-status = Status
page-payments-due-total-residual = Total Outstanding
page-payments-due-no-payments = No payments due

### Legacy (kept for compatibility)
page-payments-tab-overview = Overview
page-payments-tab-reconciliation = Reconciliation
page-payments-tab-history = History
page-payments-total-received = Received
page-payments-total-pending = Pending
page-payments-total-overdue = Overdue
page-payments-reconciliation-rate = Reconciliation Rate
page-payments-import-bank = Import Bank Statement
page-payments-match-automatic = Automatic Matching
page-payments-match-manual = Manual Matching
page-payments-unmatched = Unmatched Transactions
page-payments-matched = Matched Transactions
page-payments-col-invoice = Invoice
page-payments-col-client = Client
page-payments-col-amount = Amount
page-payments-col-due-date = Due Date
page-payments-col-paid-date = Payment Date
page-payments-col-status = Status
page-payments-col-method = Method

## ============================================================================
## AI ASSISTANT PAGE (5__AI_Assistant.py)
## ============================================================================

### Page Config
page-ai-page-title = AI Assistant - OpenFatture
page-ai-title = AI Assistant
page-ai-subtitle = Intelligent Assistant for Invoicing and Taxation
page-ai-not-configured =
    **AI not configured**

    To enable the AI Assistant:
    1. Configure credentials in the `.env` file
    2. Set `AI_PROVIDER` (openai/anthropic/ollama)
    3. Set `AI_API_KEY` (if needed)
    4. Restart the application

    See `docs/CONFIGURATION.md` for details.

### Tabs
page-ai-tab-chat = Chat Assistant
page-ai-tab-description = Generate Description
page-ai-tab-vat = VAT Suggestion
page-ai-tab-voice = Voice Chat

### General
page-ai-yes = YES
page-ai-no = NO

### Retry Logic
page-ai-retry-message = Attempt { $attempt }/{ $max_retries } failed. Retrying in { $delay }s...

### Error Messages
page-ai-error-connection = Connection error. Check your internet connection and try again.
page-ai-error-auth = Authentication error. Check your AI credentials.
page-ai-error-rate-limit = Rate limit reached. Try again in a few minutes.
page-ai-error-service-unavailable = Service temporarily unavailable. Try again later.
page-ai-error-generic = Unexpected error: { $error }...
page-ai-error-hint-connection = Hint: Check your internet connection
page-ai-error-hint-auth = Hint: Verify AI settings in preferences

### Slash Commands
page-ai-command-help-feedback =
    **Available Commands:**

    **Built-in:**
    - `/help` - Show this message
    - `/tools` - List available AI tools
    - `/stats` - Current conversation statistics
    - `/custom` - List custom commands
    - `/reload` - Reload commands from disk
    - `/clear` - Clear chat history

    **Custom:**
    Create commands in `~/.openfatture/commands/*.yaml`

    **Examples:**
    - "How do I create an invoice?"
    - "What's the VAT rate for web design?"
    - "Show me this month's invoices"

page-ai-command-tools-feedback =
    **Available AI Tools:**

    **Search and Consultation:**
    - Search invoices by client, date, amount
    - Revenue and payment statistics
    - Tax regulation consultation

    **Available Actions:**
    - Create professional invoice descriptions
    - Suggest correct VAT rates
    - Invoice compliance analysis

    **Data Integration:**
    - Access to client and product database
    - Payment history and due dates
    - Business reports and analytics

page-ai-command-stats-feedback =
    **Conversation Statistics:**

    - **Total messages:** { $total_messages }
    - **Your messages:** { $user_messages }
    - **AI responses:** { $assistant_messages }
    - **Total characters:** { NUMBER($total_chars) }
    - **Estimated tokens:** { NUMBER($estimated_tokens) }

    **Hints:**
    - Use `/clear` to start over
    - Save important conversations with Save

page-ai-command-custom-no-commands = **No custom commands found**\n\nCreate commands in `~/.openfatture/commands/*.yaml`
page-ai-command-custom-header = **Custom Commands ({ $count }):**
page-ai-command-custom-footer = Use `/help` to see all commands
page-ai-command-reload-success = **Commands reloaded:** { $old_count } { $new_count } ({ $added } added, { $removed } removed)
page-ai-command-reload-error = **Reload error:** { $error }
page-ai-command-clear-feedback = **History cleared**\n\nThe conversation has been reset.
page-ai-command-custom-expanded = **Command expanded:** `/{ $command }` { $length } characters
page-ai-command-custom-error = **Command error:** { $error }
page-ai-command-unknown = **Unknown command:** `{ $command }`\n\nUse `/help` to see available commands

### Tab 1: Chat Assistant
page-ai-chat-title = Interactive Chat
page-ai-chat-description =
    Chat with the AI assistant for:
    - Questions about invoicing and regulations
    - Tax and VAT advice
    - Payment and deadline management
    - General business consulting

page-ai-chat-save = Save
page-ai-chat-save-help = Save conversation
page-ai-chat-session-title = Chat { $count } messages
page-ai-chat-saved = Saved: { $session_id }...
page-ai-chat-save-error = Save error
page-ai-chat-reload = Reload
page-ai-chat-reload-help = Reload custom commands
page-ai-chat-reloaded = Reloaded: { $count } commands
page-ai-chat-clear = Clear

### Chat File Upload
page-ai-chat-file-upload-title = Attach File (Optional)
page-ai-chat-file-upload-label = Upload a document to discuss with AI
page-ai-chat-file-upload-help = Supports PDF, text, images and other documents
page-ai-chat-file-uploaded = File uploaded: { $name } ({ $size } bytes)
page-ai-chat-files-attached = Attached Files
page-ai-chat-files-clear-all = Clear All
page-ai-chat-files-cleared = Files cleared!

### Chat File Types
page-ai-chat-file-text-preview = - **{ $name }** (text): { $preview }
page-ai-chat-file-text = - **{ $name }** (text, { $size } bytes)
page-ai-chat-file-pdf = - **{ $name }** (PDF, { $size } bytes) - Content to analyze
page-ai-chat-file-image = - **{ $name }** (image { $format }, { $size } bytes) - Text to extract via OCR
page-ai-chat-file-other = - **{ $name }** ({ $type }, { $size } bytes)
page-ai-chat-file-analysis-hint = AI will analyze these files to provide a more accurate response.

### Custom Commands
page-ai-chat-custom-commands-title = Custom Commands
page-ai-chat-custom-commands-empty = No custom commands found. Create commands in `~/.openfatture/commands/*.yaml`
page-ai-chat-custom-commands-count = **{ $count } commands available:**
page-ai-chat-custom-commands-description = **Description:** { $desc }
page-ai-chat-custom-commands-examples = Examples
page-ai-chat-custom-commands-author = **Author:** { $author }
page-ai-chat-custom-commands-version = **Version:** { $version }

### Chat Sessions
page-ai-chat-sessions-title = Saved Sessions
page-ai-chat-sessions-empty = No saved sessions. Use the Save button to save the current conversation.
page-ai-chat-sessions-count = **{ $count } sessions available:**
page-ai-chat-sessions-load = Load
page-ai-chat-sessions-loaded = Loaded session: { $title }
page-ai-chat-sessions-load-error-empty = Empty or corrupted session
page-ai-chat-sessions-load-error = Load error: { $error }
page-ai-chat-sessions-rename = Rename
page-ai-chat-sessions-rename-todo = Rename feature to be implemented
page-ai-chat-sessions-delete = Delete
page-ai-chat-sessions-deleted = Session deleted
page-ai-chat-sessions-delete-error = Delete error

### Chat Input & Messages
page-ai-chat-input-placeholder = Type your message or use /command...
page-ai-chat-attachments = Attachments
page-ai-chat-thinking = Thinking...

### Chat Feedback
page-ai-chat-feedback-good = Good
page-ai-chat-feedback-good-comment = Good response
page-ai-chat-feedback-bad = Poor
page-ai-chat-feedback-bad-comment = Unsatisfactory response
page-ai-chat-feedback-comment = Comment
page-ai-chat-feedback-comment-label = Leave a comment about the response:
page-ai-chat-feedback-submit = Submit Comment
page-ai-chat-feedback-comment-sent = Comment sent!
page-ai-chat-feedback-comment-empty = Enter a comment
page-ai-chat-feedback-thanks = Thanks for your feedback!
page-ai-chat-feedback-error = Error sending feedback

### Tab 2: Description Generator
page-ai-desc-title = Generate Invoice Description
page-ai-desc-description =
    Generate professional descriptions for your invoices using AI.
    Provide information about the service and get a detailed description.

page-ai-desc-service-label = Service Provided *
page-ai-desc-service-placeholder = e.g., E-commerce web app development consulting
page-ai-desc-service-help = Briefly describe the service/product
page-ai-desc-hours-label = Hours Worked
page-ai-desc-hours-help = Number of hours (optional)
page-ai-desc-project-label = Project Name
page-ai-desc-project-placeholder = e.g., XYZ E-Commerce Project
page-ai-desc-project-help = Project name (optional)
page-ai-desc-rate-label = Hourly Rate (€)
page-ai-desc-rate-help = Hourly rate in euros (optional)
page-ai-desc-tech-label = Technologies
page-ai-desc-tech-placeholder = Python, FastAPI, PostgreSQL
page-ai-desc-tech-help = Technologies used, comma-separated (optional)
page-ai-desc-generate = Generate Description
page-ai-desc-error-empty = Enter a service description
page-ai-desc-generating = Generating professional description...
page-ai-desc-success = Description generated successfully!
page-ai-desc-result-title = Professional Description
page-ai-desc-deliverables = Deliverables
page-ai-desc-skills = Technical Skills
page-ai-desc-duration = **Duration:** { $hours } hours
page-ai-desc-notes = **Notes:** { $notes }
page-ai-desc-result-generated = Generated Description

### Tab 3: VAT Suggestion
page-ai-vat-title = VAT Rate Suggestion
page-ai-vat-description =
    Get AI suggestions on the correct VAT rate and tax treatment
    based on the service/product type and client.

page-ai-vat-service-label = Service/Product Description *
page-ai-vat-service-placeholder = e.g., IT consulting for management software development
page-ai-vat-service-help = Describe the service or product to invoice
page-ai-vat-client-pa-label = Client is Public Administration
page-ai-vat-client-pa-help = Check if the client is PA
page-ai-vat-amount-label = Amount (€)
page-ai-vat-amount-help = Amount in euros (optional)
page-ai-vat-client-foreign-label = Foreign Client
page-ai-vat-client-foreign-help = Check if the client is not resident in Italy
page-ai-vat-country-label = Client Country
page-ai-vat-country-placeholder = IT, FR, US...
page-ai-vat-country-help = 2-letter ISO country code
page-ai-vat-category-label = Service Category
page-ai-vat-category-help = Service category (optional)
page-ai-vat-category-consulting = Consulting
page-ai-vat-category-software = Software Development
page-ai-vat-category-training = Training
page-ai-vat-category-design = Design/Graphics
page-ai-vat-category-marketing = Marketing
page-ai-vat-category-maintenance = Maintenance
page-ai-vat-category-other = Other
page-ai-vat-suggest = Get VAT Suggestion
page-ai-vat-error-empty = Enter a service/product description
page-ai-vat-analyzing = Analyzing tax treatment...
page-ai-vat-success = Analysis complete!
page-ai-vat-treatment-title = Tax Treatment
page-ai-vat-rate-metric = VAT Rate
page-ai-vat-reverse-charge-metric = Reverse Charge
page-ai-vat-confidence-metric = Confidence
page-ai-vat-nature-code = **VAT Nature Code:** { $code }
page-ai-vat-split-payment = **Split Payment** applicable
page-ai-vat-special-regime = **Special Regime:** { $regime }
page-ai-vat-explanation-title = Explanation
page-ai-vat-legal-reference-title = Legal Reference
page-ai-vat-invoice-note-title = Invoice Note
page-ai-vat-recommendations-title = Recommendations
page-ai-vat-suggestion-title = Suggestion
page-ai-vat-error = Error: { $error }
page-ai-vat-error-generic = Analysis error: { $error }

### Tab 4: Voice Chat
page-ai-voice-title = Voice Chat with AI
page-ai-voice-not-configured =
    **Voice Chat not configured**

    To enable Voice Chat:
    1. Configure `OPENAI_API_KEY` in `.env` file
    2. Set `OPENFATTURE_VOICE_ENABLED=true`
    3. Restart the application

    See the documentation for details.

page-ai-voice-description =
    Talk to the AI assistant using your voice:
    - Record your question
    - AI transcribes and responds
    - Listen to the voice response
    - Supports context conversations

### Voice Configuration
page-ai-voice-config-title = Voice Configuration
page-ai-voice-config-provider = Provider
page-ai-voice-config-stt = STT Model
page-ai-voice-config-tts-voice = TTS Voice
page-ai-voice-config-tts-model = **TTS Model:** { $model }
page-ai-voice-config-tts-speed = **TTS Speed:** { $speed }x
page-ai-voice-config-tts-format = **TTS Format:** { $format }
page-ai-voice-config-streaming = **Streaming:** { $enabled }

### Voice History
page-ai-voice-clear = Clear Voice
page-ai-voice-history-title = Conversation History
page-ai-voice-user-message = **You:** { $text }
page-ai-voice-assistant-message = **Assistant:** { $text }
page-ai-voice-language-detected = Language detected: { $lang }
page-ai-voice-language = Language: { $lang }
page-ai-voice-metric-stt = STT: { $ms }ms
page-ai-voice-metric-llm = LLM: { $ms }ms
page-ai-voice-metric-tts = TTS: { $ms }ms
page-ai-voice-metric-total = Total: { $ms }ms
page-ai-voice-metric-total-label = Total
page-ai-voice-history-empty = No voice conversations yet. Record your first question!

### Voice Input
page-ai-voice-record-title = Record your voice
page-ai-voice-record-label = Press the button to record
page-ai-voice-record-help = Speak clearly into the microphone. Recording stops automatically after silence.
page-ai-voice-recorded = Audio recorded: { $size } bytes
page-ai-voice-process = Send and Process
page-ai-voice-processing = Processing your voice message...
page-ai-voice-success = Voice message processed successfully!
page-ai-voice-transcription-title = Transcription
page-ai-voice-response-title = AI Response
page-ai-voice-audio-response-title = Voice Response
page-ai-voice-metrics-title = Metrics
page-ai-voice-tech-details = Technical Details
page-ai-voice-error = Processing error: { $error }
page-ai-voice-error-hint-connection = Hint: Check your internet connection
page-ai-voice-error-hint-auth = Hint: Verify API settings in configuration
page-ai-voice-error-hint-rate = Hint: Rate limit reached. Try again in a few minutes

### Voice Help
page-ai-voice-help-title = How it works
page-ai-voice-help-content =
    **Voice Chat Workflow:**

    1. **Recording**: Press the button and speak into the microphone
    2. **Transcription (STT)**: OpenAI Whisper converts voice to text
    3. **Processing (LLM)**: AI understands and generates a response
    4. **Synthesis (TTS)**: OpenAI TTS converts response to audio
    5. **▶Playback**: Listen to the voice response

    **Language Support:**
    - Automatic detection from 100+ languages
    - Italian, English, French, German, Spanish and many more

    **Estimated Costs:**
    - STT (Whisper): ~$0.006 per minute of audio
    - TTS: ~$0.015 per 1,000 characters (tts-1) or ~$0.030 (tts-1-hd)
    - LLM: Standard pricing for configured model

    **Requirements:**
    - Working microphone
    - Modern browser (Chrome, Firefox, Safari, Edge)
    - Stable internet connection

### Metrics (shared across tabs)
page-ai-metric-provider = Provider
page-ai-metric-tokens = Tokens
page-ai-metric-cost = Cost

### Footer
page-ai-footer-disclaimer =
    **Hint:** The AI Assistant is a support tool. The information provided
    should always be verified with an accountant or tax advisor to ensure
    compliance with current regulations.

## ============================================================================
## CLIENTS PAGE (3__Clienti.py)
## ============================================================================

page-clients-title = Client Management
page-clients-subtitle = View and manage your clients

### Sidebar Filters
page-clients-filter-title = Filters
page-clients-filter-search = Search
page-clients-filter-search-placeholder = Company Name, VAT, Tax Code...
page-clients-filter-search-help = Search by company name, VAT number or tax code

### Actions
page-clients-action-new = New Client
page-clients-action-refresh = Refresh
page-clients-action-view = View details
page-clients-action-edit = Edit
page-clients-action-delete = Delete

### Add Client Form
page-clients-form-add-title = New Client
page-clients-form-denominazione = Company Name *
page-clients-form-denominazione-placeholder = Company or person name
page-clients-form-piva = VAT Number
page-clients-form-piva-placeholder = 12345678901
page-clients-form-cf = Tax Code
page-clients-form-cf-placeholder = RSSMRA80A01H501U
page-clients-form-sdi = SDI Code
page-clients-form-sdi-placeholder = ABC1234
page-clients-form-pec = PEC
page-clients-form-pec-placeholder = client@pec.it
page-clients-form-address = Address
page-clients-form-address-placeholder = Via Roma 123
page-clients-form-zip = ZIP Code
page-clients-form-zip-placeholder = 00100
page-clients-form-phone = Phone
page-clients-form-phone-placeholder = +39 123 456 7890
page-clients-form-city = City
page-clients-form-city-placeholder = Roma
page-clients-form-province = Province
page-clients-form-province-placeholder = RM
page-clients-form-email = Email
page-clients-form-email-placeholder = client@email.com
page-clients-form-notes = Notes
page-clients-form-notes-placeholder = Additional notes...
page-clients-form-save = Save Client
page-clients-form-cancel = Cancel

### Statistics
page-clients-stats-title = Statistics
page-clients-stats-total = Total Clients
page-clients-stats-with-pec = With PEC
page-clients-stats-with-sdi = With SDI
page-clients-stats-with-piva = With VAT Number

### Client List
page-clients-list-title = Client List

### Table Columns
page-clients-table-col-id = ID
page-clients-table-col-denominazione = Company Name
page-clients-table-col-piva = VAT Number
page-clients-table-col-cf = Tax Code
page-clients-table-col-sdi = SDI
page-clients-table-col-pec = PEC
page-clients-table-col-comune = City
page-clients-table-col-provincia = Prov.
page-clients-table-col-created = Created
page-clients-table-col-actions = Actions

### Empty State
page-clients-no-results = No clients found for '{ $term }'
page-clients-empty-state = No clients found. Create your first client!

### Quick Add Form
page-clients-quick-add-title = Create your first client
page-clients-quick-add-description = Fill in the essential details:
page-clients-quick-add-pec-optional = PEC (optional)
page-clients-quick-add-button = Create Client

### Client Detail
page-clients-detail-title = Client Details: { $name }
page-clients-detail-id = ID
page-clients-detail-denominazione = Company Name
page-clients-detail-piva = VAT Number
page-clients-detail-cf = Tax Code
page-clients-detail-sdi = SDI
page-clients-detail-pec = PEC
page-clients-detail-phone = Phone
page-clients-detail-email = Email
page-clients-detail-address = Address
page-clients-detail-city = City
page-clients-detail-notes = Notes
page-clients-detail-na = N/A
page-clients-detail-close = Close

### Edit Client
page-clients-edit-title = Edit Client: { $name }
page-clients-edit-save = Save Changes

### Delete Client
page-clients-delete-title = Delete Client: { $name }
page-clients-delete-confirm = Are you sure you want to delete client '{ $name }'?
page-clients-delete-warning = This action cannot be undone.
page-clients-delete-yes = Yes, Delete
page-clients-delete-no = Cancel

### Quick Preview
page-clients-preview-title = Quick Preview
page-clients-preview-total = Total Clients
page-clients-preview-invoices = Total Invoices
page-clients-preview-top5 = Top 5 Clients
page-clients-preview-col-client = Client
page-clients-preview-col-invoices = No. Invoices
page-clients-preview-col-revenue = Total Revenue

### Success Messages
page-clients-success-created = Client '{ $name }' created successfully!
page-clients-success-updated = Client '{ $name }' updated!
page-clients-success-deleted = Client '{ $name }' deleted!
page-clients-success-quick-created = Client '{ $name }' created!

### Error Messages
page-clients-error-denominazione-required = Company name is required
page-clients-error-create = Error creating client: { $error }
page-clients-error-update = Error updating: { $error }
page-clients-error-delete = Error deleting: { $error }
page-clients-error-not-found = Client not found
page-clients-error-loading = Error loading clients: { $error }
page-clients-error-loading-hint = Make sure the database is initialized correctly
page-clients-error-quick-create = Error: { $error }
page-clients-preview-error = Error loading data: { $error }

### Legacy (kept for compatibility)
page-clients-search = Search clients...
page-clients-filter-type = Type
page-clients-filter-country = Country
page-clients-col-name = Name/Company Name
page-clients-col-vat = VAT Number
page-clients-col-email = Email
page-clients-col-phone = Phone
page-clients-col-invoices = Invoices
page-clients-col-revenue = Revenue
page-clients-col-actions = Actions
page-clients-action-add = Add Client
page-clients-action-create-invoice = Create Invoice
page-clients-no-clients = No clients found
page-clients-add-first = Add your first client
page-clients-total-found = { $count } clients found

## ============================================================================
## REPORTS PAGE (9__Reports.py)
## ============================================================================

page-reports-page-title = Reports - OpenFatture
page-reports-title = Reports & Analytics
page-reports-subtitle = Business reports and advanced analytics
page-reports-no-data = No data available for reports
page-reports-no-data-info = Create some invoices to see reports

### Sidebar
page-reports-filter-title = Report Parameters
page-reports-filter-year = Year
page-reports-filter-quarter = Quarter (optional)
page-reports-filter-quarter-all = All
page-reports-filter-quarter-q1 = Q1
page-reports-filter-quarter-q2 = Q2
page-reports-filter-quarter-q3 = Q3
page-reports-filter-quarter-q4 = Q4

### Tabs
page-reports-tab-revenue = Revenue
page-reports-tab-vat = VAT
page-reports-tab-clients = Clients

### Revenue Tab
page-reports-revenue-title = Revenue Report
page-reports-revenue-total = Total Revenue
page-reports-revenue-total-help = Period: { $period }
page-reports-revenue-vat-total = Total VAT
page-reports-revenue-invoices = Invoices Issued
page-reports-revenue-avg = Average Invoice Value
page-reports-revenue-monthly = Monthly Trend
page-reports-revenue-chart-title = Monthly Revenue
page-reports-revenue-chart-xaxis = Month
page-reports-revenue-chart-yaxis = Revenue (€)
page-reports-revenue-count-chart = Monthly Invoice Count
page-reports-revenue-count-yaxis = Invoice Count

### VAT Tab
page-reports-vat-title = VAT Report
page-reports-vat-taxable = Total Taxable Amount
page-reports-vat-total = Total VAT
page-reports-vat-revenue-total = Total Revenue
page-reports-vat-breakdown-title = Breakdown by VAT Rate
page-reports-vat-pie-title = Taxable Amount Distribution by VAT Rate
page-reports-vat-detail-title = Detail by Rate
page-reports-vat-table-rate = VAT Rate
page-reports-vat-table-taxable = Taxable Amount
page-reports-vat-table-vat = VAT
page-reports-vat-table-total = Total

### Clients Tab
page-reports-clients-title = Clients Report
page-reports-clients-active = Active Clients
page-reports-clients-active-help = Clients with invoices issued in { $year }
page-reports-clients-top-title = Top Clients by Revenue
page-reports-clients-table-client = Client
page-reports-clients-table-invoices = Invoices
page-reports-clients-table-total = Total
page-reports-clients-table-last = Last Invoice
page-reports-clients-chart-title = Top 10 Clients by Revenue
page-reports-clients-chart-xaxis = Client
page-reports-clients-chart-yaxis = Revenue (€)

### Export
page-reports-export-title = Export Reports
page-reports-export-revenue = Export Revenue (CSV)
page-reports-export-vat = Export VAT (CSV)
page-reports-export-clients = Export Clients (CSV)
page-reports-export-download = Download CSV

page-reports-footer = <strong>Automatically updated reports</strong> • Data based on delivered or accepted invoices

## ============================================================================
## HOOKS PAGE (10__Hooks.py)
## ============================================================================

page-hooks-page-title = Hooks & Automation - OpenFatture
page-hooks-title = Hooks & Automation
page-hooks-subtitle = Automated workflow and trigger management

### Summary Metrics
page-hooks-metric-total = Total Hooks
page-hooks-metric-enabled = Active Hooks
page-hooks-metric-pre = Pre-hooks
page-hooks-metric-post = Post-hooks

### Tabs
page-hooks-tab-overview = Overview
page-hooks-tab-manage = Manage
page-hooks-tab-create = Create Hook
page-hooks-tab-test = Test

### Overview Tab
page-hooks-overview-title = Hooks Overview
page-hooks-overview-group-pre =
page-hooks-overview-group-post =
page-hooks-overview-group-on =
page-hooks-overview-status-active = Active
page-hooks-overview-status-inactive = Inactive
page-hooks-overview-timeout = { $timeout }s
page-hooks-overview-empty = No hooks found. Create your first hook in the 'Create Hook' tab!

### Manage Tab
page-hooks-manage-title = Manage Hooks
page-hooks-manage-toggle-title = Toggle Hook Status
page-hooks-manage-toggle-label = Activate { $name }
page-hooks-manage-toggle-help = Enable/disable the { $name } hook
page-hooks-manage-toggle-enabled = Hook '{ $name }' activated
page-hooks-manage-toggle-disabled = Hook '{ $name }' deactivated
page-hooks-manage-toggle-error = Error updating hook status
page-hooks-manage-details-button = Details
page-hooks-manage-details-help = Show hook details
page-hooks-manage-details-title = Details { $name }
page-hooks-manage-empty = No hooks to manage

### Create Tab
page-hooks-create-title = Create New Hook
page-hooks-create-name-label = Hook Name
page-hooks-create-name-placeholder = e.g.: post-invoice-send
page-hooks-create-name-help = Hook name (use pre-, post-, on- prefixes)
page-hooks-create-type-label = Script Type
page-hooks-create-type-help = Hook script type
page-hooks-create-type-bash = bash
page-hooks-create-type-python = python
page-hooks-create-desc-label = Description
page-hooks-create-desc-placeholder = What does this hook do...
page-hooks-create-desc-help = Brief hook description
page-hooks-create-event-label = Event Type
page-hooks-create-event-help = When the hook is executed
page-hooks-create-event-pre = pre
page-hooks-create-event-post = post
page-hooks-create-event-on = on
page-hooks-create-preview-title = Template Preview
page-hooks-create-preview-code = Template Code
page-hooks-create-button = Create Hook
page-hooks-create-error-name = Enter a name for the hook
page-hooks-create-warning-prefix = Tip: name should start with '{ $prefix }-'
page-hooks-create-success = { $message }
page-hooks-create-reload = Reload the page to see the new hook
page-hooks-create-error = { $message }

### Test Tab
page-hooks-test-title = Test Hooks
page-hooks-test-select-label = Select Hook to Test
page-hooks-test-select-help = Choose the hook to validate
page-hooks-test-info-title = Hook Information
page-hooks-test-metric-type = Event Type
page-hooks-test-metric-status = Status
page-hooks-test-metric-timeout = Timeout
page-hooks-test-metric-status-active = Active
page-hooks-test-metric-status-inactive = Inactive
page-hooks-test-validate-button = Validate Hook
page-hooks-test-validating = Validating hook...
page-hooks-test-success = Hook validated successfully!
page-hooks-test-metric-lines = Code Lines
page-hooks-test-metric-size = Size
page-hooks-test-metric-size-value = { $size } bytes
page-hooks-test-metric-executable = Executable
page-hooks-test-metric-executable-yes = Yes
page-hooks-test-metric-executable-no = No
page-hooks-test-result-message = { $message }
page-hooks-test-error = Validation error: { $error }
page-hooks-test-show-code = Show Code
page-hooks-test-code-error = Hook file not found
page-hooks-test-read-error = File read error: { $error }
page-hooks-test-empty = No hooks available for testing

page-hooks-footer =
    <strong>Hooks System:</strong> Event-based workflow automation •
    <strong>Directory:</strong> ~/.openfatture/hooks/ •
    <strong>Documentation:</strong> See CLI for advanced examples

## ============================================================================
## EVENTS PAGE (11__Events.py)
## ============================================================================

page-events-page-title = Events & Audit Trail - OpenFatture
page-events-title = Events & Audit Trail
page-events-subtitle = System event tracking and audit trail

### Summary Metrics
page-events-metric-total = Total Events
page-events-metric-total-help = Last { $days } days
page-events-metric-daily-avg = Daily Events
page-events-metric-types = Event Types
page-events-metric-entities = Tracked Entities

### Sidebar Filters
page-events-filter-title = Event Filters
page-events-filter-period = Period (days)
page-events-filter-period-help = Number of days to analyze
page-events-filter-type = Event Type
page-events-filter-type-all = All
page-events-filter-type-help = Filter by event type
page-events-filter-entity-type = Entity Type
page-events-filter-entity-type-help = Filter by entity type
page-events-filter-search = Search
page-events-filter-search-placeholder = Search in events...
page-events-filter-search-help = Search by event type or entity

### Tabs
page-events-tab-recent = Recent
page-events-tab-filtered = Filtered
page-events-tab-stats = Statistics
page-events-tab-timeline = Timeline

### Recent Tab
page-events-recent-title = Recent Events
page-events-table-timestamp = Timestamp
page-events-table-type = Event Type
page-events-table-entity = Entity
page-events-table-description = Description
page-events-table-user = User
page-events-table-user-system = System
page-events-details-button = Show Details
page-events-details-help = Show full event details
page-events-details-title = Event { $num }: { $desc }
page-events-empty = No events found in database

### Filtered Tab
page-events-filtered-title = Filtered Events
page-events-filtered-found = Found { $count } events
page-events-export-button = Export CSV
page-events-export-help = Export filtered results as CSV
page-events-export-download = Download CSV
page-events-filtered-empty = No events found with selected filters

### Stats Tab
page-events-stats-title = Event Statistics
page-events-stats-by-type = Events by Type
page-events-stats-type-col = Event Type
page-events-stats-count-col = Count
page-events-stats-by-entity = Events by Entity
page-events-stats-entity-col = Entity Type
page-events-stats-daily = Daily Activity (Last 7 Days)

### Timeline Tab
page-events-timeline-title = Entity Timeline
page-events-timeline-entity-type = Entity Type
page-events-timeline-entity-type-help = Select entity type
page-events-timeline-entity-id = Entity ID
page-events-timeline-entity-id-placeholder = e.g.: INV-001, CLI-001
page-events-timeline-entity-id-help = Enter the entity ID to track
page-events-timeline-found = Found { $count } events for { $type } { $id }
page-events-timeline-event-time = **{ $time }**
page-events-timeline-event-type = { $type }
page-events-timeline-event-details = Details
page-events-timeline-empty = No events found for { $type } { $id }
page-events-timeline-info = Select an entity type and enter an ID to see the timeline

page-events-footer =
    <strong>Event System:</strong> Complete audit trail for compliance and debugging •
    <strong>Search:</strong> Filter by type, entity and period •
    <strong>Analytics:</strong> Activity statistics and entity timeline

## ============================================================================
## HEALTH PAGE (12__Health.py)
## ============================================================================

page-health-page-title = System Health - OpenFatture
page-health-title = System Health Dashboard
page-health-subtitle = Real-time monitoring and diagnostics

### Usage Metrics
page-health-usage-title = Usage Metrics
page-health-metric-visits = Total Page Visits
page-health-metric-unique = Unique Pages
page-health-metric-session = Session Start

### Cache Statistics
page-health-cache-title = Cache Statistics
page-health-cache-cleanup = Cleaned up { $count } expired cache entries
page-health-metric-entries = Total Cache Entries
page-health-metric-functions = Cached Functions
page-health-clear-all = Clear All Caches
page-health-clear-success = All caches cleared!
page-health-cache-breakdown = Cache Breakdown by Function
page-health-table-function = Function
page-health-table-entries = Entries
page-health-cache-management = Selective Cache Management
page-health-clear-invoices = Clear Invoice Caches
page-health-clear-clients = Clear Client Caches
page-health-clear-payments = Clear Payment Caches
page-health-cleared-category = Cleared { $count } { $category } caches

### Page Visits
page-health-visits-breakdown = Page Visit Breakdown
page-health-table-page = Page
page-health-table-visits = Visits

### API Health
page-health-api-title = API Health Endpoint
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

page-health-api-sample = Show Sample Health Check JSON
page-health-best-practice =
    **Best Practice:** Monitor this dashboard regularly to catch issues early.
    Set up alerts for "unhealthy" or "degraded" statuses in production.
