# OpenFatture Web UI - Guida Utente 🌐

Guida completa all'utilizzo dell'interfaccia web di OpenFatture.

## Indice

1. [Introduzione](#introduzione)
2. [Installazione e Setup](#installazione-e-setup)
3. [Tour delle Pagine](#tour-delle-pagine)
4. [Casi d'Uso Comuni](#casi-duso-comuni)
5. [FAQ](#faq)

## Introduzione

La **Web UI di OpenFatture** è un'interfaccia moderna e intuitiva costruita con Streamlit che permette di:

- 📊 Visualizzare dashboard real-time con KPI e grafici
- 🧾 Gestire fatture in modo visuale
- 🤖 Interagire con l'AI Assistant per descrizioni e consulenza fiscale
- 💰 Monitorare pagamenti e riconciliazioni
- ⚙️ Verificare la configurazione del sistema

La Web UI **coesiste** con la CLI tradizionale, permettendo di scegliere lo strumento più adatto per ogni task.

## Installazione e Setup

### Prerequisiti

- Python 3.12+
- OpenFatture già installato e configurato
- File `.env` con configurazione base

### Step 1: Installa dipendenze Web

```bash
cd /path/to/openfatture
uv sync --extra web
```

Questo installa:
- `streamlit` - Framework web
- `plotly` - Grafici interattivi
- `altair` - Visualizzazioni dichiarative
- `streamlit-aggrid` - Tabelle avanzate
- `streamlit-extras` - Componenti extra

### Step 2: Verifica configurazione

```bash
# Assicurati che il database sia inizializzato
uv run python -c "from openfatture.storage.database.session import init_db; init_db()"

# (Opzionale) Popola con dati di esempio se database vuoto
uv run openfatture cliente add "Cliente Test" --interactive
uv run openfatture fattura crea
```

### Step 3: Lancia l'applicazione

```bash
uv run streamlit run openfatture/web/app.py
```

L'app si aprirà automaticamente nel browser all'indirizzo `http://localhost:8501`.

### Configurazione Avanzata

#### Porta Custom

```bash
uv run streamlit run openfatture/web/app.py --server.port 8080
```

#### Deploy Produzione

```bash
# Bind su tutte le interfacce
uv run streamlit run openfatture/web/app.py \
  --server.address 0.0.0.0 \
  --server.port 8501 \
  --server.fileWatcherType none \
  --browser.gatherUsageStats false
```

#### Tema Dark

```bash
uv run streamlit run openfatture/web/app.py --theme.base dark
```

#### Docker (opzionale)

Crea `Dockerfile.web`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install uv
RUN uv sync --extra web

EXPOSE 8501

CMD ["uv", "run", "streamlit", "run", "openfatture/web/app.py", \
     "--server.address", "0.0.0.0", \
     "--server.fileWatcherType", "none"]
```

Build e run:

```bash
docker build -t openfatture-web -f Dockerfile.web .
docker run -p 8501:8501 -v $(pwd)/.env:/app/.env openfatture-web
```

## Tour delle Pagine

### 🏠 Home

**Funzionalità:**
- Overview funzionalità disponibili
- Quick actions per task comuni
- Link rapidi alle pagine principali
- Statistiche sidebar (fatture, clienti, fatturato)
- Getting started guide

**Navigazione:**
- Click su card per accedere alle sezioni
- Usa sidebar per menu di navigazione

### 📊 Dashboard

**Funzionalità:**
- **KPI Cards:** Fatture totali, clienti, fatturato (totale/anno/mese)
- **Grafico Torta:** Distribuzione fatture per stato
- **Grafico Bar:** Fatturato ultimi 6 mesi
- **Tabelle:** Top 5 clienti, Ultime 5 fatture
- **Payment Stats:** Transazioni (abbinate/non abbinate/ignorate)
- **Scadenze:** Pagamenti in scadenza prossimi 30 giorni

**Interattività:**
- Grafici Plotly interattivi (zoom, pan, hover)
- Refresh automatico con caching (TTL 30s)
- Pulsante "Aggiorna Dati" per force refresh

**Best Practice:**
- Usa come "command center" per monitoring quotidiano
- Identifica subito fatture in sospeso e scadenze critiche
- Monitora trend fatturato per prendere decisioni

### 🧾 Fatture

**Funzionalità:**
- **Lista Fatture** con filtri (anno, stato)
- **Statistiche:** Totale trovate, importo, stati, media
- **Tabella Interattiva:** Ordinabile, formattata
- **Dettaglio Fattura:**
  - Header (numero, data, cliente, stato)
  - Righe fattura (descrizione, quantità, prezzo, IVA)
  - Totali (imponibile, IVA, ritenuta, bollo)
  - File (XML, PDF)
- **Azioni:** Genera XML, Invia SDI (placeholder)

**Workflow Tipico:**
1. Filtra per anno/stato
2. Identifica fattura da gestire
3. Inserisci ID e mostra dettaglio
4. Genera XML se necessario
5. Usa CLI per azioni avanzate (invio SDI)

**Limitazioni Attuali:**
- Creazione fattura: usa CLI (`openfatture fattura crea`)
- Invio SDI: usa CLI (`openfatture fattura invia <id>`)
- Modifica: usa CLI o database direttamente

### 🤖 AI Assistant

**3 Tab Principali:**

#### 💬 Chat Assistente

**Funzionalità:**
- Chat interattivo con streaming real-time
- Memoria conversazione (session-based)
- Risponde a domande su:
  - Fatturazione e normativa
  - Consigli fiscali e IVA
  - Gestione pagamenti
  - Business advice generale

**Come Usare:**
1. Scrivi domanda nel campo input
2. Attendi risposta con streaming
3. Continua conversazione (mantiene contesto)
4. Usa "Cancella" per reset

**Esempi Domande:**
- "Come funziona il reverse charge?"
- "Devo applicare IVA su consulenza IT per PA?"
- "Cosa succede se una fattura viene rifiutata da SDI?"
- "Come gestisco una fattura con split payment?"

#### 📝 Genera Descrizione

**Funzionalità:**
- Genera descrizioni professionali per fatture
- Input: servizio, ore, tariffa, progetto, tecnologie
- Output strutturato:
  - Descrizione completa
  - Deliverables
  - Competenze tecniche
  - Durata
  - Note

**Workflow:**
1. Compila form (minimo: descrizione servizio)
2. Click "Genera Descrizione"
3. Rivedi output AI
4. Copia descrizione per usarla in fattura

**Suggerimento:** Più dettagli fornisci, migliore sarà l'output!

#### 🧾 Suggerimento IVA

**Funzionalità:**
- Analizza servizio/prodotto
- Suggerisce aliquota IVA corretta
- Identifica reverse charge, split payment, regimi speciali
- Fornisce:
  - Aliquota IVA raccomandata
  - Codice Natura (se applicabile)
  - Spiegazione normativa
  - Riferimento legislativo
  - Raccomandazioni

**Workflow:**
1. Descrivi servizio/prodotto
2. Specifica tipo cliente (PA/estero)
3. Aggiungi dettagli (importo, categoria, paese)
4. Click "Ottieni Suggerimento"
5. Leggi analisi AI

**Importante:** ⚠️ L'AI è uno strumento di supporto, non sostituisce un commercialista!

### 👥 Clienti (Placeholder)

**Status:** In sviluppo

**Attualmente:**
- Preview top clienti
- Statistiche rapide

**Usa CLI per ora:**
```bash
uv run openfatture cliente list
uv run openfatture cliente add "Nome" --interactive
uv run openfatture cliente show <id>
```

### 💰 Pagamenti (Placeholder)

**Status:** In sviluppo

**Attualmente:**
- Statistiche transazioni
- Scadenze pagamenti

**Usa CLI per ora:**
```bash
uv run openfatture payment import statement.ofx --account 1
uv run openfatture payment reconcile --account 1
uv run openfatture payment queue --interactive
```

### ⚙️ Impostazioni

**Funzionalità:**
- Visualizza configurazione attuale (read-only)
- Dati azienda (P.IVA, CF, regime, indirizzo)
- PEC settings (SMTP, username)
- AI configuration (provider, model)
- Database path
- Directory paths
- System info (Python, platform, versione)

**Per Modificare:**
1. Edita file `.env` nella root
2. Riavvia Streamlit

## Casi d'Uso Comuni

### 1. Monitoring Business Quotidiano

```
1. Apri Web UI: uv run streamlit run openfatture/web/app.py
2. Vai su Dashboard (1_📊_Dashboard.py)
3. Controlla KPI: fatturato mese, fatture in sospeso
4. Verifica scadenze pagamenti
5. Identifica clienti top
```

### 2. Gestione Fattura End-to-End

```
# CLI per creazione (più veloce)
uv run openfatture fattura crea

# Web UI per monitoring
1. Vai su Fatture (2_🧾_Fatture.py)
2. Filtra per anno corrente
3. Trova fattura appena creata
4. Mostra dettaglio → Genera XML
5. Torna alla CLI per invio SDI
```

### 3. Assistenza AI per Fattura Complessa

```
1. Vai su AI Assistant (5_🤖_AI_Assistant.py)
2. Tab "Genera Descrizione"
3. Compila: "Sviluppo API REST con Python e PostgreSQL"
   - Ore: 40
   - Tariffa: 50
   - Progetto: "Sistema Gestionale XYZ"
   - Tecnologie: "Python, FastAPI, PostgreSQL, Docker"
4. Genera → Copia descrizione
5. Tab "Suggerimento IVA"
6. Descrivi servizio → Verifica aliquota consigliata
7. Usa info per creare fattura
```

### 4. Consulenza Fiscale Rapida

```
1. AI Assistant → Tab Chat
2. Domanda: "Cliente francese, consulenza IT, devo applicare IVA?"
3. AI risponde con analisi dettagliata
4. Follow-up: "Come lo indico in fattura?"
5. Usa informazioni per configurare fattura correttamente
```

### 5. Analisi Trend

```
1. Dashboard → Grafico fatturato 6 mesi
2. Identifica trend (crescita/decrescita)
3. Top Clienti → Vedi chi genera più fatturato
4. Usa insight per strategie business
```

## FAQ

### Come aggiorno i dati nella Dashboard?

**R:** La Dashboard usa cache con TTL 30s. Attendi 30s e ricarica la pagina, oppure clicca "🔄 Aggiorna Dati".

### Posso creare fatture dalla Web UI?

**R:** Al momento no, usa CLI: `uv run openfatture fattura crea`. Feature in roadmap.

### L'AI Assistant è sempre online?

**R:** Dipende dalla configurazione. Se `.env` ha `AI_PROVIDER` e `AI_API_KEY`, è attivo. Verifica su Impostazioni.

### Posso usare Web UI e CLI insieme?

**R:** Sì! Condividono stesso database. Crea con CLI, monitora con Web UI, nessun problema.

### Come cambio la porta?

**R:** `uv run streamlit run openfatture/web/app.py --server.port 8080`

### Come attivo il tema dark?

**R:** `--theme.base dark` oppure cambia in Settings (⋮) → Theme nel browser.

### L'app è lenta, come ottimizzo?

**R:**
1. Verifica cache attiva (check decoratori `@st.cache_data`)
2. Riduci limiti query (es. `limit=20` invece di `limit=1000`)
3. Chiudi tab inutilizzate
4. Usa `--server.fileWatcherType none` in produzione

### Come deploy su server remoto?

**R:**
```bash
# SSH su server
ssh user@server

# Clone repo
git clone https://github.com/gianlucamazza/openfatture.git
cd openfatture

# Setup
uv sync --extra web
cp .env.example .env
# Edita .env

# Run con bind su 0.0.0.0
uv run streamlit run openfatture/web/app.py \
  --server.address 0.0.0.0 \
  --server.port 8501 \
  --server.fileWatcherType none
```

Poi accedi da `http://server-ip:8501`.

### Supporta autenticazione multi-utente?

**R:** No al momento. Streamlit Cloud offre auth built-in. Per self-hosted, considera reverse proxy con auth (nginx + basic auth o OAuth).

### Come report bug o proporre feature?

**R:** Apri issue su GitHub: https://github.com/gianlucamazza/openfatture/issues

---

## Link Utili

- **README Web:** `../openfatture/web/README.md`
- **Configuration:** `CONFIGURATION.md`
- **CLI Reference:** `CLI_REFERENCE.md`
- **AI Architecture:** `AI_ARCHITECTURE.md`
- **Payment Tracking:** `PAYMENT_TRACKING.md`

---

**Supporto:** info@gianlucamazza.it
**Repository:** https://github.com/gianlucamazza/openfatture
