# Tax Advisor - Guida Rapida

Il **Tax Advisor** è un agente AI che suggerisce automaticamente il corretto trattamento fiscale IVA per servizi e prodotti secondo la normativa italiana FatturaPA.

## Caratteristiche

- 🧾 **Regole Fiscali Italiane**: Conosce DPR 633/72 e normativa vigente
- 📊 **Aliquote Complete**: 22%, 10%, 5%, 4%, 0% + codici natura
- 🔄 **Reverse Charge**: Rileva automaticamente inversione contabile
- 🏛️ **Split Payment**: Gestisce fatture verso PA
- 📜 **Riferimenti Normativi**: Fornisce articoli di legge precisi
- ✅ **Output Strutturato**: JSON validato con Pydantic
- 💰 **Cost Tracking**: Monitoraggio costi e token

## Quick Start

### 1. Installazione

Il Tax Advisor è incluso nel modulo AI di OpenFatture:

```bash
uv pip install openfatture
```

### 2. Configurazione

Imposta provider e API key:

```bash
# OpenAI (GPT-5)
export OPENFATTURE_AI_PROVIDER=openai
export OPENFATTURE_AI_OPENAI_API_KEY=sk-...

# Anthropic (Claude 4.5)
export OPENFATTURE_AI_PROVIDER=anthropic
export OPENFATTURE_AI_ANTHROPIC_API_KEY=sk-ant-...

# Ollama (Locale, gratuito)
export OPENFATTURE_AI_PROVIDER=ollama
```

### 3. Uso CLI

```bash
# Suggerimento base
openfatture ai suggest-vat "consulenza IT"

# Con cliente PA (split payment)
openfatture ai suggest-vat "consulenza IT" --pa

# Con cliente estero
openfatture ai suggest-vat "consulenza" --estero --paese US

# Con dettagli
openfatture ai suggest-vat "servizi pulizia cantiere" \
  --categoria "Edilizia" \
  --importo 5000

# Output JSON per scripting
openfatture ai suggest-vat "formazione" --json
```

### 4. Uso Programmatico

```python
import asyncio
from openfatture.ai.agents.tax_advisor import TaxAdvisorAgent
from openfatture.ai.domain.context import TaxContext
from openfatture.ai.providers.factory import create_provider

async def suggest_vat():
    # Crea provider (usa config da env)
    provider = create_provider()

    # Crea agent
    agent = TaxAdvisorAgent(provider=provider)

    # Crea context
    context = TaxContext(
        user_input="consulenza IT per azienda edile",
        tipo_servizio="consulenza IT per azienda edile",
        importo=5000.0
    )

    # Esegui
    response = await agent.execute(context)

    # Ottieni output strutturato
    if response.metadata.get("is_structured"):
        model = response.metadata["parsed_model"]
        print(f"Aliquota IVA: {model['aliquota_iva']}%")
        print(f"Reverse Charge: {model['reverse_charge']}")
        print(f"Spiegazione: {model['spiegazione']}")

asyncio.run(suggest_vat())
```

## Regole Fiscali Italiane

### Aliquote IVA

| Aliquota | Descrizione | Esempi |
|----------|-------------|--------|
| **22%** | Ordinaria (standard) | Consulenza, servizi IT, la maggior parte beni/servizi |
| **10%** | Ridotta | Alcuni alimenti, servizi turistici, edilizia prima casa |
| **5%** | Super-ridotta | Alimenti prima necessità sociali |
| **4%** | Minima | Libri, giornali, prodotti agricoli specifici |
| **0%** | Esente/Non imponibile | Formazione, sanità, export (vedi codici natura) |

### Codici Natura IVA (per aliquota 0%)

