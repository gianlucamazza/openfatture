# CLI commands translations
# ES (Español)

## MAIN CLI

### main - Main CLI
cli-main-title = OpenFatture - Sistema de Facturación Electrónica de Código Abierto
cli-main-description = Sistema completo para gestionar facturas electrónicas FatturaPA
cli-main-version = Versión { $version }

### main - Command Groups
cli-main-group-invoices = Gestión de Facturas
cli-main-group-clients = Gestión de Clientes
cli-main-group-products = Gestión de Productos
cli-main-group-pec = PEC y SDI
cli-main-group-batch = Operaciones por Lotes
cli-main-group-ai = Asistente IA
cli-main-group-payments = Seguimiento de Pagos
cli-main-group-preventivi = Presupuestos
cli-main-group-events = Sistema de Eventos
cli-main-group-lightning = Red Lightning
cli-main-group-web = Interfaz Web

## FATTURA Commands

### fattura - Help Texts
cli-fattura-help-numero = Número de factura
cli-fattura-help-cliente-id = ID de cliente
cli-fattura-help-anno = Año (predeterminado: año actual)
cli-fattura-help-tipo-documento = Tipo de documento (TD01, TD04, TD06, etc.)
cli-fattura-help-data = Fecha de factura (AAAA-MM-DD)
cli-fattura-help-bollo = Sello fiscal (€ 2.00)
cli-fattura-help-xml-path = Ruta al archivo XML
cli-fattura-help-formato = Formato de salida (table, json, yaml)
cli-fattura-help-all = Mostrar todas las facturas, incluso las antiguas
cli-fattura-help-invoice-id = ID de factura
cli-fattura-help-filter-status = Filtrar por estado
cli-fattura-help-limit = Número máximo de facturas a mostrar
cli-fattura-help-force = Omitir confirmación
cli-fattura-help-output = Ruta de salida
cli-fattura-help-no-validate = Omitir validación XSD
cli-fattura-help-pec = Enviar vía PEC

### fattura - Console Output
cli-fattura-create-title = [bold blue]Crear Nueva Factura[/bold blue]
cli-fattura-select-client-title = [bold cyan]Selección de Cliente[/bold cyan]
cli-fattura-no-clients-error = [red]No se encontraron clientes. Añade uno primero con 'cliente add'[/red]
cli-fattura-available-clients = [cyan]Clientes disponibles:[/cyan]
cli-fattura-client-prompt = Número de cliente
cli-fattura-client-selected = [green]Cliente: { $client_name }[/green]
cli-fattura-invalid-client-error = [red]Selección de cliente no válida[/red]

cli-fattura-add-lines-title = [bold cyan]Líneas de Factura[/bold cyan]
cli-fattura-line-description-prompt = Descripción (vacío para terminar)
cli-fattura-line-quantity-prompt = Cantidad
cli-fattura-line-unit-price-prompt = Precio unitario (€)
cli-fattura-line-vat-rate-prompt = Tasa de IVA (%)
cli-fattura-line-added = [green]Línea añadida: { $description } - € { $amount }[/green]

cli-fattura-payment-terms-title = [bold cyan]Condiciones de Pago[/bold cyan]
cli-fattura-payment-condition-prompt = Condición de pago (TP01=Por pagar, TP02=Pagado)
cli-fattura-payment-method-prompt = Método de pago (MP05=Transferencia, MP01=Efectivo, MP08=Tarjeta)
cli-fattura-payment-days-prompt = Plazo de pago (días)
cli-fattura-payment-date-prompt = Fecha de pago (AAAA-MM-DD, vacío=auto)
cli-fattura-payment-iban-prompt = IBAN (opcional)

cli-fattura-summary-title = [bold yellow]Resumen de Factura[/bold yellow]
cli-fattura-summary-client = Cliente: { $client_name }
cli-fattura-summary-lines = { $count } { $count ->
    [one] línea
   *[other] líneas
}
cli-fattura-summary-subtotal = Subtotal: € { $subtotal }
cli-fattura-summary-vat = IVA: € { $vat }
cli-fattura-summary-total = [bold]Total: € { $total }[/bold]
cli-fattura-summary-stamp = Sello fiscal: € { $stamp }

cli-fattura-confirm-prompt = [yellow]¿Confirmar creación?[/yellow]
cli-fattura-created-success = [bold green]Factura creada exitosamente![/bold green]
cli-fattura-created-number = [green]Número de factura: { $numero }/{ $anno }[/green]
cli-fattura-created-xml = [green]XML guardado: { $xml_path }[/green]

cli-fattura-list-title = [bold blue]Lista de Facturas[/bold blue]
cli-fattura-list-empty = [yellow]No se encontraron facturas[/yellow]

cli-fattura-show-title = [bold blue]Factura { $numero }/{ $anno }[/bold blue]
cli-fattura-show-not-found = [red]Factura no encontrada: { $numero }/{ $anno }[/red]

cli-fattura-delete-confirm = [yellow]¿Eliminar factura { $numero }/{ $anno }?[/yellow]
cli-fattura-delete-warning = [red]ADVERTENCIA: Esta operación no se puede deshacer[/red]
cli-fattura-delete-status-restriction = [red]No se puede eliminar factura en estado '{ $status }'[/red]
cli-fattura-delete-success = [green]Factura { $numero }/{ $anno } eliminada[/green]
cli-fattura-delete-cancelled = [yellow]Operación cancelada[/yellow]
cli-fattura-delete-cannot-delete-sent = [red]No se pueden eliminar facturas en estado INVIATA o CONSEGNATA[/red]
cli-fattura-cancelled = Cancelado.

cli-fattura-table-title-list = Facturas ({ $count })
cli-fattura-invalid-status = [red]Estado no válido: { $status }[/red]

cli-fattura-line-items-header = Líneas de Factura
cli-fattura-totals-header = Totales

cli-fattura-xml-generation-title = [bold blue]Generación XML FatturaPA[/bold blue]
cli-fattura-generating-xml = Generando XML para factura { $numero }/{ $anno }...
cli-fattura-xml-generated = [green]XML generado con éxito![/green]

cli-fattura-send-title = [bold blue]Envío de Factura a SDI[/bold blue]
cli-fattura-send-step1-xml = [cyan]1. Generando XML...[/cyan]
cli-fattura-sent-success-message = [bold green]Factura { $numero }/{ $anno } enviada con éxito![/bold green]

cli-fattura-validate-success = [green]XML válido[/green]
cli-fattura-validate-error = [red]Se encontraron errores de validación:[/red]

cli-fattura-table-numero = Nº
cli-fattura-table-data = Fecha
cli-fattura-table-cliente = Cliente
cli-fattura-table-importo = Importe
cli-fattura-table-stato = Estado
cli-fattura-table-tipo = Tipo
cli-fattura-table-pagamento = Pago
cli-fattura-table-iva = IVA
cli-fattura-table-totale = Total
cli-fattura-table-bollo = Sello
cli-fattura-table-descrizione = Descripción
cli-fattura-table-quantita = Cant.
cli-fattura-table-prezzo = Precio
cli-fattura-table-aliquota = Tasa
cli-fattura-table-importo-riga = Importe

## CLIENTE Commands

### cliente - Help Texts
cli-cliente-help-id = ID de cliente
cli-cliente-help-name = Nombre del cliente/empresa (omitir para solicitar en modo --interactive)
cli-cliente-help-denominazione = Nombre de empresa o nombre completo
cli-cliente-help-piva = Número de IVA (Partita IVA)
cli-cliente-help-partita-iva = Número de IVA
cli-cliente-help-cf = Código fiscal (Codice Fiscale)
cli-cliente-help-codice-fiscale = Código fiscal
cli-cliente-help-sdi = Código SDI
cli-cliente-help-pec = Dirección PEC
cli-cliente-help-codice-destinatario = Código de destino SDI
cli-cliente-help-interactive = Modo interactivo
cli-cliente-help-formato = Formato de salida (table, json, yaml)
cli-cliente-help-search = Término de búsqueda
cli-cliente-help-limite = Número máximo de resultados
cli-cliente-help-limit = Número máximo de resultados
cli-cliente-help-cliente-id = ID de cliente
cli-cliente-help-force = Omitir confirmación

