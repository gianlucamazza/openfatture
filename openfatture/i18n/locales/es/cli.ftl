# CLI commands translations
# ES (Español)

## MAIN CLI

### main - Main CLI
cli-main-title = OpenFatture - Sistema de Facturación Electrónica de Código Abierto
cli-main-description = Sistema completo para gestionar facturas electrónicas FatturaPA
cli-main-version = Versión { $version }

### main - Command Groups
cli-main-group-invoices = 📄 Gestión de Facturas
cli-main-group-clients = 👥 Gestión de Clientes
cli-main-group-products = 📦 Gestión de Productos
cli-main-group-pec = 📧 PEC y SDI
cli-main-group-batch = 📊 Operaciones por Lotes
cli-main-group-ai = 🤖 Asistente IA
cli-main-group-payments = 💰 Seguimiento de Pagos
cli-main-group-preventivi = 📋 Presupuestos
cli-main-group-events = 📅 Sistema de Eventos
cli-main-group-lightning = ⚡ Red Lightning
cli-main-group-web = 🌐 Interfaz Web

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
cli-fattura-create-title = [bold blue]🧾 Crear Nueva Factura[/bold blue]
cli-fattura-select-client-title = [bold cyan]Selección de Cliente[/bold cyan]
cli-fattura-no-clients-error = [red]No se encontraron clientes. Añade uno primero con 'cliente add'[/red]
cli-fattura-available-clients = [cyan]Clientes disponibles:[/cyan]
cli-fattura-client-prompt = Número de cliente
cli-fattura-client-selected = [green]✓ Cliente: { $client_name }[/green]
cli-fattura-invalid-client-error = [red]Selección de cliente no válida[/red]

cli-fattura-add-lines-title = [bold cyan]Líneas de Factura[/bold cyan]
cli-fattura-line-description-prompt = Descripción (vacío para terminar)
cli-fattura-line-quantity-prompt = Cantidad
cli-fattura-line-unit-price-prompt = Precio unitario (€)
cli-fattura-line-vat-rate-prompt = Tasa de IVA (%)
cli-fattura-line-added = [green]✓ Línea añadida: { $description } - € { $amount }[/green]

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
cli-fattura-created-success = [bold green]✓ Factura creada exitosamente![/bold green]
cli-fattura-created-number = [green]Número de factura: { $numero }/{ $anno }[/green]
cli-fattura-created-xml = [green]XML guardado: { $xml_path }[/green]

cli-fattura-list-title = [bold blue]Lista de Facturas[/bold blue]
cli-fattura-list-empty = [yellow]No se encontraron facturas[/yellow]

cli-fattura-show-title = [bold blue]Factura { $numero }/{ $anno }[/bold blue]
cli-fattura-show-not-found = [red]Factura no encontrada: { $numero }/{ $anno }[/red]

cli-fattura-delete-confirm = [yellow]¿Eliminar factura { $numero }/{ $anno }?[/yellow]
cli-fattura-delete-warning = [red]ADVERTENCIA: Esta operación no se puede deshacer[/red]
cli-fattura-delete-status-restriction = [red]No se puede eliminar factura en estado '{ $status }'[/red]
cli-fattura-delete-success = [green]✓ Factura { $numero }/{ $anno } eliminada[/green]
cli-fattura-delete-cancelled = [yellow]Operación cancelada[/yellow]
cli-fattura-delete-cannot-delete-sent = [red]No se pueden eliminar facturas en estado INVIATA o CONSEGNATA[/red]
cli-fattura-cancelled = Cancelado.

cli-fattura-table-title-list = Facturas ({ $count })
cli-fattura-invalid-status = [red]Estado no válido: { $status }[/red]

cli-fattura-line-items-header = Líneas de Factura
cli-fattura-totals-header = Totales

cli-fattura-xml-generation-title = [bold blue]🔧 Generación XML FatturaPA[/bold blue]
cli-fattura-generating-xml = Generando XML para factura { $numero }/{ $anno }...
cli-fattura-xml-generated = [green]✓ XML generado con éxito![/green]

cli-fattura-send-title = [bold blue]📤 Envío de Factura a SDI[/bold blue]
cli-fattura-send-step1-xml = [cyan]1. Generando XML...[/cyan]
cli-fattura-sent-success-message = [bold green]✓ Factura { $numero }/{ $anno } enviada con éxito![/bold green]

