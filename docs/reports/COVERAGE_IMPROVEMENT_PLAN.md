# 🎯 Piano di Miglioramento Coverage - OpenFatture

**Data**: 2025-10-17 (Aggiornato con analisi dettagliata)
**Coverage Globale Attuale**: 47% (28,677 statements, 15,286 non coperti)
**Target Globale**: 80%+

---

## 📊 Analisi Moduli Prioritari - AGGIORNATA

### ✅ Moduli con Copertura Eccellente (NO action needed)

| Modulo | Statements | Coverage | Status |
|--------|-----------|----------|--------|
| **Event Analytics** | 118 | **96%** ✅ | 16 test esistenti, solo 5 linee mancanti |
| **SDI - XML Builder** | 150 | **99%** ✅ | 19 test esistenti, solo 1 linea mancante |
| **SDI - Notifiche Parser** | 131 | **88%** ✅ | 24 test esistenti, 16 linee mancanti |
| **SDI - Notifiche Processor** | 99 | **92%** ✅ | 29 test esistenti, 8 linee mancanti |

**Totale coverage già eccellente**: 498 statements con coverage 88-99%

### 🔴 Moduli con Coverage Critica (0% - Action Required)

| Modulo | Statements | Missing | Priority | Effort |
|--------|-----------|---------|----------|--------|
| **SDI - PEC Sender** | 101 | 101 | 🔴 CRITICA | 3-4 ore |
| **SDI - XSD Validator** | 60 | 60 | 🔴 CRITICA | 2-3 ore |
| **SDI - Digital Signature** | 64 | 64 | 🟡 MEDIA | 2-3 ore |
| **SDI - Certificate Manager** | 71 | 71 | 🟡 MEDIA | 2-3 ore |
| **SDI - Signature Verifier** | 68 | 68 | 🟡 MEDIA | 2-3 ore |

**Totale statements da coprire (0%)**: 364 statements (non 862!)

### Situazione Buona (88% Coverage)

| Modulo | Statements | Missing | Priority | Effort |
|--------|-----------|---------|----------|--------|
| **Core - Database Models** | 284 | 35 | 🟢 BASSA | 1-2 ore |

**Target**: Portare da 88% → 95%+

---

## 🎯 Strategia di Implementazione (Best Practices)

### ✅ **FASE 1: Event Analytics - COMPLETATA**

**Status**: ✅ 96% coverage già raggiunta con 16 test esistenti!
**File**: `tests/core/events/test_analytics.py` (327 linee)
**Azione**: Nessuna - modulo già in ottima forma

---

### **FASE 1 (NUOVA): SDI PEC Sender** (Priorità: CRITICA, Effort: 3-4 ore)

#### Obiettivo
- **Da**: 0% (101/101 statements mancanti)
- **A**: 85%+ (85+ statements coperti)

#### File da testare
- `openfatture/sdi/pec_sender/sender.py`

#### Test da creare
**File**: `tests/unit/test_pec_sender.py`

```python
# Test Structure (da implementare):
class TestPECSender:
    # Configuration validation
    def test_sender_initialization()
    def test_missing_pec_address_validation()
    def test_missing_pec_password_validation()

    # Rate limiting
    def test_rate_limiter_integration()
    def test_rate_limit_wait_time()
    def test_rate_limit_blocking()

    # Email sending (mocked SMTP)
    def test_send_invoice_success()
    def test_send_invoice_xml_not_found()
    def test_send_invoice_with_signature()
    def test_send_invoice_updates_status()

    # Retry logic
    def test_retry_on_transient_errors()
    def test_no_retry_on_auth_errors()
    def test_exponential_backoff()
    def test_max_retries_exceeded()

    # Email construction
    def test_create_email_body()
    def test_email_headers()
    def test_xml_attachment()

    # Test email
    def test_send_test_email_success()
    def test_send_test_email_failure()
```

#### Funzioni chiave da coprire
1. `send_invoice()` - Invio fattura con validazione
2. `_send_with_retry()` - Logica retry con backoff
3. `_create_email_body()` - Generazione corpo email
4. `send_test_email()` - Email di test configurazione
5. `create_log_entry()` - Creazione log SDI

**Stima**: 15-20 test, ~400 righe di codice
**Mocking necessario**: `smtplib.SMTP_SSL`, `time.sleep`, `RateLimiter`

---

### **FASE 2: SDI XSD Validator** (Priorità: CRITICA, Effort: 2-3 ore)

