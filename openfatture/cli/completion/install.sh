#!/usr/bin/env bash
# OpenFatture CLI Completion Installer
# Installs bash and zsh completion scripts for openfatture CLI

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOLD="\033[1m"
GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[34m"
RESET="\033[0m"

echo -e "${BOLD}${BLUE}OpenFatture CLI Completion Installer${RESET}\n"

# Detect shell
detect_shell() {
    if [ -n "$BASH_VERSION" ]; then
        echo "bash"
    elif [ -n "$ZSH_VERSION" ]; then
        echo "zsh"
    else
        # Try to detect from $SHELL
        case "$SHELL" in
            */bash)
                echo "bash"
                ;;
            */zsh)
                echo "zsh"
                ;;
            *)
                echo "unknown"
                ;;
        esac
    fi
}

# Install bash completion
install_bash() {
    echo -e "${BOLD}Installing bash completion...${RESET}"

    # Try to find bash completion directory
    local bash_completion_dirs=(
        "/usr/local/etc/bash_completion.d"
        "/usr/share/bash-completion/completions"
        "/etc/bash_completion.d"
        "$HOME/.local/share/bash-completion/completions"
    )

    local installed=false

    for dir in "${bash_completion_dirs[@]}"; do
        if [ -d "$dir" ] && [ -w "$dir" ]; then
            echo -e "  ${GREEN}✓${RESET} Installing to $dir"
            cp "$SCRIPT_DIR/_openfatture.bash" "$dir/openfatture"
            installed=true
            break
        fi
    done

    if [ "$installed" = false ]; then
        # Install to user directory
        local user_dir="$HOME/.local/share/bash-completion/completions"
        mkdir -p "$user_dir"
        echo -e "  ${GREEN}✓${RESET} Installing to $user_dir (user directory)"
        cp "$SCRIPT_DIR/_openfatture.bash" "$user_dir/openfatture"
        installed=true

        # Add to .bashrc if not already present
        if ! grep -q "bash-completion/completions" "$HOME/.bashrc" 2>/dev/null; then
            echo -e "\n# Enable bash completion" >> "$HOME/.bashrc"
            echo "[ -d \"\$HOME/.local/share/bash-completion/completions\" ] && export BASH_COMPLETION_USER_DIR=\"\$HOME/.local/share/bash-completion/completions\"" >> "$HOME/.bashrc"
            echo -e "  ${YELLOW}→${RESET} Added completion path to ~/.bashrc"
        fi
    fi

    if [ "$installed" = true ]; then
        echo -e "  ${GREEN}✓${RESET} Bash completion installed successfully!"
        echo -e "  ${YELLOW}→${RESET} Run: ${BOLD}source ~/.bashrc${RESET} or restart your shell"
        return 0
    else
        echo -e "  ${YELLOW}⚠${RESET}  Could not find a suitable bash completion directory"
        echo -e "  ${YELLOW}→${RESET} Manual installation: source ${SCRIPT_DIR}/_openfatture.bash in your .bashrc"
        return 1
    fi
}

# Install zsh completion
install_zsh() {
    echo -e "${BOLD}Installing zsh completion...${RESET}"

    # Try to find zsh completion directory
    local zsh_completion_dirs=(
        "/usr/local/share/zsh/site-functions"
        "/usr/share/zsh/site-functions"
        "$HOME/.local/share/zsh/site-functions"
    )

    # Also check $fpath
    if [ -n "$fpath" ]; then
        for dir in ${fpath[@]}; do
            if [ -d "$dir" ] && [ -w "$dir" ]; then
                zsh_completion_dirs+=("$dir")
            fi
        done
    fi

    local installed=false

    for dir in "${zsh_completion_dirs[@]}"; do
        if [ -d "$dir" ] && [ -w "$dir" ]; then
            echo -e "  ${GREEN}✓${RESET} Installing to $dir"
            cp "$SCRIPT_DIR/_openfatture.zsh" "$dir/_openfatture"
            installed=true
            break
        fi
    done

    if [ "$installed" = false ]; then
        # Install to user directory
        local user_dir="$HOME/.local/share/zsh/site-functions"
        mkdir -p "$user_dir"
        echo -e "  ${GREEN}✓${RESET} Installing to $user_dir (user directory)"
        cp "$SCRIPT_DIR/_openfatture.zsh" "$user_dir/_openfatture"
        installed=true

        # Add to .zshrc if not already present
        if ! grep -q "site-functions" "$HOME/.zshrc" 2>/dev/null; then
            echo -e "\n# Enable zsh completion" >> "$HOME/.zshrc"
            echo "fpath=(\$HOME/.local/share/zsh/site-functions \$fpath)" >> "$HOME/.zshrc"
            echo "autoload -Uz compinit && compinit" >> "$HOME/.zshrc"
            echo -e "  ${YELLOW}→${RESET} Added completion path to ~/.zshrc"
        fi
    fi

    if [ "$installed" = true ]; then
        echo -e "  ${GREEN}✓${RESET} Zsh completion installed successfully!"
        echo -e "  ${YELLOW}→${RESET} Run: ${BOLD}exec zsh${RESET} or restart your shell"
        return 0
    else
        echo -e "  ${YELLOW}⚠${RESET}  Could not find a suitable zsh completion directory"
        echo -e "  ${YELLOW}→${RESET} Manual installation: add to your .zshrc:"
        echo -e "      fpath=($SCRIPT_DIR \$fpath)"
        echo -e "      autoload -Uz compinit && compinit"
        return 1
    fi
}

# Main installation
main() {
    local shell_type=$(detect_shell)

    echo -e "Detected shell: ${BOLD}$shell_type${RESET}\n"

    case "$1" in
        --bash)
            install_bash
            ;;
        --zsh)
            install_zsh
            ;;
        --all)
            install_bash
            echo ""
            install_zsh
            ;;
        *)
            # Auto-detect and install
            case "$shell_type" in
                bash)
                    install_bash
                    ;;
                zsh)
                    install_zsh
                    ;;
                *)
                    echo -e "${YELLOW}Could not detect shell. Install manually:${RESET}"
                    echo -e "  Bash: ${BOLD}$0 --bash${RESET}"
                    echo -e "  Zsh:  ${BOLD}$0 --zsh${RESET}"
                    echo -e "  Both: ${BOLD}$0 --all${RESET}"
                    exit 1
                    ;;
            esac
            ;;
    esac

    echo -e "\n${GREEN}${BOLD}Installation complete!${RESET}"
    echo -e "Try: ${BOLD}openfatture <TAB>${RESET}"
}

main "$@"