cli-fattura-validate-success = [green]✓ XML válido[/green]
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
cli-cliente-help-denominazione = Nombre de empresa o nombre completo
cli-cliente-help-partita-iva = Número de IVA
cli-cliente-help-codice-fiscale = Código fiscal
cli-cliente-help-pec = Dirección PEC
cli-cliente-help-codice-destinatario = Código de destino SDI
cli-cliente-help-formato = Formato de salida (table, json, yaml)
cli-cliente-help-search = Término de búsqueda
cli-cliente-help-limit = Número máximo de resultados

### cliente - Console Output
cli-cliente-list-title = Clientes ({ $count })
cli-cliente-list-empty = [yellow]No se encontraron clientes[/yellow]
cli-cliente-added-success = [green]✓ Cliente añadido exitosamente (ID: { $id })[/green]
cli-cliente-updated-success = [green]✓ Cliente actualizado exitosamente[/green]
cli-cliente-deleted-success = [green]✓ Cliente eliminado exitosamente[/green]
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

### ai - Console Output (describe)
cli-ai-describe-title = [bold cyan]🤖 Generación de Descripción de Factura con IA[/bold cyan]
cli-ai-describe-input-prompt = [cyan]Ingrese descripción breve:[/cyan]
cli-ai-describe-processing = [yellow]Procesando con IA...[/yellow]
cli-ai-describe-result-title = [bold green]Descripción Generada:[/bold green]
cli-ai-describe-result-text = [white]{ $text }[/white]
cli-ai-describe-copy-hint = [dim]Puede copiar esta descripción al crear una factura[/dim]
cli-ai-describe-error = [red]Error al generar descripción: { $error }[/red]

### ai - Console Output (suggest-vat)
cli-ai-vat-title = [bold cyan]🧾 Sugerencia de Tasa de IVA con IA[/bold cyan]
cli-ai-vat-input-prompt = [cyan]Descripción del servicio/producto:[/cyan]
cli-ai-vat-processing = [yellow]Analizando con IA...[/yellow]
cli-ai-vat-result-title = [bold green]Tasa de IVA Sugerida:[/bold green]
cli-ai-vat-rate = [white]{ $rate }%[/white]
cli-ai-vat-reasoning-title = [bold yellow]Razonamiento:[/bold yellow]
cli-ai-vat-reasoning-text = [white]{ $reasoning }[/white]
cli-ai-vat-warning = [yellow]⚠️  Siempre verifique con un asesor fiscal para casos complejos[/yellow]
cli-ai-vat-error = [red]Error al sugerir tasa de IVA: { $error }[/red]

### ai - Console Output (chat)
cli-ai-chat-title = [bold cyan]💬 Chat con IA[/bold cyan]
cli-ai-chat-welcome = [cyan]¡Bienvenido al Asistente de IA de OpenFatture![/cyan]
cli-ai-chat-welcome-help = [dim]Escriba sus preguntas o 'exit' para salir[/dim]
cli-ai-chat-session-loaded = [green]✓ Sesión cargada: { $session_id }[/green]
cli-ai-chat-session-created = [green]✓ Nueva sesión creada: { $session_id }[/green]
cli-ai-chat-prompt = [bold cyan]Usted:[/bold cyan]
cli-ai-chat-assistant-prefix = [bold green]Asistente:[/bold green]
cli-ai-chat-thinking = [yellow]Pensando...[/yellow]
cli-ai-chat-tool-calling = [yellow]Ejecutando herramienta: { $tool_name }[/yellow]
cli-ai-chat-tool-result = [dim]Resultado de herramienta: { $result }[/dim]
cli-ai-chat-session-saved = [green]✓ Sesión guardada[/green]
cli-ai-chat-goodbye = [cyan]¡Adiós! Sesión guardada.[/cyan]
cli-ai-chat-error = [red]Error: { $error }[/red]
cli-ai-chat-cost-info = [dim]Tokens: { $tokens } | Costo: €{ $cost }[/dim]