#### Obiettivo
- **Da**: 0% (60/60 statements mancanti)
- **A**: 85%+ (50+ statements coperti)

#### File da testare
- `openfatture/sdi/validator/xsd_validator.py`

#### Test da creare
**File**: `tests/unit/test_xsd_validator.py`

```python
# Test Structure (da implementare):
class TestFatturaPAValidator:
    # Schema loading
    def test_load_schema_success()
    def test_load_schema_file_not_found()
    def test_schema_singleton_pattern()

    # Validation
    def test_validate_valid_xml()
    def test_validate_invalid_xml()
    def test_validate_missing_required_fields()
    def test_validate_invalid_vat_format()
    def test_validate_invalid_date_format()

    # Error extraction
    def test_extract_validation_errors()
    def test_error_message_formatting()

    # Edge cases
    def test_validate_empty_xml()
    def test_validate_malformed_xml()
    def test_validate_wrong_namespace()
```

#### Funzioni chiave da coprire
1. `load_schema()` - Caricamento XSD schema v1.2
2. `validate()` - Validazione XML contro schema
3. `_extract_errors()` - Estrazione errori dettagliati
4. `get_schema_version()` - Verifica versione schema

**Stima**: 10-15 test, ~300 righe di codice
**File necessari**: Sample XML validi/invalidi, XSD schema FatturaPA v1.2

---

### **FASE 3: Digital Signature Suite** (Priorità: MEDIA, Effort: 4-6 ore)

#### Obiettivo
- **Da**: 0% (203 statements totali su 3 file)
- **A**: 80%+ (160+ statements coperti)

#### File da testare
- `openfatture/sdi/digital_signature/certificate_manager.py` (71 statements)
- `openfatture/sdi/digital_signature/signer.py` (64 statements)
- `openfatture/sdi/digital_signature/verifier.py` (68 statements)

#### Test da creare
**File**: `tests/unit/test_digital_signature.py`

```python
# Test Structure (da implementare):
class TestCertificateManager:
    # Certificate loading
    def test_load_pkcs12_certificate()
    def test_load_certificate_wrong_password()
    def test_load_certificate_file_not_found()
    def test_load_certificate_invalid_format()

    # Certificate validation
    def test_validate_certificate_valid()
    def test_validate_certificate_expired()
    def test_validate_certificate_not_yet_valid()
    def test_get_certificate_info()

class TestDigitalSigner:
    # Initialization
    def test_signer_with_certificate_path()
    def test_signer_with_certificate_manager()

    # Signing files
    def test_sign_file_success()
    def test_sign_file_enveloped_signature()
    def test_sign_file_detached_signature()
    def test_sign_file_invalid_certificate()
    def test_sign_file_not_found()

    # Signing data
    def test_sign_data_in_memory()
    def test_sign_data_cades_bes_format()

    # Verification (basic)
    def test_verify_signature_basic()
    def test_verify_signature_invalid_file()

class TestSignatureVerifier:
    # Signature verification
    def test_verify_valid_signature()
    def test_verify_invalid_signature()
    def test_verify_tampered_content()
    def test_extract_original_content()
    def test_get_signer_certificate_info()
```

#### Funzioni chiave da coprire
**CertificateManager**:
1. `load_certificate()` - Caricamento PKCS#12
2. `validate_certificate()` - Validazione certificato
3. `get_certificate_info()` - Estrazione info certificato

**DigitalSigner**:
1. `sign_file()` - Firma file XML → .p7m
2. `sign_data()` - Firma dati in memoria
3. `_create_pkcs7_signature()` - Creazione CAdES-BES
4. `verify_signature()` - Verifica base

**SignatureVerifier**:
1. `verify()` - Verifica completa firma
2. `extract_content()` - Estrazione contenuto da .p7m
3. `get_signer_info()` - Info firmatario

**Stima**: 20-25 test, ~500 righe di codice
**File necessari**: Certificato di test PKCS#12, XML di test, .p7m di test

**Note**: Alcuni test potrebbero richiedere certificati reali o mock. Target 80% (non 85%) per complessità hardware/crypto.

---

## 📅 Timeline Consigliata (AGGIORNATA)

### **Sprint 1 (Settimana 1): SDI Critical Gaps**
**Obiettivo**: Coprire i moduli critici SDI al 0%

| Giorno | Task | Effort | Coverage Target |
|--------|------|--------|-----------------|
| 1 | SDI - PEC Sender | 4h | 0% → 85% (+0.35%) |
| 2 | SDI - XSD Validator | 3h | 0% → 85% (+0.2%) |
| 3-4 | Digital Signature Suite | 6h | 0% → 80% (+0.55%) |