| Codice | Descrizione | Quando si usa |
|--------|-------------|---------------|
| **N1** | Escluse ex art.15 | Operazioni escluse dal campo IVA |
| **N2** | Non soggette | Fuori campo IVA |
| **N2.1** | Non soggette (art. 7-7septies) | Casi specifici territorialità |
| **N2.2** | Non soggette - altri casi | **Regime forfettario** |
| **N3** | Non imponibili | Export, intracomunitarie |
| **N3.1** | Non imponibili - esportazioni | **Export extra-UE** |
| **N3.2** | Non imponibili - intracomunitarie | Cessioni intra-UE con VIES |
| **N4** | Esenti | **Formazione, sanità, assicurazioni** |
| **N5** | Regime del margine | Beni usati, opere d'arte |
| **N6** | Reverse charge | **Inversione contabile** |
| **N6.7** | Reverse charge - edilizia | **Settore costruzioni** |
| **N7** | IVA assolta altro stato UE | Servizi UE con IVA estera |

### Reverse Charge (Inversione Contabile)

**Quando si applica:**
- ✅ Servizi nel settore **edilizia e costruzioni**
- ✅ **Subappalti** in edilizia (anche da non-edili)
- ✅ Servizi di pulizia, demolizione, installazione impianti per **edifici**
- ✅ Cessione **rottami, cascami** metalli
- ✅ Settore **energetico** (gas, elettricità)
- ✅ **Telecomunicazioni**, dispositivi elettronici

**Riferimento normativo:** Art. 17, comma 6, DPR 633/72

**Cosa fare:**
1. ❌ **NON addebitare IVA** in fattura
2. ✅ Indicare aliquota con **Natura N6.x**
3. ✅ Inserire **nota**: "Inversione contabile - art. 17 c. 6 lett. a-ter DPR 633/72"
4. ✅ Il **cliente** verserà l'IVA (autofattura)

### Split Payment (Scissione Pagamenti)

**Quando si applica:**
- ✅ Fatture emesse verso **Pubblica Amministrazione**
- ✅ Enti pubblici, Ministeri, Comuni, Regioni, ASL, Università statali

**Come funziona:**
1. ✅ Indicare IVA in fattura **normalmente** (es. 22%)
2. ✅ Aggiungere **nota**: "Scissione dei pagamenti - art. 17-ter DPR 633/72"
3. ✅ La PA paga solo l'**imponibile**
4. ✅ La PA versa l'IVA **direttamente all'Erario**

**Riferimento normativo:** Art. 17-ter, DPR 633/72

**Attenzione:** Non si applica a forfettari

### Regime Forfettario (RF19)

**Caratteristiche:**
- ❌ **No addebito IVA** (aliquota 0%, natura N2.2)
- ❌ No detrazione IVA sugli acquisti
- ✅ Applicabile solo con ricavi < 85.000€/anno
- ✅ Dicitura obbligatoria in fattura

**Nota da inserire:**
```
"Operazione senza applicazione dell'IVA ai sensi dell'art. 1, comma 58, L. 190/2014"
```

**Riferimento normativo:** Art. 1, commi 54-89, Legge 190/2014

## Esempi Pratici

### Esempio 1: Consulenza IT Standard

**Input:**
```bash
openfatture ai suggest-vat "consulenza IT"
```

**Output:**
```
📊 Trattamento Fiscale
├─ Aliquota IVA:    22%
├─ Reverse Charge:  ✗ NO
├─ Split Payment:   ✗ NO
└─ Confidence:      100%

📋 Spiegazione:
Le prestazioni di consulenza IT rientrano nel regime ordinario IVA.
Si applica l'aliquota standard del 22%.

📜 Riferimento normativo:
Art. 1, DPR 633/72 - Operazioni imponibili
```

### Esempio 2: Reverse Charge Edilizia

**Input:**
```bash
openfatture ai suggest-vat "consulenza IT per azienda edile"
```

**Output:**
```
📊 Trattamento Fiscale
├─ Aliquota IVA:    22%
├─ Natura IVA:      N6.7
├─ Reverse Charge:  ✓ SI
└─ Confidence:      95%

📋 Spiegazione:
Per servizi resi al settore edile e costruzioni si applica il reverse charge
(inversione contabile). Il fornitore non addebita l'IVA.

📜 Riferimento normativo:
Art. 17, comma 6, lettera a-ter, DPR 633/72

📝 Nota per fattura:
"Inversione contabile - art. 17 c. 6 lett. a-ter DPR 633/72"

💡 Raccomandazioni:
  • Verificare che il cliente operi nel settore edile
  • Non addebitare IVA in fattura
  • Il cliente verserà l'IVA in autofattura
```

