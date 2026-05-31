# Web Pages translations - Spanish
# Traducciones específicas para las páginas de la interfaz web Streamlit

## ============================================================================
## HOME PAGE (app.py)
## ============================================================================

page-home-title = OpenFatture
page-home-welcome = Bienvenido a OpenFatture
page-home-subtitle = Sistema de Facturación Electrónica de Código Abierto
page-home-description =
    OpenFatture es un sistema completo para la gestión de la facturación electrónica
    italiana, con integración SDI, IA y pagos Lightning.

page-home-features-title = Características Principales
page-home-feature-invoicing = Facturación electrónica completa con FatturaPA
page-home-feature-sdi = Integración directa con SDI (Sistema de Intercambio)
page-home-feature-ai = Asistente IA para descripciones y sugerencias de IVA
page-home-feature-payments = Conciliación automática de pagos bancarios
page-home-feature-lightning = Soporte de pagos Lightning Network
page-home-feature-batch = Operaciones por lotes para importación/exportación masiva

## Feature Grid
page-home-feature-grid-invoices-title = Facturas
page-home-feature-grid-invoices-item-1 = Creación guiada
page-home-feature-grid-invoices-item-2 = Gestión de clientes
page-home-feature-grid-invoices-item-3 = Generación XML
page-home-feature-grid-invoices-item-4 = Envío SDI vía PEC
page-home-feature-grid-invoices-item-5 = Seguimiento de notificaciones
page-home-feature-grid-invoices-button = Ir a Facturas

page-home-feature-grid-payments-title = Pagos
page-home-feature-grid-payments-item-1 = Importar extractos bancarios
page-home-feature-grid-payments-item-2 = Conciliación automática
page-home-feature-grid-payments-item-3 = Reconciliación
page-home-feature-grid-payments-item-4 = Recordatorios de vencimiento
page-home-feature-grid-payments-item-5 = Pista de auditoría
page-home-feature-grid-payments-button = Ir a Pagos

page-home-feature-grid-ai-title = Asistente IA
page-home-feature-grid-ai-item-1 = Chat interactivo
page-home-feature-grid-ai-item-2 = Descripciones automáticas
page-home-feature-grid-ai-item-3 = Consultoría fiscal
page-home-feature-grid-ai-item-4 = Previsión de flujo de caja
page-home-feature-grid-ai-item-5 = Verificación de cumplimiento
page-home-feature-grid-ai-button = Probar la IA

## Quick Actions
page-home-quick-actions = Acciones Rápidas
page-home-action-new-invoice = Nueva Factura
page-home-action-new-client = Nuevo Cliente
page-home-action-dashboard = Panel de Control
page-home-action-batch = Operaciones por Lotes

## Advanced Tools
page-home-advanced-tools = Herramientas Avanzadas
page-home-advanced-reports = Informes
page-home-advanced-hooks = Hooks
page-home-advanced-events = Eventos

## Getting Started
page-home-getting-started = Primeros Pasos
page-home-getting-started-title = Primeros Pasos

page-home-step-1-title = 1. Configure el entorno
page-home-step-1-item-1 = Asegúrese de que `.env` esté configurado correctamente
page-home-step-1-item-2 = Verifique los datos de la empresa (CIF/NIF, régimen fiscal)
page-home-step-1-item-3 = Configure las credenciales PEC para envío SDI

page-home-step-2-title = 2. Cree sus primeros clientes
page-home-step-2-item-1 = Vaya a "Clientes" "Agregar Cliente"
page-home-step-2-item-2 = Ingrese los datos fiscales (CIF/NIF, código fiscal)
page-home-step-2-item-3 = Especifique SDI o PEC para recepción de facturas

page-home-step-3-title = 3. Emita su primera factura
page-home-step-3-item-1 = "Facturas" "Nueva Factura"
page-home-step-3-item-2 = Seleccione cliente y agregue líneas
page-home-step-3-item-3 = Genere XML y envíe a SDI

page-home-step-4-title = 4. Explore el Asistente IA
page-home-step-4-item-1 = Pruebe el chat para preguntas fiscales
page-home-step-4-item-2 = Genere descripciones inteligentes
page-home-step-4-item-3 = Obtenga sugerencias de IVA automáticas

page-home-docs-title = Documentación

## Footer
page-home-footer-version = OpenFatture v{ $version }
page-home-footer-license = Licencia MIT
page-home-footer-tagline = Hecho con por freelancers, para freelancers

page-home-help = Ayuda y Documentación
page-home-github = Repositorio GitHub
page-home-report-bug = Reportar un Error
page-home-about = Acerca de

## ============================================================================
## DASHBOARD PAGE (1__Dashboard.py)
## ============================================================================

page-dashboard-title = Panel de Control
page-dashboard-subtitle = Vista General del Negocio en Tiempo Real

### KPI Cards
page-dashboard-kpi-section = Métricas Principales
page-dashboard-kpi-total-invoices = Total Facturas
page-dashboard-kpi-total-revenue = Facturación Total
page-dashboard-kpi-total-clients = Clientes Activos
page-dashboard-kpi-revenue-month = Facturación Mensual
page-dashboard-kpi-pending-payments = Pagos Pendientes
page-dashboard-kpi-avg-invoice = Importe Medio por Factura
page-dashboard-kpi-this-month = Este Mes
page-dashboard-kpi-this-year = Este Año
page-dashboard-kpi-growth = Crecimiento

### Charts
page-dashboard-chart-invoices-by-status = Facturas por Estado
page-dashboard-chart-revenue-6-months = Facturación Últimos 6 Meses
page-dashboard-chart-yaxis-revenue = Facturación (€)
page-dashboard-chart-xaxis-month = Mes
page-dashboard-chart-revenue-title = Tendencia de Facturación
page-dashboard-chart-invoices-title = Facturas por Mes
page-dashboard-chart-clients-title = Principales Clientes
page-dashboard-chart-status-title = Facturas por Estado
page-dashboard-chart-payments-title = Estado de Pagos

### Tables
page-dashboard-top-clients = Top 5 Clientes
page-dashboard-recent-invoices = Últimas 5 Facturas
page-dashboard-col-client = Cliente
page-dashboard-col-num-invoices = N.º Facturas
page-dashboard-col-num-invoices-short = Facturas
page-dashboard-col-revenue = Facturación
page-dashboard-col-number = Número
page-dashboard-col-date = Fecha
page-dashboard-col-total = Total
page-dashboard-col-status = Estado
page-dashboard-col-invoice = Factura
page-dashboard-col-due-date = Vencimiento
page-dashboard-col-days = Días
page-dashboard-col-days-delta = Δ Días
page-dashboard-col-days-help = Días hasta vencimiento
page-dashboard-col-residual = Pendiente
page-dashboard-col-residual-amount = Importe Pendiente
page-dashboard-col-category = Categoría

### Payment Tracking
page-dashboard-payment-tracking = Seguimiento de Pagos
page-dashboard-payment-unmatched = Sin Emparejar
page-dashboard-payment-matched = Emparejados
page-dashboard-payment-ignored = Ignorados
page-dashboard-payment-total = Total Transacciones
page-dashboard-payment-due-30 = Vencimientos de Pago (Próximos 30 días)
page-dashboard-total-outstanding = Total Pendiente de Cobro
page-dashboard-category-overdue = Vencido
page-dashboard-category-due-soon = Próximo a vencer
page-dashboard-category-upcoming = Próximo

### Messages
page-dashboard-no-invoices = No hay facturas disponibles
page-dashboard-no-data = No hay datos disponibles
page-dashboard-no-clients = No hay clientes disponibles
page-dashboard-no-payments-due = No hay pagos pendientes
page-dashboard-error-loading = Error al cargar el panel: { $error }
page-dashboard-refresh-button = Actualizar Datos

### Recent Activity
page-dashboard-recent-activity = Actividad Reciente

## ============================================================================
## INVOICES PAGE (2__Fatture.py)
## ============================================================================

page-invoices-title = Gestión de Facturas
page-invoices-subtitle = Visualice y gestione todas sus facturas

### Sidebar Filters
page-invoices-filter-title = Filtros
page-invoices-filter-year = Año
page-invoices-filter-all = Todos
page-invoices-filter-status = Estado
page-invoices-filter-max-results = Resultados máximos
page-invoices-no-invoices-in-db = No hay facturas disponibles
page-invoices-filter-client = Cliente
page-invoices-filter-date-from = Desde Fecha
page-invoices-filter-date-to = Hasta Fecha
page-invoices-filter-amount-min = Importe Mínimo
page-invoices-filter-amount-max = Importe Máximo
page-invoices-filter-search = Buscar facturas...