### cliente - Console Output
cli-cliente-name-required = [red]Error: El nombre del cliente es obligatorio[/red]
cli-cliente-no-clients = [yellow]No se encontraron clientes. Añade uno con 'cliente add'[/yellow]
cli-cliente-list-title = Clientes ({ $count })
cli-cliente-list-empty = [yellow]No se encontraron clientes[/yellow]
cli-cliente-added-success = [green]Cliente añadido exitosamente (ID: { $id })[/green]
cli-cliente-updated-success = [green]Cliente actualizado exitosamente[/green]
cli-cliente-deleted-success = [green]Cliente eliminado exitosamente[/green]
cli-cliente-deleted = [green]Cliente '{ $name }' eliminado[/green]
cli-cliente-cancelled = Cancelado.
cli-cliente-not-found = [red]Cliente no encontrado: { $id }[/red]
cli-cliente-has-invoices = [yellow]Advertencia: Este cliente tiene { $count } { $count ->
    [one] factura
   *[other] facturas
}[/yellow]
cli-cliente-cannot-delete = [red]No se puede eliminar cliente con facturas[/red]
cli-cliente-delete-confirm = [yellow]¿Eliminar cliente { $denominazione }?[/yellow]

### cliente - Prompts
cli-cliente-prompt-denominazione = Nombre de empresa
cli-cliente-prompt-partita-iva = Número de IVA
cli-cliente-prompt-codice-fiscale = Código fiscal
cli-cliente-prompt-indirizzo = Dirección
cli-cliente-prompt-cap = Código postal
cli-cliente-prompt-comune = Ciudad
cli-cliente-prompt-provincia = Provincia
cli-cliente-prompt-nazione = País
cli-cliente-prompt-pec = Dirección PEC
cli-cliente-prompt-codice-destinatario = Código de destino SDI
cli-cliente-prompt-email = Correo electrónico
cli-cliente-prompt-telefono = Teléfono
cli-cliente-prompt-regime-fiscale = Régimen fiscal (RF01, RF19, etc.)

### cliente - Table Labels
cli-cliente-table-id = ID
cli-cliente-table-denominazione = Nombre
cli-cliente-table-partita-iva = IVA
cli-cliente-table-codice-fiscale = Código Fiscal
cli-cliente-table-comune = Ciudad
cli-cliente-table-provincia = Provincia
cli-cliente-table-pec = PEC
cli-cliente-table-codice-destinatario = Código SDI
cli-cliente-table-fatture = Facturas
cli-cliente-table-indirizzo = Dirección
cli-cliente-table-cap = CP
cli-cliente-table-nazione = País
cli-cliente-table-email = Correo

cli-cliente-column-id = ID
cli-cliente-column-name = Nombre
cli-cliente-column-piva = N.º IVA
cli-cliente-column-sdi-pec = SDI/PEC
cli-cliente-column-invoices = Facturas

cli-cliente-label-id = ID
cli-cliente-label-name = Nombre
cli-cliente-label-piva = Número IVA
cli-cliente-label-cf = Código Fiscal
cli-cliente-label-address = Dirección
cli-cliente-label-sdi = Código SDI
cli-cliente-label-pec = PEC
cli-cliente-label-email = Correo electrónico
cli-cliente-label-phone = Teléfono
cli-cliente-label-total-invoices = Facturas Totales
cli-cliente-label-created = Creado

cli-cliente-show-title = [bold blue]Detalles del Cliente: { $name }[/bold blue]
cli-cliente-prompt-civic-number = Número cívico (opcional)
cli-cliente-prompt-pec-address = Dirección PEC (si SDI es 0000000)
cli-cliente-confirm-delete = ¿Está seguro de que desea eliminar?
cli-cliente-confirm-delete-client = ¿Eliminar cliente '{ $name }'?

## ============================================================================
## Batch Commands - Operaciones por Lotes
## ============================================================================

### batch - Help Text
cli-batch-help-csv-file = Ruta al archivo CSV con las facturas
cli-batch-help-dry-run = Validar sin importar
cli-batch-help-send-summary = Enviar resumen por correo electrónico
cli-batch-help-output-file = Ruta del archivo CSV de salida
cli-batch-help-anno = Filtrar por año
cli-batch-help-stato = Filtrar por estado
cli-batch-help-limit = Número máximo de resultados

### batch - Console Output (import)
cli-batch-import-title = [bold blue]Importación por Lotes de Facturas[/bold blue]
cli-batch-file-not-found = [red]Archivo no encontrado: { $file }[/red]
cli-batch-file-info-name = [cyan]Archivo:[/cyan] { $name }
cli-batch-file-info-size = [cyan]Tamaño:[/cyan] { $size } bytes
cli-batch-mode-dry-run = [cyan]Modo:[/cyan] Dry run (solo validación)
cli-batch-mode-import = [cyan]Modo:[/cyan] Importación
cli-batch-dry-run-warning = [yellow]Modo dry run - no se guardarán datos[/yellow]
cli-batch-warning-dry-run = [yellow]Modo dry run - no se guardarán datos[/yellow]

cli-batch-results-title = [bold]Resultados de Importación:[/bold]
cli-batch-metric-total = Filas totales
cli-batch-metric-processed = Procesadas
cli-batch-metric-succeeded = Exitosas
cli-batch-metric-failed = Fallidas
cli-batch-metric-success-rate = Tasa de éxito
cli-batch-metric-duration = Duración
cli-batch-metric-label = Métrica
cli-batch-metric-value = Valor

cli-batch-errors-title = [bold red]Errores:[/bold red]
cli-batch-errors-more = [dim]... y { $count } errores más[/dim]

cli-batch-success-all = [bold green]¡Todas las facturas importadas exitosamente![/bold green]
cli-batch-warning-failed = [yellow]{ $count } facturas no importadas[/yellow]

cli-batch-email-not-configured = [yellow]Notificación por correo no configurada.[/yellow]
cli-batch-sending-email = [dim]Enviando resumen por correo...[/dim]
cli-batch-email-sending = [dim]Enviando resumen por correo...[/dim]
cli-batch-email-sent = [dim]Resumen enviado a { $email }[/dim]
cli-batch-email-failed = [yellow]Error al enviar resumen: { $error }[/yellow]

cli-batch-error-general = [red]Error: { $error }[/red]

### batch - Console Output (export)
cli-batch-export-title = [bold blue]Exportación por Lotes de Facturas[/bold blue]
cli-batch-filter-year = [cyan]Filtro:[/cyan] Año = { $anno }
cli-batch-filter-status = [cyan]Filtro:[/cyan] Estado = { $stato }
cli-batch-invalid-status = [red]Estado no válido: { $stato }[/red]
cli-batch-no-invoices = [yellow]No se encontraron facturas[/yellow]
cli-batch-invoices-count = [cyan]Facturas:[/cyan] { $count }

cli-batch-export-success = [bold green]¡{ $count } facturas exportadas![/bold green]
cli-batch-export-file-path = [cyan]Archivo:[/cyan] { $path }
cli-batch-export-file = [cyan]Archivo:[/cyan] { $path }
cli-batch-export-file-size = [cyan]Tamaño:[/cyan] { $size } bytes
cli-batch-export-size = [cyan]Tamaño:[/cyan] { $size } bytes
cli-batch-export-failed = [red]Exportación fallida[/red]

### batch - Console Output (history)
cli-batch-history-title = [bold blue]Historial de Operaciones por Lotes[/bold blue]
cli-batch-history-not-implemented = [yellow]Seguimiento de historial no implementado completamente aún[/yellow]
cli-batch-history-future-features = [dim]En producción, mostrará:[/dim]
cli-batch-history-will-show = [dim]En producción, mostrará:[/dim]
cli-batch-history-feature-datetime = • Fecha/hora de la operación
cli-batch-history-feature-type = • Tipo (import/export)
cli-batch-history-feature-records = • Registros procesados
cli-batch-history-feature-counts = • Conteos de éxito/fallo
cli-batch-history-feature-errors = • Resúmenes de errores

cli-batch-history-example-title = [bold]Ejemplo de historial:[/bold]
cli-batch-history-example = [bold]Ejemplo de historial:[/bold]
cli-batch-history-column-date = Fecha
cli-batch-history-col-date = Fecha
cli-batch-history-column-type = Tipo
cli-batch-history-col-type = Tipo
cli-batch-history-column-records = Registros
cli-batch-history-col-records = Registros
cli-batch-history-column-success = Éxito
cli-batch-history-col-success = Éxito
cli-batch-history-column-failed = Fallidos
cli-batch-history-col-failed = Fallidos