### Esempio 3: Split Payment PA

**Input:**
```bash
openfatture ai suggest-vat "consulenza IT" --pa
```

**Output:**
```
📊 Trattamento Fiscale
├─ Aliquota IVA:    22%
├─ Split Payment:   ✓ SI
└─ Confidence:      100%

📋 Spiegazione:
Per servizi resi alla Pubblica Amministrazione si applica lo split payment.
L'IVA viene indicata in fattura ma sarà versata dalla PA all'Erario.

📝 Nota per fattura:
"Scissione dei pagamenti - art. 17-ter DPR 633/72"

💡 Raccomandazioni:
  • Indicare IVA in fattura normalmente
  • La PA verserà IVA all'Erario
  • Incassare solo l'imponibile
```

### Esempio 4: Formazione Esente

**Input:**
```bash
openfatture ai suggest-vat "corso di formazione professionale"
```

**Output:**
```
📊 Trattamento Fiscale
├─ Aliquota IVA:    0%
├─ Natura IVA:      N4
├─ Regime:          ESENTE
└─ Confidence:      90%

📋 Spiegazione:
Le prestazioni di formazione professionale sono esenti da IVA.

📜 Riferimento normativo:
Art. 10, comma 1, n. 20, DPR 633/72

📝 Nota per fattura:
"Operazione esente IVA ai sensi dell'art. 10, c. 1, n. 20, DPR 633/72"

💡 Raccomandazioni:
  • Verificare finalità educative riconosciute
  • Per corsi aziendali generici potrebbe applicarsi 22%
```

### Esempio 5: Export Extra-UE

**Input:**
```bash
openfatture ai suggest-vat "consulenza IT" --estero --paese US
```

**Output:**
```
📊 Trattamento Fiscale
├─ Aliquota IVA:    0%
├─ Natura IVA:      N3.1
├─ Regime:          EXPORT
└─ Confidence:      85%

📋 Spiegazione:
Le prestazioni verso clienti extra-UE sono non imponibili in Italia.

📜 Riferimento normativo:
Art. 7-ter, DPR 633/72 - Territorialità servizi

📝 Nota per fattura:
"Operazione non imponibile IVA - art. 7-ter DPR 633/72"

💡 Raccomandazioni:
  • Verificare residenza fiscale committente
  • Conservare documentazione attestante ubicazione
  • Per B2C (consumatori) regole diverse: verificare
```

## Casistiche Particolari

### Settore Edilizia

| Servizio | Reverse Charge | Codice Natura |
|----------|:--------------:|:-------------:|
| Consulenza IT per impresa edile | ✅ SI | N6.7 |
| Consulenza IT generica | ❌ NO | - |
| Pulizia cantiere edile | ✅ SI | N6.7 |
| Pulizia uffici | ❌ NO | - |
| Installazione impianti in edificio | ✅ SI | N6.7 |
| Manutenzione software | ❌ NO | - |

### Aliquote Ridotte

| Prodotto/Servizio | Aliquota | Riferimento |
|-------------------|:--------:|-------------|
| Libri (cartacei ed ebook) | 4% | Tab. A, parte II, n. 18 |
| Giornali e periodici | 4% | Tab. A, parte II, n. 18 |
| Alimenti prima necessità | 4-10% | Tab. A, parte II-III |
| Servizi turistici | 10% | Tab. A, parte III, n. 123 |
| Edilizia prima casa | 10% | DL 83/2012 |

## Configurazione Avanzata

### Custom Settings

```python
from openfatture.ai.config import AISettings
from openfatture.ai.providers.factory import create_provider

# Settings personalizzate
settings = AISettings(
    provider="anthropic",
    anthropic_model="claude-4.5-haiku",  # Più veloce
    temperature=0.1,  # Più deterministico
    max_tokens=600
)

provider = create_provider(settings=settings)
agent = TaxAdvisorAgent(provider=provider)
```

### Batch Processing

