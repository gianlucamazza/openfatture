# OpenFatture - Makefile System

Sistema di build modulare per OpenFatture con organizzazione per area funzionale.

## 📁 Struttura

```
Makefile                 # Orchestrator principale
makefiles/
├── base.mk             # Install, clean, format, lint
├── test.mk             # Testing (unit, integration, AI, payment)
├── docker.mk           # Docker & Docker Compose
├── dev.mk              # Development tools (DB, run, shell)
├── ai.mk               # AI assistant commands
├── ci.mk               # CI/CD & release management
└── media.mk            # Media automation (videos, screenshots)
```

## 🚀 Quick Start

### Comandi Base

```bash
# Mostra help categorizzato
make help

# Setup completo ambiente di sviluppo
make dev-setup

# Installa dipendenze
make install

# Esegui test suite
make test

# Avvia OpenFatture in modalità interattiva
make run-interactive
```

### Help Categorizzato

```bash
make help-base      # Comandi base (install, clean, lint, format)
make help-test      # Comandi testing
make help-docker    # Docker e compose
make help-dev       # Development tools
make help-ai        # AI assistant
make help-ci        # CI/CD
make help-media     # Media automation
make help-all       # Tutti i comandi disponibili
```

## 📚 Categorie

### Base Commands (`makefiles/base.mk`)

**Installazione:**
```bash
make install        # Installa tutte le dipendenze
make install-prod   # Solo dipendenze production
make install-dev    # Dipendenze development + pre-commit hooks
make sync           # Aggiorna lockfile
```

**Pulizia:**
```bash
make clean          # Pulisce cache e file temporanei
make clean-all      # Pulizia profonda (inclusi build artifacts)
```

**Formattazione & Linting:**
```bash
make format         # Formatta codice (black + ruff)
make lint           # Esegue tutti i linter (black, ruff, mypy)
make lint-check     # Check formattazione (no modifiche)
make type-check     # Solo type checking (mypy)
make pre-commit     # Esegue pre-commit hooks
```

### Testing Commands (`makefiles/test.mk`)

**Test Generali:**
```bash
make test           # Test completi con coverage
make test-all       # Suite completa
make test-fast      # Test veloci (senza coverage)
make test-watch     # Watch mode
make test-parallel  # Test in parallelo
```

**Test per Modulo:**
```bash
make test-unit          # Solo unit tests
make test-integration   # Solo integration tests
make test-core          # Test core module
make test-sdi           # Test SDI module
make test-cli           # Test CLI
make test-utils         # Test utilities
```

**Test AI:**
```bash
make test-ai                # Tutti i test AI
make test-ai-unit           # Unit tests AI
make test-ai-integration    # Integration tests AI
make test-ai-streaming      # Test streaming
make test-ai-cache          # Test cache
make test-ai-token-counter  # Test token counter
```

**Test Payment:**
```bash
make test-payment           # Payment module (coverage ≥80%)
make test-payment-domain    # Domain tests
make test-payment-matchers  # Matchers tests
```

**Coverage:**
```bash
make coverage               # Report coverage completo
make coverage-report        # Apre report HTML
make coverage-html          # Genera solo HTML
make coverage-xml           # Genera XML (per CI)
make coverage-threshold     # Verifica threshold (80%)
```

**Shortcut:**
```bash
make t      # = test-all
make tw     # = test-watch
make tu     # = test-unit
make ti     # = test-integration
make ta     # = test-ai
make tp     # = test-payment
```

### Docker Commands (`makefiles/docker.mk`)

**Build:**
```bash
make docker-build           # Build immagine
make docker-build-no-cache  # Build senza cache
make docker-build-dev       # Build development
```

**Run:**
```bash
make docker-run         # Esegui container
make docker-shell       # Shell nel container
make docker-interactive # OpenFatture interattivo
```

**Compose:**
```bash
make compose-up                # Avvia servizi base
make compose-up-postgres       # Con PostgreSQL
make compose-up-ai             # Con Redis (AI cache)
make compose-up-worker         # Con payment worker
make compose-up-full           # Stack completo
make compose-down              # Ferma servizi
make compose-logs              # Visualizza logs
make compose-ps                # Mostra servizi attivi
```

**Manutenzione:**
```bash
make docker-clean           # Rimuovi containers/images
make docker-prune           # Pulizia risorse Docker
make docker-volumes-clean   # Rimuovi volumes (ATTENZIONE!)
make docker-test            # Test immagine Docker
make docker-health          # Check health containers
```

**Shortcut:**
```bash
make db     # = docker-build
make dr     # = docker-run
make ds     # = docker-shell
make cu     # = compose-up
make cd     # = compose-down
make cl     # = compose-logs
```

### Development Commands (`makefiles/dev.mk`)

**Setup:**
```bash
make dev-setup      # Setup completo ambiente dev
make dev-env        # Info ambiente di sviluppo
make dev-check      # Verifica prerequisiti
```