### ai - Console Output (voice-chat)
cli-ai-voice-title = [bold cyan]🎤 Chat de Voz con IA[/bold cyan]
cli-ai-voice-welcome = [cyan]¡Bienvenido al Chat de Voz![/cyan]
cli-ai-voice-recording-prompt = [yellow]Presione ENTER para comenzar a grabar ({ $duration }s)...[/yellow]
cli-ai-voice-recording = [bold yellow]🔴 Grabando...[/bold yellow]
cli-ai-voice-processing = [yellow]Procesando audio...[/yellow]
cli-ai-voice-transcription-title = [bold green]Usted dijo:[/bold green]
cli-ai-voice-transcription-text = [white]{ $text }[/white]
cli-ai-voice-language-detected = [dim]Idioma: { $language }[/dim]
cli-ai-voice-thinking = [yellow]Asistente pensando...[/yellow]
cli-ai-voice-response-title = [bold green]Asistente:[/bold green]
cli-ai-voice-response-text = [white]{ $text }[/white]
cli-ai-voice-playing = [cyan]🔊 Reproduciendo respuesta...[/cyan]
cli-ai-voice-audio-saved = [dim]Audio guardado: { $path }[/dim]
cli-ai-voice-goodbye = [cyan]¡Adiós![/cyan]
cli-ai-voice-error = [red]Error: { $error }[/red]

### ai - Console Output (forecast)
cli-ai-forecast-title = [bold cyan]📊 Pronóstico de Flujo de Caja con IA[/bold cyan]
cli-ai-forecast-loading-data = [yellow]Cargando datos históricos...[/yellow]
cli-ai-forecast-data-stats = [cyan]Facturas: { $invoices } | Pagos: { $payments }[/cyan]
cli-ai-forecast-training = [yellow]Entrenando modelos ML...[/yellow]
cli-ai-forecast-training-progress = [yellow]{ $progress }%[/yellow]
cli-ai-forecast-predicting = [yellow]Generando pronóstico...[/yellow]
cli-ai-forecast-results-title = [bold green]📊 Pronóstico de Flujo de Caja - Próximos { $months } { $months ->
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
cli-ai-intelligence-title = [bold cyan]🧠 Análisis de Inteligencia de Negocio[/bold cyan]
cli-ai-intelligence-analyzing = [yellow]Analizando datos de negocio...[/yellow]
cli-ai-intelligence-report-title = [bold green]Perspectivas de Negocio:[/bold green]
cli-ai-intelligence-section = [bold yellow]{ $section }[/bold yellow]
cli-ai-intelligence-insight = • { $insight }
cli-ai-intelligence-error = [red]Error de análisis: { $error }[/red]

### ai - Console Output (compliance)
cli-ai-compliance-title = [bold cyan]✅ Verificación de Cumplimiento[/bold cyan]
cli-ai-compliance-checking = [yellow]Verificando factura { $numero }/{ $anno }...[/yellow]
cli-ai-compliance-passed = [bold green]✓ Todas las verificaciones de cumplimiento pasadas[/bold green]
cli-ai-compliance-warnings = [yellow]⚠️  { $count } { $count ->
    [one] advertencia encontrada
   *[other] advertencias encontradas
}[/yellow]
cli-ai-compliance-errors = [red]❌ { $count } { $count ->
    [one] error encontrado
   *[other] errores encontrados
}[/red]
cli-ai-compliance-check-item = [{ $status }] { $message }
cli-ai-compliance-error = [red]Error de verificación de cumplimiento: { $error }[/red]

### ai - Console Output (rag)
cli-ai-rag-title = [bold cyan]📚 Búsqueda de Documentos RAG[/bold cyan]
cli-ai-rag-indexing = [yellow]Indexando documentos...[/yellow]
cli-ai-rag-indexed = [green]✓ { $count } { $count ->
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
cli-ai-feedback-title = [bold cyan]📝 Comentarios de IA[/bold cyan]
cli-ai-feedback-prompt-rating = [cyan]Calificar respuesta (1-5):[/cyan]
cli-ai-feedback-prompt-comment = [cyan]Comentario (opcional):[/cyan]
cli-ai-feedback-thanks = [green]✓ ¡Gracias por sus comentarios![/green]
cli-ai-feedback-saved = [green]Comentarios guardados en sesión { $session_id }[/green]
cli-ai-feedback-error = [red]Error de comentarios: { $error }[/red]
