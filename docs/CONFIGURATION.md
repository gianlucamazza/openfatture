# Configuration Reference

Riferimento completo per tutte le opzioni di configurazione di OpenFatture.

---

## Panoramica

OpenFatture usa variabili d'ambiente per la configurazione, caricate da file `.env` tramite **Pydantic Settings**.

**File di configurazione:**
- `.env` - Configurazione locale (NON committare!)
- `.env.example` - Template con valori di esempio

**Precedenza:**
1. Variabili d'ambiente del sistema
2. File `.env`
3. Valori di default nel codice

---

## Database

### `DATABASE_URL`

**Descrizione**: URL di connessione al database

**Tipo**: String

**Default**: `sqlite:///./openfatture.db`

**Esempi**:
```env
# SQLite (sviluppo)
DATABASE_URL=sqlite:///./openfatture.db

# PostgreSQL (produzione)
DATABASE_URL=postgresql://user:password@localhost:5432/openfatture

# PostgreSQL con SSL
DATABASE_URL=postgresql://user:password@host:5432/db?sslmode=require
```

**Note**:
- SQLite va bene per sviluppo e freelancer singoli
- PostgreSQL raccomandato per produzione o multi-utente
- Il database viene creato automaticamente se non esiste

**Troubleshooting**:
```bash
# Verifica connessione
uv run python -c "
from openfatture.storage.database.session import get_session
session = next(get_session())
print('✅ Database connesso')
"
```

---

## Dati Aziendali (Cedente Prestatore)

Questi sono i tuoi dati aziendali che appariranno su tutte le fatture.

### `CEDENTE_DENOMINAZIONE`

**Descrizione**: Ragione sociale o nome completo

**Tipo**: String

**Required**: ✅ Obbligatorio

**Esempio**:
```env
CEDENTE_DENOMINAZIONE=Mario Rossi
# oppure
CEDENTE_DENOMINAZIONE=Acme Consulting SRL
```

**Note**:
- Per ditte individuali: nome e cognome
- Per società: ragione sociale completa
- Verrà mostrato nell'XML e nelle email

---

### `CEDENTE_PARTITA_IVA`

**Descrizione**: Partita IVA (11 cifre)

**Tipo**: String (11 caratteri)

**Required**: ✅ Obbligatorio

**Esempio**:
```env
CEDENTE_PARTITA_IVA=12345678901
```

**Validazione**:
- Deve essere esattamente 11 cifre
- Solo numeri
- Algoritmo di controllo non verificato (puoi estendere)

**Note**:
- Usata come identificatore univoco
- Necessaria per invio SDI

---

### `CEDENTE_CODICE_FISCALE`

**Descrizione**: Codice fiscale

**Tipo**: String (16 caratteri alfanumerici)

**Required**: ✅ Obbligatorio

**Esempio**:
```env
# Persona fisica
CEDENTE_CODICE_FISCALE=RSSMRA80A01H501U

# Società (uguale a P.IVA)
CEDENTE_CODICE_FISCALE=12345678901
```

**Note**:
- Per persone fisiche: codice fiscale standard (16 caratteri)
- Per società: solitamente uguale alla P.IVA
- Obbligatorio per FatturaPA

---

### `CEDENTE_REGIME_FISCALE`

**Descrizione**: Codice regime fiscale

**Tipo**: String

**Default**: `RF19`

**Valori comuni**:
```env
# Regime forfettario (flat tax 5-15%)
CEDENTE_REGIME_FISCALE=RF19

# Regime ordinario
CEDENTE_REGIME_FISCALE=RF01

# Regime dei minimi
CEDENTE_REGIME_FISCALE=RF02
```