### Quick Actions
page-invoices-action-quick-title = Acciones Rápidas
page-invoices-action-new-invoice = Nueva Factura
page-invoices-action-new-invoice-info =
    **Función en desarrollo**

    Por ahora, cree facturas mediante CLI:
    ```bash
    uv run openfatture fattura crea
    ```

    ¡La creación guiada en la interfaz web estará disponible pronto!
page-invoices-action-refresh = Actualizar Lista

### Main Content
page-invoices-list-title = ### Lista de Facturas
page-invoices-no-invoices-found = No se encontraron facturas con los filtros seleccionados

### Stats Metrics
page-invoices-stats-count = Facturas Encontradas
page-invoices-stats-total = Total
page-invoices-stats-statuses = Estados Diferentes
page-invoices-stats-average = Importe Promedio

### Table
page-invoices-table-title = #### Tabla de Facturas
page-invoices-col-id = ID
page-invoices-col-number = Número
page-invoices-col-date = Fecha
page-invoices-col-client = Cliente
page-invoices-col-total-eur = Total €
page-invoices-col-status = Estado
page-invoices-col-lines = Líneas
page-invoices-col-amount = Importe
page-invoices-col-payment = Pago
page-invoices-col-actions = Acciones

### Invoice Detail Section
page-invoices-detail-title = ### Detalle de Factura
page-invoices-detail-input-id = Ingrese ID de factura para visualizar
page-invoices-detail-show-button = Mostrar Detalle
page-invoices-detail-error-not-found = Factura con ID { $id } no encontrada
page-invoices-detail-success = Factura { $number }/{ $year }

### Detail Header Metrics
page-invoices-detail-number = Número
page-invoices-detail-date = Fecha de Emisión
page-invoices-detail-client = Cliente
page-invoices-detail-type = Tipo
page-invoices-detail-status = Estado
page-invoices-detail-sdi-number = Número SDI

### Detail Line Items
page-invoices-detail-lines-title = #### Líneas de Factura
page-invoices-detail-lines-col-num = #
page-invoices-detail-lines-col-desc = Descripción
page-invoices-detail-lines-col-qty = Cantidad
page-invoices-detail-lines-col-price = Precio €
page-invoices-detail-lines-col-vat = IVA %
page-invoices-detail-lines-col-total = Total €
page-invoices-detail-lines-empty = No hay líneas disponibles

### Detail Totals
page-invoices-detail-totals-title = #### Totales
page-invoices-detail-totals-taxable = Base Imponible
page-invoices-detail-totals-vat = IVA
page-invoices-detail-totals-withholding = Retención
page-invoices-detail-totals-stamp = Sello
page-invoices-detail-totals-total = **TOTAL**

### Detail Files
page-invoices-detail-files-title = #### Archivos
page-invoices-detail-files-xml-exists = XML: `{ $path }`
page-invoices-detail-files-xml-missing = XML aún no generado
page-invoices-detail-files-pdf-exists = PDF: `{ $path }`
page-invoices-detail-files-pdf-missing = PDF aún no generado

### Detail Actions
page-invoices-detail-actions-title = #### Acciones
page-invoices-detail-actions-generate-xml = Generar XML
page-invoices-detail-actions-generating-xml = Generando XML...
page-invoices-detail-actions-error = Error: { $error }
page-invoices-detail-actions-xml-success = ¡XML generado con éxito!
page-invoices-detail-actions-send-sdi = Enviar a SDI
page-invoices-detail-actions-generate-pdf = Generar PDF
page-invoices-detail-actions-cli-feature = Función CLI

### Error Messages
page-invoices-error-loading = Error al cargar facturas: { $error }

### Legacy (kept for compatibility)
page-invoices-action-view = Ver
page-invoices-action-edit = Editar
page-invoices-action-delete = Eliminar
page-invoices-action-send = Enviar a SDI
page-invoices-action-download-xml = Descargar XML
page-invoices-action-download-pdf = Descargar PDF
page-invoices-action-duplicate = Duplicar
page-invoices-no-invoices = No se encontraron facturas
page-invoices-create-first = Cree su primera factura
page-invoices-total-found = { $count } facturas encontradas
page-invoices-selected = { $count } seleccionadas

## ============================================================================
## INVOICE CREATION PAGE (13__Crea_Fattura.py)
## ============================================================================

### Page Configuration
page-invoice-create-page-title = Crear Factura - OpenFatture
page-invoice-create-title = Creación Guiada de Factura

### Wizard Progress
page-invoice-create-wizard-title = Creación de Factura - Paso { $step }/{ $total }

### Step Labels
page-invoice-create-step-1-label = Seleccionar Cliente
page-invoice-create-step-2-label = Detalles de Factura
page-invoice-create-step-3-label = Agregar Productos
page-invoice-create-step-4-label = Asistencia IA
page-invoice-create-step-5-label = Resumen y Crear

### Step 1: Select Client
page-invoice-create-step-1-header = Seleccionar Cliente
page-invoice-create-client-search-label = Buscar cliente existente
page-invoice-create-client-search-placeholder = Nombre empresa, NIF/CIF...
page-invoice-create-client-search-help = Deje en blanco para ver todos los clientes
page-invoice-create-client-existing-title = Clientes existentes
page-invoice-create-client-vat-label = NIF/CIF
page-invoice-create-client-select-label = Seleccionar cliente
page-invoice-create-client-select-help = Elija un cliente existente o cree uno nuevo
page-invoice-create-client-create-title = O crear nuevo cliente
page-invoice-create-client-create-expander = Crear nuevo cliente
page-invoice-create-client-name-label = Nombre de Empresa *
page-invoice-create-client-name-placeholder = Nombre de empresa o persona
page-invoice-create-client-vat-input-label = NIF/CIF
page-invoice-create-client-vat-placeholder = 12345678901
page-invoice-create-client-fiscal-code-label = Código Fiscal
page-invoice-create-client-fiscal-code-placeholder = Código fiscal (si es persona física)
page-invoice-create-client-address-label = Dirección
page-invoice-create-client-address-placeholder = Calle Roma 123, 00100 Roma
page-invoice-create-client-email-label = Email
page-invoice-create-client-email-placeholder = cliente@email.com
page-invoice-create-client-phone-label = Teléfono
page-invoice-create-client-phone-placeholder = +34 123 456 789
page-invoice-create-client-regime-label = Régimen Fiscal
page-invoice-create-client-regime-ordinary = RF01 - Ordinario
page-invoice-create-client-regime-flat = RF19 - Módulos
page-invoice-create-client-create-button = Crear Cliente
page-invoice-create-client-name-required = El nombre de empresa es obligatorio
page-invoice-create-client-create-success = ¡Cliente '{ $name }' creado con éxito!
page-invoice-create-client-create-error = Error al crear el cliente: { $error }

### Step 2: Invoice Details
page-invoice-create-step-2-header = Detalles de Factura
page-invoice-create-details-client-selected = Cliente seleccionado: **{ $name }**
page-invoice-create-details-regime = Régimen fiscal: { $regime }
page-invoice-create-details-number-label = Número de Factura
page-invoice-create-details-number-help = Número secuencial de la factura
page-invoice-create-details-year-label = Año
page-invoice-create-details-year-help = Año fiscal
page-invoice-create-details-date-label = Fecha de Emisión
page-invoice-create-details-date-help = Fecha de emisión de la factura
page-invoice-create-details-due-date-label = Fecha de Vencimiento
page-invoice-create-details-due-date-help = Fecha de vencimiento del pago
page-invoice-create-details-additional-title = Detalles Adicionales
page-invoice-create-details-subject-label = Asunto/Descripción
page-invoice-create-details-subject-placeholder = Descripción general de la factura...
page-invoice-create-details-subject-help = Descripción general de servicios/productos
page-invoice-create-details-notes-label = Notas
page-invoice-create-details-notes-placeholder = Notas adicionales...
page-invoice-create-details-notes-help = Notas internas o de factura

