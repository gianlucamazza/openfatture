#!/usr/bin/env bash
# OpenFatture bash completion script
# Install: source this file or add to ~/.bashrc
#   source /path/to/_openfatture.bash

_openfatture_completion() {
    local cur prev opts base

    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Top-level commands
    local commands="init config cliente fattura ai notifiche pec report batch chat"

    # Handle subcommands
    case "${COMP_WORDS[1]}" in
        cliente)
            local cliente_cmds="add list show update delete"
            case "${prev}" in
                cliente)
                    COMPREPLY=( $(compgen -W "${cliente_cmds}" -- ${cur}) )
                    return 0
                    ;;
            esac
            ;;
        fattura)
            local fattura_cmds="crea list show delete xml pdf invia"
            case "${prev}" in
                fattura)
                    COMPREPLY=( $(compgen -W "${fattura_cmds}" -- ${cur}) )
                    return 0
                    ;;
                --stato)
                    local stati="bozza da_inviare inviata consegnata accettata rifiutata scartata errore"
                    COMPREPLY=( $(compgen -W "${stati}" -- ${cur}) )
                    return 0
                    ;;
                --pdf-template|--template|-t)
                    local templates="minimalist professional branded"
                    COMPREPLY=( $(compgen -W "${templates}" -- ${cur}) )
                    return 0
                    ;;
            esac
            ;;
        ai)
            local ai_cmds="chat describe tax forecast check rag"
            case "${prev}" in
                ai)
                    COMPREPLY=( $(compgen -W "${ai_cmds}" -- ${cur}) )
                    return 0
                    ;;
                --provider)
                    local providers="anthropic openai ollama"
                    COMPREPLY=( $(compgen -W "${providers}" -- ${cur}) )
                    return 0
                    ;;
                --model)
                    local models="claude-3-5-sonnet-20241022 gpt-4o llama3.1"
                    COMPREPLY=( $(compgen -W "${models}" -- ${cur}) )
                    return 0
                    ;;
            esac
            ;;
        config)
            local config_cmds="show set get validate"
            case "${prev}" in
                config)
                    COMPREPLY=( $(compgen -W "${config_cmds}" -- ${cur}) )
                    return 0
                    ;;
            esac
            ;;
        notifiche)
            local notifiche_cmds="process list"
            case "${prev}" in
                notifiche)
                    COMPREPLY=( $(compgen -W "${notifiche_cmds}" -- ${cur}) )
                    return 0
                    ;;
            esac
            ;;
        pec)
            local pec_cmds="test"
            case "${prev}" in
                pec)
                    COMPREPLY=( $(compgen -W "${pec_cmds}" -- ${cur}) )
                    return 0
                    ;;
            esac
            ;;
        report)
            local report_cmds="vendite clienti scadenze export"
            case "${prev}" in
                report)
                    COMPREPLY=( $(compgen -W "${report_cmds}" -- ${cur}) )
                    return 0
                    ;;
            esac
            ;;
        batch)
            local batch_cmds="import-csv generate-bulk"
            case "${prev}" in
                batch)
                    COMPREPLY=( $(compgen -W "${batch_cmds}" -- ${cur}) )
                    return 0
                    ;;
            esac
            ;;
    esac

    # File completion for certain options
    case "${prev}" in
        -o|--output|--xml|--csv|--logo-path)
            COMPREPLY=( $(compgen -f -- ${cur}) )
            return 0
            ;;
    esac

    # Suggest top-level commands if at command level
    if [[ ${COMP_CWORD} -eq 1 ]] ; then
        COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
        return 0
    fi

    # Common options
    local common_opts="--help --version --verbose --quiet"

    COMPREPLY=( $(compgen -W "${common_opts}" -- ${cur}) )
    return 0
}

# Register completion function
complete -F _openfatture_completion openfatture
