### main - Main CLI

## CONFIG Commands - Gestión de Configuración
cli-config-help-key = Clave de configuración (ej. pec.address)
cli-config-help-value = Valor de configuración
cli-config-show-title = Configuración de OpenFatture
cli-config-column-setting = Configuración
cli-config-column-value = Valor
cli-config-label-app-version = Versión de la App
cli-config-label-debug-mode = Modo Debug
cli-config-label-database-url = URL de Base de Datos
cli-config-label-data-dir = Directorio de Datos
cli-config-label-archive-dir = Directorio de Archivo
cli-config-label-certificates-dir = Directorio de Certificados
cli-config-label-company-name = Nombre de Empresa
cli-config-label-partita-iva = Partita IVA
cli-config-label-codice-fiscale = Codice Fiscale
cli-config-label-tax-regime = Régimen Fiscal
cli-config-label-pec-address = Dirección PEC
cli-config-label-pec-smtp-server = Servidor SMTP PEC
cli-config-label-sdi-pec-address = Dirección PEC SDI
cli-config-label-notification-email = Email de Notificaciones
cli-config-label-notifications-enabled = Notificaciones Habilitadas
cli-config-label-locale = Idioma
cli-config-label-email-logo-url = URL del Logo de Email
cli-config-label-primary-color = Color Primario
cli-config-label-secondary-color = Color Secundario
cli-config-label-email-footer = Pie de Email
cli-config-label-ai-provider = Proveedor de IA
cli-config-label-ai-model = Modelo de IA
cli-config-label-ai-base-url = URL Base de IA
cli-config-label-ai-api-key = Clave API de IA
cli-config-label-chat-enabled = Chat Habilitado
cli-config-label-chat-auto-save = Auto-Guardado de Chat
cli-config-label-max-messages = Máx Mensajes/Sesión
cli-config-label-max-tokens = Máx Tokens/Sesión
cli-config-label-tools-enabled = Herramientas Habilitadas
cli-config-label-tool-access = Acceso a Herramientas IA
cli-config-label-extra-tools = Herramientas Adicionales
cli-config-not-set = [red]No configurado[/red]
cli-config-not-set-optional = [yellow]No configurado[/yellow]
cli-config-set = [green]Configurada[/green]
cli-config-yes = [green]Sí[/green]
cli-config-no = [red]No[/red]
cli-config-auto-generated = [dim]Auto-generado[/dim]
cli-config-reload-success = [green]Configuración recargada[/green]
cli-config-set-success = [green]Configurado { $key } = { $value }[/green]
cli-config-saved-to = [dim]Guardado en { $path }[/dim]
cli-config-invalid-key = [red]Clave de configuración inválida: { $key }[/red]
cli-config-error = [red]Error: { $error }[/red]
cli-config-column-source = Origen
cli-config-source-env = entorno
cli-config-source-keyring = llavero
cli-config-source-file = archivo de credenciales
cli-config-source-config = config.toml
cli-config-source-default = predeterminado
cli-config-file-path = [dim]Archivo de configuración: { $path }[/dim]
cli-config-secret-backend = [dim]Secretos: { $backend }[/dim]
cli-config-secret-saved = [green]{ $key } guardado en: { $backend }[/green]
cli-config-env-override = [yellow]{ $key } está definido por una variable de entorno: el valor guardado se ignora mientras siga definida.[/yellow]
cli-config-unset-success = [green]{ $key } eliminado[/green]
cli-config-unset-missing = [yellow]{ $key } no estaba definido[/yellow]
cli-config-invalid-value = [red]Valor no válido para { $key }: { $error }[/red]
cli-config-migrate-moved = [green]Movidos a { $backend }: { $keys }[/green]
cli-config-migrate-imported = [green]Importados en config.toml: { $keys }[/green]
cli-config-migrate-conflicts = [yellow]Ya definidos, no sobrescritos: { $keys }[/yellow]
cli-config-migrate-nothing = Nada que migrar.
cli-config-migrate-source-kept = [dim]{ $path } no se ha modificado: elimínalo tras comprobarlo.[/dim]
## Assistant and status
assistant-describe-what-you-need = Describe lo que necesitas. /help para los comandos · /exit para salir
assistant-thinking = Pensando…
assistant-request-error = La solicitud falló. Usa --debug para ver los detalles.
assistant-confirm-operation = ¿Confirmar esta operación? [y/N]
assistant-help = Comandos con barra
    /help     Mostrar esta ayuda
    /exit     Salir (también: exit, quit, q)
    /session  Mostrar el ID de sesión
    /clear    Borrar los mensajes de la sesión