### Step 3: Invoice Lines
page-invoice-create-step-3-header = Productos y Servicios
page-invoice-create-lines-title = Líneas de factura
page-invoice-create-lines-description-label = Descripción
page-invoice-create-lines-quantity-label = Cantidad
page-invoice-create-lines-price-label = Precio Unitario (€)
page-invoice-create-lines-row-total = Total línea: { $total }
page-invoice-create-lines-remove-button = Eliminar
page-invoice-create-lines-add-title = Agregar nueva línea
page-invoice-create-lines-description-input-label = Descripción *
page-invoice-create-lines-description-placeholder = Descripción del producto/servicio...
page-invoice-create-lines-quantity-input-label = Cantidad
page-invoice-create-lines-quantity-help = Cantidad del producto/servicio
page-invoice-create-lines-price-input-label = Precio Unitario (€)
page-invoice-create-lines-price-help = Precio unitario sin IVA
page-invoice-create-lines-vat-label = Tipo de IVA
page-invoice-create-lines-vat-help = Tipo de IVA aplicable
page-invoice-create-lines-add-button = Agregar Línea
page-invoice-create-lines-description-required = La descripción es obligatoria
page-invoice-create-lines-add-success = ¡Línea agregada!
page-invoice-create-lines-totals-title = Totales
page-invoice-create-lines-subtotal-label = Base Imponible
page-invoice-create-lines-vat-amount-label = IVA
page-invoice-create-lines-total-label = Total

### Step 4: AI Assistance
page-invoice-create-step-4-header = Asistencia IA
page-invoice-create-ai-description-title = Generar Descripciones con IA
page-invoice-create-ai-description-button = Sugerir descripciones para líneas
page-invoice-create-ai-description-no-lines = Primero agregue líneas a la factura
page-invoice-create-ai-description-generating = Generando descripciones...
page-invoice-create-ai-description-improved = ¡Descripción de línea { $row } mejorada!
page-invoice-create-ai-description-error = Error al generar descripción para línea { $row }: { $error }
page-invoice-create-ai-vat-title = Consejos de IVA
page-invoice-create-ai-vat-button = Verificar tipos de IVA
page-invoice-create-ai-vat-no-lines = Primero agregue líneas a la factura
page-invoice-create-ai-vat-checking = Verificando tipos de IVA...
page-invoice-create-ai-vat-suggestion = Línea { $row }: Tipo de IVA sugerido { $suggested }% en lugar de { $current }%
page-invoice-create-ai-vat-apply = Aplicar { $rate }% a línea { $row }
page-invoice-create-ai-vat-updated = ¡Tipo de IVA actualizado!
page-invoice-create-ai-vat-info = Línea { $row }: { $info }
page-invoice-create-ai-vat-error = Error al verificar IVA para línea { $row }: { $error }
page-invoice-create-ai-compliance-title = Verificación de Conformidad
page-invoice-create-ai-compliance-button = Verificar conformidad de factura
page-invoice-create-ai-compliance-no-number = Falta número de factura
page-invoice-create-ai-compliance-no-lines = No hay líneas de factura
page-invoice-create-ai-compliance-line-no-desc = Línea { $row }: falta descripción
page-invoice-create-ai-compliance-line-qty-invalid = Línea { $row }: la cantidad debe ser > 0
page-invoice-create-ai-compliance-line-price-invalid = Línea { $row }: el precio unitario debe ser > 0
page-invoice-create-ai-compliance-issues-found = Problemas encontrados
page-invoice-create-ai-compliance-success = ¡La factura cumple con los requisitos básicos!

### Step 5: Summary
page-invoice-create-step-5-header = Resumen y Creación
page-invoice-create-summary-client-title = Cliente
page-invoice-create-summary-client-vat = NIF/CIF: { $vat }
page-invoice-create-summary-client-regime = Régimen: { $regime }
page-invoice-create-summary-invoice-title = Factura
page-invoice-create-summary-invoice-date = Emisión: { $date }
page-invoice-create-summary-invoice-due = Vencimiento: { $date }
page-invoice-create-summary-lines-title = Líneas de Factura
page-invoice-create-summary-table-description = Descripción
page-invoice-create-summary-table-quantity = Cant.
page-invoice-create-summary-table-price = Precio
page-invoice-create-summary-table-vat = IVA
page-invoice-create-summary-table-total = Total
page-invoice-create-summary-totals-title = Totales
page-invoice-create-summary-totals-subtotal = Base Imponible
page-invoice-create-summary-totals-vat = IVA
page-invoice-create-summary-totals-total = Total Factura
page-invoice-create-summary-create-button = Crear Factura
page-invoice-create-summary-creating = Creando factura...
page-invoice-create-summary-error-create-failed = No se puede crear la factura
page-invoice-create-summary-success = ¡Factura { $number }/{ $year } creada con éxito!
page-invoice-create-summary-next-steps =
    **Próximos pasos:**
    1. **Validar** la factura: `openfatture fattura valida { $number }`
    2. **Enviar** a SDI: `openfatture pec invia { $number }`
    3. **Monitorear** estado en la página de Facturas
page-invoice-create-summary-error = Error al crear la factura: { $error }

### Navigation
page-invoice-create-nav-back = Atrás
page-invoice-create-nav-next = Siguiente
page-invoice-create-nav-success = ¡Factura creada con éxito!
page-invoice-create-nav-create-another = Crear otra factura

## ============================================================================
## CLIENTS PAGE (3__Clienti.py)
## ============================================================================

page-clients-title = Gestión de Clientes
page-clients-subtitle = Visualice y gestione sus clientes

### Filters
page-clients-search = Buscar clientes...
page-clients-filter-type = Tipo
page-clients-filter-country = País

### Table Headers
page-clients-col-name = Nombre/Razón Social
page-clients-col-vat = CIF/NIF
page-clients-col-email = Email
page-clients-col-phone = Teléfono
page-clients-col-invoices = Facturas
page-clients-col-revenue = Facturación
page-clients-col-actions = Acciones

### Actions
page-clients-action-add = Agregar Cliente
page-clients-action-view = Ver
page-clients-action-edit = Editar
page-clients-action-delete = Eliminar
page-clients-action-create-invoice = Crear Factura

### Messages
page-clients-no-clients = No se encontraron clientes
page-clients-add-first = Agregue su primer cliente
page-clients-total-found = { $count } clientes encontrados

## ============================================================================
## ============================================================================
## PAYMENTS PAGE (4__Pagamenti.py)
## ============================================================================

### Page Config
page-payments-page-title = Pagos - OpenFatture
page-payments-title = Seguimiento y Conciliación de Pagos

### Sidebar Filters
page-payments-filter-title = Filtros
page-payments-filter-bank-account = Cuenta Bancaria
page-payments-filter-all-accounts = Todas
page-payments-filter-status = Estado
page-payments-no-accounts-configured = No hay cuentas bancarias configuradas

### Status Labels
page-payments-status-all = Todas
page-payments-status-unmatched = Por Conciliar
page-payments-status-matched = Conciliadas
page-payments-status-ignored = Ignoradas
page-payments-status-paired = Emparejadas

### Sidebar Actions
page-payments-action-import = Importar
page-payments-action-import-help = Importar extracto bancario
page-payments-action-refresh = Actualizar

### Import Form
page-payments-import-title = Importar Extracto Bancario
page-payments-import-select-account = Seleccionar cuenta bancaria *
page-payments-import-select-account-help = Elige la cuenta donde importar las transacciones
page-payments-import-no-account-error = No hay cuentas bancarias configuradas. Crea una antes de importar.
page-payments-import-file-label = Seleccionar archivo de extracto
page-payments-import-file-help = Soporta formatos: OFX, QFX, CSV, QIF
page-payments-import-bank-preset = Banco (para CSV)
page-payments-import-bank-preset-help = Selecciona el banco para el análisis correcto del CSV
page-payments-import-auto-match = Auto-emparejar pagos
page-payments-import-auto-match-help = Intenta automáticamente emparejar las transacciones con facturas
page-payments-import-confidence = Umbral de confianza
page-payments-import-confidence-help = Confianza mínima para auto-emparejamiento
page-payments-import-button = Importar Transacciones
page-payments-import-error-no-account = Selecciona una cuenta bancaria
page-payments-import-error-no-file = Selecciona un archivo para importar
page-payments-import-importing = Importando transacciones...
page-payments-import-metric-imported = Transacciones Importadas
page-payments-import-metric-errors = Errores
page-payments-import-metric-duplicates = Duplicados
page-payments-import-format-detected = Formato detectado: { $format }
page-payments-import-errors-title = Errores durante la importación
page-payments-import-success-refresh = ¡Datos actualizados!
page-payments-import-close = Cerrar

### Bank Accounts Overview
page-payments-accounts-title = Cuentas Bancarias
page-payments-accounts-current-balance = Saldo Actual
page-payments-accounts-iban = IBAN: ...{ $last4 }
page-payments-accounts-bank = Banco: { $name }

### Payment Statistics
page-payments-stats-title = Estadísticas de Pagos
page-payments-stats-accounts = Cuentas Bancarias
page-payments-stats-transactions = Transacciones Totales
page-payments-stats-balance = Saldo Total
page-payments-stats-reconciled = Conciliadas
page-payments-stats-distribution-title = Distribución por Estado
page-payments-stats-distribution-status = Estado
page-payments-stats-distribution-transactions = Transacciones

