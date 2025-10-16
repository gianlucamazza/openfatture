"""End-to-end tests for custom commands with real workflows.

Tests the complete integration of custom commands with:
- Real database interactions
- Complete AI workflows
- Example commands from docs/examples/custom-commands/
- Session persistence and cost tracking
"""

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
import yaml

from openfatture.ai.agents.chat_agent import ChatAgent
from openfatture.ai.domain.context import ChatContext
from openfatture.ai.domain.message import Message, Role
from openfatture.ai.domain.response import AgentResponse, ResponseStatus, UsageMetrics
from openfatture.ai.providers.base import BaseLLMProvider
from openfatture.ai.session import ChatSession
from openfatture.cli.commands.custom_commands import CustomCommandRegistry
from openfatture.storage.database.base import get_session, init_db
from openfatture.storage.database.models import Cliente, Fattura, RigaFattura, StatoFattura


class E2EMockProvider(BaseLLMProvider):
    """Mock provider for E2E testing with realistic responses."""

    def __init__(self):
        super().__init__()
        self._provider_name = "e2e-mock"
        self.model = "e2e-mock-model"
        self._supports_streaming = True
        self._supports_tools = True
        self.calls = []

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def supports_streaming(self) -> bool:
        return self._supports_streaming

    @property
    def supports_tools(self) -> bool:
        return self._supports_tools

    async def generate(self, messages, **kwargs):
        """Generate realistic responses based on custom command input."""
        self.calls.append({"messages": messages, "kwargs": kwargs})

        last_message = messages[-1] if messages else Message(role=Role.USER, content="")
        content_lower = last_message.content.lower()

        # Check most specific patterns first (order matters!)
        if "compliance check" in content_lower or "verifica compliance" in content_lower:
            content = """**🔍 COMPLIANCE CHECK - FATTURA 2025-042**

---

## 1. Validazione Formale
✅ Dati cedente completi e corretti
✅ Dati cessionario completi e corretti
✅ Numero fattura valido e progressivo
✅ Data emissione valida
✅ Codice destinatario presente

## 2. Righe Fattura
✅ Descrizioni dettagliate (>20 caratteri)
✅ Quantità e unità di misura presenti
✅ Prezzi unitari corretti
✅ Totali calcolati correttamente

## 3. Trattamento Fiscale
✅ Aliquote IVA corrette (22% standard)
⚠️ **ATTENZIONE:** Verificare se cliente PA richiede split payment
✅ Ritenuta d'acconto NON necessaria (servizi B2B)
✅ Bollo virtuale: NON richiesto (importo con IVA >77,47€)

## 4. Compliance SDI
✅ Schema FatturaPA v1.9 rispettato
✅ Codice ATECO valido
✅ Nessun pattern noto di rigetto

## 5. Best Practices
✅ Descrizione professionale e dettagliata
✅ Note fattura appropriate
✅ Riferimenti normativi corretti

---

## Risultato Finale
✅ **READY per invio SDI**

**Probabilità di accettazione:** 95%

**Nota:** Se il cliente è PA, aggiungere codice EsigibilitaIVA = "S" per split payment.
"""
        elif "report mensile" in content_lower or "report completo" in content_lower:
            content = """**📊 REPORT MENSILE - OTTOBRE 2025**

---

## 1. Fatturazione
- **Fatture emesse:** 12
- **Imponibile totale:** €15,000.00
- **IVA totale:** €3,300.00
- **Totale fatturato:** €18,300.00
- **Variazione vs settembre:** +15% 📈
- **Media per fattura:** €1,525.00

## 2. Incassi
- **Totale incassato:** €14,500.00
- **Fatture pagate:** 10
- **Fatture in sospeso:** 2 (€1,750.00)
- **Tempo medio incasso:** 28 giorni
- **Cash flow projection (3 mesi):**
  - Novembre: €16,000 (atteso)
  - Dicembre: €14,000 (atteso)
  - Gennaio: €18,500 (atteso)

## 3. Top Clienti
1. **Acme Corp** - €4,500.00 (5 fatture)
2. **Beta SRL** - €3,200.00 (3 fatture)
3. **Gamma SpA** - €2,800.00 (2 fatture)
4. **Delta Ltd** - €2,100.00 (1 fattura)
5. **Epsilon Inc** - €1,900.00 (1 fattura)

**Nuovi clienti:** 2 (Delta Ltd, Epsilon Inc)
**Clienti con fatture scadute:** 1 (Acme Corp - €750)

## 4. Analisi Fiscale
- **IVA a debito:** €3,300.00
- **IVA a credito:** €450.00 (acquisti)
- **IVA netta da versare:** €2,850.00
- **Ritenute d'acconto subite:** €0.00
- **Bolli virtuali applicati:** 2 (€4.00)

## 5. Insights & Raccomandazioni
📈 **Tendenze positive:**
- Crescita del 15% rispetto al mese precedente
- 2 nuovi clienti acquisiti
- Tempo medio di incasso stabile (28 giorni)

⚠️ **Criticità:**
- 1 fattura scaduta (Acme Corp) - inviare sollecito
- 2 fatture in scadenza entro 7 giorni - monitorare

✅ **Azioni consigliate:**
1. Contattare Acme Corp per sollecito pagamento fattura scaduta
2. Pianificare strategia per dicembre (mese storicamente più debole)
3. Valutare incentivi per clienti top (Beta SRL, Gamma SpA)
4. Preparare liquidazione IVA trimestrale (scadenza: 16/11/2025)
"""
        elif "cerca nel database" in content_lower or (
            "informazioni complete" in content_lower and "cliente" in content_lower
        ):
            content = """**👤 CLIENTE: ACME CORP**

---

## Dati Anagrafici
- **Denominazione:** Acme Corp SRL
- **P.IVA:** 12345678901
- **Codice Fiscale:** 12345678901
- **Regime Fiscale:** RF01 (Regime Ordinario)
- **Codice Destinatario:** ABCDEFG
- **PEC:** fatture@acmecorp.pec.it

## Statistiche Fatturazione
- **Fatture emesse:** 15
- **Importo totale:** €12,500.00
- **Media per fattura:** €833.33
- **Ultima fattura:** 2025-09-15 (€750.00)

## Stato Pagamenti
- ✅ **Pagate:** 12 fatture (€10,000.00)
- ⏳ **In sospeso:** 2 fatture (€1,750.00)
- ⚠️ **Scadute:** 1 fattura (€750.00) - Scadenza: 2025-09-30

## Ultime 5 Fatture
1. 2025-042 - €750.00 - 15/09/2025 - ⚠️ SCADUTA
2. 2025-038 - €1,000.00 - 05/09/2025 - ✅ PAGATA
3. 2025-031 - €500.00 - 20/08/2025 - ✅ PAGATA
4. 2025-025 - €1,200.00 - 10/08/2025 - ✅ PAGATA
5. 2025-018 - €800.00 - 01/08/2025 - ✅ PAGATA

⚠️ **ATTENZIONE:** Cliente ha 1 fattura scaduta. Contattare per sollecito pagamento.
"""
        elif "fattura completa" in content_lower or "crea una fattura" in content_lower:
            content = """**📄 FATTURA GENERATA**

**Cliente:** Acme Corp
**Servizio:** Consulenza web
**Importo:** 500€

---

## 1. Descrizione Professionale
Consulenza professionale per lo sviluppo di un'applicazione web completa, inclusa analisi dei requisiti, progettazione dell'architettura, implementazione delle funzionalità core e testing.

## 2. Trattamento IVA
- **Aliquota consigliata:** 22% (servizi professionali standard)
- **Codice IVA:** Aliquota ordinaria
- **Imponibile:** 500€
- **IVA:** 110€
- **Totale:** 610€

## 3. Compliance SDI
✅ **CONFORME** - Pronta per l'invio a SDI

- Descrizione dettagliata (>20 caratteri)
- IVA corretta per servizi professionali B2B
- Nessuna casistica speciale richiesta
- Bollo: NON necessario (importo >77,47€ con IVA)

Vuoi procedere con la creazione della fattura?
"""
        # Simulate /iva suggestion response
        elif (
            "suggerisci aliquota iva" in content_lower
            or "quale aliquota" in content_lower
            or "iva" in content_lower
        ):
            content = """**💶 SUGGERIMENTO IVA**

---

## Servizio Analizzato
IT consulting per società di costruzioni

## Aliquota Consigliata
**22%** - Aliquota ordinaria

## Motivazione
I servizi professionali di consulenza IT rientrano nella categoria dei servizi generici soggetti ad aliquota ordinaria del 22% (art. 1, DPR 633/72).

## Regime Speciale?
❌ **Reverse Charge:** NON applicabile
- Il reverse charge (inversione contabile) si applica principalmente a servizi edili e cessioni di beni specifici
- I servizi IT generici non rientrano in questa casistica

❌ **Split Payment:** Verifica necessaria
- Se il cliente è una Pubblica Amministrazione, potrebbe essere richiesto lo split payment
- Indicare codice "S" nel campo EsigibilitaIVA se applicabile

## Note per Fattura
Suggerimento: Se il cliente è PA, aggiungere:
"Scissione dei pagamenti ai sensi dell'art. 17-ter, DPR 633/1972"
"""
        else:
            content = "Risposta AI generica per testing E2E."

        return AgentResponse(
            content=content,
            status=ResponseStatus.SUCCESS,
            provider=self.provider_name,
            model=self.model,
            usage=UsageMetrics(
                prompt_tokens=100,
                completion_tokens=300,
                total_tokens=400,
                estimated_cost_usd=0.004,
            ),
            latency_ms=500,
        )

    async def stream(self, messages, **kwargs):
        response = await self.generate(messages, **kwargs)
        for chunk in response.content.split():
            yield chunk + " "

    def count_tokens(self, text: str) -> int:
        return len(text.split())

    def estimate_cost(self, usage: UsageMetrics) -> float:
        return usage.total_tokens * 0.00001

    async def health_check(self) -> bool:
        return True