cli-batch-history-todo = [dim]Por hacer: Añadir modelo BatchOperation a la base de datos[/dim]

## ============================================================================
## Preventivo Commands - Gestión de Presupuestos
## ============================================================================

### preventivo - Help Text
cli-preventivo-help-cliente-id = ID del Cliente
cli-preventivo-help-validita = Período de validez en días
cli-preventivo-help-stato = Filtrar por estado
cli-preventivo-help-anno = Filtrar por año
cli-preventivo-help-cliente = Filtrar por ID de cliente
cli-preventivo-help-limit = Número máximo de resultados
cli-preventivo-help-preventivo-id = ID del Presupuesto
cli-preventivo-help-force = Omitir confirmación
cli-preventivo-help-tipo-documento = Tipo de documento de factura (TD01, TD06, etc.)
cli-preventivo-help-new-stato = Nuevo estado (borrador, enviado, aceptado, rechazado, vencido)

### preventivo - Console Output (crea)
cli-preventivo-create-title = [bold blue]Crear Nuevo Presupuesto[/bold blue]
cli-preventivo-no-clients = [red]No se encontraron clientes. Agregue primero un cliente con 'openfatture cliente add'[/red]
cli-preventivo-select-client = [cyan]Clientes disponibles:[/cyan]
cli-preventivo-client-id-prompt = Seleccione ID del cliente
cli-preventivo-client-not-found = [red]Cliente { $id } no encontrado[/red]
cli-preventivo-client-selected = [green]Cliente: { $name }[/green]
cli-preventivo-validity-info = [dim]Validez: { $days } días (vencimiento: { $date })[/dim]

cli-preventivo-add-items-title = [bold]Agregar líneas[/bold]
cli-preventivo-add-items-hint = [dim]Ingrese descripción vacía para terminar[/dim]
cli-preventivo-item-description-prompt = Descripción del artículo { $num }
cli-preventivo-item-quantity-prompt = Cantidad
cli-preventivo-item-price-prompt = Precio unitario (€)
cli-preventivo-item-vat-prompt = Tasa de IVA (%)
cli-preventivo-item-unit-prompt = Unidad de medida
cli-preventivo-item-added = [green]Agregado: { $desc } - €{ $total }[/green]

cli-preventivo-no-items = [yellow]No se agregaron líneas. Creación de presupuesto cancelada.[/yellow]
cli-preventivo-add-notes-prompt = ¿Agregar notas?
cli-preventivo-notes-prompt = Notas
cli-preventivo-add-conditions-prompt = ¿Agregar términos y condiciones?
cli-preventivo-conditions-prompt = Términos y condiciones

cli-preventivo-error-general = [red]Error: { $error }[/red]
cli-preventivo-created-success = [bold green]¡Presupuesto creado exitosamente![/bold green]
cli-preventivo-next-convert = [dim]Siguiente: openfatture preventivo converti { $id } (para crear factura)[/dim]

### preventivo - Console Output (lista)
cli-preventivo-invalid-status = [red]Estado no válido: { $stato }[/red]
cli-preventivo-valid-statuses = Válidos: { $statuses }
cli-preventivo-no-preventivi = [yellow]No se encontraron presupuestos[/yellow]
cli-preventivo-list-title = Presupuestos ({ $count })

cli-preventivo-column-id = ID
cli-preventivo-column-number = Número
cli-preventivo-column-date = Fecha
cli-preventivo-column-expiration = Vencimiento
cli-preventivo-column-client = Cliente
cli-preventivo-column-total = Total
cli-preventivo-column-status = Estado

### preventivo - Console Output (show)
cli-preventivo-not-found = [red]Presupuesto { $id } no encontrado[/red]
cli-preventivo-show-title = [bold blue]Presupuesto { $numero }/{ $anno }[/bold blue]

cli-preventivo-field-client = Cliente
cli-preventivo-field-issue-date = Fecha de emisión
cli-preventivo-field-expiration = Fecha de vencimiento
cli-preventivo-field-validity = Validez
cli-preventivo-field-validity-days = { $days } días
cli-preventivo-field-status = Estado
cli-preventivo-warning-expired = [red]ADVERTENCIA[/red]
cli-preventivo-expired = [red]¡Vencido![/red]

cli-preventivo-line-items-title = [bold]Líneas:[/bold]
cli-preventivo-line-item-number = #
cli-preventivo-line-item-description = Descripción
cli-preventivo-line-item-quantity = Cant
cli-preventivo-line-item-price = Precio
cli-preventivo-line-item-vat = IVA%
cli-preventivo-line-item-total = Total

cli-preventivo-totals-title = [bold]Totales:[/bold]
cli-preventivo-total-imponibile = Base imponible
cli-preventivo-total-iva = IVA
cli-preventivo-total-total = [bold]TOTAL[/bold]

cli-preventivo-notes-title = [bold]Notas:[/bold]
cli-preventivo-conditions-title = [bold]Términos y Condiciones:[/bold]

### preventivo - Console Output (delete)
cli-preventivo-confirm-delete = ¿Eliminar presupuesto { $numero }/{ $anno }?
cli-preventivo-cancelled = Cancelado.
cli-preventivo-deleted = [green]Presupuesto { $numero }/{ $anno } eliminado[/green]

### preventivo - Console Output (converti)
cli-preventivo-convert-title = [bold blue]Conversión de Presupuesto a Factura[/bold blue]
cli-preventivo-convert-summary-numero = [cyan]Presupuesto: { $numero }/{ $anno }[/cyan]
cli-preventivo-convert-summary-client = [cyan]Cliente: { $name }[/cyan]
cli-preventivo-convert-summary-total = [cyan]Total: €{ $total }[/cyan]
cli-preventivo-invalid-doc-type = [red]Tipo de documento no válido: { $tipo }[/red]
cli-preventivo-valid-doc-types = Válidos: TD01, TD06, etc.
cli-preventivo-confirm-convert = ¿Convertir a factura?
cli-preventivo-convert-cancelled = [yellow]Cancelado.[/yellow]
cli-preventivo-converted-success = [bold green]¡Presupuesto convertido exitosamente![/bold green]

cli-preventivo-invoice-title = Factura { $numero }/{ $anno }
cli-preventivo-invoice-field-client = Cliente
cli-preventivo-invoice-field-date = Fecha
cli-preventivo-invoice-field-doc-type = Tipo de documento
cli-preventivo-invoice-field-items = Líneas
cli-preventivo-invoice-field-imponibile = Base imponible
cli-preventivo-invoice-field-iva = IVA
cli-preventivo-invoice-field-total = [bold]TOTAL[/bold]

cli-preventivo-invoice-id-info = [dim]ID de Factura: { $id }[/dim]
cli-preventivo-original-preventivo-info = [dim]Presupuesto original: { $numero }/{ $anno } (ID: { $id })[/dim]
cli-preventivo-next-send = [dim]Siguiente: openfatture fattura invia { $id } --pec[/dim]

### preventivo - Console Output (aggiorna-stato)
cli-preventivo-status-updated = [green]Estado del presupuesto actualizado: { $stato }[/green]

## AI Commands