### Transactions List
page-payments-transactions-title = Transacciones
page-payments-table-col-id = ID
page-payments-table-col-date = Fecha
page-payments-table-col-amount = Importe
page-payments-table-col-description = Descripción
page-payments-table-col-reference = Referencia
page-payments-table-col-status = Estado
page-payments-table-col-invoice = Factura
page-payments-table-col-actions = Acciones
page-payments-action-view-details = Ver detalles
page-payments-action-match = Conciliar
page-payments-transactions-summary = **Total mostrado:** { $total } de { $count } transacciones
page-payments-no-transactions-filtered = No se encontraron transacciones con los filtros seleccionados
page-payments-no-transactions = No hay transacciones

### Quick Start Guide
page-payments-quickstart-title = Cómo empezar con pagos
page-payments-quickstart-content =
    ### Primeros Pasos

    1. **Añadir una cuenta bancaria**
       ```bash
       uv run openfatture payment account add "Cuenta Negocio" --iban IT123...
       ```

    2. **Importar un extracto bancario**
       ```bash
       uv run openfatture payment import extracto.ofx --account 1
       ```

    3. **Conciliar automáticamente**
       ```bash
       uv run openfatture payment match --auto-apply
       ```

    4. **Verificar conciliaciones**
       ```bash
       uv run openfatture payment status
       ```

### Error Messages
page-payments-error-loading = Error al cargar pagos: { $error }
page-payments-error-loading-hint = Verifica que la base de datos esté inicializada correctamente

### Transaction Detail Modal
page-payments-detail-title = Detalles de Transacción { $id }...
page-payments-detail-id = ID
page-payments-detail-date = Fecha
page-payments-detail-amount = Importe
page-payments-detail-description = Descripción
page-payments-detail-reference = Referencia
page-payments-detail-counterparty = Contraparte
page-payments-detail-status = Estado
page-payments-detail-confidence = Confianza de Emparejamiento
page-payments-detail-linked-invoice = Factura Vinculada
page-payments-detail-close = Cerrar
page-payments-detail-not-found = Transacción no encontrada

### Match Transaction Modal
page-payments-match-title = Conciliar Transacción { $amount }
page-payments-match-date = Fecha
page-payments-match-amount = Importe
page-payments-match-description = Descripción
page-payments-match-reference = Referencia
page-payments-match-counterparty = Contraparte
page-payments-match-status = Estado
page-payments-match-suggestions-title = Emparejamientos Sugeridos
page-payments-match-client = Cliente: { $client }
page-payments-match-confidence = Confianza
page-payments-match-days-diff = ±{ $days } días
page-payments-match-button = Emparejar
page-payments-match-matching = Emparejando transacción...
page-payments-match-success = Transacción emparejada con factura { $number }
page-payments-match-error = Error: { $error }
page-payments-match-no-suggestions = No se encontraron emparejamientos automáticos
page-payments-match-manual-title = Búsqueda Manual
page-payments-match-manual-search = Buscar factura
page-payments-match-manual-placeholder = Número de factura, cliente...
page-payments-match-manual-help = Introduce número de factura o nombre de cliente
page-payments-match-manual-results = Resultados de búsqueda:
page-payments-match-manual-button = Emparejar
page-payments-match-manual-success = ¡Emparejada!
page-payments-match-manual-no-results = No se encontraron facturas
page-payments-match-close = Cerrar

### Quick Stats Section
page-payments-quick-stats-title = ### Estadísticas de Pagos
page-payments-quick-stats-unmatched = No Emparejadas
page-payments-quick-stats-matched = Emparejadas
page-payments-quick-stats-ignored = Ignoradas
page-payments-quick-stats-total = Total
page-payments-quick-stats-error = Error al cargar datos: { $error }

### Payment Due Section
page-payments-due-title = ### Vencimientos Próximos 30 Días
page-payments-due-col-invoice = Factura
page-payments-due-col-client = Cliente
page-payments-due-col-due-date = Vencimiento
page-payments-due-col-residual = Pendiente
page-payments-due-col-status = Estado
page-payments-due-total-residual = Total Pendiente
page-payments-due-no-payments = No hay pagos pendientes

### Legacy (kept for compatibility)
page-payments-tab-overview = Resumen
page-payments-tab-reconciliation = Conciliación
page-payments-tab-history = Historial
page-payments-total-received = Recibido
page-payments-total-pending = Por Cobrar
page-payments-total-overdue = Vencido
page-payments-reconciliation-rate = Tasa de Conciliación
page-payments-import-bank = Importar Extracto Bancario
page-payments-match-automatic = Conciliación Automática
page-payments-match-manual = Conciliación Manual
page-payments-unmatched = Transacciones No Conciliadas
page-payments-matched = Transacciones Conciliadas
page-payments-col-invoice = Factura
page-payments-col-client = Cliente
page-payments-col-amount = Importe
page-payments-col-due-date = Vencimiento
page-payments-col-paid-date = Fecha de Pago
page-payments-col-status = Estado
page-payments-col-method = Método

## ============================================================================
## AI ASSISTANT PAGE (5__AI_Assistant.py)
## ============================================================================

### Page Config
page-ai-page-title = Asistente IA - OpenFatture
page-ai-title = Asistente IA
page-ai-subtitle = Asistente Inteligente para Facturación y Fiscalidad
page-ai-not-configured =
    **IA no configurada**

    Para habilitar el Asistente IA:
    1. Configure las credenciales en el archivo `.env`
    2. Establezca `AI_PROVIDER` (openai/anthropic/ollama)
    3. Establezca `AI_API_KEY` (si es necesario)
    4. Reinicie la aplicación

    Consulte `docs/CONFIGURATION.md` para más detalles.

### Tabs
page-ai-tab-chat = Chat con Asistente
page-ai-tab-description = Generar Descripción
page-ai-tab-vat = Sugerencia de IVA
page-ai-tab-voice = Chat de Voz

### General
page-ai-yes = SÍ
page-ai-no = NO

### Retry Logic
page-ai-retry-message = Intento { $attempt }/{ $max_retries } fallido. Reintentando en { $delay }s...

### Error Messages
page-ai-error-connection = Error de conexión. Verifique su conexión a internet e inténtelo de nuevo.
page-ai-error-auth = Error de autenticación. Verifique sus credenciales de IA.
page-ai-error-rate-limit = Límite de velocidad alcanzado. Inténtelo de nuevo en unos minutos.
page-ai-error-service-unavailable = Servicio temporalmente no disponible. Inténtelo más tarde.
page-ai-error-generic = Error inesperado: { $error }...
page-ai-error-hint-connection = Sugerencia: Verifique su conexión a internet
page-ai-error-hint-auth = Sugerencia: Verifique la configuración de IA en las preferencias

### Slash Commands
page-ai-command-help-feedback =
    **Comandos Disponibles:**

    **Integrados:**
    - `/help` - Mostrar este mensaje
    - `/tools` - Listar herramientas de IA disponibles
    - `/stats` - Estadísticas de conversación actual
    - `/custom` - Listar comandos personalizados
    - `/reload` - Recargar comandos desde disco
    - `/clear` - Limpiar historial de chat

    **Personalizados:**
    Crear comandos en `~/.openfatture/commands/*.yaml`

    **Ejemplos:**
    - "¿Cómo creo una factura?"
    - "¿Cuál es la tasa de IVA para diseño web?"
    - "Muéstrame las facturas de este mes"

page-ai-command-tools-feedback =
    **Herramientas de IA Disponibles:**

    **Búsqueda y Consulta:**
    - Buscar facturas por cliente, fecha, importe
    - Estadísticas de ingresos y pagos
    - Consulta de normativa fiscal

    **Acciones Disponibles:**
    - Crear descripciones profesionales de facturas
    - Sugerir tasas de IVA correctas
    - Análisis de cumplimiento de facturas

    **Integración de Datos:**
    - Acceso a base de datos de clientes y productos
    - Historial de pagos y fechas de vencimiento
    - Informes y análisis de negocio

page-ai-command-stats-feedback =
    **Estadísticas de Conversación:**

    - **Mensajes totales:** { $total_messages }
    - **Tus mensajes:** { $user_messages }
    - **Respuestas IA:** { $assistant_messages }
    - **Caracteres totales:** { NUMBER($total_chars) }
    - **Tokens estimados:** { NUMBER($estimated_tokens) }

    **Sugerencias:**
    - Usa `/clear` para empezar de nuevo
    - Guarda conversaciones importantes con Guardar

