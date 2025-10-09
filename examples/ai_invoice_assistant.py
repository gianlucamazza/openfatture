"""
Invoice Assistant Usage Examples.

This script demonstrates how to use the Invoice Assistant agent
to generate professional Italian invoice descriptions.

Requirements:
    - API key for your chosen provider (OpenAI, Anthropic, or Ollama)
    - Set environment variable: OPENFATTURE_AI_OPENAI_API_KEY or OPENFATTURE_AI_ANTHROPIC_API_KEY

Run:
    python examples/ai_invoice_assistant.py
"""

import asyncio
import json

from openfatture.ai.agents.invoice_assistant import InvoiceAssistantAgent
from openfatture.ai.domain.context import InvoiceContext
from openfatture.ai.providers.factory import create_provider
from openfatture.storage.database.models import Cliente


async def example_1_basic_description():
    """Example 1: Generate a basic invoice description."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Basic Invoice Description")
    print("=" * 80 + "\n")

    # Create provider (uses environment configuration)
    provider = create_provider()

    # Create agent
    agent = InvoiceAssistantAgent(provider=provider)

    # Create context with minimal information
    context = InvoiceContext(
        user_input="3 ore consulenza web",
        servizio_base="3 ore consulenza web",
        ore_lavorate=3.0,
    )

    # Execute agent
    response = await agent.execute(context)

    # Display results
    if response.metadata.get("is_structured"):
        model = response.metadata["parsed_model"]
        print(f"Descrizione Completa:\n{model['descrizione_completa']}\n")
        print(f"Deliverables: {', '.join(model['deliverables'])}")
        print(f"Competenze: {', '.join(model['competenze'])}")
        print(f"Durata: {model['durata_ore']}h")
    else:
        print(response.content)

    print(f"\nCost: ${response.usage.estimated_cost_usd:.4f}")


async def example_2_with_technologies():
    """Example 2: Description with technologies and project context."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Description with Technologies")
    print("=" * 80 + "\n")

    provider = create_provider()
    agent = InvoiceAssistantAgent(provider=provider)

    context = InvoiceContext(
        user_input="sviluppo backend API",
        servizio_base="sviluppo backend API",
        ore_lavorate=8.0,
        tariffa_oraria=100.0,
        progetto="E-commerce Platform",
        tecnologie=["Python", "FastAPI", "PostgreSQL", "Docker"],
        deliverables=["API REST", "Documentazione OpenAPI", "Test Suite"],
    )

    response = await agent.execute(context)

    if response.metadata.get("is_structured"):
        model = response.metadata["parsed_model"]
        print(json.dumps(model, indent=2, ensure_ascii=False))
    else:
        print(response.content)

    print(f"\nTokens used: {response.usage.total_tokens}")
    print(f"Cost: ${response.usage.estimated_cost_usd:.4f}")


