# OpenFatture Web UI 🌐

Web interface moderna per OpenFatture basata su **Streamlit**.

## Funzionalità ✨

### Implementate

- **🏠 Home** - Landing page con link rapidi e getting started
- **📊 Dashboard** - KPI real-time, grafici interattivi (Plotly), statistiche business
- **🧾 Fatture** - Lista, filtri, dettaglio, generazione XML
- **🤖 AI Assistant** - Chat interattivo, generazione descrizioni, suggerimenti IVA
- **⚙️ Impostazioni** - Visualizzazione configurazione sistema

### In Sviluppo

- **📈 Analytics** - Grafici avanzati, export report

## Installazione 📦

### 1. Installa dipendenze web

```bash
# Dalla root del progetto
uv sync --extra web
```

### 2. Verifica configurazione

Assicurati che `.env` sia configurato correttamente:

```bash
# Dati azienda (obbligatori)
CEDENTE_PARTITA_IVA=01234567890
CEDENTE_DENOMINAZIONE="La Mia Azienda"
CEDENTE_REGIME_FISCALE=RF19

# PEC per invio SDI (obbligatorio per invio)
PEC_USERNAME=username@pec.it
PEC_PASSWORD=your_password
PEC_SMTP_SERVER=smtp.pec.aruba.it
PEC_SMTP_PORT=465

# AI (opzionale, per AI Assistant)
AI_PROVIDER=openai
AI_API_KEY=sk-...
AI_MODEL=gpt-4-turbo-preview
```

Vedi `.env.example` o `docs/CONFIGURATION.md` per la configurazione completa.

### 3. Inizializza database (se non già fatto)

```bash
uv run python -c "from openfatture.storage.database.session import init_db; init_db()"
```

## Lancio 🚀

### Modalità Sviluppo

```bash
# Dalla root del progetto
uv run streamlit run openfatture/web/app.py
```

### Modalità Produzione

```bash
# Con configurazione custom
uv run streamlit run openfatture/web/app.py --server.port 8501 --server.address 0.0.0.0
```

### Opzioni Streamlit

```bash
# Porta custom
uv run streamlit run openfatture/web/app.py --server.port 8080

# Disabilita file watcher (prod)
uv run streamlit run openfatture/web/app.py --server.fileWatcherType none

# Dark theme
uv run streamlit run openfatture/web/app.py --theme.base dark
```

## Architettura 🏗️

```
openfatture/web/
├── app.py                      # Entry point / Home page
├── pages/                      # Multi-page app
│   ├── 1_📊_Dashboard.py
│   ├── 2_🧾_Fatture.py
│   ├── 3_👥_Clienti.py
│   ├── 4_💰_Pagamenti.py
│   ├── 5_🤖_AI_Assistant.py
│   └── 6_⚙️_Impostazioni.py
├── services/                   # Adapter services
│   ├── invoice_service.py     # Business logic wrapper con caching
│   └── ai_service.py          # AI providers async/sync bridge
├── utils/                      # Utilities
│   ├── async_helpers.py       # Async/await bridge
│   ├── cache.py               # Caching strategies
│   └── state.py               # Session state helpers
└── components/                 # Reusable UI components (future)
```

## Best Practices 📚

### Caching

```python
import streamlit as st

# Cache per dati che cambiano raramente (TTL 5 min)
@st.cache_data(ttl=300)
def get_clients():
    # ...

# Cache per risorse costose (singleton)
@st.cache_resource
def get_ai_provider():
    # ...
```

### Session State

```python
from openfatture.web.utils.state import init_state, get_state

# Initialize con default
page = init_state("current_page", "home")

# Get con fallback
filters = get_state("filters", {})
```

### Async Operations

```python
from openfatture.web.utils.async_helpers import run_async

# Esegui coroutine in contesto sync
result = run_async(ai_agent.execute(context))

# Oppure usa service wrapper
ai_service = get_ai_service()  # già gestisce async/sync
response = ai_service.chat(message, history)
```

## Integrazione con CLI 🔄

La Web UI **non sostituisce** la CLI, ma la **complementa**:

✅ **Coesistono perfettamente** - Condividono stesso database e business logic
✅ **Stesso .env** - Configurazione unica
✅ **Dati sincronizzati** - Modifiche CLI visibili in Web UI e viceversa

### Workflow Ibrido

```bash
# Crea fattura con CLI (più veloce per power users)
uv run openfatture fattura crea

# Monitora dashboard con Web UI
uv run streamlit run openfatture/web/app.py

# Usa AI Assistant per descrizioni
# (disponibile sia in CLI che Web UI)
```

## Troubleshooting 🔧

### Errore: "ModuleNotFoundError: No module named 'streamlit'"

```bash
uv sync --extra web
```

### Errore: "Database not initialized"

```bash
uv run python -c "from openfatture.storage.database.session import init_db; init_db()"
```

### Cache non aggiornata

```python
# In Streamlit
st.cache_data.clear()  # Pulisci cache
st.rerun()             # Ricarica page
```

Oppure usa il pulsante "🔄 Aggiorna" nelle pagine.

### AI Assistant non funziona

1. Verifica `.env`:
   - `AI_PROVIDER` impostato (openai/anthropic/ollama)
   - `AI_API_KEY` presente (se necessario)
   - `AI_MODEL` specificato

2. Test provider:
   ```bash
   uv run openfatture ai chat "test"
   ```

3. Check logs per errori dettagliati

## Performance Tips 🚄

### Caching Aggressivo

```python
# Cache invoices per 30s (cambiano raramente)
@st.cache_data(ttl=30)
def get_invoices():
    # ...
```

### Lazy Loading

```python
# Carica dati solo quando necessario
if st.button("Mostra Dettaglio"):
    invoice = get_invoice_detail(id)  # Carica solo su click
```

### Pagination

```python
# Limita risultati
invoices = get_invoices(limit=50)
```

## Roadmap 🗺️

### Phase 1 (Completato) ✅
- [x] Struttura base multi-page
- [x] Dashboard con KPI e grafici
- [x] Lista fatture con filtri
- [x] AI Assistant (chat, descrizioni, tax)
- [x] Utilities (cache, async, state)

### Phase 2 (Next) 🔨
- [x] Wizard creazione fattura
- [x] Gestione clienti (CRUD completo)
- [x] Upload estratti conto
- [x] Matching pagamenti interattivo

### Phase 3 (Future) 🚀
- [ ] Cash flow forecast visualization
- [ ] Compliance checker UI
- [ ] Export report (PDF, Excel)
- [ ] Advanced analytics
- [ ] User authentication

## Contributing 🤝

Per contribuire alla Web UI:

1. Segui le convenzioni esistenti
2. Usa type hints
3. Aggiungi docstrings
4. Testa su browser diversi
5. Mantieni compatibilità CLI

## Support & Docs 📖

- **Main README:** `../../README.md`
- **Configuration:** `../../docs/CONFIGURATION.md`
- **CLI Reference:** `../../docs/CLI_REFERENCE.md`
- **AI Architecture:** `../../docs/AI_ARCHITECTURE.md`
- **Issues:** https://github.com/gianlucamazza/openfatture/issues

---

Made with ❤️ using Streamlit