page-ai-command-custom-no-commands = **No se encontraron comandos personalizados**\n\nCree comandos en `~/.openfatture/commands/*.yaml`
page-ai-command-custom-header = **Comandos Personalizados ({ $count }):**
page-ai-command-custom-footer = Use `/help` para ver todos los comandos
page-ai-command-reload-success = **Comandos recargados:** { $old_count } { $new_count } ({ $added } añadidos, { $removed } eliminados)
page-ai-command-reload-error = **Error de recarga:** { $error }
page-ai-command-clear-feedback = **Historial limpiado**\n\nLa conversación se ha reiniciado.
page-ai-command-custom-expanded = **Comando expandido:** `/{ $command }` { $length } caracteres
page-ai-command-custom-error = **Error de comando:** { $error }
page-ai-command-unknown = **Comando desconocido:** `{ $command }`\n\nUse `/help` para ver los comandos disponibles

### Tab 1: Chat Assistant
page-ai-chat-title = Chat Interactivo
page-ai-chat-description =
    Chatea con el asistente IA para:
    - Preguntas sobre facturación y normativa
    - Consejos fiscales y de IVA
    - Gestión de pagos y plazos
    - Consultoría general de negocios

page-ai-chat-save = Guardar
page-ai-chat-save-help = Guardar conversación
page-ai-chat-session-title = Chat { $count } mensajes
page-ai-chat-saved = Guardado: { $session_id }...
page-ai-chat-save-error = Error al guardar
page-ai-chat-reload = Recargar
page-ai-chat-reload-help = Recargar comandos personalizados
page-ai-chat-reloaded = Recargados: { $count } comandos
page-ai-chat-clear = Limpiar

### Chat File Upload
page-ai-chat-file-upload-title = Adjuntar Archivo (Opcional)
page-ai-chat-file-upload-label = Suba un documento para discutirlo con la IA
page-ai-chat-file-upload-help = Soporta PDF, texto, imágenes y otros documentos
page-ai-chat-file-uploaded = Archivo subido: { $name } ({ $size } bytes)
page-ai-chat-files-attached = Archivos Adjuntos
page-ai-chat-files-clear-all = Limpiar Todos
page-ai-chat-files-cleared = ¡Archivos limpiados!

### Chat File Types
page-ai-chat-file-text-preview = - **{ $name }** (texto): { $preview }
page-ai-chat-file-text = - **{ $name }** (texto, { $size } bytes)
page-ai-chat-file-pdf = - **{ $name }** (PDF, { $size } bytes) - Contenido para analizar
page-ai-chat-file-image = - **{ $name }** (imagen { $format }, { $size } bytes) - Texto para extraer vía OCR
page-ai-chat-file-other = - **{ $name }** ({ $type }, { $size } bytes)
page-ai-chat-file-analysis-hint = La IA analizará estos archivos para proporcionar una respuesta más precisa.

### Custom Commands
page-ai-chat-custom-commands-title = Comandos Personalizados
page-ai-chat-custom-commands-empty = No se encontraron comandos personalizados. Cree comandos en `~/.openfatture/commands/*.yaml`
page-ai-chat-custom-commands-count = **{ $count } comandos disponibles:**
page-ai-chat-custom-commands-description = **Descripción:** { $desc }
page-ai-chat-custom-commands-examples = Ejemplos
page-ai-chat-custom-commands-author = **Autor:** { $author }
page-ai-chat-custom-commands-version = **Versión:** { $version }

### Chat Sessions
page-ai-chat-sessions-title = Sesiones Guardadas
page-ai-chat-sessions-empty = No hay sesiones guardadas. Use el botón Guardar para guardar la conversación actual.
page-ai-chat-sessions-count = **{ $count } sesiones disponibles:**
page-ai-chat-sessions-load = Cargar
page-ai-chat-sessions-loaded = Sesión cargada: { $title }
page-ai-chat-sessions-load-error-empty = Sesión vacía o corrupta
page-ai-chat-sessions-load-error = Error de carga: { $error }
page-ai-chat-sessions-rename = Renombrar
page-ai-chat-sessions-rename-todo = Función de renombrado por implementar
page-ai-chat-sessions-delete = Eliminar
page-ai-chat-sessions-deleted = Sesión eliminada
page-ai-chat-sessions-delete-error = Error al eliminar

### Chat Input & Messages
page-ai-chat-input-placeholder = Escriba su mensaje o use /comando...
page-ai-chat-attachments = Adjuntos
page-ai-chat-thinking = Pensando...

### Chat Feedback
page-ai-chat-feedback-good = Bueno
page-ai-chat-feedback-good-comment = Buena respuesta
page-ai-chat-feedback-bad = Malo
page-ai-chat-feedback-bad-comment = Respuesta insatisfactoria
page-ai-chat-feedback-comment = Comentario
page-ai-chat-feedback-comment-label = Deje un comentario sobre la respuesta:
page-ai-chat-feedback-submit = Enviar Comentario
page-ai-chat-feedback-comment-sent = ¡Comentario enviado!
page-ai-chat-feedback-comment-empty = Introduzca un comentario
page-ai-chat-feedback-thanks = ¡Gracias por su comentario!
page-ai-chat-feedback-error = Error al enviar comentario

### Tab 2: Description Generator
page-ai-desc-title = Generar Descripción de Factura
page-ai-desc-description =
    Genere descripciones profesionales para sus facturas usando IA.
    Proporcione información sobre el servicio y obtenga una descripción detallada.

page-ai-desc-service-label = Servicio Proporcionado *
page-ai-desc-service-placeholder = ej., Consultoría de desarrollo de aplicación web de comercio electrónico
page-ai-desc-service-help = Describa brevemente el servicio/producto
page-ai-desc-hours-label = Horas Trabajadas
page-ai-desc-hours-help = Número de horas (opcional)
page-ai-desc-project-label = Nombre del Proyecto
page-ai-desc-project-placeholder = ej., Proyecto E-Commerce XYZ
page-ai-desc-project-help = Nombre del proyecto (opcional)
page-ai-desc-rate-label = Tarifa por Hora (€)
page-ai-desc-rate-help = Tarifa por hora en euros (opcional)
page-ai-desc-tech-label = Tecnologías
page-ai-desc-tech-placeholder = Python, FastAPI, PostgreSQL
page-ai-desc-tech-help = Tecnologías utilizadas, separadas por comas (opcional)
page-ai-desc-generate = Generar Descripción
page-ai-desc-error-empty = Introduzca una descripción del servicio
page-ai-desc-generating = Generando descripción profesional...
page-ai-desc-success = ¡Descripción generada con éxito!
page-ai-desc-result-title = Descripción Profesional
page-ai-desc-deliverables = Entregables
page-ai-desc-skills = Habilidades Técnicas
page-ai-desc-duration = **Duración:** { $hours } horas
page-ai-desc-notes = **Notas:** { $notes }
page-ai-desc-result-generated = Descripción Generada

### Tab 3: VAT Suggestion
page-ai-vat-title = Sugerencia de Tasa de IVA
page-ai-vat-description =
    Obtenga sugerencias de IA sobre la tasa de IVA correcta y el tratamiento fiscal
    según el tipo de servicio/producto y cliente.

page-ai-vat-service-label = Descripción del Servicio/Producto *
page-ai-vat-service-placeholder = ej., Consultoría informática para desarrollo de software de gestión
page-ai-vat-service-help = Describa el servicio o producto a facturar
page-ai-vat-client-pa-label = Cliente es Administración Pública
page-ai-vat-client-pa-help = Marque si el cliente es AP
page-ai-vat-amount-label = Importe (€)
page-ai-vat-amount-help = Importe en euros (opcional)
page-ai-vat-client-foreign-label = Cliente Extranjero
page-ai-vat-client-foreign-help = Marque si el cliente no es residente en Italia
page-ai-vat-country-label = País del Cliente
page-ai-vat-country-placeholder = IT, FR, US...
page-ai-vat-country-help = Código de país ISO de 2 letras
page-ai-vat-category-label = Categoría de Servicio
page-ai-vat-category-help = Categoría del servicio (opcional)
page-ai-vat-category-consulting = Consultoría
page-ai-vat-category-software = Desarrollo de Software
page-ai-vat-category-training = Formación
page-ai-vat-category-design = Diseño/Gráficos
page-ai-vat-category-marketing = Marketing
page-ai-vat-category-maintenance = Mantenimiento
page-ai-vat-category-other = Otro
page-ai-vat-suggest = Obtener Sugerencia de IVA
page-ai-vat-error-empty = Introduzca una descripción del servicio/producto
page-ai-vat-analyzing = Analizando tratamiento fiscal...
page-ai-vat-success = ¡Análisis completado!
page-ai-vat-treatment-title = Tratamiento Fiscal
page-ai-vat-rate-metric = Tasa de IVA
page-ai-vat-reverse-charge-metric = Inversión del Sujeto Pasivo
page-ai-vat-confidence-metric = Confianza
page-ai-vat-nature-code = **Código de Naturaleza IVA:** { $code }
page-ai-vat-split-payment = **Pago Fraccionado** aplicable
page-ai-vat-special-regime = **Régimen Especial:** { $regime }
page-ai-vat-explanation-title = Explicación
page-ai-vat-legal-reference-title = Referencia Legal
page-ai-vat-invoice-note-title = Nota para Factura
page-ai-vat-recommendations-title = Recomendaciones
page-ai-vat-suggestion-title = Sugerencia
page-ai-vat-error = Error: { $error }
page-ai-vat-error-generic = Error durante análisis: { $error }