async def example_3_with_client():
    """Example 3: Description with client information."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Description with Client Context")
    print("=" * 80 + "\n")

    # Create a sample client
    cliente = Cliente(
        denominazione="Acme Corporation",
        partita_iva="12345678901",
        codice_destinatario="ABC1234",
    )

    provider = create_provider()
    agent = InvoiceAssistantAgent(provider=provider)

    context = InvoiceContext(
        user_input="audit sicurezza applicazione",
        servizio_base="audit sicurezza applicazione",
        ore_lavorate=16.0,
        tariffa_oraria=150.0,
        cliente=cliente,
        tecnologie=["OWASP", "Security Testing", "Penetration Testing"],
        deliverables=[
            "Report audit completo",
            "Lista vulnerabilità",
            "Piano remediation",
            "Best practices",
        ],
    )

    response = await agent.execute(context)

    if response.metadata.get("is_structured"):
        model = response.metadata["parsed_model"]

        print(f"Cliente: {cliente.denominazione}")
        print(f"\nDescrizione:\n{model['descrizione_completa']}")
        print(f"\nDeliverables:")
        for item in model["deliverables"]:
            print(f"  • {item}")
        print(f"\nCompetenze:")
        for skill in model["competenze"]:
            print(f"  • {skill}")

        # Calculate total
        total = context.ore_lavorate * context.tariffa_oraria
        print(f"\nDurata: {model['durata_ore']}h @ €{context.tariffa_oraria}/h")
        print(f"Totale: €{total:.2f}")

    print(f"\nCost: ${response.usage.estimated_cost_usd:.4f}")


async def example_4_batch_descriptions():
    """Example 4: Generate multiple descriptions in batch."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Batch Description Generation")
    print("=" * 80 + "\n")

    provider = create_provider()
    agent = InvoiceAssistantAgent(provider=provider)

    services = [
        {
            "servizio": "formazione team sviluppo",
            "ore": 6.0,
            "tech": ["Clean Code", "Design Patterns", "TDD"],
        },
        {
            "servizio": "migrazione database",
            "ore": 4.0,
            "tech": ["SQL", "PostgreSQL", "Data Migration"],
        },
        {
            "servizio": "code review e refactoring",
            "ore": 5.0,
            "tech": ["Python", "Code Quality", "Refactoring"],
        },
    ]

    results = []

    for service in services:
        context = InvoiceContext(
            user_input=service["servizio"],
            servizio_base=service["servizio"],
            ore_lavorate=service["ore"],
            tecnologie=service["tech"],
        )

        response = await agent.execute(context)
        results.append(response)

        if response.metadata.get("is_structured"):
            model = response.metadata["parsed_model"]
            print(f"\n✅ {service['servizio'].upper()}")
            print(f"   Ore: {service['ore']}h")
            print(f"   Deliverables: {len(model['deliverables'])}")
            print(f"   Competenze: {', '.join(model['competenze'][:3])}...")

    # Show aggregate metrics
    total_tokens = sum(r.usage.total_tokens for r in results)
    total_cost = sum(r.usage.estimated_cost_usd for r in results)

    print(f"\n📊 Batch Statistics:")
    print(f"   Total requests: {len(results)}")
    print(f"   Total tokens: {total_tokens}")
    print(f"   Total cost: ${total_cost:.4f}")

    # Show agent metrics
    metrics = agent.get_metrics()
    print(f"\n🤖 Agent Metrics:")
    print(f"   Avg tokens/request: {metrics['avg_tokens_per_request']:.0f}")
    print(f"   Avg cost/request: ${metrics['avg_cost_per_request']:.4f}")


async def example_5_error_handling():
    """Example 5: Error handling and validation."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Error Handling")
    print("=" * 80 + "\n")

    provider = create_provider()
    agent = InvoiceAssistantAgent(provider=provider)

    # Test 1: Empty servizio_base (should fail validation)
    print("Test 1: Empty servizio_base")
    context = InvoiceContext(
        user_input="",
        servizio_base="",
        ore_lavorate=5.0,
    )

    response = await agent.execute(context)
    print(f"Status: {response.status.value}")
    print(f"Error: {response.error}\n")

    # Test 2: Negative hours (should fail validation)
    print("Test 2: Negative hours")
    context = InvoiceContext(
        user_input="test",
        servizio_base="test service",
        ore_lavorate=-5.0,
    )

    response = await agent.execute(context)
    print(f"Status: {response.status.value}")
    print(f"Error: {response.error}\n")

    # Test 3: Valid input (should succeed)
    print("Test 3: Valid input")
    context = InvoiceContext(
        user_input="consulenza",
        servizio_base="consulenza IT",
        ore_lavorate=2.0,
    )

    response = await agent.execute(context)
    print(f"Status: {response.status.value}")
    if response.metadata.get("is_structured"):
        print(f"Success! Generated {len(response.metadata['parsed_model']['deliverables'])} deliverables")


async def main():
    """Run all examples."""
    print("\n🤖 Invoice Assistant - Usage Examples")
    print("=" * 80)

    # Run examples
    await example_1_basic_description()
    await example_2_with_technologies()
    await example_3_with_client()
    await example_4_batch_descriptions()
    await example_5_error_handling()

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
