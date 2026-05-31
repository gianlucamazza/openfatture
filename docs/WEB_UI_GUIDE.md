# OpenFatture Web UI - Guida Utente

Guida completa all'utilizzo dell'interfaccia web di OpenFatture.

## Indice

1. [Introduzione](#introduzione)
2. [Installazione e Setup](#installazione-e-setup)
3. [Tour delle Pagine](#tour-delle-pagine)
4. [Casi d'Uso Comuni](#casi-duso-comuni)
5. [FAQ](#faq)

## Introduzione

La **Web UI di OpenFatture** è un'interfaccia moderna e intuitiva costruita con Streamlit che permette di:

- Visualizzare dashboard real-time con KPI e grafici
- Gestire fatture in modo visuale
- Interagire con l'AI Assistant per descrizioni e consulenza fiscale
- Monitorare pagamenti e riconciliazioni
- Verificare la configurazione del sistema

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

### Home

**Funzionalità:**
- Overview funzionalità disponibili
- Quick actions per task comuni
- Link rapidi alle pagine principali
- Statistiche sidebar (fatture, clienti, fatturato)
- Getting started guide

**Navigazione:**
- Click su card per accedere alle sezioni
- Usa sidebar per menu di navigazione

### Dashboard

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

### Fatture

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

### AI Assistant

**4 Tab Principali:**

#### Chat Assistente

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

#### Voice Chat

**Funzionalità:**
- **Interazione vocale** hands-free con l'AI Assistant
- **Speech-to-Text:** Trascrizione automatica con OpenAI Whisper (100+ lingue)
- **Text-to-Speech:** Sintesi vocale con voce personalizzabile
- **Memoria conversazione:** Mantiene contesto tra più interazioni vocali
- **Supporto multilingua:** Rilevamento automatico della lingua
- **Riproduzione audio:** Ascolta la risposta dell'AI direttamente nel browser

**Come Usare:**
1. Assicurati che il microfono sia abilitato nel browser
2. Click sul pulsante "Registra Audio" e concedi permessi microfono
3. Parla la tua domanda (es. "Quale IVA per consulenza web?")
4. Attendi elaborazione:
   - Trascrizione audio testo
   - Elaborazione risposta AI
   - Sintesi vocale risposta
5. Ascolta la risposta audio automaticamente
6. Visualizza trascrizione e risposta testuale
7. Continua la conversazione vocale (mantiene contesto)

**Configurazione Richiesta:**

Aggiungi al file `.env`:
```bash
# Abilita voice features
VOICE_ENABLED=true

# OpenAI API key (richiesta per Whisper + TTS)
OPENAI_API_KEY=sk-...

# Configurazione STT (Speech-to-Text)
VOICE_STT_MODEL=whisper-1         # Modello Whisper
VOICE_STT_LANGUAGE=it             # Lingua (lascia vuoto per auto-detect)

# Configurazione TTS (Text-to-Speech)
VOICE_TTS_MODEL=tts-1             # tts-1 o tts-1-hd (alta qualità)
VOICE_TTS_VOICE=nova              # Voce: nova, alloy, echo, fable, onyx, shimmer
VOICE_TTS_SPEED=1.0               # Velocità: 0.25-4.0
VOICE_TTS_FORMAT=mp3              # Formato: mp3, opus, aac, flac
```

**Selezione Voce TTS:**

| Voce | Genere | Caratteristiche | Consigliato per |
|------|--------|-----------------|-----------------|
| **nova** | Femminile | Calda, conversazionale | **Italiano, uso generale** |
| alloy | Neutro | Bilanciata, professionale | Inglese, tecnico |
| echo | Maschile | Chiara, articolata | Presentazioni |
| fable | Maschile | British, espressivo | Storytelling |
| onyx | Maschile | Profonda, autorevole | Business formale |
| shimmer | Femminile | Dolce, gentile | Francese, customer service |

**Workflow Tipico:**

1. **Prima volta:** Verifica configurazione in Impostazioni Voice Config
2. **Registra domanda:** Click "Registra" e parla naturalmente
3. **Rivedi trascrizione:** Controlla che il testo sia corretto
4. **Ascolta risposta:** Audio riprodotto automaticamente
5. **Continua conversazione:** Mantiene memoria dei messaggi precedenti
6. **Reset:** Click "Cancella" per nuova conversazione

**Esempi Domande Vocali:**
- "Crea una fattura per consulenza web di tre ore"
- "Quale aliquota IVA devo usare per formazione online?"
- "Quante fatture ho emesso questo mese?"
- "How does reverse charge work in Italy?"
- "¿Qué IVA aplico a servicios digitales?"

**Supporto Lingue:**

Whisper rileva automaticamente oltre 100 lingue, tra cui:
- Italiano (it)
- Inglese (en)
- Spagnolo (es)
- Francese (fr)
- Tedesco (de)
- Portoghese (pt)
- Olandese (nl)

**Costi Indicativi:**

- **STT (Whisper):** ~€0.006 per minuto audio
- **TTS:** ~€0.015 per 1.000 caratteri (tts-1), ~€0.030 per 1.000 caratteri (tts-1-hd)
- **Esempio conversazione 5 minuti:**
  - Registrazione: 5 min × €0.006 = €0.03
  - Risposta (500 caratteri): 0.5 × €0.015 = €0.0075
  - **Totale: ~€0.04 per conversazione**

**Performance:**

- **Latenza STT:** 1-3 secondi per audio 5-10 secondi
- **Latenza TTS:** 1-2 secondi per risposta 100-200 caratteri
- **Latenza totale:** 3-7 secondi per interazione completa
- **Qualità audio:** 16kHz mono (default), 48kHz stereo (opzionale)

**Troubleshooting:**

- **Microfono non rilevato:** Verifica permessi browser (icona lucchetto URL)
- **Trascrizione errata:** Parla più chiaramente o riduci rumore ambiente
- **Nessun audio risposta:** Controlla volume sistema e formato audio supportato
- **Errore API:** Verifica `OPENAI_API_KEY` valida in `.env`
- **Voice non disponibile:** Assicurati che `VOICE_ENABLED=true` in `.env`

**Test Configurazione:**

```bash
# Verifica voice config da CLI
uv run openfatture config show | grep VOICE

# Test voice chat da terminale
uv run openfatture ai voice-chat --duration 5

# Test interattivo con conversazione
uv run openfatture ai voice-chat --interactive
```

**Vantaggi Voice Chat:**

**Hands-Free:** Ideale per multitasking o mobilità
**Accessibilità:** Supporto per utenti con disabilità visive
**Multilingua:** Cambia lingua on-the-fly senza configurazione
**Naturale:** Conversazione più fluida rispetto a testo
**Mobile-Friendly:** Ottimo per smartphone e tablet

**Limitazioni Attuali:**

Richiede connessione internet (API OpenAI)
Latenza ~5s per risposta completa
Costi API per ogni interazione
Qualità dipende da microfono e ambiente

**Alternative CLI:**

Se preferisci il terminale, usa il comando `voice-chat`:
```bash
# Singola interazione
uv run openfatture ai voice-chat --duration 10

# Modalità interattiva
uv run openfatture ai voice-chat --interactive

# Salva audio per debug
uv run openfatture ai voice-chat --save-audio --interactive
```

#### Genera Descrizione

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

#### Suggerimento IVA

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

**Importante:** L'AI è uno strumento di supporto, non sostituisce un commercialista!

### Clienti (Placeholder)

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

### Pagamenti (Placeholder)

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

### Lightning

**Funzionalità:**
- **Status Connessione:** Verifica connessione LND e stato canali
- **Configurazione Lightning:** Visualizza e modifica impostazioni Lightning
- **Creazione Invoice:** Genera Lightning invoice da form web
- **Lista Invoice:** Mostra tutte le invoice Lightning con filtri
- **Dettaglio Invoice:** Visualizza QR code, payment request, stato
- **Monitoraggio Pagamenti:** Lista pagamenti ricevuti con dettagli
- **Statistiche Canali:** Capacità, bilanci, fee policy
- **Liquidity Management:** Monitora e gestisci liquidità canali

**Workflow Tipico:**
1. Verifica connessione LND nella sezione Status
2. Controlla configurazione e modifica se necessario
3. Crea nuova invoice inserendo importo e descrizione
4. Mostra dettaglio invoice per ottenere QR code/payment request
5. Condividi con cliente per pagamento istantaneo
6. Monitora ricevimento pagamento in tempo reale

**Caratteristiche Principali:**
- **QR Code Integrato:** Mostra QR code scannable per pagamenti mobili
- **Payment Request Copiabile:** Click per copiare payment request
- **Aggiornamenti Real-time:** Status invoice si aggiorna automaticamente
- **Conversione BTC/EUR:** Mostra equivalenti in entrambe le valute
- **Webhook Status:** Visualizza configurazione webhook se abilitata

**Prerequisiti:**
- Lightning abilitato in `.env` (`LIGHTNING_ENABLED=true`)
- LND node attivo e connesso
- Certificato TLS e macaroon configurati
- Almeno un canale con capacità inbound

**CLI Alternative:**
```bash
# Status e configurazione
uv run openfatture lightning status
uv run openfatture config set lightning_enabled true

# Gestione invoice
uv run openfatture lightning invoice create --amount 100.00 --description "Test"
uv run openfatture lightning invoice list
uv run openfatture lightning invoice status <id>

# Monitoraggio canali
uv run openfatture lightning channels
uv run openfatture lightning liquidity status
```

**Troubleshooting dalla Web UI:**
- **Connessione Fallita:** Verifica LND sia attivo e configurato correttamente
- **Nessuna Capacità:** Apri canali o attendi rebalancing automatico
- **Rate Conversione:** Controlla connessione internet e API provider
- **Invoice Scaduta:** Crea nuova invoice con expiry più lungo

### Impostazioni

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
2. Vai su Dashboard (1__Dashboard.py)
3. Controlla KPI: fatturato mese, fatture in sospeso
4. Verifica scadenze pagamenti
5. Identifica clienti top
```

### 2. Gestione Fattura End-to-End

```
# CLI per creazione (più veloce)
uv run openfatture fattura crea

# Web UI per monitoring
1. Vai su Fatture (2__Fatture.py)
2. Filtra per anno corrente
3. Trova fattura appena creata
4. Mostra dettaglio Genera XML
5. Torna alla CLI per invio SDI
```

### 3. Assistenza AI per Fattura Complessa

```
1. Vai su AI Assistant (5__AI_Assistant.py)
2. Tab "Genera Descrizione"
3. Compila: "Sviluppo API REST con Python e PostgreSQL"
   - Ore: 40
   - Tariffa: 50
   - Progetto: "Sistema Gestionale XYZ"
   - Tecnologie: "Python, FastAPI, PostgreSQL, Docker"
4. Genera Copia descrizione
5. Tab "Suggerimento IVA"
6. Descrivi servizio Verifica aliquota consigliata
7. Usa info per creare fattura
```

### 4. Consulenza Fiscale Rapida

```
1. AI Assistant Tab Chat
2. Domanda: "Cliente francese, consulenza IT, devo applicare IVA?"
3. AI risponde con analisi dettagliata
4. Follow-up: "Come lo indico in fattura?"
5. Usa informazioni per configurare fattura correttamente
```

### 5. Analisi Trend

```
1. Dashboard Grafico fatturato 6 mesi
2. Identifica trend (crescita/decrescita)
3. Top Clienti Vedi chi genera più fatturato
4. Usa insight per strategie business
```

## FAQ

### Come aggiorno i dati nella Dashboard?

**R:** La Dashboard usa cache con TTL 30s. Attendi 30s e ricarica la pagina, oppure clicca "Aggiorna Dati".

### Posso creare fatture dalla Web UI?

**R:** Al momento no, usa CLI: `uv run openfatture fattura crea`. Feature in roadmap.

### L'AI Assistant è sempre online?

**R:** Dipende dalla configurazione. Se `.env` ha `AI_PROVIDER` e `AI_API_KEY`, è attivo. Verifica su Impostazioni.

### Posso usare Web UI e CLI insieme?

**R:** Sì! Condividono stesso database. Crea con CLI, monitora con Web UI, nessun problema.

### Come cambio la porta?

**R:** `uv run streamlit run openfatture/web/app.py --server.port 8080`

### Come attivo il tema dark?

**R:** `--theme.base dark` oppure cambia in Settings (⋮) Theme nel browser.

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