### Tab 4: Voice Chat
page-ai-voice-title = Chat de Voz con IA
page-ai-voice-not-configured =
    **Chat de Voz no configurado**

    Para habilitar el Chat de Voz:
    1. Configure `OPENAI_API_KEY` en el archivo `.env`
    2. Establezca `OPENFATTURE_VOICE_ENABLED=true`
    3. Reinicie la aplicación

    Consulte la documentación para más detalles.

page-ai-voice-description =
    Hable con el asistente IA usando su voz:
    - Grabe su pregunta
    - La IA transcribe y responde
    - Escuche la respuesta de voz
    - Soporta conversaciones con contexto

### Voice Configuration
page-ai-voice-config-title = Configuración de Voz
page-ai-voice-config-provider = Proveedor
page-ai-voice-config-stt = Modelo STT
page-ai-voice-config-tts-voice = Voz TTS
page-ai-voice-config-tts-model = **Modelo TTS:** { $model }
page-ai-voice-config-tts-speed = **Velocidad TTS:** { $speed }x
page-ai-voice-config-tts-format = **Formato TTS:** { $format }
page-ai-voice-config-streaming = **Streaming:** { $enabled }

### Voice History
page-ai-voice-clear = Limpiar Voz
page-ai-voice-history-title = Historial de Conversación
page-ai-voice-user-message = **Tú:** { $text }
page-ai-voice-assistant-message = **Asistente:** { $text }
page-ai-voice-language-detected = Idioma detectado: { $lang }
page-ai-voice-language = Idioma: { $lang }
page-ai-voice-metric-stt = STT: { $ms }ms
page-ai-voice-metric-llm = LLM: { $ms }ms
page-ai-voice-metric-tts = TTS: { $ms }ms
page-ai-voice-metric-total = Total: { $ms }ms
page-ai-voice-metric-total-label = Total
page-ai-voice-history-empty = Aún no hay conversaciones de voz. ¡Grabe su primera pregunta!

### Voice Input
page-ai-voice-record-title = Grabe su voz
page-ai-voice-record-label = Presione el botón para grabar
page-ai-voice-record-help = Hable claramente en el micrófono. La grabación se detiene automáticamente después del silencio.
page-ai-voice-recorded = Audio grabado: { $size } bytes
page-ai-voice-process = Enviar y Procesar
page-ai-voice-processing = Procesando su mensaje de voz...
page-ai-voice-success = ¡Mensaje de voz procesado con éxito!
page-ai-voice-transcription-title = Transcripción
page-ai-voice-response-title = Respuesta de IA
page-ai-voice-audio-response-title = Respuesta de Voz
page-ai-voice-metrics-title = Métricas
page-ai-voice-tech-details = Detalles Técnicos
page-ai-voice-error = Error durante el procesamiento: { $error }
page-ai-voice-error-hint-connection = Sugerencia: Verifique su conexión a internet
page-ai-voice-error-hint-auth = Sugerencia: Verifique la configuración de API en las configuraciones
page-ai-voice-error-hint-rate = Sugerencia: Límite de solicitudes alcanzado. Inténtelo de nuevo en unos minutos

### Voice Help
page-ai-voice-help-title = Cómo funciona
page-ai-voice-help-content =
    **Flujo de Chat de Voz:**

    1. **Grabación**: Presione el botón y hable en el micrófono
    2. **Transcripción (STT)**: OpenAI Whisper convierte la voz en texto
    3. **Procesamiento (LLM)**: La IA comprende y genera una respuesta
    4. **Síntesis (TTS)**: OpenAI TTS convierte la respuesta en audio
    5. **▶Reproducción**: Escuche la respuesta de voz

    **Soporte de Idiomas:**
    - Detección automática de más de 100 idiomas
    - Italiano, Inglés, Francés, Alemán, Español y muchos más

    **Costos Estimados:**
    - STT (Whisper): ~$0.006 por minuto de audio
    - TTS: ~$0.015 por 1,000 caracteres (tts-1) o ~$0.030 (tts-1-hd)
    - LLM: Precio estándar del modelo configurado

    **Requisitos:**
    - Micrófono funcional
    - Navegador moderno (Chrome, Firefox, Safari, Edge)
    - Conexión a internet estable

### Metrics (shared across tabs)
page-ai-metric-provider = Proveedor
page-ai-metric-tokens = Tokens
page-ai-metric-cost = Costo

### Footer
page-ai-footer-disclaimer =
    **Sugerencia:** El Asistente IA es una herramienta de apoyo. La información proporcionada
    siempre debe ser verificada con un contador o asesor fiscal para garantizar
    el cumplimiento de las normativas vigentes.

## ============================================================================
## CLIENTS PAGE (3__Clienti.py)
## ============================================================================

page-clients-title = Gestión de Clientes
page-clients-subtitle = Ver y gestionar tus clientes

### Sidebar Filters
page-clients-filter-title = Filtros
page-clients-filter-search = Buscar
page-clients-filter-search-placeholder = Razón Social, NIF, CIF...
page-clients-filter-search-help = Buscar por razón social, NIF o CIF

### Actions
page-clients-action-new = Nuevo Cliente
page-clients-action-refresh = Actualizar
page-clients-action-view = Ver detalles
page-clients-action-edit = Editar
page-clients-action-delete = Eliminar

### Add Client Form
page-clients-form-add-title = Nuevo Cliente
page-clients-form-denominazione = Razón Social *
page-clients-form-denominazione-placeholder = Nombre de empresa o persona
page-clients-form-piva = NIF/CIF
page-clients-form-piva-placeholder = 12345678901
page-clients-form-cf = Código Fiscal
page-clients-form-cf-placeholder = RSSMRA80A01H501U
page-clients-form-sdi = Código SDI
page-clients-form-sdi-placeholder = ABC1234
page-clients-form-pec = PEC
page-clients-form-pec-placeholder = cliente@pec.it
page-clients-form-address = Dirección
page-clients-form-address-placeholder = Calle Roma 123
page-clients-form-zip = Código Postal
page-clients-form-zip-placeholder = 00100
page-clients-form-phone = Teléfono
page-clients-form-phone-placeholder = +34 123 456 789
page-clients-form-city = Ciudad
page-clients-form-city-placeholder = Madrid
page-clients-form-province = Provincia
page-clients-form-province-placeholder = M
page-clients-form-email = Email
page-clients-form-email-placeholder = cliente@email.com
page-clients-form-notes = Notas
page-clients-form-notes-placeholder = Notas adicionales...
page-clients-form-save = Guardar Cliente
page-clients-form-cancel = Cancelar

### Statistics
page-clients-stats-title = Estadísticas
page-clients-stats-total = Total Clientes
page-clients-stats-with-pec = Con PEC
page-clients-stats-with-sdi = Con SDI
page-clients-stats-with-piva = Con NIF/CIF

### Client List
page-clients-list-title = Lista de Clientes

### Table Columns
page-clients-table-col-id = ID
page-clients-table-col-denominazione = Razón Social
page-clients-table-col-piva = NIF/CIF
page-clients-table-col-cf = Código Fiscal
page-clients-table-col-sdi = SDI
page-clients-table-col-pec = PEC
page-clients-table-col-comune = Ciudad
page-clients-table-col-provincia = Prov.
page-clients-table-col-created = Creado
page-clients-table-col-actions = Acciones

### Empty State
page-clients-no-results = No se encontraron clientes para '{ $term }'
page-clients-empty-state = No hay clientes. ¡Crea tu primer cliente!