**Database:**
```bash
make db-init        # Inizializza database
make db-reset       # Reset database (ATTENZIONE!)
make db-seed        # Popola con dati di esempio
make db-shell       # Apri shell SQLite
make db-backup      # Backup database
make db-restore     # Restore (usage: make db-restore BACKUP=filename)
```

**Run:**
```bash
make run                # OpenFatture CLI
make run-interactive    # Modalità interattiva
make run-help           # Help
make run-version        # Versione
make run-config         # Mostra configurazione
make run-stats          # Statistiche fatture
```

**Shell:**
```bash
make shell      # Python shell con OpenFatture
make ipython    # IPython shell
make jupyter    # Jupyter notebook
```

**Documentazione:**
```bash
make docs-build     # Build documentation
make docs-serve     # Serve su http://localhost:8000
make docs-clean     # Pulisce build docs
```

**Shortcut:**
```bash
make i      # = run-interactive
make s      # = shell
```

### AI Commands (`makefiles/ai.mk`)

**Assistant:**
```bash
make ai-chat            # Avvia chat assistant
make ai-describe        # Genera descrizione fattura
                        # Usage: make ai-describe TEXT="sviluppo API"
make ai-suggest-vat     # Suggerisci aliquota IVA
                        # Usage: make ai-suggest-vat DESC="consulenza IT"
make ai-forecast        # Previsione flusso di cassa
make ai-check           # Verifica compliance fattura
```

**Sessioni:**
```bash
make ai-session-list        # Lista sessioni
make ai-session-show        # Dettagli sessione
                            # Usage: make ai-session-show ID=xxx
make ai-session-export      # Esporta sessione
                            # Usage: make ai-session-export ID=xxx FORMAT=json
make ai-session-clear       # Cancella vecchie sessioni
```

**Cache:**
```bash
make ai-cache-info      # Statistiche cache
make ai-cache-clear     # Svuota cache
make ai-cache-warmup    # Pre-carica cache
```

**Provider:**
```bash
make ai-providers           # Lista provider disponibili
make ai-test-openai         # Test connessione OpenAI
make ai-test-anthropic      # Test connessione Anthropic
make ai-test-ollama         # Test connessione Ollama
make ai-setup-ollama        # Setup Ollama con llama3.2
```

**Development:**
```bash
make lint-ai            # Lint solo modulo AI
make test-ai-full       # Suite completa test AI
make ai-benchmark       # Benchmark performance
```

**Demo:**
```bash
make ai-demo-chat       # Demo chat assistant
make ai-demo-invoice    # Demo invoice assistant
```

**Shortcut:**
```bash
make chat       # = ai-chat
make forecast   # = ai-forecast
```

### CI/CD Commands (`makefiles/ci.mk`)

**Pipeline CI:**
```bash
make ci             # Pipeline CI completa
make ci-install     # Install per CI
make ci-test        # Test per CI
make ci-lint        # Lint per CI
make ci-coverage    # Coverage per CI
make ci-security    # Security checks per CI
make ci-docker      # Build + test Docker
make ci-all         # CI completa + Docker
```

**Security:**
```bash
make security               # Tutti i security checks
make security-bandit        # Bandit security scanner
make security-safety        # Check vulnerabilità note
make security-audit         # Audit completo
make security-report        # Report HTML
```

**Version Management:**
```bash
make bump-patch         # Bump patch (0.0.X)
make bump-minor         # Bump minor (0.X.0)
make bump-major         # Bump major (X.0.0)
make show-version       # Mostra versione corrente
```

**Build & Publish:**
```bash
make build              # Build packages
make build-check        # Build + validazione
make publish            # Pubblica su PyPI
make publish-test       # Pubblica su TestPyPI
```

**Release:**
```bash
make release-patch      # Release patch
make release-minor      # Release minor
make release-major      # Release major
make release-notes      # Genera release notes
```

**Git:**
```bash
make git-status         # Git status
make git-check          # Verifica working dir pulita
make git-tag            # Crea tag versione
make git-tag-push       # Push tags
make git-changelog      # Genera changelog
```

**GitHub Actions:**
```bash
make gh-actions-list        # Lista workflows
make gh-actions-validate    # Valida workflows
make gh-actions-test        # Test con act (locale)
```

**Reports:**
```bash
make report-coverage    # Report coverage
make report-security    # Report security
make report-all         # Tutti i report
```

**Shortcut:**
```bash
make check      # = ci
make validate   # = ci-lint + ci-type-check
```

### Media Automation (`makefiles/media.mk`)

**Prerequisiti:**
```bash
make media-install      # Installa tools (VHS, ffmpeg)
make media-check        # Verifica prerequisiti
make media-reset        # Reset ambiente demo
```

**Video Generation (VHS):**
```bash
make media-scenarioA    # Video Scenario A (Onboarding)
make media-scenarioB    # Video Scenario B (Invoice Creation)
make media-scenarioC    # Video Scenario C (AI Assistant)
make media-scenarioD    # Video Scenario D (Batch Operations)
make media-scenarioE    # Video Scenario E (PEC Integration)
make media-all          # Genera tutti i video
```

