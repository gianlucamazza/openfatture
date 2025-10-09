"""
Tax Advisor Usage Examples.

This script demonstrates how to use the Tax Advisor agent
to suggest correct VAT treatment for Italian invoices.

Requirements:
    - API key for your chosen provider (OpenAI, Anthropic, or Ollama)
    - Set environment variable: OPENFATTURE_AI_OPENAI_API_KEY or OPENFATTURE_AI_ANTHROPIC_API_KEY

Run:
    python examples/ai_tax_advisor.py
"""

import asyncio
import json

from openfatture.ai.agents.tax_advisor import TaxAdvisorAgent
from openfatture.ai.domain.context import TaxContext
from openfatture.ai.providers.factory import create_provider


async def example_1_standard_vat():
    """Example 1: Standard VAT rate (22%)."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Standard VAT Rate")
    print("=" * 80 + "\n")

    # Create provider (uses environment configuration)
    provider = create_provider()

    # Create agent
    agent = TaxAdvisorAgent(provider=provider)

    # Create context
    context = TaxContext(
        user_input="consulenza IT",
        tipo_servizio="consulenza IT"
    )

    # Execute agent
    response = await agent.execute(context)

    # Display results
    if response.metadata.get("is_structured"):
        model = response.metadata["parsed_model"]
        print(f"Aliquota IVA: {model['aliquota_iva']}%")
        print(f"Spiegazione: {model['spiegazione']}")
        print(f"Riferimento: {model['riferimento_normativo']}")
    else:
        print(response.content)

    print(f"\nCost: ${response.usage.estimated_cost_usd:.4f}")


async def example_2_reverse_charge():
    """Example 2: Reverse charge for construction sector."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Reverse Charge (Edilizia)")
    print("=" * 80 + "\n")

    provider = create_provider()
    agent = TaxAdvisorAgent(provider=provider)

    context = TaxContext(
        user_input="consulenza IT per azienda edile",
        tipo_servizio="consulenza IT per azienda edile",
        importo=5000.0
    )

    response = await agent.execute(context)

    if response.metadata.get("is_structured"):
        model = response.metadata["parsed_model"]
        print(json.dumps(model, indent=2, ensure_ascii=False))
    else:
        print(response.content)


async def example_3_split_payment():
    """Example 3: Split payment for Public Administration."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Split Payment (Pubblica Amministrazione)")
    print("=" * 80 + "\n")

    provider = create_provider()
    agent = TaxAdvisorAgent(provider=provider)

    context = TaxContext(
        user_input="consulenza IT per Comune di Milano",
        tipo_servizio="consulenza IT",
        cliente_pa=True,
        importo=3000.0
    )

    response = await agent.execute(context)

    if response.metadata.get("is_structured"):
        model = response.metadata["parsed_model"]
        print(f"Aliquota IVA: {model['aliquota_iva']}%")
        print(f"Split Payment: {'SI' if model['split_payment'] else 'NO'}")
        print(f"\nSpiegazione:\n{model['spiegazione']}")
        print(f"\nNota per fattura:\n{model.get('note_fattura', 'N/A')}")

        if model.get("raccomandazioni"):
            print("\nRaccomandazioni:")
            for racc in model["raccomandazioni"]:
                print(f"  • {racc}")


async def example_4_exempt_services():
    """Example 4: Exempt services (formazione, sanità)."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Servizi Esenti (Formazione)")
    print("=" * 80 + "\n")

    provider = create_provider()
    agent = TaxAdvisorAgent(provider=provider)

    context = TaxContext(
        user_input="corso di formazione professionale",
        tipo_servizio="formazione professionale",
        categoria_servizio="Educazione",
        importo=1500.0
    )

    response = await agent.execute(context)

    if response.metadata.get("is_structured"):
        model = response.metadata["parsed_model"]
        print(f"Aliquota IVA: {model['aliquota_iva']}%")
        print(f"Codice Natura: {model.get('codice_natura', 'N/A')}")
        print(f"Regime: {model.get('regime_speciale', 'Standard')}")
        print(f"\nRiferimento normativo:\n{model['riferimento_normativo']}")