**Sprint 1 Result**: 47% → 48.1% coverage (+1.1%)

**Note**: Event Analytics (96%), XML Builder (99%), Notifiche Parser (88%), Notifiche Processor (92%) già coperti - nessuna azione necessaria!

### **Sprint 2 (Opzionale): Perfezionamento Moduli Esistenti**
**Obiettivo**: Portare moduli esistenti da 88-96% a 95%+

| Giorno | Task | Effort | Coverage Target |
|--------|------|--------|-----------------|
| 1 | Event Analytics: 96% → 98% | 1h | Coprire 5 linee mancanti |
| 2 | SDI Notifiche Parser: 88% → 95% | 2h | Coprire 16 linee mancanti |
| 3 | SDI Notifiche Processor: 92% → 95% | 1h | Coprire 8 linee mancanti |
| 4 | XML Builder: 99% → 100% | 30min | Coprire 1 linea mancante |

**Sprint 2 Result**: 48.1% → 48.5% coverage (+0.4%)

### **Total Estimated Coverage Improvement**
- **Starting**: 47%
- **After Sprint 1**: ~48.1% (+1.1%)
- **After Sprint 2 (optional)**: ~48.5% (+1.5%)
- **Additional work needed**: 48.5% → 80% = **31.5%** (requires testing 100+ other modules)

---

## 🛠️ Metodologia Best Practices

### 1. **Test-First Approach**
- Leggere il codice sorgente
- Identificare funzioni pubbliche e scenari business
- Scrivere test PRIMA di refactoring

### 2. **Coverage Incrementale**
- Targetizzare 1 modulo alla volta
- Validare test con `pytest -v --cov=openfatture/[module]`
- Aim for 85%+ per modulo (non 100% - diminishing returns)

### 3. **Test Structure**
```python
# tests/[module]/test_[feature].py

import pytest
from openfatture.[module] import ClassUnderTest

class TestFeatureName:
    """Test [feature] functionality."""

    @pytest.fixture
    def sample_data(self):
        \"\"\"Fixture with sample data.\"\"\"
        return {...}

    def test_happy_path(self, sample_data):
        \"\"\"Test successful scenario.\"\"\"
        # Arrange
        # Act
        # Assert

    def test_error_handling(self):
        \"\"\"Test error scenarios.\"\"\"
        with pytest.raises(ExpectedException):
            # Act that should fail

    def test_edge_case(self):
        \"\"\"Test boundary conditions.\"\"\"
        # Test empty input, None, extreme values
```

### 4. **Mocking Strategico**
- Mock dipendenze esterne (PEC SMTP, File System)
- NON mockare business logic
- Usare fixtures per dati di test riutilizzabili

### 5. **Validation Loop**
```bash
# Per ogni modulo:
1. uv run pytest tests/[module]/ -v --cov=openfatture/[module]
2. Verificare coverage report
3. Identificare linee mancanti (coverage HTML)
4. Aggiungere test mirati
5. Ripetere fino a target 85%+
```

---

## ✅ Acceptance Criteria

### Per ogni modulo testato:

- [ ] **Coverage**: ≥85% statements
- [ ] **Test Count**: ≥10 test significativi
- [ ] **Test Categories**:
  - [ ] Happy path (funzionamento normale)
  - [ ] Error handling (gestione errori)
  - [ ] Edge cases (casi limite)
  - [ ] Integration (dove applicabile)

- [ ] **Code Quality**:
  - [ ] Tutti i test passano
  - [ ] No test duplicati
  - [ ] Fixtures riutilizzabili
  - [ ] Nomi test descrittivi

- [ ] **Documentation**:
  - [ ] Docstring per ogni test class
  - [ ] Comment per test complessi
  - [ ] README se necessario

---

## 📊 Progress Tracking

### Coverage Checkpoints

| Milestone | Target Coverage | Modules Completed | ETA |
|-----------|----------------|-------------------|-----|
| M1 - Event Analytics | +0.5% | 1/10 | Day 1 |
| M2 - Core Completion | +0.3% | 2/10 | Day 1 |
| M3 - XML Builder | +0.5% | 3/10 | Day 3 |
| M4 - XSD Validator | +0.2% | 4/10 | Day 4 |
| M5 - PEC Sender | +0.3% | 5/10 | Day 5 |
| M6 - Notifiche Parser | +0.4% | 6/10 | Day 7 |
| M7 - Notifiche Processor | +0.3% | 7/10 | Day 8 |
| M8 - Digital Signature | +0.6% | 10/10 | Day 10 |