**Codici completi**:
| Codice | Descrizione |
|--------|-------------|
| RF01 | Ordinario |
| RF02 | Contribuenti minimi |
| RF04 | Agricoltura e attività connesse |
| RF05 | Vendita sali e tabacchi |
| RF06 | Commercio fiammiferi |
| RF07 | Editoria |
| RF08 | Gestione servizi telefonia pubblica |
| RF09 | Rivendita documenti di trasporto |
| RF10 | Intrattenimenti/spettacoli/giochi |
| RF11 | Agenzie viaggi e turismo |
| RF12 | Agriturismo |
| RF13 | Vendite a domicilio |
| RF14 | Rivendita beni usati/oggetti arte |
| RF15 | Agenzie vendite all'asta |
| RF16 | IVA per cassa P.A. |
| RF17 | IVA per cassa altri |
| RF18 | Altro |
| RF19 | **Forfettario** (più comune) |

---

### `CEDENTE_INDIRIZZO`

**Descrizione**: Indirizzo completo (via e numero civico)

**Tipo**: String

**Required**: ✅ Obbligatorio

**Esempio**:
```env
CEDENTE_INDIRIZZO=Via Giuseppe Garibaldi 42
```

---

### `CEDENTE_CAP`

**Descrizione**: Codice di Avviamento Postale

**Tipo**: String (5 cifre)

**Required**: ✅ Obbligatorio

**Esempio**:
```env
CEDENTE_CAP=00100
```

---

### `CEDENTE_COMUNE`

**Descrizione**: Nome del comune

**Tipo**: String

**Required**: ✅ Obbligatorio

**Esempio**:
```env
CEDENTE_COMUNE=Roma
```

**Note**:
- Deve corrispondere al comune ufficiale
- Usare il nome completo (es. "Reggio Emilia", non "Reggio E.")

---

### `CEDENTE_PROVINCIA`

**Descrizione**: Sigla provincia (2 caratteri)

**Tipo**: String (2 caratteri)

**Required**: ✅ Obbligatorio

**Esempio**:
```env
CEDENTE_PROVINCIA=RM
```

**Province comuni**:
- RM = Roma
- MI = Milano
- TO = Torino
- NA = Napoli
- FI = Firenze
- BO = Bologna