assistant-input = Tú ›
assistant-operation = Operación: { $name }
assistant-tool-running = En ejecución · { $name }
assistant-incomplete = Respuesta incompleta.
assistant-session = Sesión: { $session }
assistant-not-persisted = no guardada
assistant-cleared = Mensajes de la sesión borrados.
assistant-no-session = No hay ninguna sesión guardada que borrar.
assistant-unknown-command = Comando desconocido: { $command }. Prueba /help.
assistant-turn-failed = Solicitud no completada. Usa --debug para ver los detalles.
assistant-interrupted = Solicitud interrumpida. Las operaciones ya iniciadas pueden haber tenido efecto: comprueba su estado antes de volver a intentarlo.
assistant-missing-extra = Faltan dependencias de IA: reinstala OpenFatture con el extra ai.
assistant-tool-completed = Completado · { $name }
assistant-tool-failed = No completado · { $name }
status-blocking-fields = Campos que bloquean la facturación
status-field = Campo
status-problem = Problema
status-missing = Falta
status-invalid = No válido
status-local-only = Las comprobaciones describen la configuración local. La autenticación de la IA y la entrega al SDI no se verifican con este comando.
cli-database-unavailable = Base de datos no disponible. Comprueba DATABASE_URL y los permisos; usa --debug para ver los detalles.
assistant-reconciled = Resultado verificado registrado. Usa /resume para continuar.
assistant-reconcile-invalid = Conciliación no válida: se requieren call_id, result y evidence.
assistant-resolve-pending-first = Resuelve el turno pendiente con /resume antes de borrar el historial.
assistant-resuming = Reanudando el turno interrumpido…
assistant-uncertain-tool = Resultado de herramienta incierto: usa /pending y /reconcile antes de /resume.
assistant-no-pending = No hay ningún turno pendiente.

## Shared command output
cli-common-error = [red]Error:[/red] { $error }
## FATTURA Commands
cli-fattura-journal-submission = Envío n.º { $id } · factura { $invoice } · { $filename } · { $outcome }
cli-fattura-journal-receipt = Recibo n.º { $id } · factura { $invoice } · { $outcome } · origen { $source }
cli-fattura-journal-empty = No hay envíos ni recibos SDI registrados.
cli-fattura-associate-confirm = ¿Asociar el recibo { $receipt } a la factura { $invoice }?
cli-fattura-receipt-associated = Recibo asociado
cli-fattura-resolve-confirm = ¿Confirmas que el envío { $attempt } { $sent ->
        [yes] fue transmitido
       *[no] no fue transmitido
    }?
cli-fattura-submission-resolved = Verificación registrada

## CLIENTE Commands
## PAGAMENTO Commands
## INIT Command
cli-init-title = [bold blue]Configuración de OpenFatture[/bold blue]
cli-init-structured-needs-no-interactive = Usa --no-interactive con un formato de salida estructurado
cli-init-creating-dirs = [cyan]Creando directorios...[/cyan]
cli-init-dirs-created = Directorios de datos creados
cli-init-initializing-db = [cyan]Inicializando la base de datos...[/cyan]
cli-init-backup = Copia de seguridad antes de la actualización: { $path }
cli-init-database = Base de datos { $state ->
        [empty] creada
        [current] ya actualizada
        [outdated] actualizada
        [unversioned] adoptada y actualizada
       *[other] { $state }
    }: { $url }
