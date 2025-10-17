# Lightning Network - Guida Compliance Italia 🇮🇹

**Versione:** 1.0 | **Data:** Gennaio 2025 | **Normativa:** Legge di Bilancio 2023-2025

---

## Indice

1. [Introduzione](#introduzione)
2. [Quadro Normativo Italiano](#quadro-normativo-italiano)
3. [Tassazione delle Criptovalute in Italia](#tassazione-delle-criptovalute-in-italia)
4. [Anti-Money Laundering (AML)](#anti-money-laundering-aml)
5. [Quadro RW - Dichiarazione Crypto](#quadro-rw---dichiarazione-crypto)
6. [Comandi CLI per Compliance](#comandi-cli-per-compliance)
7. [Workflow Compliance Completo](#workflow-compliance-completo)
8. [Best Practices](#best-practices)
9. [FAQ](#faq)
10. [Risorse Utili](#risorse-utili)

---

## Introduzione

OpenFatture integra strumenti di compliance automatica per **pagamenti Lightning Network**, conformi alla normativa fiscale italiana 2025. Questa guida spiega:

- Come funziona la tassazione crypto in Italia (capital gains, Quadro RW)
- Obblighi Anti-Money Laundering (AML) per pagamenti sopra soglia
- Comandi CLI per generare report fiscali per commercialisti
- Best practices per rimanere conformi

> **⚠️ DISCLAIMER:** Questa guida ha scopo informativo. Per consulenza fiscale personalizzata, rivolgersi a un commercialista o consulente fiscale certificato.

---

## Quadro Normativo Italiano

### Legge di Bilancio 2023-2025 (Art. 67, c. 1-ter del TUIR)

**Principali novità:**

1. **Capital Gains Tax:** 26% nel 2025, 33% dal 2026 in poi
2. **Eliminazione soglia 2.000 EUR:** Ogni capital gain è tassabile (prima solo sopra 2.000 EUR)
3. **Quadro RW obbligatorio:** Dichiarazione crypto obbligatoria per tutti i possessori
4. **AML Threshold:** 5.000 EUR (D.Lgs. 231/2007) - Identificazione cliente obbligatoria

### Definizioni

- **Capital Gain/Loss:** Differenza tra prezzo di vendita e costo di acquisto del BTC
- **Costo di acquisto:** Prezzo pagato per acquisire i BTC (se tracciabile)
- **Quadro RW:** Sezione della dichiarazione dei redditi per investimenti/attività estere (include crypto)
- **AML (Anti-Money Laundering):** Normativa anti-riciclaggio

---

## Tassazione delle Criptovalute in Italia

### Come Funziona

Quando ricevi un pagamento Lightning per una fattura:

1. **Vendi BTC per EUR:** Il pagamento in BTC viene convertito in EUR al tasso di cambio attuale
2. **Capital Gain = EUR ricevuti - Costo di acquisto BTC** (se applicabile)
3. **Imposta = Capital Gain × 26% (o 33% dal 2026)**

### Esempio Pratico

```
Scenario:
- Fattura: 1.000 EUR
- Tasso BTC/EUR: 50.000 EUR/BTC
- BTC ricevuti: 0.02 BTC
- Costo di acquisto BTC: 800 EUR (se hai comprato i BTC in precedenza)

Capital Gain:
1.000 EUR (valore attuale) - 800 EUR (costo acquisto) = 200 EUR

Imposta dovuta (2025):
200 EUR × 26% = 52 EUR
```

### Aliquote per Anno

| Anno | Aliquota Capital Gains |
|------|------------------------|
| 2023 | 26% |
| 2024 | 26% |
| 2025 | 26% |
| 2026+ | **33%** |

---

## Anti-Money Laundering (AML)

### Soglia AML: 5.000 EUR

**Normativa:** D.Lgs. 231/2007 (Decreto Antiriciclaggio)

Se ricevi un pagamento Lightning **≥ 5.000 EUR**, devi:

1. **Identificare il cliente** (KYC - Know Your Customer)
2. **Conservare i documenti** (copia documento identità, proof of address)
3. **Registrare la verifica** nel sistema OpenFatture

### Procedura AML OpenFatture

```bash
# 1. Lista pagamenti non verificati
openfatture lightning aml list-unverified --threshold 5000

# 2. Verifica manuale cliente
openfatture lightning aml verify abc123... \
  --verified-by compliance@example.com \
  --notes "Documento identità verificato" \
  --client-id 42
```

### Sanzioni per Non Conformità

- Multe da **2.500 EUR a 50.000 EUR** per violazioni AML
- Sospensione attività fino a 2 anni (casi gravi)
- Segnalazione all'UIF (Unità di Informazione Finanziaria)

---

## Quadro RW - Dichiarazione Crypto

### Cos'è il Quadro RW?

Sezione del Modello Redditi (ex Unico) dove dichiarare:

- Investimenti esteri
- Conti correnti esteri
- **Criptovalute** (dal 2023)

### Obbligatorietà

- **Dal 2025:** Quadro RW obbligatorio per **tutti** i possessori di crypto, anche senza capital gains
- **Prima del 2025:** Obbligatorio solo se possesso > 51.645,69 EUR per 7 giorni lavorativi consecutivi

### Come Compilare con OpenFatture

```bash
# Genera report Quadro RW per anno fiscale
openfatture lightning report quadro-rw \
  --tax-year 2025 \
  --format csv \
  --output quadro_rw_2025.csv
```

Il file CSV contiene:

- Data operazione (settled_at)
- Importo BTC (amount_msat convertito)
- Importo EUR (eur_amount_declared)
- Codice fiscale/P.IVA cliente (se disponibile)
- Capital gain/loss (capital_gain_eur)

Fornisci questo file al tuo commercialista per la compilazione del Quadro RW.

---

## Comandi CLI per Compliance

### Compliance Check Generale

Verifica compliance completa per anno fiscale:

```bash
openfatture lightning compliance-check --tax-year 2025
```

**Output:**

```
🔍 Lightning Compliance Check - 2025

📊 Tax Year Summary
  Number of payments:         12
  Total revenue (EUR):        15,000.00 €
  Total capital gains (EUR):  2,500.00 €
  Estimated tax owed (EUR):   650.00 €

🛡️ AML Compliance (Threshold: 5,000 EUR)
  Total over threshold:       2
  Verified:                   1
  Unverified:                 ⚠️ 1 REQUIRE VERIFICATION

📋 Quadro RW Declaration (Mandatory from 2025)
  Invoices requiring declaration: 12
  Action required:            ⚠️ Declare all crypto holdings in Quadro RW

⚠️ Data Quality
  Invoices with missing tax data: 0
  Status:                     ✅ All settled invoices have tax data

❌ Compliance Issues Found: 1 unverified AML payment(s)
```

**Con dettagli verbose:**

```bash
openfatture lightning compliance-check --tax-year 2025 --verbose
```

---

### Report Quadro RW

Genera report per dichiarazione Quadro RW:

```bash
# CSV per commercialista
openfatture lightning report quadro-rw \
  --tax-year 2025 \
  --format csv \
  --output quadro_rw_2025.csv

# JSON per elaborazione automatica
openfatture lightning report quadro-rw \
  --tax-year 2025 \
  --format json
```

---

### Report Capital Gains

Genera report capital gains dettagliato:

```bash
# CSV
openfatture lightning report capital-gains \
  --tax-year 2025 \
  --format csv \
  --output capital_gains_2025.csv

# JSON
openfatture lightning report capital-gains \
  --tax-year 2025 \
  --format json
```

**Output:**

```csv
payment_hash,settled_at,btc_amount,eur_amount,btc_eur_rate,acquisition_cost_eur,capital_gain_eur,tax_rate,tax_owed_eur
abc123...,2025-03-15 10:30:00,0.02,1000.00,50000.00,800.00,200.00,0.26,52.00
def456...,2025-06-20 14:45:00,0.01,500.00,50000.00,400.00,100.00,0.26,26.00
...
```

---

### Report AML

Genera report conformità AML:

```bash
openfatture lightning report aml \
  --threshold 5000 \
  --output aml_compliance_2025.json
```

**Output JSON:**

```json
{
  "threshold_eur": 5000.0,
  "total_over_threshold": 2,
  "verified_count": 1,
  "unverified_count": 1,
  "compliance_rate": 50.0,
  "generated_at": "2025-10-17T12:00:00Z",
  "payments_over_threshold": [
    {
      "payment_hash": "abc123...",
      "amount_eur": 6000.0,
      "settled_at": "2025-06-15T10:30:00Z",
      "verified": false,
      "verification_date": null,
      "client_id": 42,
      "fattura_id": 101
    }
  ]
}
```

---

### Gestione AML

#### Lista Pagamenti Non Verificati

```bash
openfatture lightning aml list-unverified --threshold 5000
```

**Output:**

```
Unverified Payments (1 total)
┌──────────────┬─────────────┬────────────────┬────────────┐
│ Payment Hash │ Amount (EUR)│ Settled At     │ Fattura ID │
├──────────────┼─────────────┼────────────────┼────────────┤
│ abc123...    │  6,000.00 € │ 2025-06-15 ... │ 101        │
└──────────────┴─────────────┴────────────────┴────────────┘

⚠️ Action Required: These payments require client identity verification
Use: openfatture lightning aml verify <payment-hash> --verified-by <email>
```

#### Verifica Pagamento AML

```bash
openfatture lightning aml verify abc123... \
  --verified-by compliance@example.com \
  --notes "Documento identità verificato - Carta d'identità n. 12345" \
  --client-id 42
```

**Output:**

```
✅ Verifying AML Payment: abc123...

✅ Payment verified successfully

Payment Hash:  abc123...
Amount (EUR):  6,000.00 €
Settled At:    2025-06-15 10:30
Verified By:   compliance@example.com
Verified At:   2025-10-17 12:00
Notes:         Documento identità verificato - Carta d'identità n. 12345
```

---

## Workflow Compliance Completo

### Step 1: Ricezione Pagamento Lightning

Quando un pagamento Lightning viene ricevuto:

1. OpenFatture registra automaticamente:
   - Tasso BTC/EUR al momento del settlement
   - Importo EUR dichiarato
   - Capital gain (se costo di acquisto BTC è noto)
   - Flag AML se importo ≥ 5.000 EUR

### Step 2: Verifica AML (se necessaria)

Se il pagamento supera 5.000 EUR:

```bash
# Lista pagamenti da verificare
openfatture lightning aml list-unverified

# Identifica cliente (offline - processo KYC manuale)
# - Raccogli copia documento identità
# - Raccogli proof of address
# - Conserva documenti per 10 anni

# Registra verifica
openfatture lightning aml verify <payment_hash> \
  --verified-by compliance@example.com \
  --notes "KYC completato - Documento XYZ" \
  --client-id <id_cliente>
```

### Step 3: Check Compliance Periodico

Esegui check mensile/trimestrale:

```bash
openfatture lightning compliance-check --tax-year 2025 --verbose
```

Risolvi eventuali problemi:

- Pagamenti AML non verificati → Verifica cliente
- Dati fiscali mancanti → Integra tasso BTC/EUR e costo acquisto

### Step 4: Fine Anno Fiscale

Prima della dichiarazione dei redditi (entro 30 settembre anno successivo):

```bash
# 1. Genera report Quadro RW
openfatture lightning report quadro-rw \
  --tax-year 2025 \
  --format csv \
  --output quadro_rw_2025.csv

# 2. Genera report capital gains
openfatture lightning report capital-gains \
  --tax-year 2025 \
  --format csv \
  --output capital_gains_2025.csv

# 3. Genera report AML per audit
openfatture lightning report aml \
  --output aml_compliance_2025.json
```

### Step 5: Consegna Report al Commercialista

Fornisci al commercialista:

- `quadro_rw_2025.csv` - Per compilazione Quadro RW
- `capital_gains_2025.csv` - Per calcolo imposte capital gains
- `aml_compliance_2025.json` - Per audit trail (opzionale)

---

## Best Practices

### 1. Registra Sempre il Costo di Acquisto BTC

Se hai comprato BTC in precedenza, registra il costo di acquisto per calcolare capital gains accurati:

```python
# Durante creazione invoice Lightning
invoice_service.create_invoice_from_fattura(
    fattura_id=123,
    totale_eur=Decimal("1000.00"),
    descrizione="Consulenza IT",
    cliente_nome="Acme Corp",
    acquisition_cost_eur=Decimal("800.00")  # ⬅️ IMPORTANTE
)
```

### 2. Verifica AML Tempestivamente

Non aspettare la fine dell'anno. Verifica clienti sopra soglia immediatamente dopo il pagamento:

```bash
# Check giornaliero
openfatture lightning aml list-unverified
```

### 3. Backup Report Fiscali

Conserva tutti i report per almeno **10 anni** (obbligo normativo):

```bash
mkdir -p ~/openfatture_compliance/2025
openfatture lightning report quadro-rw --tax-year 2025 \
  --format csv --output ~/openfatture_compliance/2025/quadro_rw.csv
```

### 4. Automatizza Check Compliance

Aggiungi al cron/scheduler:

```bash
# Ogni lunedì mattina
0 9 * * 1 /usr/local/bin/openfatture lightning compliance-check --tax-year $(date +%Y)
```

### 5. Documenta Tutto

Per ogni pagamento AML, conserva:

- Copia documento identità
- Proof of address (bolletta, estratto conto)
- Note sulla verifica
- Data e ora della verifica

---

## FAQ

### 1. Devo dichiarare anche se ho solo ricevuto pagamenti Lightning senza capital gains?

**Sì.** Dal 2025, il Quadro RW è obbligatorio per **tutti** i possessori di crypto, anche senza capital gains.

### 2. Come calcolo il costo di acquisto BTC se li ho comprati anni fa?

Usa il prezzo pagato all'epoca (consult exchange records, bank statements). Se non hai tracciabilità, potrebbe essere considerato costo zero (tassazione su tutto l'importo).

### 3. I pagamenti Lightning sotto 5.000 EUR richiedono verifica AML?

**No.** Solo pagamenti ≥ 5.000 EUR richiedono identificazione cliente. Tuttavia, conserva sempre i dati del cliente (nome, P.IVA) per audit.

### 4. Cosa succede se non verifico un pagamento AML?

Rischio di sanzioni da **2.500 EUR a 50.000 EUR** per violazione normativa antiriciclaggio.

### 5. Posso usare OpenFatture per altre criptovalute (non solo Lightning)?

Attualmente OpenFatture supporta solo Lightning Network (Bitcoin Layer 2). Per altre crypto, consulta il commercialista.

### 6. Dove trovo il tasso BTC/EUR utilizzato per il calcolo?

OpenFatture registra automaticamente il tasso BTC/EUR al momento del settlement usando CoinGecko o CoinMarketCap. Vedi:

```bash
# In report capital gains
openfatture lightning report capital-gains --tax-year 2025 --format csv
# Colonna: btc_eur_rate
```

### 7. Come gestisco pagamenti parziali in Lightning?

Ogni settlement Lightning è registrato separatamente. Se una fattura riceve più pagamenti Lightning, ciascuno avrà il proprio record con tasso BTC/EUR al momento del settlement.

### 8. Devo pagare imposta di bollo digitale (2 EUR) per fatture Lightning?

**Sì**, se la fattura è elettronica e supera 77,47 EUR (stesso obbligo di FatturaPA).

---

## Risorse Utili

### Documentazione Ufficiale

- **Agenzia delle Entrate - Criptovalute:** https://www.agenziaentrate.gov.it/
- **D.Lgs. 231/2007 (AML):** https://www.normattiva.it/
- **Legge di Bilancio 2023:** Art. 67, c. 1-ter del TUIR

### Strumenti OpenFatture

- **Guida Lightning Network:** `docs/LIGHTNING_NETWORK.md`
- **Troubleshooting:** `docs/LIGHTNING_TROUBLESHOOTING.md`
- **Architettura:** `docs/ARCHITECTURE_DIAGRAMS.md`

### Consulenza Professionale

Per consulenza fiscale personalizzata:

- **Commercialisti Certificati Bitcoin/Crypto:** Lista su https://bitcoin-italia.org/
- **Studio Legale Tributario:** Specializzato in crypto

### Comunità

- **Bitcoin Italia Forum:** https://bitcointalk.org/
- **Reddit /r/ItalyInformatica:** https://reddit.com/r/ItalyInformatica
- **Telegram Gruppo OpenFatture:** (in sviluppo)

---

## Changelog

- **v1.0 (Gennaio 2025):** Prima versione - Compliance Lightning Network per Italia

---

**🇮🇹 Fatto con ❤️ per freelance e PMI italiane**

Per domande o segnalazioni: https://github.com/venerelabs/openfatture/issues