**Screenshot:**
```bash
make media-screenshots              # Cattura tutti gli screenshot
make media-screenshots-scenario     # Scenario specifico
                                    # Usage: make media-screenshots-scenario SCENARIO=A
```

**Ottimizzazione:**
```bash
make media-optimize             # Ottimizza tutti i video
make media-optimize-file        # Ottimizza file specifico
                                # Usage: make media-optimize-file FILE=video.mp4
```

**Conversione:**
```bash
make media-to-gif       # Converti in GIF
                        # Usage: make media-to-gif FILE=video.mp4
make media-to-webm      # Converti in WebM
                        # Usage: make media-to-webm FILE=video.mp4
```

**Info & Pulizia:**
```bash
make media-list         # Lista tutti i file media
make media-info         # Info sui file media
make media-test         # Test automazione (dry run)
make media-clean        # Pulisce output (ATTENZIONE!)
make media-clean-cache  # Pulisce cache VHS
```

**Demo:**
```bash
make demo-reset         # Reset ambiente demo
make demo-data          # Mostra file demo
make demo-prepare       # Prepara ambiente demo
```

**Shortcut:**
```bash
make video          # = media-all
make screenshots    # = media-screenshots
```

## 🔧 Workflows Comuni

### Setup Iniziale
```bash
# 1. Setup completo
make dev-setup

# 2. Modifica .env con le tue configurazioni
nano .env

# 3. Inizializza database
make db-init

# 4. Esegui test
make test

# 5. Avvia applicazione
make run-interactive
```

### Development Loop
```bash
# Test in watch mode (in un terminale)
make test-watch

# Sviluppa...

# Formatta e verifica
make format && make lint

# Test completi
make test-all
```

### Docker Development
```bash
# Build e test
make docker-build
make docker-test

# Run
make docker-run

# O con compose (stack completo)
make compose-up-full

# Visualizza logs
make compose-logs

# Stop
make compose-down
```

### CI/CD Pipeline
```bash
# Esegui pipeline locale
make ci

# Security audit
make security

# Release
make release-patch

# Push tag
make git-tag-push
```

### Media Automation
```bash
# Setup tools
make media-install

# Genera tutti i video demo
make media-all

# Cattura screenshot
make media-screenshots

# Ottimizza
make media-optimize
```

## 🎯 Target Compositi

Target che combinano più operazioni:

```bash
make all            # Build pipeline completo
make setup          # Setup environment
make check          # Quick check (lint + test)
make full-test      # Tutti i test (unit, integration, AI, payment, services)
make full-check     # Check qualità completo
make quick          # Validazione veloce
```

## 📊 Informazioni

```bash
make info       # Info progetto completo
make version    # Versione OpenFatture
make env        # Info ambiente
make status     # Git status
```

## 🔍 Tips & Best Practices

### 1. Help Contestuale
Ogni categoria ha il suo help:
```bash
make help-<category>
```

### 2. Shortcut
Usa gli shortcut per comandi frequenti:
```bash
make t      # test-all
make f      # format
make l      # lint-all
make i      # run-interactive
make chat   # ai-chat
```

### 3. Parametri
Alcuni comandi accettano parametri:
```bash
make ai-describe TEXT="sviluppo web"
make db-restore BACKUP=backup_20250101.db
make media-screenshots-scenario SCENARIO=A
```

### 4. Environment
Specifica l'ambiente:
```bash
ENV=prod make install    # Installa solo prod dependencies
```

### 5. Parallel Execution
Make supporta l'esecuzione parallela:
```bash
make -j4 test-unit test-ai    # Esegui in parallelo
```

### 6. Dry Run
Visualizza cosa farebbe un comando senza eseguirlo:
```bash
make -n test    # Dry run
```

### 7. Debug
Abilita debug mode:
```bash
make -d test    # Debug completo
make -p         # Print database
```

## 🐛 Troubleshooting

### "uv not installed"
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### "Docker not installed"
```bash
brew install docker  # macOS
```

### Target non trovato
Verifica che tutti i file .mk siano presenti:
```bash
ls -la makefiles/
```

### Warning su target duplicati
Sono stati rimossi nella versione finale. Se persistono, controlla eventuali alias.

## 📝 Estensione

Per aggiungere nuovi target:

1. **Modifica file appropriato** in `makefiles/`
2. **Aggiungi commento con ##** per help automatico:
   ```makefile
   my-target: ## Descrizione target
       @echo "Doing something..."
   ```
3. **Dichiara .PHONY** se non crea file
4. **Usa variabili globali** dal Makefile principale
5. **Test** con `make help-<category>`

## 🎨 Colori

Il sistema usa colori per migliorare la leggibilità:
- 🔵 BLUE - Informazioni
- 🟢 GREEN - Successo
- 🟡 YELLOW - Warning
- 🔴 RED - Errore
- 🔷 CYAN - Highlight
- 🟣 MAGENTA - Titoli

## 📄 License

Questo sistema di build è parte di OpenFatture (MIT License).

---

**Realizzato con ❤️ per OpenFatture**