cli-init-configure-company = [bold yellow]Configuremos los datos de tu empresa[/bold yellow]
cli-init-overwrite-confirm = [yellow]Ya existe un perfil de OpenFatture. ¿Sobrescribir la configuración de empresa e IA?[/yellow]
cli-init-config-preserved = [green]Configuración existente conservada.[/green] Los directorios y la base de datos se han verificado igualmente.
cli-init-company-section = [bold]Datos de la empresa (Cedente Prestatore)[/bold]
cli-init-prompt-name = Empresa o tu nombre
cli-init-prompt-partita-iva = Partita IVA (11 dígitos)
cli-init-invalid-partita-iva = [red]Partita IVA no válida. Inténtalo de nuevo.[/red]
cli-init-prompt-codice-fiscale = Codice fiscale (16 caracteres)
cli-init-invalid-codice-fiscale = [red]Codice fiscale no válido. Inténtalo de nuevo.[/red]
cli-init-prompt-regime = Régimen fiscal (usa tu código RF real)
cli-init-invalid-regime = [red]Introduce un régimen fiscal admitido por FatturaPA.[/red]
cli-init-prompt-address = Dirección (calle)
cli-init-prompt-cap = Código postal (CAP)
cli-init-prompt-city = Municipio (Comune)
cli-init-prompt-province = Provincia (2 letras, p. ej. RM)
cli-init-pec-section = [bold]Configuración PEC[/bold]
cli-init-prompt-pec-address = Tu dirección PEC
cli-init-prompt-pec-password = Contraseña PEC
cli-init-prompt-pec-smtp = Servidor SMTP PEC
cli-init-notifications-section = [bold]Notificaciones por correo[/bold]
cli-init-prompt-notification-email = Correo para notificaciones (avisos SDI, resúmenes)
cli-init-prompt-locale = Idioma (it/en/de/es/fr)
cli-init-ai-section = [bold]Configuración de IA (opcional)[/bold]
cli-init-ai-description = [dim]Configura las funciones de IA: descripciones de facturas, sugerencias fiscales y asistente conversacional.[/dim]
cli-init-ai-confirm = ¿Configurar ahora las funciones de IA? (También puedes hacerlo más tarde con openfatture config)
cli-init-ai-provider = Proveedor de IA
cli-init-ai-skip = Omitir por ahora
cli-init-api-key-from = [cyan]{ $provider } seleccionado: obtén una clave API en:[/cyan]
cli-init-ollama-selected = [cyan]Ollama seleccionado: ¡modelo local gratuito![/cyan]
cli-init-ollama-install = Instalar: [bold]ollama pull { $model }[/bold]
cli-init-ollama-start = Iniciar: [bold]ollama serve[/bold]
cli-init-prompt-api-key = Clave API (déjala vacía para configurarla más tarde)
cli-init-config-saved = Configuración guardada en: { $path }
cli-init-secrets-saved = Secretos guardados { $backend ->
        [keyring] en el llavero del sistema
       *[file] en el archivo privado de credenciales
    }
cli-init-complete-title = Configuración completada
cli-init-complete-body = [bold green]Configuración terminada[/bold green]

    Próximos pasos:
      • Comprueba el estado: [cyan]openfatture status[/cyan]
      • Revisa la configuración: [cyan]openfatture config show[/cyan]
      • Asistente (requiere [cyan]uv sync --extra ai[/cyan]): [cyan]openfatture -m "Muestra las facturas abiertas"[/cyan]
      • Ayuda: [cyan]openfatture --help[/cyan]

## STATUS Command
cli-status-readiness = [bold]Preparación[/bold]  núcleo: [cyan]{ $core ->
        [yes] listo
       *[no] no listo
    }[/cyan]  asistente: [cyan]{ $assistant ->
        [yes] configurado
       *[no] no configurado
    }[/cyan]
cli-status-title = Estado de OpenFatture
cli-status-label-ai-api-key-configured = Clave API de IA configurada
cli-status-label-assistant-backend = Backend del asistente
cli-status-label-assistant-backend-id = ID del backend del asistente
cli-status-label-config-file = Archivo de configuración
cli-status-label-secret-backend = Almacén de secretos
cli-status-checks-title = Comprobaciones de preparación
cli-status-column-check = Comprobación
cli-status-yes = sí
cli-status-no = no
cli-status-next-steps = [bold]Próximos pasos[/bold]
cli-status-extras-title = Extras opcionales (módulos funcionales)
cli-status-column-extra = Extra
cli-status-column-installed = Instalado
cli-status-extensions-title = Extensiones
cli-status-column-mechanism = Mecanismo
cli-status-column-detail = Detalle
cli-status-hooks = hooks (admitidos)
cli-status-hooks-detail = { $path } ({ $count ->
        [one] 1 script
       *[other] { $count } scripts
    })
cli-status-plugins = plugins en proceso

## Global
cli-main-version = [bold blue]OpenFatture[/bold blue] versión { $version }
cli-output-unsupported-format = Formatos admitidos: { $formats }

## Rich formatter
cli-formatter-error = [bold red]Error:[/bold red] { $error }
cli-formatter-unknown-error = Error desconocido
cli-formatter-ai-response = [bold]Respuesta de IA[/bold]
cli-formatter-unknown = desconocido
cli-formatter-provider = Proveedor: { $provider }
cli-formatter-model = Modelo: { $model }
cli-formatter-tokens = Tokens: { $tokens }
cli-formatter-cost = Coste: { $cost }
cli-formatter-latency = Latencia: { $latency } ms

## Localized refusals of application services (error_code)
cli-error-receipt-not-associable = El recibo no existe o ya está asociado.
cli-error-evidence-required = Se requiere una evidencia verificada (--evidence).
cli-error-submission-not-found = Intento de envío no encontrado.
cli-error-submission-already-resolved = El intento de envío ya está resuelto.
cli-error-sdi-evidence-contradicts = Las evidencias SDI registradas contradicen el resultado "no enviado".
cli-error-submission-concurrent-update = El intento se resolvió mientras tanto: recarga y vuelve a intentarlo.

