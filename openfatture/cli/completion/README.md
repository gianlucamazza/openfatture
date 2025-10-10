# OpenFatture CLI Completion

Shell completion scripts for **bash** and **zsh** that provide tab-completion for OpenFatture CLI commands, subcommands, and options.

## Features

✅ **Command completion**: `openfatture <TAB>` → shows all available commands
✅ **Subcommand completion**: `openfatture fattura <TAB>` → shows fattura subcommands
✅ **Option completion**: `openfatture fattura crea --<TAB>` → shows available options
✅ **Value completion**: `--stato <TAB>` → shows valid invoice stati
✅ **File completion**: `-o <TAB>` → shows files for output paths
✅ **Template completion**: `--template <TAB>` → shows available PDF templates
✅ **Provider completion**: `--provider <TAB>` → shows AI providers

## Quick Installation

### Automatic Installation (Recommended)

```bash
# Navigate to the completion directory
cd openfatture/cli/completion

# Run the installer (auto-detects your shell)
./install.sh

# Or install for specific shell:
./install.sh --bash   # Bash only
./install.sh --zsh    # Zsh only
./install.sh --all    # Both shells
```

After installation, restart your shell or run:
- **Bash**: `source ~/.bashrc`
- **Zsh**: `exec zsh`

### Manual Installation

#### Bash

1. **System-wide installation** (requires sudo):
   ```bash
   sudo cp _openfatture.bash /usr/local/etc/bash_completion.d/openfatture
   ```

2. **User installation** (no sudo):
   ```bash
   mkdir -p ~/.local/share/bash-completion/completions
   cp _openfatture.bash ~/.local/share/bash-completion/completions/openfatture

   # Add to ~/.bashrc:
   echo 'export BASH_COMPLETION_USER_DIR="$HOME/.local/share/bash-completion/completions"' >> ~/.bashrc
   ```

3. **Source directly** (temporary):
   ```bash
   source _openfatture.bash
   ```

#### Zsh

1. **System-wide installation** (requires sudo):
   ```bash
   sudo cp _openfatture.zsh /usr/local/share/zsh/site-functions/_openfatture
   ```

2. **User installation** (no sudo):
   ```bash
   mkdir -p ~/.local/share/zsh/site-functions
   cp _openfatture.zsh ~/.local/share/zsh/site-functions/_openfatture

   # Add to ~/.zshrc:
   echo 'fpath=(~/.local/share/zsh/site-functions $fpath)' >> ~/.zshrc
   echo 'autoload -Uz compinit && compinit' >> ~/.zshrc
   ```

3. **Reload zsh completions**:
   ```bash
   exec zsh
   # or
   rm -f ~/.zcompdump && compinit
   ```

## Usage Examples

### Basic Command Completion

```bash
$ openfatture <TAB>
ai       batch    chat     cliente  config   fattura  init     notifiche  pec      report
```

### Subcommand Completion

```bash
$ openfatture fattura <TAB>
crea    delete  invia   list    pdf     show    xml

$ openfatture ai <TAB>
chat     check    describe  forecast  rag      tax
```

### Option Completion

```bash
$ openfatture fattura crea --<TAB>
--cliente        --help           --pdf            --pdf-template

$ openfatture fattura list --stato <TAB>
accettata  bozza  consegnata  da_inviare  errore  inviata  rifiutata  scartata
```

### PDF Template Completion

```bash
$ openfatture fattura pdf 123 --template <TAB>
branded        minimalist     professional
```

### AI Provider Completion

```bash
$ openfatture ai chat --provider <TAB>
anthropic  ollama  openai
```

## Supported Completions

### Commands
- `init` - Initialize project
- `config` - Configuration management
- `cliente` - Client management
- `fattura` - Invoice management
- `ai` - AI-powered features
- `notifiche` - SDI notifications
- `pec` - PEC operations
- `report` - Reports
- `batch` - Batch operations
- `chat` - Interactive chat