@pytest.fixture
def e2e_db_session():
    """Create a test database session with sample data."""
    # Initialize test database
    init_db("sqlite:///:memory:")
    session = get_session()

    try:
        # Create test client
        cliente = Cliente(
            denominazione="Acme Corp SRL",
            partita_iva="12345678901",
            codice_fiscale="12345678901",
            codice_destinatario="ABCDEFG",
            pec="fatture@acmecorp.pec.it",
            indirizzo="Via Test 123",
            cap="00100",
            comune="Roma",
            provincia="RM",
            nazione="IT",
        )
        session.add(cliente)
        session.commit()

        # Create test invoices
        for i in range(15):
            fattura = Fattura(
                numero=str(i + 1).zfill(3),
                anno=2025,
                data_emissione=date.today() - timedelta(days=90 - i * 5),
                cliente=cliente,
                tipo_documento="TD01",
                stato=StatoFattura.CONSEGNATA if i < 12 else StatoFattura.DA_INVIARE,
                imponibile=Decimal("500.00") + Decimal(i * 50),
                iva=Decimal("110.00") + Decimal(i * 11),
                totale=Decimal("610.00") + Decimal(i * 61),
            )
            session.add(fattura)

            # Add invoice line
            imponibile_riga = Decimal("500.00") + Decimal(i * 50)
            iva_riga = imponibile_riga * Decimal("0.22")
            riga = RigaFattura(
                fattura=fattura,
                numero_riga=1,
                descrizione=f"Servizio professionale {i+1}",
                quantita=Decimal("1.00"),
                prezzo_unitario=imponibile_riga,
                aliquota_iva=Decimal("22.00"),
                imponibile=imponibile_riga,
                iva=iva_riga,
                totale=imponibile_riga + iva_riga,
            )
            session.add(riga)

        session.commit()

        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def e2e_registry():
    """Load real example commands from docs."""
    # Use real example commands directory
    examples_dir = (
        Path(__file__).parent.parent.parent.parent / "docs" / "examples" / "custom-commands"
    )

    if not examples_dir.exists():
        pytest.skip(f"Example commands directory not found: {examples_dir}")

    return CustomCommandRegistry(commands_dir=examples_dir)