## Command-line help
cli-help-app = Facturación electrónica con asistente. Ejecuta openfatture para conversar.
cli-help-epilog = Ejemplos: openfatture · openfatture -m "Muestra las facturas impagadas"
cli-help-version = Muestra la versión y sale.
cli-help-debug = Muestra registros de diagnóstico y trazas.
cli-help-format = Formato de salida: rich, json, markdown, stream-json, html
cli-help-panel-assistant = Asistente
cli-help-panel-setup = Configuración y diagnóstico
cli-help-panel-sdi = Verificaciones SDI
cli-help-init = Inicializa OpenFatture
cli-help-config = Gestiona la configuración
cli-help-status = Comprueba la configuración y la disponibilidad
cli-help-fattura = Registro SDI y resoluciones con prueba manual
cli-help-assistant-message = Solicitud para el asistente.
cli-help-assistant-stream = Muestra la respuesta mientras se genera.
cli-help-assistant-session = Reanuda una sesión guardada por su ID (activa el guardado).
cli-help-assistant-options-alone = --message y --session solo valen para el asistente, sin un comando.
cli-help-init-interactive = Asistente de configuración interactivo
cli-help-status-json = Devuelve el estado en JSON.
cli-help-config-show =
    Muestra la configuración efectiva.

    Para cada valor indica el origen: entorno, llavero o archivo de credenciales, config.toml, predeterminado.
cli-help-config-reload = Recarga la configuración desde el entorno, el almacén de secretos y config.toml.
cli-help-config-set =
    Establece un valor de configuración.

    Solo se escribe KEY. Los secretos (claves API, contraseñas) van al llavero del sistema, o al archivo privado de credenciales si no hay llavero; los demás valores a config.toml. Las claves anidadas usan puntos, por ejemplo debug_config.enable_debug_logging.
cli-help-config-unset = Elimina KEY de config.toml o del almacén de secretos y restablece el valor predeterminado.
cli-help-config-migrate =
    Saca los secretos en texto plano de config.toml e importa opcionalmente un archivo .env.

    Los secretos van al llavero (o al archivo privado de credenciales); los demás valores de --env-file se añaden a config.toml solo si no están ya definidos. El archivo de origen nunca se modifica.
cli-help-config-env-file = Importa la configuración de un archivo dotenv (los valores existentes se conservan).
cli-help-invoice-id = ID de la factura
cli-help-sdi-journal = Muestra los envíos PEC y los recibos SDI registrados, sin enviar nada.
cli-help-associate-receipt = Asocia un recibo sin resolver a una factura, tras una verificación manual.
cli-help-receipt-id = ID del recibo SDI
cli-help-receipt-evidence = Evidencia verificada (p. ej. una referencia)
cli-help-resolve-submission = Resuelve un envío PEC incierto, tras verificar el resultado del transporte.
cli-help-attempt-id = ID del intento de envío
cli-help-resolve-sent = Resultado verificado: enviado o no enviado
cli-help-resolve-evidence = Evidencia verificada (p. ej. la referencia del proveedor)
cli-help-install-completion = Instala el autocompletado para la shell actual.
cli-help-show-completion = Muestra el autocompletado para la shell actual, para copiarlo o personalizarlo.
cli-help-help-option = Muestra este mensaje y sale.

## Startup setup and status next steps
status-next-init = Ejecuta: openfatture init
status-next-set-field = openfatture config set { $field } '<valor>'
status-next-ai-extra = Para el asistente: uv sync --extra ai
status-next-ai-key = openfatture config set ai_api_key '<clave>' (o ai_provider ollama)
status-next-try = Prueba: openfatture -m "Muestra las facturas abiertas"
status-next-core-ready = La base está lista; instala el extra ai para usar el asistente
status-next-help = openfatture --help
status-next-upgrade-db = Actualiza el esquema de la base de datos: openfatture init
status-next-newer-db = La base de datos es más reciente que esta versión: actualiza OpenFatture
status-next-migrate-secrets = Mueve los secretos en claro al llavero: openfatture config migrate
status-next-dotenv = ./.env no se lee: usa `uv run --env-file .env ...` o impórtalo con `openfatture config migrate --env-file .env`
cli-setup-running = Falta la configuración: inicio openfatture init.
cli-setup-required = Falta la configuración: ejecuta `openfatture init`.
cli-setup-newer-database = La base de datos viene de una versión más reciente de OpenFatture: actualiza OpenFatture.
cli-setup-ai-key = No hay clave API para { $provider }: ejecuta `openfatture config set ai_api_key` o usa `openfatture config set ai_provider ollama`.