### ai - Help Texts
cli-ai-help-text = Texto a procesar
cli-ai-help-invoice-id = ID de factura
cli-ai-help-provider = Proveedor de IA (openai, anthropic, ollama)
cli-ai-help-model = Nombre del modelo de IA
cli-ai-help-temperature = Temperatura (0.0-2.0)
cli-ai-help-max-tokens = Tokens máximos
cli-ai-help-interactive = Modo interactivo
cli-ai-help-session-id = ID de sesión de chat
cli-ai-help-stream = Habilitar streaming
cli-ai-help-save-session = Guardar sesión después del chat
cli-ai-help-list-sessions = Listar sesiones disponibles
cli-ai-help-months = Número de meses a pronosticar
cli-ai-help-confidence = Nivel de confianza (0.0-1.0)
cli-ai-help-retrain = Reentrenar modelo con datos recientes
cli-ai-help-show-metrics = Mostrar métricas del modelo
cli-ai-help-invoice-numero = Número de factura
cli-ai-help-year = Año de factura
cli-ai-help-context = Contexto adicional
cli-ai-help-language = Código de idioma
cli-ai-help-format = Formato de salida
cli-ai-help-embedding-model = Modelo de embeddings
cli-ai-help-chunk-size = Tamaño de fragmento para documentos
cli-ai-help-collection = Nombre de colección RAG
cli-ai-help-query = Consulta de búsqueda
cli-ai-help-top-k = Número de resultados
cli-ai-help-rating = Calificación (1-5)
cli-ai-help-comment = Texto de comentario
cli-ai-help-duration = Duración de grabación en segundos
cli-ai-help-save-audio = Guardar archivos de audio para depuración
cli-ai-help-no-playback = Desactivar reproducción de audio
cli-ai-help-sample-rate = Tasa de muestreo de audio
cli-ai-help-service-description = Descripción del servicio a expandir
cli-ai-help-hours-worked = Horas trabajadas
cli-ai-help-hourly-rate = Tarifa por hora (€)
cli-ai-help-project-name = Nombre del proyecto
cli-ai-help-technologies = Tecnologías usadas (separadas por coma)
cli-ai-help-json-output = Salida en formato JSON
cli-ai-help-stream = Streaming de respuesta en tiempo real
cli-ai-help-client-pa = Cliente es Administración Pública
cli-ai-help-client-foreign = Cliente extranjero (fuera de Italia)
cli-ai-help-country-code = Código de país del cliente (IT, FR, DE, etc.)
cli-ai-help-service-category = Categoría de servicio
cli-ai-help-amount-eur = Importe en euros
cli-ai-help-ateco-code = Código ATECO
cli-ai-help-chat-message = Mensaje a enviar al chat

### ai - Console Output (describe)
cli-ai-describe-title = [bold cyan]Generación de Descripción de Factura con IA[/bold cyan]
cli-ai-describe-input-prompt = [cyan]Ingrese descripción breve:[/cyan]
cli-ai-describe-processing = [yellow]Procesando con IA...[/yellow]
cli-ai-describe-result-title = [bold green]Descripción Generada:[/bold green]
cli-ai-describe-result-text = [white]{ $text }[/white]
cli-ai-describe-copy-hint = [dim]Puede copiar esta descripción al crear una factura[/dim]
cli-ai-describe-error = [red]Error al generar descripción: { $error }[/red]
cli-ai-describe-activity = Actividad: [yellow]{ $activity }[/yellow]
cli-ai-describe-generating = Generando descripción detallada...
cli-ai-describe-input-service = Servicio
cli-ai-describe-input-hours = Horas trabajadas
cli-ai-describe-input-rate = Tarifa por hora
cli-ai-describe-input-project = Proyecto
cli-ai-describe-input-technologies = Tecnologías
cli-ai-describe-input-client-pa = Cliente PA
cli-ai-describe-input-client-foreign = Cliente extranjero
cli-ai-describe-input-country = País
cli-ai-describe-input-category = Categoría
cli-ai-describe-input-amount = Importe
cli-ai-describe-input-ateco = Código ATECO

### ai - Console Output (suggest-vat)
cli-ai-vat-title = [bold cyan]Sugerencia de Tasa de IVA con IA[/bold cyan]
cli-ai-vat-input-prompt = [cyan]Descripción del servicio/producto:[/cyan]
cli-ai-vat-processing = [yellow]Analizando con IA...[/yellow]
cli-ai-vat-result-title = [bold green]Tasa de IVA Sugerida:[/bold green]
cli-ai-vat-rate = [white]{ $rate }%[/white]
cli-ai-vat-reasoning-title = [bold yellow]Razonamiento:[/bold yellow]
cli-ai-vat-reasoning-text = [white]{ $reasoning }[/white]
cli-ai-vat-warning = [yellow]Siempre verifique con un asesor fiscal para casos complejos[/yellow]
cli-ai-vat-error = [red]Error al sugerir tasa de IVA: { $error }[/red]
cli-ai-vat-query = Consulta: [yellow]{ $query }[/yellow]
cli-ai-vat-analyzing = Analizando normativa IVA...
cli-ai-vat-disclaimer = [yellow]Esta es una sugerencia. Consulte siempre a un contador.[/yellow]
cli-ai-vat-processing = Procesando sugerencia de IVA...
cli-ai-vat-input-service = Servicio
cli-ai-vat-input-client-pa = Cliente PA
cli-ai-vat-input-client-foreign = Cliente extranjero
cli-ai-input-country = País
cli-ai-vat-input-category = Categoría
cli-ai-vat-input-amount = Importe
cli-ai-vat-input-ateco = Código ATECO
cli-ai-vat-result-rate = Tasa de IVA recomendada
cli-ai-vat-result-nature = Naturaleza (si aplica)
cli-ai-vat-result-reasoning = Motivación
cli-ai-vat-result-legal-ref = Referencia normativa
cli-ai-vat-result-confidence = Nivel de confianza
cli-ai-vat-result-warnings = Advertencias
cli-ai-vat-result-note = Nota adicional

### ai - Console Output (chat)
cli-ai-chat-title = [bold cyan]Chat con IA[/bold cyan]
cli-ai-chat-welcome = [cyan]¡Bienvenido al Asistente de IA de OpenFatture![/cyan]
cli-ai-chat-welcome-help = [dim]Escriba sus preguntas o 'exit' para salir[/dim]
cli-ai-chat-session-loaded = [green]Sesión cargada: { $session_id }[/green]
cli-ai-chat-session-created = [green]Nueva sesión creada: { $session_id }[/green]
cli-ai-chat-prompt = [bold cyan]Usted:[/bold cyan]
cli-ai-chat-assistant-prefix = [bold green]Asistente:[/bold green]
cli-ai-chat-thinking = [yellow]Pensando...[/yellow]
cli-ai-chat-tool-calling = [yellow]Ejecutando herramienta: { $tool_name }[/yellow]
cli-ai-chat-tool-result = [dim]Resultado de herramienta: { $result }[/dim]
cli-ai-chat-session-saved = [green]Sesión guardada[/green]
cli-ai-chat-goodbye = [cyan]¡Adiós! Sesión guardada.[/cyan]
cli-ai-chat-error = [red]Error: { $error }[/red]
cli-ai-chat-cost-info = [dim]Tokens: { $tokens } | Costo: €{ $cost }[/dim]
cli-ai-chat-assistant-response = [bold cyan]Asistente:[/bold cyan]
cli-ai-chat-you = [bold green]Usted:[/bold green]
cli-ai-chat-instructions = Instrucciones: Haga preguntas sobre facturas, clientes, IVA o gestión fiscal
cli-ai-chat-invalid-session = [red]Sesión no encontrada: { $session_id }[/red]
cli-ai-chat-no-sessions = [yellow]No hay sesiones disponibles[/yellow]
cli-ai-chat-exported = [green]Conversación exportada: { $path }[/green]
cli-ai-chat-export-error = [red]Error de exportación: { $error }[/red]

### Métricas de IA
cli-ai-metrics-provider = Proveedor
cli-ai-metrics-model = Modelo
cli-ai-metrics-tokens = Tokens usados
cli-ai-metrics-cost = Costo estimado
cli-ai-metrics-latency = Latencia

### Errores generales de IA
cli-ai-error-unknown = Error desconocido durante la ejecución del comando de IA
cli-ai-error-provider-init = Error de inicialización del proveedor de IA: { $error }
cli-ai-error-context-load = Error al cargar contexto empresarial: { $error }

### ai - Console Output (voice-chat)
cli-ai-voice-title = [bold cyan]Chat de Voz con IA[/bold cyan]
cli-ai-voice-welcome = [cyan]¡Bienvenido al Chat de Voz![/cyan]
cli-ai-voice-recording-prompt = [yellow]Presione ENTER para comenzar a grabar ({ $duration }s)...[/yellow]
cli-ai-voice-recording = [bold yellow]Grabando...[/bold yellow]
cli-ai-voice-processing = [yellow]Procesando audio...[/yellow]
cli-ai-voice-transcription-title = [bold green]Usted dijo:[/bold green]
cli-ai-voice-transcription-text = [white]{ $text }[/white]
cli-ai-voice-language-detected = [dim]Idioma: { $language }[/dim]
cli-ai-voice-thinking = [yellow]Asistente pensando...[/yellow]
cli-ai-voice-response-title = [bold green]Asistente:[/bold green]
cli-ai-voice-response-text = [white]{ $text }[/white]
cli-ai-voice-playing = [cyan]Reproduciendo respuesta...[/cyan]
cli-ai-voice-audio-saved = [dim]Audio guardado: { $path }[/dim]
cli-ai-voice-goodbye = [cyan]¡Adiós![/cyan]
cli-ai-voice-error = [red]Error: { $error }[/red]