[Lista completa province italiane](https://it.wikipedia.org/wiki/Province_d%27Italia)

---

### `CEDENTE_NAZIONE`

**Descrizione**: Codice nazione ISO 3166-1 alpha-2

**Tipo**: String (2 caratteri)

**Default**: `IT`

**Esempio**:
```env
CEDENTE_NAZIONE=IT
```

**Note**:
- Quasi sempre `IT` per utenti italiani
- Altri codici solo per società estere

---

### `CEDENTE_TELEFONO`

**Descrizione**: Numero di telefono (opzionale)

**Tipo**: String (opzionale)

**Default**: None

**Esempio**:
```env
CEDENTE_TELEFONO=+39 06 12345678
CEDENTE_TELEFONO=06 12345678
CEDENTE_TELEFONO=3331234567
```

**Note**:
- Formato libero (con o senza prefisso)
- Raccomandato per comunicazioni con clienti

---

### `CEDENTE_EMAIL`

**Descrizione**: Email aziendale (opzionale)

**Tipo**: String (opzionale)

**Default**: None

**Esempio**:
```env
CEDENTE_EMAIL=info@tuaazienda.it
```

**Note**:
- Diversa dalla PEC
- Usata per comunicazioni generiche
- Può apparire sulle fatture

---

## Configurazione PEC

La PEC (Posta Elettronica Certificata) è necessaria per inviare fatture al SDI.

### `PEC_ADDRESS`

**Descrizione**: Tuo indirizzo PEC

**Tipo**: String (email)

**Required**: ✅ Obbligatorio (per invio fatture)

**Esempio**:
```env
PEC_ADDRESS=tuaazienda@pec.it
```

**Note**:
- Deve essere una PEC valida e attiva
- Usata come mittente per invio SDI
- Verifica che sia ancora attiva

---

### `PEC_PASSWORD`

**Descrizione**: Password della PEC

**Tipo**: String

**Required**: ✅ Obbligatorio (per invio fatture)

**Esempio**:
```env
PEC_PASSWORD=la_tua_password_sicura
```

**Sicurezza**:
- ⚠️ NON committare il file `.env` su Git!
- Usa password forte
- Cambia regolarmente
- Considera variabili d'ambiente per produzione

---

### `PEC_SMTP_SERVER`

**Descrizione**: Server SMTP del provider PEC

**Tipo**: String (hostname)

**Default**: `smtp.pec.it`

**Provider comuni**:
```env
# Aruba
PEC_SMTP_SERVER=smtp.pec.aruba.it

# Register
PEC_SMTP_SERVER=smtps.pec.register.it

# Legalmail
PEC_SMTP_SERVER=smtp.legalmail.it

# PosteCert
PEC_SMTP_SERVER=smtp.postecert.it

# InfoCert
PEC_SMTP_SERVER=smtp.pec.infocert.it

# Actalis
PEC_SMTP_SERVER=smtp.pec.actalis.it
```

**Note**:
- Varia per provider
- Controlla documentazione del tuo provider
- Solitamente usa SSL/TLS sulla porta 465

---

### `PEC_SMTP_PORT`

**Descrizione**: Porta SMTP

**Tipo**: Integer

**Default**: `465`

**Valori comuni**:
```env
# SSL/TLS (raccomandato)
PEC_SMTP_PORT=465

# STARTTLS (meno comune per PEC)
PEC_SMTP_PORT=587
```

**Note**:
- Porta 465 è la più comune per PEC
- Usa sempre connessione cifrata

---

### `SDI_PEC_ADDRESS`

**Descrizione**: Indirizzo PEC del Sistema di Interscambio

**Tipo**: String (email)

**Default**: `sdi01@pec.fatturapa.it`

**Esempio**:
```env
SDI_PEC_ADDRESS=sdi01@pec.fatturapa.it
```

**Note**:
- Questo è l'indirizzo ufficiale del SDI
- Raramente cambia
- Non modificare a meno che non sia esplicitamente richiesto

---

## Email Templates & Branding

Configurazione per personalizzare le email automatiche.

### `EMAIL_LOGO_URL`

**Descrizione**: URL del logo aziendale per email

**Tipo**: String (URL, opzionale)

**Default**: None

**Esempio**:
```env
EMAIL_LOGO_URL=https://tuosito.com/logo.png
```

**Requisiti immagine**:
- Formato: PNG, JPG, SVG
- Dimensione raccomandata: 200x60px
- Sfondo trasparente (PNG)
- Hosting pubblico (HTTPS)

**Note**:
- Se non specificato, usa solo testo
- Migliora il branding delle email
- Testalo con `preview()` prima

---

### `EMAIL_PRIMARY_COLOR`

**Descrizione**: Colore primario per template email

**Tipo**: String (colore hex)

**Default**: `#1976D2` (blu Material Design)

**Esempio**:
```env
EMAIL_PRIMARY_COLOR=#1976D2  # Blu
EMAIL_PRIMARY_COLOR=#4CAF50  # Verde
EMAIL_PRIMARY_COLOR=#FF5722  # Arancione
```

**Note**:
- Formato: `#RRGGBB` (hex)
- Usato per intestazioni, pulsanti, badge
- Mantieni buon contrasto con bianco/nero

---

### `EMAIL_SECONDARY_COLOR`

**Descrizione**: Colore secondario per template email

**Tipo**: String (colore hex)

**Default**: `#424242` (grigio scuro)

**Esempio**:
```env
EMAIL_SECONDARY_COLOR=#424242  # Grigio scuro
EMAIL_SECONDARY_COLOR=#212121  # Nero
```

**Note**:
- Usato per testo secondario, footer
- Deve avere buon contrasto con sfondo

---

### `EMAIL_FOOTER_TEXT`

**Descrizione**: Testo personalizzato nel footer email

**Tipo**: String (opzionale)

**Default**: None (usa dati cedente)

**Esempio**:
```env
EMAIL_FOOTER_TEXT=© 2025 Acme SRL - P.IVA 12345678901 - Tutti i diritti riservati
```

**Note**:
- Supporta testo semplice (no HTML)
- Apparirà in tutte le email
- Se non specificato, usa automaticamente dati cedente

---

### `NOTIFICATION_EMAIL`

**Descrizione**: Email per notifiche automatiche SDI

**Tipo**: String (email)

**Required**: ✅ Obbligatorio (per email features)

**Esempio**:
```env
NOTIFICATION_EMAIL=admin@tuaazienda.it
```

**Riceve notifiche per**:
- Attestazioni trasmissione SDI (AT)
- Ricevute consegna (RC)
- Notifiche scarto (NS)
- Mancate consegne (MC)
- Esiti cliente (NE)
- Riepiloghi batch operations
- Test PEC

**Note**:
- Può essere diversa dalla PEC
- Controlla questa casella quotidianamente
- Può essere una mailing list

---

### `NOTIFICATION_ENABLED`

**Descrizione**: Abilita/disabilita notifiche email

**Tipo**: Boolean

**Default**: `true`

**Esempio**:
```env
NOTIFICATION_ENABLED=true   # Abilita notifiche
NOTIFICATION_ENABLED=false  # Disabilita notifiche
```

**Note**:
- Utile per disabilitare temporaneamente
- Le notifiche vengono comunque processate (solo non inviate via email)
- In produzione, mantieni sempre `true`

---

### `LOCALE`

**Descrizione**: Lingua per email e UI

**Tipo**: String

**Default**: `it`

**Valori supportati**:
```env
LOCALE=it  # Italiano
LOCALE=en  # English
```

**Note**:
- Cambia lingua di tutte le email
- I18n completo per IT e EN
- Aggiungere altre lingue modificando `i18n/*.json`

---

## Firma Digitale

Configurazione opzionale per firmare digitalmente le fatture XML.

### `SIGNATURE_CERTIFICATE_PATH`

**Descrizione**: Percorso al certificato di firma digitale

**Tipo**: Path (opzionale)

**Default**: None

**Esempio**:
```env
SIGNATURE_CERTIFICATE_PATH=/path/to/certificate.p12
SIGNATURE_CERTIFICATE_PATH=/home/user/.openfatture/cert.pfx
```

**Formati supportati**:
- `.p12` / `.pfx` - PKCS#12 (più comune)
- `.pem` - PEM format

**Note**:
- Opzionale ma fortemente raccomandato
- Riduce rischio di scarto SDI
- Aumenta valore legale della fattura

---

### `SIGNATURE_CERTIFICATE_PASSWORD`

**Descrizione**: Password del certificato

**Tipo**: String (opzionale)

**Default**: None

**Esempio**:
```env
SIGNATURE_CERTIFICATE_PASSWORD=password_certificato
```

**Sicurezza**:
- ⚠️ MAI committare su Git!
- Usa password forte
- Considera vault per produzione

---

## Configurazione AI

Opzionale: abilita funzionalità AI/LLM per suggerimenti intelligenti.

### `AI_PROVIDER`

**Descrizione**: Provider LLM

**Tipo**: String

**Default**: `openai`

**Valori supportati**:
```env
AI_PROVIDER=openai     # OpenAI (GPT-4, GPT-3.5)
AI_PROVIDER=anthropic  # Anthropic (Claude)
AI_PROVIDER=ollama     # Ollama (modelli locali)
```

---

### `AI_MODEL`

**Descrizione**: Nome modello LLM

**Tipo**: String

**Default**: `gpt-4-turbo-preview`

**Esempi**:
```env
# OpenAI
AI_MODEL=gpt-4-turbo-preview
AI_MODEL=gpt-3.5-turbo

# Anthropic
AI_MODEL=claude-3-5-sonnet-20241022
AI_MODEL=claude-3-opus-20240229

# Ollama (locale)
AI_MODEL=llama3
AI_MODEL=mistral
```

---

### `AI_API_KEY`

**Descrizione**: API key del provider

**Tipo**: String (opzionale)

**Default**: None

**Esempio**:
```env
# OpenAI
AI_API_KEY=sk-proj-...

# Anthropic
AI_API_KEY=sk-ant-...
```

**Note**:
- Non necessaria per Ollama (locale)
- ⚠️ MAI committare su Git!

---

### `AI_BASE_URL`

**Descrizione**: URL base API (per modelli locali)

**Tipo**: String (URL, opzionale)

**Default**: None

**Esempio**:
```env
# Ollama locale
AI_BASE_URL=http://localhost:11434

# OpenAI proxy
AI_BASE_URL=https://api.openai-proxy.com/v1
```

---

### `AI_TEMPERATURE`

**Descrizione**: Temperatura LLM (creatività)

**Tipo**: Float (0.0 - 2.0)

**Default**: `0.7`

**Esempio**:
```env
AI_TEMPERATURE=0.0  # Deterministico
AI_TEMPERATURE=0.7  # Bilanciato
AI_TEMPERATURE=1.5  # Creativo
```

---

### `AI_MAX_TOKENS`

**Descrizione**: Lunghezza massima risposta

**Tipo**: Integer

**Default**: `2000`

**Esempio**:
```env
AI_MAX_TOKENS=1000   # Risposte brevi
AI_MAX_TOKENS=4000   # Risposte lunghe
```

---

## Paths & Directories

Configurazione opzionale delle directory di lavoro.

### `DATA_DIR`

**Descrizione**: Directory dati applicazione

**Tipo**: Path

**Default**: `~/.openfatture/data`

**Esempio**:
```env
DATA_DIR=/var/lib/openfatture/data
```

---

### `ARCHIVIO_DIR`

**Descrizione**: Directory archivio fatture (XML, PDF)

**Tipo**: Path

**Default**: `~/.openfatture/archivio`

**Esempio**:
```env
ARCHIVIO_DIR=/mnt/storage/fatture
```

**Note**:
- Conserva per 10 anni (obbligo di legge)
- Backup regolare raccomandato

---

### `CERTIFICATES_DIR`

**Descrizione**: Directory certificati

**Tipo**: Path

**Default**: `~/.openfatture/certificates`

**Esempio**:
```env
CERTIFICATES_DIR=/etc/openfatture/certs
```

---

## Best Practices

### Sicurezza

1. **NON committare `.env` su Git**
   ```bash
   echo ".env" >> .gitignore
   ```

2. **Usa variabili d'ambiente in produzione**
   ```bash
   export PEC_PASSWORD=secret
   ```

3. **Ruota password regolarmente**

4. **Usa certificati firma digitale**

### Performance

1. **PostgreSQL per produzione**
   ```env
   DATABASE_URL=postgresql://...
   ```

2. **Cache AI responses** (implementazione futura)

### Backup

1. **Database regolare**
   ```bash
   cp openfatture.db backup_$(date +%Y%m%d).db
   ```

2. **Archivio fatture** (obbligatorio 10 anni)

---

## Troubleshooting

### Verificare Configurazione

```bash
uv run python -c "
from openfatture.utils.config import get_settings
s = get_settings()

print('=== CONFIGURAZIONE ===')
print(f'Cedente: {s.cedente_denominazione}')
print(f'P.IVA: {s.cedente_partita_iva}')
print(f'PEC: {s.pec_address}')
print(f'SMTP: {s.pec_smtp_server}:{s.pec_smtp_port}')
print(f'Notifiche: {s.notification_email}')
print(f'Database: {s.database_url}')
print(f'Locale: {s.locale}')
"
```

### Testare PEC

```bash
uv run python -c "
from openfatture.utils.config import get_settings
from openfatture.utils.email.sender import TemplatePECSender

sender = TemplatePECSender(settings=get_settings())
success, error = sender.send_test_email()

if success:
    print('✅ PEC OK')
else:
    print(f'❌ ERROR: {error}')
"
```

---

## Riferimenti

- [FatturaPA Specifiche Tecniche](https://www.fatturapa.gov.it/it/norme-e-regole/documentazione-fattura-elettronica/formato-fatturapa/)
- [SDI - Sistema di Interscambio](https://www.fatturapa.gov.it/it/sdi/)
- [Codici Regime Fiscale](https://www.agenziaentrate.gov.it/)