@pytest.fixture
def e2e_mock_provider():
    """Create E2E mock provider."""
    return E2EMockProvider()


@pytest.mark.e2e
@pytest.mark.asyncio
class TestCustomCommandsE2E:
    """End-to-end tests for custom commands with real workflows."""

    async def test_fattura_rapida_complete_workflow(self, e2e_registry, e2e_mock_provider):
        """Test complete /fattura-rapida workflow."""
        # Check command is loaded
        assert e2e_registry.has_command("fattura-rapida")

        # Expand command
        expanded = e2e_registry.execute(
            "fattura-rapida", args=["Acme Corp", "Consulenza web", "500"]
        )

        # Verify expansion contains expected elements
        assert "Acme Corp" in expanded
        assert "Consulenza web" in expanded
        assert "500" in expanded
        assert "fattura completa" in expanded.lower()

        # Execute with ChatAgent
        agent = ChatAgent(provider=e2e_mock_provider, enable_tools=False)
        context = ChatContext(user_input=expanded)
        response = await agent.execute(context)

        # Verify response
        assert response.status == ResponseStatus.SUCCESS
        assert "Acme Corp" in response.content
        assert "22%" in response.content  # IVA suggestion
        assert "CONFORME" in response.content or "READY" in response.content  # Compliance check
        assert e2e_mock_provider.calls  # Provider was called

    async def test_cliente_info_with_database(
        self, e2e_registry, e2e_mock_provider, e2e_db_session
    ):
        """Test /cliente-info with real database data."""
        # Check command is loaded
        assert e2e_registry.has_command("cliente-info")

        # Expand command
        expanded = e2e_registry.execute("cliente-info", args=["Acme Corp"])

        # Verify expansion
        assert "Acme Corp" in expanded
        assert (
            "cerca nel database" in expanded.lower() or "informazioni complete" in expanded.lower()
        )

        # Execute with ChatAgent
        agent = ChatAgent(provider=e2e_mock_provider, enable_tools=False)
        context = ChatContext(user_input=expanded)
        response = await agent.execute(context)

        # Verify response contains client info
        assert response.status == ResponseStatus.SUCCESS
        assert "Acme Corp" in response.content
        assert "12345678901" in response.content  # P.IVA
        assert "Fatture" in response.content or "fatture" in response.content
        assert "€" in response.content  # Amounts

    async def test_iva_suggestion_workflow(self, e2e_registry, e2e_mock_provider):
        """Test /iva VAT suggestion workflow."""
        # Check command is loaded
        assert e2e_registry.has_command("iva")

        # Expand command
        expanded = e2e_registry.execute("iva", args=["IT consulting per società di costruzioni"])

        # Verify expansion
        assert "IT consulting" in expanded
        assert "iva" in expanded.lower() or "aliquota" in expanded.lower()

        # Execute with ChatAgent
        agent = ChatAgent(provider=e2e_mock_provider, enable_tools=False)
        context = ChatContext(user_input=expanded)
        response = await agent.execute(context)

        # Verify response
        assert response.status == ResponseStatus.SUCCESS
        assert "22%" in response.content  # Standard VAT rate
        assert "Reverse Charge" in response.content or "reverse charge" in response.content
        assert "DPR" in response.content  # Legal reference

    async def test_compliance_check_workflow(self, e2e_registry, e2e_mock_provider):
        """Test /compliance-check complete workflow."""
        # Check command is loaded
        assert e2e_registry.has_command("compliance-check")

        # Expand command
        expanded = e2e_registry.execute("compliance-check", args=["2025-042"])

        # Verify expansion
        assert "2025-042" in expanded
        assert "compliance" in expanded.lower() or "verifica" in expanded.lower()

        # Execute with ChatAgent
        agent = ChatAgent(provider=e2e_mock_provider, enable_tools=False)
        context = ChatContext(user_input=expanded)
        response = await agent.execute(context)

        # Verify response
        assert response.status == ResponseStatus.SUCCESS
        assert "2025-042" in response.content
        assert "SDI" in response.content
        assert "✅" in response.content or "READY" in response.content
        assert "%" in response.content  # Acceptance probability

    async def test_report_mensile_workflow(self, e2e_registry, e2e_mock_provider):
        """Test /report-mensile monthly report workflow."""
        # Check command is loaded
        assert e2e_registry.has_command("report-mensile")

        # Expand command (current month)
        expanded = e2e_registry.execute("report-mensile", args=["Ottobre", "2025"])

        # Verify expansion
        assert "Ottobre" in expanded or "ottobre" in expanded
        assert "report" in expanded.lower()

        # Execute with ChatAgent
        agent = ChatAgent(provider=e2e_mock_provider, enable_tools=False)
        context = ChatContext(user_input=expanded)
        response = await agent.execute(context)

        # Verify response
        assert response.status == ResponseStatus.SUCCESS
        assert "Ottobre" in response.content.upper() or "OTTOBRE" in response.content
        assert "Fatture" in response.content or "fatture" in response.content
        assert "€" in response.content
        assert "IVA" in response.content
        assert "Top" in response.content or "top" in response.content  # Top clients

    async def test_session_persistence_across_commands(self, e2e_registry, e2e_mock_provider):
        """Test that session persists across multiple custom commands."""
        session = ChatSession()
        agent = ChatAgent(provider=e2e_mock_provider, enable_tools=False)

        # Execute first command
        expanded1 = e2e_registry.execute("cliente-info", args=["Acme Corp"])
        session.add_user_message(expanded1)
        context1 = ChatContext(user_input=expanded1, session_id=session.id)
        response1 = await agent.execute(context1)

        session.add_assistant_message(
            response1.content,
            provider=response1.provider,
            model=response1.model,
            tokens=response1.usage.total_tokens,
            cost=response1.usage.estimated_cost_usd,
        )

        # Execute second command
        expanded2 = e2e_registry.execute("fattura-rapida", args=["Acme Corp", "Consulting", "500"])
        session.add_user_message(expanded2)
        context2 = ChatContext(user_input=expanded2, session_id=session.id)
        response2 = await agent.execute(context2)

        session.add_assistant_message(
            response2.content,
            provider=response2.provider,
            model=response2.model,
            tokens=response2.usage.total_tokens,
            cost=response2.usage.estimated_cost_usd,
        )

        # Verify session
        assert session.metadata.message_count == 4  # 2 user + 2 assistant
        assert session.metadata.total_tokens > 0
        assert session.metadata.total_cost_usd > 0
        messages = session.get_messages()
        assert len(messages) == 4

    async def test_all_example_commands_load_correctly(self, e2e_registry):
        """Test that all example commands load without errors."""
        commands = e2e_registry.list_commands()

        # Check expected commands are loaded
        expected_commands = [
            "fattura-rapida",
            "iva",
            "cliente-info",
            "report-mensile",
            "compliance-check",
        ]

        loaded_names = [cmd.name for cmd in commands]

        for expected in expected_commands:
            assert expected in loaded_names, f"Command '{expected}' not loaded"

        # Verify each command has required fields
        for cmd in commands:
            assert cmd.name
            assert cmd.description
            assert cmd.template
            assert cmd.category
            assert isinstance(cmd.aliases, list)

    async def test_command_aliases_work(self, e2e_registry, e2e_mock_provider):
        """Test that command aliases work correctly."""
        # Test /fr alias for /fattura-rapida
        assert e2e_registry.has_command("fr")
        expanded1 = e2e_registry.execute("fr", args=["Client", "Service", "100"])
        expanded2 = e2e_registry.execute("fattura-rapida", args=["Client", "Service", "100"])
        assert expanded1 == expanded2

        # Test /ci alias for /cliente-info
        assert e2e_registry.has_command("ci")
        expanded3 = e2e_registry.execute("ci", args=["Test Client"])
        expanded4 = e2e_registry.execute("cliente-info", args=["Test Client"])
        assert expanded3 == expanded4

    async def test_cost_tracking_across_workflow(self, e2e_registry, e2e_mock_provider):
        """Test that costs are tracked correctly across custom command workflow."""
        session = ChatSession()
        agent = ChatAgent(provider=e2e_mock_provider, enable_tools=False)

        # Execute multiple commands
        commands_to_test = [
            ("cliente-info", ["Acme Corp"]),
            ("iva", ["IT consulting"]),
            ("compliance-check", ["2025-042"]),
        ]

        for cmd_name, cmd_args in commands_to_test:
            expanded = e2e_registry.execute(cmd_name, args=cmd_args)
            session.add_user_message(expanded)

            context = ChatContext(user_input=expanded, session_id=session.id)
            response = await agent.execute(context)

            session.add_assistant_message(
                response.content,
                provider=response.provider,
                model=response.model,
                tokens=response.usage.total_tokens,
                cost=response.usage.estimated_cost_usd,
            )

        # Verify cost tracking
        assert session.metadata.total_tokens > 0
        assert session.metadata.total_cost_usd > 0
        assert session.metadata.message_count == 6  # 3 user + 3 assistant
        assert len(e2e_mock_provider.calls) == 3