### Quick Add Form
page-clients-quick-add-title = Crear tu primer cliente
page-clients-quick-add-description = Completa los datos esenciales:
page-clients-quick-add-pec-optional = PEC (opcional)
page-clients-quick-add-button = Crear Cliente

### Client Detail
page-clients-detail-title = Detalles del Cliente: { $name }
page-clients-detail-id = ID
page-clients-detail-denominazione = Razón Social
page-clients-detail-piva = NIF/CIF
page-clients-detail-cf = Código Fiscal
page-clients-detail-sdi = SDI
page-clients-detail-pec = PEC
page-clients-detail-phone = Teléfono
page-clients-detail-email = Email
page-clients-detail-address = Dirección
page-clients-detail-city = Ciudad
page-clients-detail-notes = Notas
page-clients-detail-na = N/A
page-clients-detail-close = Cerrar

### Edit Client
page-clients-edit-title = Editar Cliente: { $name }
page-clients-edit-save = Guardar Cambios

### Delete Client
page-clients-delete-title = Eliminar Cliente: { $name }
page-clients-delete-confirm = ¿Estás seguro de que quieres eliminar el cliente '{ $name }'?
page-clients-delete-warning = Esta acción no se puede deshacer.
page-clients-delete-yes = Sí, Eliminar
page-clients-delete-no = Cancelar

### Quick Preview
page-clients-preview-title = Vista Rápida
page-clients-preview-total = Total Clientes
page-clients-preview-invoices = Total Facturas
page-clients-preview-top5 = Top 5 Clientes
page-clients-preview-col-client = Cliente
page-clients-preview-col-invoices = Nº Facturas
page-clients-preview-col-revenue = Facturación Total

### Success Messages
page-clients-success-created = Cliente '{ $name }' creado con éxito!
page-clients-success-updated = Cliente '{ $name }' actualizado!
page-clients-success-deleted = Cliente '{ $name }' eliminado!
page-clients-success-quick-created = Cliente '{ $name }' creado!

### Error Messages
page-clients-error-denominazione-required = La razón social es obligatoria
page-clients-error-create = Error al crear el cliente: { $error }
page-clients-error-update = Error al actualizar: { $error }
page-clients-error-delete = Error al eliminar: { $error }
page-clients-error-not-found = Cliente no encontrado
page-clients-error-loading = Error al cargar clientes: { $error }
page-clients-error-loading-hint = Verifica que la base de datos esté inicializada correctamente
page-clients-error-quick-create = Error: { $error }
page-clients-preview-error = Error al cargar datos: { $error }

### Legacy (kept for compatibility)
page-clients-search = Buscar clientes...
page-clients-filter-type = Tipo
page-clients-filter-country = País
page-clients-col-name = Nombre/Razón Social
page-clients-col-vat = NIF/CIF
page-clients-col-email = Email
page-clients-col-phone = Teléfono
page-clients-col-invoices = Facturas
page-clients-col-revenue = Facturación
page-clients-col-actions = Acciones
page-clients-action-add = Añadir Cliente
page-clients-action-create-invoice = Crear Factura
page-clients-no-clients = No se encontraron clientes
page-clients-add-first = Añade tu primer cliente
page-clients-total-found = { $count } clientes encontrados

## ============================================================================
## PÁGINA DE INFORMES (9__Reports.py)
## ============================================================================

page-reports-page-title = Informes - OpenFatture
page-reports-title = Informes y Análisis
page-reports-subtitle = Informes empresariales y análisis avanzados
page-reports-no-data = No hay datos disponibles para los informes
page-reports-no-data-info = Crea algunas facturas para ver los informes

### Barra lateral
page-reports-filter-title = Parámetros del Informe
page-reports-filter-year = Año
page-reports-filter-quarter = Trimestre (opcional)
page-reports-filter-quarter-all = Todos
page-reports-filter-quarter-q1 = T1
page-reports-filter-quarter-q2 = T2
page-reports-filter-quarter-q3 = T3
page-reports-filter-quarter-q4 = T4

### Pestañas
page-reports-tab-revenue = Facturación
page-reports-tab-vat = IVA
page-reports-tab-clients = Clientes

### Pestaña de Facturación
page-reports-revenue-title = Informe de Facturación
page-reports-revenue-total = Facturación Total
page-reports-revenue-total-help = Período: { $period }
page-reports-revenue-vat-total = IVA Total
page-reports-revenue-invoices = Facturas Emitidas
page-reports-revenue-avg = Valor Medio de Factura
page-reports-revenue-monthly = Tendencia Mensual
page-reports-revenue-chart-title = Facturación Mensual
page-reports-revenue-chart-xaxis = Mes
page-reports-revenue-chart-yaxis = Facturación (€)
page-reports-revenue-count-chart = Número de Facturas Mensuales
page-reports-revenue-count-yaxis = Número de Facturas

### Pestaña de IVA
page-reports-vat-title = Informe de IVA
page-reports-vat-taxable = Base Imponible Total
page-reports-vat-total = IVA Total
page-reports-vat-revenue-total = Facturación Total
page-reports-vat-breakdown-title = Desglose por Tipo de IVA
page-reports-vat-pie-title = Distribución de Base Imponible por Tipo de IVA
page-reports-vat-detail-title = Detalle por Tipo
page-reports-vat-table-rate = Tipo de IVA
page-reports-vat-table-taxable = Base Imponible
page-reports-vat-table-vat = IVA
page-reports-vat-table-total = Total

### Pestaña de Clientes
page-reports-clients-title = Informe de Clientes
page-reports-clients-active = Clientes Activos
page-reports-clients-active-help = Clientes con facturas emitidas en { $year }
page-reports-clients-top-title = Top Clientes por Facturación
page-reports-clients-table-client = Cliente
page-reports-clients-table-invoices = Facturas
page-reports-clients-table-total = Total
page-reports-clients-table-last = Última Factura
page-reports-clients-chart-title = Top 10 Clientes por Facturación
page-reports-clients-chart-xaxis = Cliente
page-reports-clients-chart-yaxis = Facturación (€)

### Exportar
page-reports-export-title = Exportar Informes
page-reports-export-revenue = Exportar Facturación (CSV)
page-reports-export-vat = Exportar IVA (CSV)
page-reports-export-clients = Exportar Clientes (CSV)
page-reports-export-download = Descargar CSV

page-reports-footer = <strong>Informes actualizados automáticamente</strong> • Datos basados en facturas entregadas o aceptadas

## ============================================================================
## PÁGINA DE HOOKS (10__Hooks.py)
## ============================================================================

page-hooks-page-title = Hooks y Automatización - OpenFatture
page-hooks-title = Hooks y Automatización
page-hooks-subtitle = Gestión de flujos de trabajo automatizados y triggers

### Métricas de Resumen
page-hooks-metric-total = Hooks Totales
page-hooks-metric-enabled = Hooks Activos
page-hooks-metric-pre = Pre-hooks
page-hooks-metric-post = Post-hooks

### Pestañas
page-hooks-tab-overview = Vista General
page-hooks-tab-manage = Gestionar
page-hooks-tab-create = Crear Hook
page-hooks-tab-test = Probar

### Pestaña de Vista General
page-hooks-overview-title = Vista General de Hooks
page-hooks-overview-group-pre =
page-hooks-overview-group-post =
page-hooks-overview-group-on =
page-hooks-overview-status-active = Activo
page-hooks-overview-status-inactive = Inactivo
page-hooks-overview-timeout = { $timeout }s
page-hooks-overview-empty = No se encontraron hooks. ¡Crea tu primer hook en la pestaña 'Crear Hook'!

### Pestaña de Gestión
page-hooks-manage-title = Gestionar Hooks
page-hooks-manage-toggle-title = Cambiar Estado de Hooks
page-hooks-manage-toggle-label = Activar { $name }
page-hooks-manage-toggle-help = Habilitar/deshabilitar el hook { $name }
page-hooks-manage-toggle-enabled = Hook '{ $name }' activado
page-hooks-manage-toggle-disabled = Hook '{ $name }' desactivado
page-hooks-manage-toggle-error = Error al actualizar el estado del hook
page-hooks-manage-details-button = Detalles
page-hooks-manage-details-help = Mostrar detalles del hook
page-hooks-manage-details-title = Detalles { $name }
page-hooks-manage-empty = No hay hooks para gestionar