async def example_5_reduced_vat():
    """Example 5: Reduced VAT rate (10%, 4%)."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Aliquota Ridotta (Libri)")
    print("=" * 80 + "\n")

    provider = create_provider()
    agent = TaxAdvisorAgent(provider=provider)

    context = TaxContext(
        user_input="vendita libri scolastici",
        tipo_servizio="libri scolastici",
        categoria_servizio="Editoria",
        importo=250.0
    )

    response = await agent.execute(context)

    if response.metadata.get("is_structured"):
        model = response.metadata["parsed_model"]
        print(f"Aliquota IVA: {model['aliquota_iva']}%")
        print(f"Spiegazione: {model['spiegazione']}")


async def example_6_export():
    """Example 6: Export to non-EU country."""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Export Extra-UE")
    print("=" * 80 + "\n")

    provider = create_provider()
    agent = TaxAdvisorAgent(provider=provider)

    context = TaxContext(
        user_input="consulenza IT per cliente USA",
        tipo_servizio="consulenza IT",
        cliente_estero=True,
        paese_cliente="US",
        importo=10000.0
    )

    response = await agent.execute(context)

    if response.metadata.get("is_structured"):
        model = response.metadata["parsed_model"]
        print(f"Aliquota IVA: {model['aliquota_iva']}%")
        print(f"Codice Natura: {model.get('codice_natura', 'N/A')}")
        print(f"\nSpiegazione:\n{model['spiegazione']}")
        print(f"\nRaccomandazioni:")
        for racc in model.get("raccomandazioni", []):
            print(f"  • {racc}")


async def example_7_batch_analysis():
    """Example 7: Batch VAT analysis for multiple services."""
    print("\n" + "=" * 80)
    print("EXAMPLE 7: Batch VAT Analysis")
    print("=" * 80 + "\n")

    provider = create_provider()
    agent = TaxAdvisorAgent(provider=provider)

    services = [
        {"tipo": "consulenza IT", "importo": 5000},
        {"tipo": "formazione professionale", "importo": 2000},
        {"tipo": "libri tecnici", "importo": 300},
        {"tipo": "servizi pulizia cantiere", "importo": 1500},
    ]

    results = []

    for service in services:
        context = TaxContext(
            user_input=service["tipo"],
            tipo_servizio=service["tipo"],
            importo=service["importo"]
        )

        response = await agent.execute(context)
        results.append(response)

        if response.metadata.get("is_structured"):
            model = response.metadata["parsed_model"]
            print(f"\n✅ {service['tipo'].upper()}")
            print(f"   Aliquota: {model['aliquota_iva']}%")
            print(f"   Reverse charge: {'SI' if model['reverse_charge'] else 'NO'}")
            print(f"   Natura: {model.get('codice_natura', 'N/A')}")

    # Aggregate stats
    total_cost = sum(r.usage.estimated_cost_usd for r in results)
    print(f"\n📊 Total analysis cost: ${total_cost:.4f}")


async def example_8_complex_scenario():
    """Example 8: Complex scenario with multiple conditions."""
    print("\n" + "=" * 80)
    print("EXAMPLE 8: Scenario Complesso (Subappalto Edile)")
    print("=" * 80 + "\n")

    provider = create_provider()
    agent = TaxAdvisorAgent(provider=provider)

    context = TaxContext(
        user_input="servizi di pulizia e manutenzione per cantiere edile",
        tipo_servizio="servizi di pulizia e manutenzione",
        categoria_servizio="Edilizia",
        importo=8000.0,
        codice_ateco="81.21.00"
    )

    response = await agent.execute(context)

    if response.metadata.get("is_structured"):
        model = response.metadata["parsed_model"]

        print("🧾 ANALISI FISCALE DETTAGLIATA")
        print("-" * 80)
        print(f"\nAliquota IVA:        {model['aliquota_iva']}%")
        print(f"Reverse Charge:      {'✓ SI' if model['reverse_charge'] else '✗ NO'}")
        print(f"Codice Natura:       {model.get('codice_natura', 'N/A')}")
        print(f"Regime Speciale:     {model.get('regime_speciale', 'N/A')}")
        print(f"Confidence:          {int(model['confidence'] * 100)}%")

        print(f"\n📋 SPIEGAZIONE:")
        print(model['spiegazione'])

        print(f"\n📜 RIFERIMENTO NORMATIVO:")
        print(model['riferimento_normativo'])

        if model.get('note_fattura'):
            print(f"\n📝 NOTA PER FATTURA:")
            print(f'"{model["note_fattura"]}"')

        if model.get('raccomandazioni'):
            print(f"\n💡 RACCOMANDAZIONI:")
            for racc in model['raccomandazioni']:
                print(f"  • {racc}")


async def main():
    """Run all examples."""
    print("\n🧾 Tax Advisor - Usage Examples")
    print("=" * 80)

    # Run examples
    await example_1_standard_vat()
    await example_2_reverse_charge()
    await example_3_split_payment()
    await example_4_exempt_services()
    await example_5_reduced_vat()
    await example_6_export()
    await example_7_batch_analysis()
    await example_8_complex_scenario()

    print("\n" + "=" * 80)
    print("✅ All examples completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    # Note: You need to set environment variables before running:
    # export OPENFATTURE_AI_PROVIDER=openai  # or anthropic, ollama
    # export OPENFATTURE_AI_OPENAI_API_KEY=sk-...
    # or
    # export OPENFATTURE_AI_ANTHROPIC_API_KEY=sk-ant-...

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have set the required environment variables:")
        print("  OPENFATTURE_AI_PROVIDER (openai, anthropic, or ollama)")
        print("  OPENFATTURE_AI_OPENAI_API_KEY or OPENFATTURE_AI_ANTHROPIC_API_KEY")