@pytest.mark.e2e
@pytest.mark.asyncio
class TestCustomCommandsReload:
    """Test command reload functionality."""

    async def test_reload_commands_picks_up_new_files(self, tmp_path):
        """Test that reload() picks up new command files."""
        # Create registry with temp directory
        registry = CustomCommandRegistry(commands_dir=tmp_path)
        assert len(registry.list_commands()) == 0

        # Add new command file
        command_data = {
            "name": "new-cmd",
            "description": "New test command",
            "template": "Test: {{ arg1 }}",
        }
        file_path = tmp_path / "new-cmd.yaml"
        with open(file_path, "w") as f:
            yaml.dump(command_data, f)

        # Reload
        registry.reload()

        # Verify new command is loaded
        assert len(registry.list_commands()) == 1
        assert registry.has_command("new-cmd")

    async def test_reload_commands_updates_modified_files(self, tmp_path):
        """Test that reload() updates modified command files."""
        # Create initial command
        command_data = {
            "name": "test-cmd",
            "description": "Original description",
            "template": "Original: {{ arg1 }}",
        }
        file_path = tmp_path / "test-cmd.yaml"
        with open(file_path, "w") as f:
            yaml.dump(command_data, f)

        registry = CustomCommandRegistry(commands_dir=tmp_path)
        original_desc = registry.get_command("test-cmd").description

        # Modify command file
        command_data["description"] = "Updated description"
        command_data["template"] = "Updated: {{ arg1 }}"
        with open(file_path, "w") as f:
            yaml.dump(command_data, f)

        # Reload
        registry.reload()

        # Verify command is updated
        updated_cmd = registry.get_command("test-cmd")
        assert updated_cmd.description != original_desc
        assert updated_cmd.description == "Updated description"
        assert "Updated" in updated_cmd.template