### Fattura Subcommands
- `crea` - Create invoice (with `--pdf`, `--pdf-template`)
- `list` - List invoices (with `--stato`, `--anno`)
- `show` - Show details
- `delete` - Delete invoice
- `xml` - Generate XML
- `pdf` - Generate PDF (with `--template`, `--color`, `--watermark`)
- `invia` - Send to SDI

### AI Subcommands
- `chat` - Interactive assistant
- `describe` - Generate descriptions
- `tax` - VAT suggestions
- `forecast` - Payment prediction
- `check` - Compliance checking
- `rag` - Semantic search

### Invoice Stati (--stato completion)
- `bozza` - Draft
- `da_inviare` - To be sent
- `inviata` - Sent
- `consegnata` - Delivered
- `accettata` - Accepted
- `rifiutata` - Rejected
- `scartata` - Discarded
- `errore` - Error

### PDF Templates (--template completion)
- `minimalist` - Simple black & white
- `professional` - Corporate blue
- `branded` - Custom colors & watermark

### AI Providers (--provider completion)
- `anthropic` - Claude models
- `openai` - GPT models
- `ollama` - Local LLMs

## Troubleshooting

### Completion not working

1. **Check installation**:
   ```bash
   # Bash
   ls -la /usr/local/etc/bash_completion.d/openfatture
   # or
   ls -la ~/.local/share/bash-completion/completions/openfatture

   # Zsh
   ls -la /usr/local/share/zsh/site-functions/_openfatture
   # or
   ls -la ~/.local/share/zsh/site-functions/_openfatture
   ```

2. **Verify bash completion is enabled**:
   ```bash
   # Check if bash-completion is installed
   brew list bash-completion  # macOS
   dpkg -l bash-completion    # Debian/Ubuntu
   rpm -qa bash-completion    # RedHat/Fedora
   ```

3. **Reload completions**:
   ```bash
   # Bash
   source ~/.bashrc

   # Zsh
   rm -f ~/.zcompdump
   exec zsh
   ```

4. **Test manually**:
   ```bash
   # Bash
   source _openfatture.bash
   complete -p openfatture  # Should show: complete -F _openfatture_completion openfatture

   # Zsh
   source _openfatture.zsh
   ```

### Permission denied during installation

Run with sudo for system-wide installation:
```bash
sudo ./install.sh
```

Or use user installation (no sudo required):
```bash
./install.sh  # Will auto-detect and install to user directory if needed
```

## Development

### Testing Completions

#### Bash
```bash
# Source the completion script
source _openfatture.bash

# Test completions
openfatture <TAB>
openfatture fattura <TAB>
openfatture ai chat --<TAB>
```

#### Zsh
```bash
# Source the completion script
autoload -Uz compinit
fpath=(. $fpath)
compinit
source _openfatture.zsh

# Test completions
openfatture <TAB>
openfatture fattura <TAB>
openfatture ai chat --<TAB>
```

### Adding New Commands

1. **Update bash completion** (`_openfatture.bash`):
   - Add command to `commands` variable
   - Add subcommands case in `case "${COMP_WORDS[1]}"` block
   - Add option completions if needed

2. **Update zsh completion** (`_openfatture.zsh`):
   - Add command to `commands` array (with description)
   - Add subcommands array (e.g., `mycommand_commands`)
   - Add case in `subcommand` state
   - Add arguments in `args` state

3. **Test the changes**:
   ```bash
   # Bash
   source _openfatture.bash

   # Zsh
   unfunction _openfatture
   source _openfatture.zsh
   ```

## Files

- `_openfatture.bash` - Bash completion script (142 LOC)
- `_openfatture.zsh` - Zsh completion script (203 LOC)
- `install.sh` - Installation helper (200 LOC)
- `README.md` - This file

## License

Part of the OpenFatture project. See main LICENSE file.
