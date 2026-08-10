#!/usr/bin/env python3
"""Script per validare gli schemi di tutti i tool OpenAI."""

import json

from openfatture.ai.tools.registry import get_tool_registry

# Inizializza registry e carica tutti i tool
registry = get_tool_registry()
all_tools = registry.list_tools()

print(f"\nValidazione di {len(all_tools)} tool registrati...\n")

errors = []
warnings = []
validated = 0

for tool in all_tools:
    tool_name = tool.name

    try:
        # Genera schema OpenAI
        openai_schema = tool.to_openai_function()

        # Validazione 1: Verifica che lo schema sia JSON serializable
        try:
            json.dumps(openai_schema)
        except (TypeError, ValueError) as e:
            errors.append(f"{tool_name}: Schema non serializzabile in JSON - {e}")
            continue

        # Validazione 2: Verifica campi obbligatori OpenAI
        required_fields = ["name", "description", "parameters"]
        for field in required_fields:
            if field not in openai_schema:
                errors.append(f"{tool_name}: Campo obbligatorio mancante '{field}'")

        # Validazione 3: Verifica struttura parameters
        if "parameters" in openai_schema:
            params = openai_schema["parameters"]

            # Deve essere un object con type, properties, required
            if params.get("type") != "object":
                errors.append(
                    f"{tool_name}: parameters.type deve essere 'object', trovato '{params.get('type')}'"
                )

            if "properties" not in params:
                errors.append(f"{tool_name}: parameters.properties mancante")
                continue

            # Validazione 4: Verifica ogni parametro
            for param_name, param_schema in params.get("properties", {}).items():
                # Verifica type obbligatorio
                if "type" not in param_schema:
                    errors.append(f"{tool_name}.{param_name}: Campo 'type' mancante")
                    continue

                param_type = param_schema["type"]

                # Validazione 5: ARRAY deve avere items
                if param_type == "array":
                    if "items" not in param_schema:
                        errors.append(
                            f"{tool_name}.{param_name}: Parametro ARRAY senza campo 'items' (BLOCKER per OpenAI)"
                        )
                    else:
                        # Verifica che items sia un dict valido
                        items = param_schema["items"]
                        if not isinstance(items, dict):
                            errors.append(
                                f"{tool_name}.{param_name}: Campo 'items' deve essere un object, trovato {type(items)}"
                            )
                        elif "type" not in items:
                            warnings.append(
                                f"{tool_name}.{param_name}: items senza campo 'type' (raccomandato)"
                            )

                # Validazione 6: description raccomandata
                if "description" not in param_schema:
                    warnings.append(f"{tool_name}.{param_name}: Manca 'description' (raccomandato)")

        # Validazione 7: description non vuota
        if not openai_schema.get("description"):
            warnings.append(f"{tool_name}: Description vuota (raccomandato)")

        validated += 1

    except Exception as e:
        errors.append(f"{tool_name}: Errore durante validazione - {e}")

# Stampa report
print("=" * 80)
print("REPORT VALIDAZIONE TOOL SCHEMAS")
print("=" * 80)

print(f"\nTool validati con successo: {validated}/{len(all_tools)}")

if errors:
    print(f"\nERRORI CRITICI ({len(errors)}):")
    print("-" * 80)
    for error in errors:
        print(f"  {error}")
else:
    print("\nNessun errore critico!")

if warnings:
    print(f"\nWARNING ({len(warnings)}):")
    print("-" * 80)
    for warning in warnings[:10]:  # Mostra solo primi 10 warning
        print(f"  {warning}")
    if len(warnings) > 10:
        print(f"  ... e altri {len(warnings) - 10} warning")
else:
    print("\nNessun warning!")

print("\n" + "=" * 80)

if errors:
    print("\nVALIDAZIONE FALLITA - Fix richiesti prima di usare con OpenAI API")
    exit(1)
else:
    print("\nVALIDAZIONE COMPLETATA - Tutti gli schemi sono validi!")

    # Stampa esempio di schema generato per il tool problematico
    print("\nEsempio schema generato per 'create_preventivo':")
    print("-" * 80)
    preventivo_tool = next((t for t in all_tools if t.name == "create_preventivo"), None)
    if preventivo_tool:
        schema = preventivo_tool.to_openai_function()
        print(json.dumps(schema, indent=2))

    exit(0)