```python
async def analyze_batch(services):
    provider = create_provider()
    agent = TaxAdvisorAgent(provider=provider)

    results = []
    for service in services:
        context = TaxContext(
            tipo_servizio=service["tipo"],
            importo=service["importo"]
        )
        response = await agent.execute(context)
        results.append(response)

    return results

# Analizza 100 servizi
services = [{"tipo": "...", "importo": 1000} for _ in range(100)]
results = await analyze_batch(services)
```

## Troubleshooting

### Errore: "tipo_servizio è richiesto"

```bash
# ❌ Errato
openfatture ai suggest-vat ""

# ✅ Corretto
openfatture ai suggest-vat "consulenza IT"
```

### Confidence Bassa (<70%)

Se la confidence è bassa, il sistema raccomanda:
1. Verificare con commercialista
2. Fornire più dettagli (categoria, ATECO, cliente)
3. Consultare normativa specifica

```bash
# Fornire più contesto per aumentare confidence
openfatture ai suggest-vat "consulenza" \
  --categoria "IT e Software" \
  --ateco "62.01.00" \
  --importo 5000
```

### Risultati Inattesi

Se i suggerimenti sembrano incorretti:
1. ✅ Verificare descrizione servizio sia chiara
2. ✅ Specificare --pa se cliente è PA
3. ✅ Indicare --estero per clienti esteri
4. ✅ Verificare categoria ATECO

## Costi e Performance

### Costi per Richiesta

| Provider | Model | Costo Medio |
|----------|-------|-------------|
| OpenAI | GPT-5 | $0.008 |
| OpenAI | GPT-5-mini | $0.0006 |
| Anthropic | Claude 4.5 Sonnet | $0.006 |
| Anthropic | Claude 4.5 Haiku | $0.0008 |
| Ollama | Llama 3.2 | $0 (locale) |

### Performance

- **Latency media**: 400-600ms
- **Accuracy**: >95% per casi standard
- **Coverage**: Tutte aliquote e codici natura

## Integrazione con Fatturazione

```python
from openfatture.ai.agents.tax_advisor import TaxAdvisorAgent
from openfatture.ai.domain.context import TaxContext
from openfatture.ai.providers.factory import create_provider
from openfatture.core.fatture.service import FatturaService

async def create_invoice_with_tax_suggestion():
    # Suggerisci trattamento fiscale
    provider = create_provider()
    tax_agent = TaxAdvisorAgent(provider=provider)

    context = TaxContext(
        tipo_servizio="consulenza IT",
        importo=5000.0,
        cliente_pa=True
    )

    tax_response = await tax_agent.execute(context)
    tax_model = tax_response.metadata["parsed_model"]

    # Crea fattura con suggerimento
    fattura_service = FatturaService(session)
    fattura = fattura_service.crea_fattura(
        cliente_id=1,
        descrizione="Consulenza IT",
        quantita=1,
        prezzo_unitario=5000.0,
        aliquota_iva=tax_model["aliquota_iva"],
        note=tax_model.get("note_fattura")
    )

    print(f"Fattura creata: {fattura.numero}")
    print(f"IVA applicata: {tax_model['aliquota_iva']}%")
```

## Limitazioni

⚠️ **IMPORTANTE:**
- Il Tax Advisor fornisce **suggerimenti** basati su AI
- **NON sostituisce** il parere di un commercialista
- Per casistiche complesse, **consultare sempre** un professionista
- Verificare sempre i **riferimenti normativi** forniti
- Normativa fiscale può **cambiare**: mantenere aggiornato

## Prossimi Passi

- 📖 Leggi [AI Architecture](../docs/AI_ARCHITECTURE.md)
- 🧪 Esegui [esempi](ai_tax_advisor.py)
- 🤝 Contribuisci: [GitHub](https://github.com/venerelabs/openfatture)

## Supporto

- 📚 Documentazione: [docs/](../docs/)
- 💬 Issues: [GitHub Issues](https://github.com/venerelabs/openfatture/issues)
- 📧 Email: support@openfatture.dev

---

**Last Updated**: October 2025
**OpenFatture Version**: 0.1.0
**AI Module**: Phase 4.3 - Tax Advisor