### ai - Console Output (forecast)
cli-ai-forecast-title = [bold cyan]Pronóstico de Flujo de Caja con IA[/bold cyan]
cli-ai-forecast-loading-data = [yellow]Cargando datos históricos...[/yellow]
cli-ai-forecast-data-stats = [cyan]Facturas: { $invoices } | Pagos: { $payments }[/cyan]
cli-ai-forecast-training = [yellow]Entrenando modelos ML...[/yellow]
cli-ai-forecast-training-progress = [yellow]{ $progress }%[/yellow]
cli-ai-forecast-predicting = [yellow]Generando pronóstico...[/yellow]
cli-ai-forecast-results-title = [bold green]Pronóstico de Flujo de Caja - Próximos { $months } { $months ->
    [one] mes
   *[other] meses
}[/bold green]
cli-ai-forecast-month = [cyan]{ $month }[/cyan]
cli-ai-forecast-predicted = Predicho: € { $amount }
cli-ai-forecast-confidence = Confianza: { $confidence }%
cli-ai-forecast-lower-bound = Límite inferior: € { $lower }
cli-ai-forecast-upper-bound = Límite superior: € { $upper }
cli-ai-forecast-metrics-title = [bold yellow]Métricas del Modelo:[/bold yellow]
cli-ai-forecast-mae = MAE: { $mae }
cli-ai-forecast-rmse = RMSE: { $rmse }
cli-ai-forecast-mape = MAPE: { $mape }%
cli-ai-forecast-insufficient-data = [yellow]Datos insuficientes. Se necesitan al menos { $required } facturas/pagos para entrenar.[/yellow]
cli-ai-forecast-error = [red]Error de pronóstico: { $error }[/red]

### ai - Console Output (intelligence)
cli-ai-intelligence-title = [bold cyan]Análisis de Inteligencia de Negocio[/bold cyan]
cli-ai-intelligence-analyzing = [yellow]Analizando datos de negocio...[/yellow]
cli-ai-intelligence-report-title = [bold green]Perspectivas de Negocio:[/bold green]
cli-ai-intelligence-section = [bold yellow]{ $section }[/bold yellow]
cli-ai-intelligence-insight = • { $insight }
cli-ai-intelligence-error = [red]Error de análisis: { $error }[/red]

### ai - Console Output (compliance)
cli-ai-compliance-title = [bold cyan]Verificación de Cumplimiento[/bold cyan]
cli-ai-compliance-checking = [yellow]Verificando factura { $numero }/{ $anno }...[/yellow]
cli-ai-compliance-passed = [bold green]Todas las verificaciones de cumplimiento pasadas[/bold green]
cli-ai-compliance-warnings = [yellow]{ $count } { $count ->
    [one] advertencia encontrada
   *[other] advertencias encontradas
}[/yellow]
cli-ai-compliance-errors = [red]{ $count } { $count ->
    [one] error encontrado
   *[other] errores encontrados
}[/red]
cli-ai-compliance-check-item = [{ $status }] { $message }
cli-ai-compliance-error = [red]Error de verificación de cumplimiento: { $error }[/red]

### ai - Console Output (rag)
cli-ai-rag-title = [bold cyan]Búsqueda de Documentos RAG[/bold cyan]
cli-ai-rag-indexing = [yellow]Indexando documentos...[/yellow]
cli-ai-rag-indexed = [green]{ $count } { $count ->
    [one] documento indexado
   *[other] documentos indexados
}[/green]
cli-ai-rag-searching = [yellow]Buscando en base de conocimiento...[/yellow]
cli-ai-rag-results-title = [bold green]Resultados de Búsqueda:[/bold green]
cli-ai-rag-result-item = { $rank }. [bold]{ $title }[/bold] (puntuación: { $score })
cli-ai-rag-result-text = { $text }
cli-ai-rag-no-results = [yellow]No se encontraron resultados[/yellow]
cli-ai-rag-error = [red]Error de RAG: { $error }[/red]

### ai - Console Output (feedback)
cli-ai-feedback-title = [bold cyan]Comentarios de IA[/bold cyan]
cli-ai-feedback-prompt-rating = [cyan]Calificar respuesta (1-5):[/cyan]
cli-ai-feedback-prompt-comment = [cyan]Comentario (opcional):[/cyan]
cli-ai-feedback-thanks = [green]¡Gracias por sus comentarios![/green]
cli-ai-feedback-saved = [green]Comentarios guardados en sesión { $session_id }[/green]
cli-ai-feedback-error = [red]Error de comentarios: { $error }[/red]

## ============================================================================
## EVENTS Commands - Historial de Eventos y Auditoría
## ============================================================================

### Help Texts - Comandos y Opciones
cli-events-help = Ver y analizar historial de eventos

# list command
cli-events-list-help-type = Filtrar por tipo de evento
cli-events-list-help-entity = Filtrar por tipo de entidad (factura, cliente, pago, etc.)
cli-events-list-help-entity-id = Filtrar por ID de entidad
cli-events-list-help-last-hours = Mostrar eventos de las últimas N horas
cli-events-list-help-last-days = Mostrar eventos de los últimos N días
cli-events-list-help-limit = Número máximo de eventos a mostrar

# show command
cli-events-show-help-event-id = ID de Evento (UUID)

# stats command
cli-events-stats-help-last-hours = Estadísticas de las últimas N horas
cli-events-stats-help-last-days = Estadísticas de los últimos N días

# timeline command
cli-events-timeline-help-entity-type = Tipo de entidad (invoice, client, etc.)
cli-events-timeline-help-entity-id = ID de Entidad

# search command
cli-events-search-help-query = Cadena de búsqueda
cli-events-search-help-limit = Número máximo de resultados

# dashboard command
cli-events-dashboard-help-days = Número de días a analizar

# trends command
cli-events-trends-help-days = Número de días a analizar
cli-events-trends-help-type = Filtrar por tipo de evento

### Table Columns - Encabezados de Columnas
cli-events-column-timestamp = Fecha/Hora
cli-events-column-event-type = Tipo de Evento
cli-events-column-entity = Entidad
cli-events-column-entity-type = Tipo de Entidad
cli-events-column-summary = Resumen
cli-events-column-count = Cantidad
cli-events-column-percentage = Porcentaje
cli-events-column-match = Coincidencia

### Titles and Headers - Títulos y Encabezados
cli-events-list-title = Historial de Eventos ({ $count } eventos)
cli-events-show-panel-title = [bold]Detalles del Evento: { $event_type }[/bold]
cli-events-stats-table-by-type = Eventos por Tipo
cli-events-stats-table-by-entity = Eventos por Tipo de Entidad
cli-events-stats-panel-title = [bold]Estadísticas de Eventos - { $range }[/bold]
cli-events-timeline-panel-title = [bold]Línea de Tiempo de Eventos: { $entity_type } #{ $entity_id }[/bold]
cli-events-search-results-title = Resultados de Búsqueda: '{ $query }' ({ $count } eventos)
cli-events-types-table-title = Tipos de Evento Disponibles
cli-events-dashboard-panel-title = [bold]Panel de Análisis de Eventos - Últimos { $days } Días[/bold]
cli-events-dashboard-table-entity-activity = Actividad por Entidad
cli-events-trends-panel-title = [bold]Tendencias de Eventos - Últimos { $days } Días[/bold]
cli-events-trends-panel-title-filtered = [bold]Tendencias de Eventos - Últimos { $days } Días ({ $event_type })[/bold]

### Labels - Etiquetas de Campos
cli-events-show-label-event-id = ID de Evento
cli-events-show-label-event-type = Tipo de Evento
cli-events-show-label-occurred-at = Ocurrió el
cli-events-show-label-published-at = Publicado el
cli-events-show-label-entity-type = Tipo de Entidad
cli-events-show-label-entity-id = ID de Entidad
cli-events-show-label-user-id = ID de Usuario
cli-events-show-label-event-data = Datos del Evento
cli-events-show-label-metadata = Metadatos

