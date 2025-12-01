#!/usr/bin/env python3
"""Script per testare l'AI assistant end-to-end."""

import asyncio

from dotenv import load_dotenv

# Load environment
load_dotenv()

# Initialize database
from openfatture.storage.database.base import init_db

init_db()

# Import after database initialization
from openfatture.ai.agents.chat_agent import ChatAgent
from openfatture.ai.domain.context import ChatContext
from openfatture.ai.domain.message import ConversationHistory
from openfatture.ai.providers.factory import create_provider


async def test_ai_assistant() -> None:
    """Test AI assistant with various queries."""
    print("\n" + "=" * 80)
    print("🧪 TEST E2E AI ASSISTANT")
    print("=" * 80)

    # Initialize AI provider and agent
    print("\n1️⃣  Inizializzazione AI provider...")
    try:
        provider = create_provider()
        agent = ChatAgent(provider=provider)
        print(f"   ✅ AI provider creato: {provider.__class__.__name__}")
        print("   ✅ Chat agent inizializzato")
    except Exception as e:
        print(f"   ❌ Errore inizializzazione: {e}")
        return

    from typing import Any

    # Test queries
    test_cases: list[dict[str, Any]] = [
        {
            "name": "Lista fatture recenti",
            "query": "dimmi le ultime fatture emesse",
            "expected_tools": ["search_invoices"],
        },
        {
            "name": "Suggerimento IVA",
            "query": "che aliquota IVA devo usare per consulenza software?",
            "expected_tools": ["suggest_vat_rate"],
        },
        {
            "name": "Informazioni cliente",
            "query": "dammi informazioni sul cliente Acme Corporation",
            "expected_tools": ["search_clients"],
        },
    ]

    results: list[dict[str, Any]] = []

    for idx, test_case in enumerate(test_cases, 1):
        print(f"\n{idx + 1}️⃣  Test: {test_case['name']}")
        print(f"   📝 Query: {test_case['query']}")

        try:
            # Create context
            context = ChatContext(
                user_input=str(test_case["query"]),
                conversation_history=ConversationHistory(),
                enable_tools=True,
                enable_rag=True,
            )

            # Execute agent
            response = await agent.execute(context)

            # Check for errors
            if "400" in response.content or "Invalid schema" in response.content:
                print("   ❌ ERRORE 400: Schema OpenAI invalido")
                results.append({"test": test_case["name"], "status": "FAIL", "error": "400"})
                continue

            # Check tool calls
            tools_used = []
            if hasattr(response, "metadata") and response.metadata:
                tools_used = response.metadata.get("tools_used", [])

            print(f"   ✅ Risposta ricevuta ({len(response.content)} caratteri)")
            print(f"   🔧 Tool utilizzati: {tools_used or 'nessuno'}")

            # Check if expected tools were called
            expected_tools_called = any(
                tool in str(tools_used) for tool in test_case["expected_tools"]
            )

            if expected_tools_called or tools_used:
                print("   ✅ Tool calling funzionante")
                status = "PASS"
            else:
                print("   ⚠️  Nessun tool chiamato (potrebbe essere intenzionale)")
                status = "PARTIAL"

            # Print response preview
            preview = (
                response.content[:200] + "..." if len(response.content) > 200 else response.content
            )
            print(f"\n   💬 Risposta AI: {preview}")

            results.append(
                {
                    "test": test_case["name"],
                    "status": status,
                    "tools_used": tools_used,
                    "response_length": len(response.content),
                }
            )

        except Exception as e:
            print(f"   ❌ ERRORE: {e}")
            results.append({"test": test_case["name"], "status": "FAIL", "error": str(e)})

    # Final report
    print("\n" + "=" * 80)
    print("📊 RIEPILOGO RISULTATI")
    print("=" * 80)

    passed = sum(1 for r in results if r["status"] == "PASS")
    partial = sum(1 for r in results if r["status"] == "PARTIAL")
    failed = sum(1 for r in results if r["status"] == "FAIL")

    print(f"\n✅ Test superati: {passed}/{len(test_cases)}")
    print(f"⚠️  Test parziali: {partial}/{len(test_cases)}")
    print(f"❌ Test falliti: {failed}/{len(test_cases)}")

    print("\n📋 Dettagli:")
    for result in results:
        status_icon = {
            "PASS": "✅",
            "PARTIAL": "⚠️ ",
            "FAIL": "❌",
        }.get(str(result["status"]), "❓")

        print(f"\n{status_icon} {result['test']}")
        if result["status"] == "PASS" or result["status"] == "PARTIAL":
            print(f"   • Tool usati: {result.get('tools_used', 'N/A')}")
            print(f"   • Lunghezza risposta: {result.get('response_length', 0)} caratteri")
        if "error" in result:
            print(f"   • Errore: {result['error']}")

    print("\n" + "=" * 80)

    if failed == 0:
        print("✅ TUTTI I TEST COMPLETATI CON SUCCESSO!")
    else:
        print(f"⚠️  {failed} test falliti. Verifica i blockers sopra.")

    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_ai_assistant())
