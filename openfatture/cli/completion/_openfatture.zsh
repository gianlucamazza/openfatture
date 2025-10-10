#compdef openfatture
# OpenFatture zsh completion script
# Install: Place in $fpath (e.g., /usr/local/share/zsh/site-functions)
#   or source this file in ~/.zshrc

_openfatture() {
    local -a commands
    local -a cliente_commands
    local -a fattura_commands
    local -a ai_commands
    local -a config_commands
    local -a notifiche_commands
    local -a report_commands
    local -a batch_commands

    # Top-level commands
    commands=(
        'init:Initialize OpenFatture project'
        'config:Manage configuration'
        'cliente:Manage clients'
        'fattura:Manage invoices'
        'ai:AI-powered features'
        'notifiche:Process SDI notifications'
        'pec:PEC email operations'
        'report:Generate reports'
        'batch:Batch operations'
        'chat:Interactive AI chat'
    )

    # Subcommands
    cliente_commands=(
        'add:Add a new client'
        'list:List all clients'
        'show:Show client details'
        'update:Update client information'
        'delete:Delete a client'
    )

    fattura_commands=(
        'crea:Create a new invoice (wizard)'
        'list:List invoices'
        'show:Show invoice details'
        'delete:Delete an invoice'
        'xml:Generate FatturaPA XML'
        'pdf:Generate PDF invoice'
        'invia:Send invoice to SDI via PEC'
    )

    ai_commands=(
        'chat:Interactive AI assistant'
        'describe:Generate invoice description from natural language'
        'tax:Get VAT rate suggestions'
        'forecast:Predict payment dates with ML'
        'check:Run compliance checks'
        'rag:Semantic search in documents'
    )

    config_commands=(
        'show:Show current configuration'
        'set:Set configuration value'
        'get:Get configuration value'
        'validate:Validate configuration'
    )

    notifiche_commands=(
        'process:Process SDI notification XML'
        'list:List received notifications'
    )

    report_commands=(
        'vendite:Sales report'
        'clienti:Client summary'
        'scadenze:Payment due dates'
        'export:Export data to CSV/JSON'
    )

    batch_commands=(
        'import-csv:Import invoices from CSV'
        'generate-bulk:Generate multiple invoices'
    )

    # State argument
    local curcontext="$curcontext" state line
    typeset -A opt_args

    _arguments -C \
        '1: :->command' \
        '2: :->subcommand' \
        '*: :->args' \
        && return 0

    case $state in
        command)
            _describe -t commands 'openfatture command' commands
            ;;
        subcommand)
            case $line[1] in
                cliente)
                    _describe -t cliente_commands 'cliente command' cliente_commands
                    ;;
                fattura)
                    _describe -t fattura_commands 'fattura command' fattura_commands
                    ;;
                ai)
                    _describe -t ai_commands 'ai command' ai_commands
                    ;;
                config)
                    _describe -t config_commands 'config command' config_commands
                    ;;
                notifiche)
                    _describe -t notifiche_commands 'notifiche command' notifiche_commands
                    ;;
                report)
                    _describe -t report_commands 'report command' report_commands
                    ;;
                batch)
                    _describe -t batch_commands 'batch command' batch_commands
                    ;;
            esac
            ;;
        args)
            case $line[1] in
                fattura)
                    case $line[2] in
                        crea|pdf)
                            _arguments \
                                '--pdf[Generate PDF]' \
                                '--pdf-template[PDF template]:template:(minimalist professional branded)' \
                                '--template[PDF template]:template:(minimalist professional branded)' \
                                '--color[Primary color (hex)]' \
                                '--watermark[Watermark text]' \
                                '--output[Output path]:file:_files' \
                                '--cliente[Client ID]'
                            ;;
                        list)
                            _arguments \
                                '--stato[Filter by status]:status:(bozza da_inviare inviata consegnata accettata rifiutata scartata errore)' \
                                '--anno[Filter by year]' \
                                '--limit[Max results]'
                            ;;
                        xml)
                            _arguments \
                                '--output[Output path]:file:_files' \
                                '--no-validate[Skip XSD validation]'
                            ;;
                        invia)
                            _arguments \
                                '--pec[Send via PEC (default)]'
                            ;;
                    esac
                    ;;
                ai)
                    case $line[2] in
                        chat|describe|tax|forecast|check)
                            _arguments \
                                '--provider[AI provider]:provider:(anthropic openai ollama)' \
                                '--model[AI model]:model:(claude-3-5-sonnet-20241022 gpt-4o llama3.1)' \
                                '--stream[Enable streaming]' \
                                '--no-cache[Disable caching]'
                            ;;
                        forecast)
                            _arguments \
                                '--fattura-id[Invoice ID]' \
                                '--cliente-id[Client ID]' \
                                '--giorni[Forecast days]'
                            ;;
                    esac
                    ;;
                report)
                    _arguments \
                        '--anno[Year]' \
                        '--mese[Month]' \
                        '--format[Output format]:format:(json csv html)' \
                        '--output[Output path]:file:_files'
                    ;;
            esac
            ;;
    esac
}

_openfatture "$@"