### Dashboard Metrics - Métricas del Panel
cli-events-dashboard-metric-total = Eventos Totales
cli-events-dashboard-metric-types = Tipos de Evento
cli-events-dashboard-metric-velocity = Eventos/Hora (24h)
cli-events-dashboard-metric-trend = Tendencia
cli-events-dashboard-section-top-types = [bold]Tipos de Evento Principales[/bold]
cli-events-dashboard-column-events = Eventos

### Messages - Mensajes de Salida
cli-events-no-events = [yellow]No se encontraron eventos que coincidan con los criterios[/yellow]
cli-events-show-not-found = [red]Evento con ID '{ $event_id }' no encontrado[/red]
cli-events-filters-applied =
    [dim]Filtros: { $filters }[/dim]
cli-events-stats-all-time = Todo el Tiempo
cli-events-stats-last-hours = Últimas { $hours } horas
cli-events-stats-last-days = Últimos { $days } días
cli-events-stats-total =
    [bold]Eventos Totales:[/bold] { $total }

cli-events-stats-most-recent = [bold]Evento Más Reciente:[/bold] { $event_type } el { $timestamp }
cli-events-stats-oldest = [bold]Evento Más Antiguo:[/bold] { $event_type } el { $timestamp }
cli-events-timeline-no-events = [yellow]No se encontraron eventos para { $entity_type } con ID { $entity_id }[/yellow]
cli-events-timeline-total =
    [dim]Total de eventos: { $total }[/dim]
cli-events-search-no-results = [yellow]No se encontraron eventos que coincidan con '{ $query }'[/yellow]
cli-events-types-no-events = [yellow]Aún no se han registrado eventos[/yellow]
cli-events-dashboard-most-recent = [dim]Más Reciente: { $event_type } el { $timestamp }[/dim]
cli-events-trends-no-events = [yellow]No se encontraron eventos para el período especificado[/yellow]
cli-events-trends-summary = [dim]Total: { $total } eventos | Promedio: { $avg } eventos/día[/dim]

## ============================================================================
## LIGHTNING Commands - Lightning Network y Cumplimiento
## ============================================================================

### Help Texts - Comandos y Opciones
cli-lightning-help = Gestión de pagos Lightning Network
cli-lightning-report-help = Generar informes de cumplimiento
cli-lightning-aml-help = Gestión Anti-Blanqueo de Capitales

### Status Command
cli-lightning-status-title = Estado Lightning Network
cli-lightning-status-disabled = Estado: Deshabilitado
cli-lightning-status-disabled-hint-env = Establezca lightning_enabled=true en .env para habilitar pagos Lightning
cli-lightning-status-disabled-hint-cmd = Use 'openfatture config set lightning_enabled true' para habilitar
cli-lightning-status-enabled = Estado: Habilitado
cli-lightning-status-host = Host: { $host }
cli-lightning-status-timeout = Tiempo de espera: { $timeout }s
cli-lightning-status-max-retries = Máx. reintentos: { $max_retries }
cli-lightning-status-btc-provider = Proveedor BTC: { $provider }
cli-lightning-status-liquidity = Monitoreo de liquidez: { $status }

cli-lightning-btc-provider-coingecko = CoinGecko
cli-lightning-btc-provider-cmc = CoinMarketCap
cli-lightning-btc-provider-fallback = Fallback
cli-lightning-liquidity-enabled = Habilitado
cli-lightning-liquidity-disabled = Deshabilitado

### Invoice Command
cli-lightning-disabled-error = Lightning está deshabilitado. Habilite con: openfatture config set lightning_enabled true
cli-lightning-invoice-title = Creación de Factura Lightning
cli-lightning-invoice-not-available = Función aún no disponible - Integración Lightning en desarrollo

### Channels Command
cli-lightning-channels-title = Canales Lightning
cli-lightning-channels-not-available = No hay canales configurados - Integración Lightning en desarrollo

### Liquidity Command
cli-lightning-liquidity-title = Liquidez de Canales
cli-lightning-liquidity-not-available = Monitoreo de liquidez no disponible - Integración Lightning en desarrollo

### Compliance Check Command
cli-lightning-compliance-opt-tax-year = Año fiscal a verificar (predeterminado: año actual)
cli-lightning-compliance-opt-verbose = Mostrar información detallada

cli-lightning-compliance-title =

    [bold cyan]Verificación de Cumplimiento Lightning - { $year }[/bold cyan]

cli-lightning-compliance-summary-title = [bold]Resumen del Año Fiscal[/bold]
cli-lightning-compliance-summary-payments = Número de pagos:
cli-lightning-compliance-summary-revenue = Ingresos totales (EUR):
cli-lightning-compliance-summary-gains = Ganancias de capital totales (EUR):
cli-lightning-compliance-summary-tax = Impuestos estimados (EUR):

cli-lightning-compliance-aml-title = [bold]Cumplimiento Anti-Blanqueo (Umbral: 5.000 EUR)[/bold]
cli-lightning-compliance-aml-total = Total sobre el umbral:
cli-lightning-compliance-aml-verified = Verificados:
cli-lightning-compliance-aml-unverified = No verificados:
cli-lightning-compliance-aml-status-ok = OK
cli-lightning-compliance-aml-status-require = { $count } REQUIEREN VERIFICACIÓN

cli-lightning-compliance-quadro-title = [bold]Declaración Quadro RW (Obligatorio desde 2025)[/bold]
cli-lightning-compliance-quadro-count = Facturas que requieren declaración:
cli-lightning-compliance-action-required = Acción requerida:
cli-lightning-compliance-quadro-action = [yellow]Declarar todas las tenencias crypto en Quadro RW[/yellow]
cli-lightning-compliance-status = Estado:
cli-lightning-compliance-quadro-status-ok = [green]No se requieren declaraciones[/green]

cli-lightning-compliance-data-quality-title = [bold]Calidad de Datos[/bold]
cli-lightning-compliance-data-quality-missing = Facturas con datos fiscales faltantes:
cli-lightning-compliance-data-quality-action = [red]Agregar tasa BTC/EUR e importe EUR para cumplimiento fiscal[/red]
cli-lightning-compliance-data-quality-status-ok = [green]Todas las facturas liquidadas tienen datos fiscales[/green]

cli-lightning-compliance-issue-aml = { $count } pago(s) Anti-Blanqueo no verificado(s)
cli-lightning-compliance-issue-missing-data = { $count } factura(s) sin datos fiscales
cli-lightning-compliance-issues-found = [bold red]Problemas de Cumplimiento Encontrados: { $issues }[/bold red]

cli-lightning-compliance-passed = [bold green]Todas las Verificaciones de Cumplimiento Pasadas[/bold green]

cli-lightning-compliance-verbose-title = [bold]Pagos Anti-Blanqueo No Verificados:[/bold]
cli-lightning-compliance-verbose-item =   • { $hash }... - { $amount } EUR - Liquidado: { $date }

cli-lightning-compliance-error = [bold red]Error al ejecutar la verificación de cumplimiento: { $error }[/bold red]

### Report Commands - Common Options
cli-lightning-report-opt-tax-year = Año fiscal para el informe
cli-lightning-report-opt-format = Formato de salida: json o csv
cli-lightning-report-opt-output = Ruta del archivo de salida (opcional, imprime en stdout si no se proporciona)

cli-lightning-report-invalid-format = [bold red]Formato no válido. Use 'json' o 'csv'[/bold red]
cli-lightning-report-saved = [green]Informe guardado en: { $path }[/green]

cli-lightning-report-summary = [cyan]Total de facturas en el informe: { $count }[/cyan]

### Quadro RW Report
cli-lightning-report-quadro-title =

    [bold cyan]Generando Informe Quadro RW - { $year } ({ $format })[/bold cyan]

cli-lightning-report-quadro-error = [bold red]Error al generar el informe Quadro RW: { $error }[/bold red]

### Capital Gains Report
cli-lightning-report-gains-title =

    [bold cyan]Generando Informe de Ganancias de Capital - { $year } ({ $format })[/bold cyan]

cli-lightning-report-gains-summary-count = [cyan]Total de facturas con ganancias: { $count }[/cyan]
cli-lightning-report-gains-summary-total = [yellow]Ganancias de capital totales: { $total } EUR[/yellow]
cli-lightning-report-gains-summary-tax = [red]Impuestos estimados ({ $rate }%): { $tax } EUR[/red]
cli-lightning-report-gains-error = [bold red]Error al generar el informe de ganancias de capital: { $error }[/bold red]