**Total Improvement**: +3.1% (47% → 50.1%)

---

## 🚀 Getting Started - AGGIORNATO

### Prossimo Step Immediato

**FASE 1 - SDI PEC Sender** (Start NOW):

```bash
# 1. Leggere il codice
cat openfatture/sdi/pec_sender/sender.py

# 2. Creare file test
touch tests/unit/test_pec_sender.py

# 3. Struttura iniziale test
cat > tests/unit/test_pec_sender.py << 'EOF'
"""Tests for PEC sender functionality."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from openfatture.sdi.pec_sender.sender import PECSender, create_log_entry

pytestmark = pytest.mark.unit

class TestPECSender:
    """Test PEC sender functionality."""

    @pytest.fixture
    def pec_sender(self, test_settings):
        """Create PEC sender for testing."""
        return PECSender(settings=test_settings)

    # TODO: Add tests here

EOF

# 4. Run coverage baseline
uv run pytest tests/unit/test_pec_sender.py -v --cov=openfatture/sdi/pec_sender
```

**ALTERNATIVE: Verifica copertura esistente** (Raccomandato PRIMA di scrivere nuovi test):

```bash
# Verifica coverage SDI esistente
uv run pytest tests/unit/test_sdi_notifiche.py tests/unit/test_xml_builder.py -v --cov=openfatture/sdi

# Output atteso:
# - parser.py: 88% ✅
# - processor.py: 92% ✅
# - fatturapa.py: 99% ✅
# - pec_sender.py: 0% ❌ (da implementare)
# - xsd_validator.py: 0% ❌ (da implementare)
```

### Command Reference

```bash
# Run specific module tests with coverage
uv run pytest tests/[module]/ -v --cov=openfatture/[module] --cov-report=html

# View coverage for specific file
open htmlcov/[filename].html

# Run all priority modules
uv run pytest tests/core/events/ tests/sdi/ tests/storage/ -v --cov

# Check overall progress
uv run pytest tests/ --cov=openfatture --cov-report=term | grep "TOTAL"
```

---

## 📈 Success Metrics - AGGIORNATO

### Definition of Done (per questo piano CORRETTO)

- [x] **Coverage Report Analizzato**: ✅ DONE (Scoperto che molto era già coperto!)
- [x] **Event Analytics**: ✅ 96% coverage già raggiunta (16 test esistenti)
- [x] **SDI - XML Builder**: ✅ 99% coverage già raggiunta (19 test esistenti)
- [x] **SDI - Notifiche Parser**: ✅ 88% coverage già raggiunta (24 test esistenti)
- [x] **SDI - Notifiche Processor**: ✅ 92% coverage già raggiunta (29 test esistenti)
- [ ] **SDI - PEC Sender**: 0% → 85% (DA IMPLEMENTARE)
- [ ] **SDI - XSD Validator**: 0% → 85% (DA IMPLEMENTARE)
- [ ] **Digital Signature Suite**: 0% → 80% (DA IMPLEMENTARE)
- [ ] **Coverage Globale**: 47% → 48.1%+ (Sprint 1)
- [ ] **Tutti i test passing**: 100%
- [ ] **Documentation updated**: README con coverage badges

### Long-term Goal
- **Target finale**: 80%+ coverage globale
- **ETA**: Molto più lungo del previsto (31.5% gap dopo Sprint 1+2)
- **Approccio**: Incrementale, modulo per modulo
- **Realtà**: La maggior parte del lavoro sarà su moduli non-SDI (AI, Payment, Lightning, CLI, Web, etc.)

---

**Generated**: 2025-10-17 01:05 UTC
**Updated**: 2025-10-17 (post-analysis correction)
**Next Review**: Dopo completamento Sprint 1 (PEC Sender, XSD Validator, Digital Signature)
**Owner**: Team OpenFatture

**KEY INSIGHT**: Il piano iniziale sovrastimava il lavoro necessario. Molti moduli SDI sono già ben coperti (88-99%). Il vero lavoro è su:
1. PEC Sender (critico per SDI submission)
2. XSD Validator (critico per quality gate)
3. Digital Signature (opzionale ma utile)
4. Tutti gli altri 100+ moduli non ancora analizzati (AI, Payment, CLI, Web, etc.)