### Pestaña de Creación
page-hooks-create-title = Crear Nuevo Hook
page-hooks-create-name-label = Nombre del Hook
page-hooks-create-name-placeholder = ej.: post-invoice-send
page-hooks-create-name-help = Nombre del hook (usa prefijos pre-, post-, on-)
page-hooks-create-type-label = Tipo de Script
page-hooks-create-type-help = Tipo de script para el hook
page-hooks-create-type-bash = bash
page-hooks-create-type-python = python
page-hooks-create-desc-label = Descripción
page-hooks-create-desc-placeholder = Qué hace este hook...
page-hooks-create-desc-help = Breve descripción del hook
page-hooks-create-event-label = Tipo de Evento
page-hooks-create-event-help = Cuándo se ejecuta el hook
page-hooks-create-event-pre = pre
page-hooks-create-event-post = post
page-hooks-create-event-on = on
page-hooks-create-preview-title = Vista Previa de Plantilla
page-hooks-create-preview-code = Código de Plantilla
page-hooks-create-button = Crear Hook
page-hooks-create-error-name = Introduce un nombre para el hook
page-hooks-create-warning-prefix = Sugerencia: el nombre debería empezar con '{ $prefix }-'
page-hooks-create-success = { $message }
page-hooks-create-reload = Recarga la página para ver el nuevo hook
page-hooks-create-error = { $message }

### Pestaña de Pruebas
page-hooks-test-title = Probar Hooks
page-hooks-test-select-label = Seleccionar Hook para Probar
page-hooks-test-select-help = Elige el hook a validar
page-hooks-test-info-title = Información del Hook
page-hooks-test-metric-type = Tipo de Evento
page-hooks-test-metric-status = Estado
page-hooks-test-metric-timeout = Timeout
page-hooks-test-metric-status-active = Activo
page-hooks-test-metric-status-inactive = Inactivo
page-hooks-test-validate-button = Validar Hook
page-hooks-test-validating = Validando hook...
page-hooks-test-success = ¡Hook validado con éxito!
page-hooks-test-metric-lines = Líneas de Código
page-hooks-test-metric-size = Tamaño
page-hooks-test-metric-size-value = { $size } bytes
page-hooks-test-metric-executable = Ejecutable
page-hooks-test-metric-executable-yes = Sí
page-hooks-test-metric-executable-no = No
page-hooks-test-result-message = { $message }
page-hooks-test-error = Error de validación: { $error }
page-hooks-test-show-code = Mostrar Código
page-hooks-test-code-error = Archivo de hook no encontrado
page-hooks-test-read-error = Error al leer el archivo: { $error }
page-hooks-test-empty = No hay hooks disponibles para probar

page-hooks-footer =
    <strong>Sistema de Hooks:</strong> Automatización de flujos de trabajo basada en eventos •
    <strong>Directorio:</strong> ~/.openfatture/hooks/ •
    <strong>Documentación:</strong> Ver CLI para ejemplos avanzados

## ============================================================================
## PÁGINA DE EVENTOS (11__Events.py)
## ============================================================================

page-events-page-title = Eventos y Auditoría - OpenFatture
page-events-title = Eventos y Auditoría
page-events-subtitle = Seguimiento de eventos del sistema y registro de auditoría

### Métricas de Resumen
page-events-metric-total = Eventos Totales
page-events-metric-total-help = Últimos { $days } días
page-events-metric-daily-avg = Eventos Diarios
page-events-metric-types = Tipos de Evento
page-events-metric-entities = Entidades Rastreadas

### Filtros de Barra Lateral
page-events-filter-title = Filtros de Eventos
page-events-filter-period = Período (días)
page-events-filter-period-help = Número de días a analizar
page-events-filter-type = Tipo de Evento
page-events-filter-type-all = Todos
page-events-filter-type-help = Filtrar por tipo de evento
page-events-filter-entity-type = Tipo de Entidad
page-events-filter-entity-type-help = Filtrar por tipo de entidad
page-events-filter-search = Buscar
page-events-filter-search-placeholder = Buscar en eventos...
page-events-filter-search-help = Buscar por tipo de evento o entidad

### Pestañas
page-events-tab-recent = Recientes
page-events-tab-filtered = Filtrados
page-events-tab-stats = Estadísticas
page-events-tab-timeline = Línea de Tiempo

### Pestaña de Recientes
page-events-recent-title = Eventos Recientes
page-events-table-timestamp = Fecha y Hora
page-events-table-type = Tipo de Evento
page-events-table-entity = Entidad
page-events-table-description = Descripción
page-events-table-user = Usuario
page-events-table-user-system = Sistema
page-events-details-button = Mostrar Detalles
page-events-details-help = Mostrar detalles completos del evento
page-events-details-title = Evento { $num }: { $desc }
page-events-empty = No se encontraron eventos en la base de datos

### Pestaña de Filtrados
page-events-filtered-title = Eventos Filtrados
page-events-filtered-found = Se encontraron { $count } eventos
page-events-export-button = Exportar CSV
page-events-export-help = Exportar resultados filtrados como CSV
page-events-export-download = Descargar CSV
page-events-filtered-empty = No se encontraron eventos con los filtros seleccionados

### Pestaña de Estadísticas
page-events-stats-title = Estadísticas de Eventos
page-events-stats-by-type = Eventos por Tipo
page-events-stats-type-col = Tipo de Evento
page-events-stats-count-col = Cantidad
page-events-stats-by-entity = Eventos por Entidad
page-events-stats-entity-col = Tipo de Entidad
page-events-stats-daily = Actividad Diaria (Últimos 7 Días)

### Pestaña de Línea de Tiempo
page-events-timeline-title = Línea de Tiempo de Entidad
page-events-timeline-entity-type = Tipo de Entidad
page-events-timeline-entity-type-help = Seleccionar tipo de entidad
page-events-timeline-entity-id = ID de Entidad
page-events-timeline-entity-id-placeholder = ej.: INV-001, CLI-001
page-events-timeline-entity-id-help = Introduce el ID de la entidad a rastrear
page-events-timeline-found = Se encontraron { $count } eventos para { $type } { $id }
page-events-timeline-event-time = **{ $time }**
page-events-timeline-event-type = { $type }
page-events-timeline-event-details = Detalles
page-events-timeline-empty = No se encontraron eventos para { $type } { $id }
page-events-timeline-info = Selecciona un tipo de entidad e introduce un ID para ver la línea de tiempo

page-events-footer =
    <strong>Sistema de Eventos:</strong> Registro de auditoría completo para cumplimiento y depuración •
    <strong>Búsqueda:</strong> Filtrar por tipo, entidad y período •
    <strong>Análisis:</strong> Estadísticas de actividad y línea de tiempo de entidad

## ============================================================================
## PÁGINA DE SALUD (12__Health.py)
## ============================================================================

page-health-page-title = Salud del Sistema - OpenFatture
page-health-title = Panel de Salud del Sistema
page-health-subtitle = Monitoreo y diagnóstico en tiempo real

### Métricas de Uso
page-health-usage-title = Métricas de Uso
page-health-metric-visits = Visitas Totales a Páginas
page-health-metric-unique = Páginas Únicas
page-health-metric-session = Inicio de Sesión

### Estadísticas de Caché
page-health-cache-title = Estadísticas de Caché
page-health-cache-cleanup = Se limpiaron { $count } entradas de caché caducadas
page-health-metric-entries = Entradas de Caché Totales
page-health-metric-functions = Funciones en Caché
page-health-clear-all = Limpiar Todas las Cachés
page-health-clear-success = ¡Todas las cachés se limpiaron!
page-health-cache-breakdown = Desglose de Caché por Función
page-health-table-function = Función
page-health-table-entries = Entradas
page-health-cache-management = Gestión Selectiva de Caché
page-health-clear-invoices = Limpiar Cachés de Facturas
page-health-clear-clients = Limpiar Cachés de Clientes
page-health-clear-payments = Limpiar Cachés de Pagos
page-health-cleared-category = Se limpiaron { $count } cachés de { $category }

### Visitas a Páginas
page-health-visits-breakdown = Desglose de Visitas a Páginas
page-health-table-page = Página
page-health-table-visits = Visitas

### API de Salud
page-health-api-title = Endpoint de API de Salud
page-health-api-info =
    Para monitoreo externo, usa la función `quick_health_check()`:

    ```python
    from openfatture.web.utils.health import quick_health_check

    health = quick_health_check()
    # Devuelve: {"status": "healthy|degraded|unhealthy", "checks": [...]}
    ```

    Esto puede exponerse a través de un endpoint API para herramientas de monitoreo como:
    - Prometheus
    - Datadog
    - New Relic
    - Paneles de monitoreo personalizados

page-health-api-sample = Mostrar Ejemplo de JSON de Comprobación de Salud
page-health-best-practice =
    **Mejores Prácticas:** Monitorea este panel regularmente para detectar problemas temprano.
    Configura alertas para estados "unhealthy" o "degraded" en producción.