### AML Report
cli-lightning-aml-opt-threshold = Umbral Anti-Blanqueo en EUR
cli-lightning-aml-opt-format = Formato de salida: solo json
cli-lightning-aml-opt-verbose = Mostrar información detallada

cli-lightning-aml-report-title =

    [bold cyan]Generando Informe de Cumplimiento Anti-Blanqueo (Umbral: { $threshold } EUR)[/bold cyan]

cli-lightning-aml-report-summary-total = [cyan]Total sobre el umbral: { $total }[/cyan]
cli-lightning-aml-report-summary-verified = [green]Verificados: { $verified }[/green]
cli-lightning-aml-report-summary-unverified-ok = No verificados: 0
cli-lightning-aml-report-summary-unverified-warning = No verificados: { $count }
cli-lightning-aml-report-summary-rate = [yellow]Tasa de cumplimiento: { $rate }%[/yellow]

cli-lightning-aml-report-action-required =

    [bold yellow]Acción Requerida: Verificar pagos no verificados con proceso Anti-Blanqueo[/bold yellow]
cli-lightning-aml-report-action-hint = [dim]Use: openfatture lightning aml list-unverified para ver detalles[/dim]

cli-lightning-aml-report-error = [bold red]Error al generar el informe Anti-Blanqueo: { $error }[/bold red]

### AML List Unverified Command
cli-lightning-aml-list-title =

    [bold cyan]Pagos Anti-Blanqueo No Verificados (Umbral: { $threshold } EUR)[/bold cyan]

cli-lightning-aml-list-empty = [green]No se encontraron pagos no verificados[/green]

cli-lightning-aml-list-table-title = Pagos No Verificados ({ $count } totales)
cli-lightning-aml-list-col-hash = Hash de Pago
cli-lightning-aml-list-col-amount = Importe (EUR)
cli-lightning-aml-list-col-settled = Liquidado El
cli-lightning-aml-list-col-fattura = ID Factura
cli-lightning-aml-list-col-client = ID Cliente
cli-lightning-aml-list-col-description = Descripción

cli-lightning-aml-list-action-required = [bold yellow]Acción Requerida: Estos pagos requieren verificación de identidad del cliente[/bold yellow]
cli-lightning-aml-list-action-hint = [dim]Use: openfatture lightning aml verify <payment-hash> --verified-by <email>[/dim]

cli-lightning-aml-list-error = [bold red]Error al listar pagos no verificados: { $error }[/bold red]

### AML Verify Command
cli-lightning-aml-verify-arg-hash = Hash del pago a verificar
cli-lightning-aml-verify-opt-by = Email de la persona que verifica
cli-lightning-aml-verify-opt-notes = Notas de verificación (opcional)
cli-lightning-aml-verify-opt-client = ID Cliente (opcional)

cli-lightning-aml-verify-title =

    [bold cyan]Verificando Pago Anti-Blanqueo: { $hash }...[/bold cyan]

cli-lightning-aml-verify-not-found = [bold red]Factura no encontrada: { $hash }[/bold red]
cli-lightning-aml-verify-already-verified = [yellow]Pago ya verificado el { $date }[/yellow]
cli-lightning-aml-verify-below-threshold = [yellow]El pago no supera el umbral Anti-Blanqueo, pero se marca como verificado de todos modos[/yellow]
cli-lightning-aml-verify-success = [green]Pago verificado con éxito[/green]

cli-lightning-aml-verify-label-hash = Hash de Pago:
cli-lightning-aml-verify-label-amount = Importe (EUR):
cli-lightning-aml-verify-label-settled = Liquidado El:
cli-lightning-aml-verify-label-by = Verificado Por:
cli-lightning-aml-verify-label-at = Verificado El:
cli-lightning-aml-verify-label-notes = Notas:

cli-lightning-aml-verify-error = [bold red]Error al verificar el pago: { $error }[/bold red]

## ============================================================================
## REPORT Commands - Informes y Estadísticas
## ============================================================================

### Help Texts - Comandos y Opciones
cli-report-iva-help-anno = Año
cli-report-iva-help-trimestre = Trimestre (Q1-Q4)
cli-report-clienti-help-anno = Año
cli-report-scadenze-help-finestra = Número de días considerados "próximo a vencer" (default: 14)

### Titles and Headers - VAT Report
cli-report-iva-title =

    [bold blue]Informe de IVA - { $anno }[/bold blue]

cli-report-iva-quarter =

    [cyan]Trimestre: { $trimestre } ({ $mese_inizio }-{ $mese_fine })[/cyan]

cli-report-iva-full-year =

    [cyan]Año completo[/cyan]

cli-report-iva-summary-title = Resumen de IVA
cli-report-iva-breakdown-title =

    [bold]Desglose por tipo de IVA:[/bold]

### Titles and Headers - Client Report
cli-report-clienti-title =

    [bold blue]Informe de Facturación de Clientes - { $anno }[/bold blue]

cli-report-clienti-table-title = Principales Clientes - { $anno }

### Titles and Headers - Due Dates Report
cli-report-scadenze-title =

    [bold blue]Resumen de Fechas de Vencimiento[/bold blue]

### Table Columns - VAT Report
cli-report-iva-column-metric = Métrica
cli-report-iva-column-amount = Importe
cli-report-iva-column-vat-rate = Tipo de IVA
cli-report-iva-column-imponibile = Base Imponible
cli-report-iva-column-vat = IVA

### Table Columns - Client Report
cli-report-clienti-column-rank = Pos.
cli-report-clienti-column-client = Cliente
cli-report-clienti-column-invoices = Facturas
cli-report-clienti-column-revenue = Facturación

### Table Columns - Due Dates Report
cli-report-scadenze-column-invoice = Factura
cli-report-scadenze-column-client = Cliente
cli-report-scadenze-column-due-date = Fecha Vencimiento
cli-report-scadenze-column-days-delta = Δ días
cli-report-scadenze-column-residual = Pendiente
cli-report-scadenze-column-paid = Pagado
cli-report-scadenze-column-total = Total
cli-report-scadenze-column-status = Estado

### Labels - VAT Report
cli-report-iva-label-num-invoices = Número de facturas
cli-report-iva-label-imponibile = Total base imponible
cli-report-iva-label-total-vat = Total IVA
cli-report-iva-label-total-revenue-bold = [bold]Facturación total[/bold]

### Messages - General
cli-report-no-invoices = [yellow]No se encontraron facturas para el período seleccionado[/yellow]
cli-report-no-invoices-year = [yellow]No se encontraron facturas para el año seleccionado[/yellow]

### Messages - VAT Report
cli-report-iva-error-invalid-quarter = [red]Trimestre no válido. Use Q1, Q2, Q3 o Q4[/red]

### Messages - Client Report
cli-report-clienti-total-revenue =

    [bold]Facturación total: { $totale }[/bold]

### Messages - Due Dates Report
cli-report-scadenze-no-outstanding =

    [green]No hay pagos pendientes. ¡Todas las facturas están liquidadas![/green]

cli-report-scadenze-hidden-upcoming =

    [dim]… { $count } pagos futuros adicionales no mostrados. Use --finestra o exporte datos del módulo de pagos para más detalles.[/dim]

cli-report-scadenze-total-outstanding =

    [bold]Saldo pendiente total: { $totale }[/bold]

### Section Titles - Due Dates Report
cli-report-scadenze-section-overdue = [red]Vencidos[/red]
cli-report-scadenze-section-due-soon = [yellow]Próximo a vencer (<= { $finestra } días)[/yellow]
cli-report-scadenze-section-upcoming = [cyan]Próximos pagos[/cyan]

cli-report-scadenze-section-total = [bold { $color }]Total pendiente: { $totale } • Pagos: { $count }[/]

### Payment Status Labels - Due Dates Report
cli-report-scadenze-status-overdue = Vencido
cli-report-scadenze-status-partial = Parcial
cli-report-scadenze-status-due = Por pagar

## ============================================================================
## PEC Commands - Pruebas y Configuración PEC
## ============================================================================

### Titles
cli-pec-test-title = [bold blue]Prueba de Configuración PEC[/bold blue]
cli-pec-info-title = [bold blue]Configuración PEC[/bold blue]

### Labels
cli-pec-label-address = [cyan]Dirección PEC:[/cyan]
cli-pec-label-smtp-server = [cyan]Servidor SMTP:[/cyan]
cli-pec-label-smtp-port = [cyan]Puerto SMTP:[/cyan]
cli-pec-label-template = [cyan]Plantilla:[/cyan] test/test_email.html + .txt
cli-pec-label-locale = [cyan]Idioma:[/cyan]
cli-pec-label-password = Contraseña
cli-pec-label-sdi-pec = PEC SDI

### Table Headers
cli-pec-table-setting = Configuración
cli-pec-table-value = Valor

### Error Messages
cli-pec-error-no-address = [red]Dirección PEC no configurada[/red]
cli-pec-error-no-address-hint = Ejecuta: [cyan]openfatture init[/cyan] para configurar
cli-pec-error-no-password = [red]Contraseña PEC no configurada[/red]
cli-pec-error-no-password-hint = Configúrala en tu archivo .env: PEC_PASSWORD=tu_contraseña

### Test Messages
cli-pec-sending-test = Enviando email de prueba con plantilla profesional...
cli-pec-test-success = [bold green]Email de prueba enviado correctamente![/bold green]
cli-pec-test-check-inbox = Revisa tu bandeja PEC: { $pec_address }
cli-pec-test-email-includes = [dim]El email incluye:[/dim]
cli-pec-test-feature-html = • HTML profesional + texto plano
cli-pec-test-feature-branding = • Marca de tu empresa
cli-pec-test-feature-language = • Idioma: { $language }
cli-pec-test-more-testing = [dim]Para más pruebas de email:[/dim]
cli-pec-test-cmd-email-test = [cyan]openfatture email test[/cyan]  - Prueba completa de email
cli-pec-test-cmd-email-preview = [cyan]openfatture email preview[/cyan] - Vista previa de plantillas

cli-pec-test-failed =
    [red]Prueba fallida: { $error }[/red]
cli-pec-test-common-issues = [yellow]Problemas comunes:[/yellow]
cli-pec-issue-credentials = • Credenciales PEC incorrectas
cli-pec-issue-smtp = • Servidor SMTP incorrecto
cli-pec-issue-firewall = • Firewall bloqueando puerto 465
cli-pec-issue-mailbox = • Buzón PEC lleno

### Info Messages
cli-pec-not-set = [red]No configurado[/red]
cli-pec-password-set = [green]Configurada[/green]

## ============================================================================
## NOTIFICHE Commands - Gestión de Notificaciones SDI
## ============================================================================

### Help Text
cli-notifiche-help-file-path = Ruta al archivo XML de notificación SDI
cli-notifiche-help-no-email = Omitir notificación automática por email
cli-notifiche-help-tipo = Filtrar por tipo (AT, RC, NS, MC, NE)
cli-notifiche-help-limit = Número máximo de resultados
cli-notifiche-help-notification-id = ID de Notificación

### Titles
cli-notifiche-process-title = [bold blue]Procesando Notificación SDI[/bold blue]
cli-notifiche-list-title = [bold blue]Notificaciones SDI[/bold blue]
cli-notifiche-show-title = [bold blue]{ $emoji } Notificación { $id }: { $tipo }[/bold blue]

### Table Headers
cli-notifiche-table-field = Campo
cli-notifiche-table-value = Valor
cli-notifiche-column-id = ID
cli-notifiche-column-type = Tipo
cli-notifiche-column-date = Fecha
cli-notifiche-column-invoice = Factura
cli-notifiche-column-client = Cliente
cli-notifiche-column-sdi-id = ID SDI

### Labels
cli-notifiche-label-type = Tipo
cli-notifiche-label-sdi-id = ID SDI
cli-notifiche-label-file = Archivo
cli-notifiche-label-date = Fecha
cli-notifiche-label-message = Mensaje
cli-notifiche-label-errors = Errores
cli-notifiche-label-invoice = Factura
cli-notifiche-label-client = Cliente
cli-notifiche-label-invoice-status = Estado de Factura
cli-notifiche-label-received = Recibido
cli-notifiche-label-description = Descripción
cli-notifiche-label-xml-path = Ruta XML

### Messages
cli-notifiche-file-not-found = [red]Archivo no encontrado: { $file_path }[/red]
cli-notifiche-file-label = [cyan]Archivo:[/cyan] { $name }
cli-notifiche-size-label = [cyan]Tamaño:[/cyan] { $size } bytes
cli-notifiche-auto-email-enabled =
    [dim]Email automático habilitado { $email }[/dim]

cli-notifiche-processing = Procesando notificación...
cli-notifiche-error =
    [red]Error: { $error }[/red]
cli-notifiche-success = [bold green]Notificación procesada correctamente![/bold green]
cli-notifiche-errors-count = { $count } error(es)
cli-notifiche-email-sent =
    [dim]Notificación por email enviada a { $email }[/dim]

cli-notifiche-no-notifications = [yellow]No se encontraron notificaciones[/yellow]
cli-notifiche-process-hint = [dim]Procesa notificaciones con:[/dim]
cli-notifiche-process-cmd = [cyan]openfatture notifiche process <archivo.xml>[/cyan]
cli-notifiche-list-table-title = Notificaciones ({ $count })

cli-notifiche-not-found = [red]Notificación { $notification_id } no encontrada[/red]

## ============================================================================
## CONFIG Commands - Gestión de Configuración
## ============================================================================

### Help Text
cli-config-help-key = Clave de configuración (ej. pec.address)
cli-config-help-value = Valor de configuración

### Titles
cli-config-show-title = Configuración de OpenFatture

### Table Headers
cli-config-column-setting = Configuración
cli-config-column-value = Valor

### Section Labels - Application
cli-config-label-app-version = Versión de la App
cli-config-label-debug-mode = Modo Debug

### Section Labels - Database
cli-config-label-database-url = URL de Base de Datos

### Section Labels - Paths
cli-config-label-data-dir = Directorio de Datos
cli-config-label-archive-dir = Directorio de Archivo
cli-config-label-certificates-dir = Directorio de Certificados

### Section Labels - Company Data
cli-config-label-company-name = Nombre de Empresa
cli-config-label-partita-iva = Partita IVA
cli-config-label-codice-fiscale = Codice Fiscale
cli-config-label-tax-regime = Régimen Fiscal

### Section Labels - PEC
cli-config-label-pec-address = Dirección PEC
cli-config-label-pec-smtp-server = Servidor SMTP PEC
cli-config-label-sdi-pec-address = Dirección PEC SDI

### Section Labels - Email & Notifications
cli-config-label-notification-email = Email de Notificaciones
cli-config-label-notifications-enabled = Notificaciones Habilitadas
cli-config-label-locale = Idioma
cli-config-label-email-logo-url = URL del Logo de Email
cli-config-label-primary-color = Color Primario
cli-config-label-secondary-color = Color Secundario
cli-config-label-email-footer = Pie de Email

### Section Labels - AI Configuration
cli-config-label-ai-provider = Proveedor de IA
cli-config-label-ai-model = Modelo de IA
cli-config-label-ai-base-url = URL Base de IA
cli-config-label-ai-api-key = Clave API de IA
cli-config-label-chat-enabled = Chat Habilitado
cli-config-label-chat-auto-save = Auto-Guardado de Chat
cli-config-label-max-messages = Máx Mensajes/Sesión
cli-config-label-max-tokens = Máx Tokens/Sesión
cli-config-label-tools-enabled = Herramientas Habilitadas
cli-config-label-enabled-tools = Herramientas Habilitadas

### Status Values
cli-config-not-set = [red]No configurado[/red]
cli-config-not-set-optional = [yellow]No configurado[/yellow]
cli-config-set = [green]Configurada[/green]
cli-config-yes = [green]Sí[/green]
cli-config-no = [red]No[/red]
cli-config-auto-generated = [dim]Auto-generado[/dim]
cli-config-all-tools = todas
cli-config-tools-count = { $count } herramientas

### Messages
cli-config-reload-success = [green]Configuración recargada[/green]
cli-config-set-success = [green]Configurado { $key } = { $value }[/green]
cli-config-saved-to = [dim]Guardado en { $path }[/dim]
cli-config-invalid-key = [red]Clave de configuración inválida: { $key }[/red]
cli-config-error = [red]Error: { $error }[/red]
