#!/usr/bin/env python3
"""
Generate CLI .ftl translation files from extracted JSON.

This script reads I18N_STRINGS_STRUCTURED.json and generates
Fluent .ftl files for all supported locales.
"""

import json
from pathlib import Path

# Locales to generate
LOCALES = ["it", "en", "es", "fr", "de"]

# Base directory
BASE_DIR = Path(__file__).parent.parent
JSON_FILE = BASE_DIR / "I18N_STRINGS_STRUCTURED.json"
LOCALES_DIR = BASE_DIR / "openfatture" / "i18n" / "locales"


def generate_ftl_content(data: dict, locale: str) -> str:
    """Generate .ftl content for a specific locale.

    For now, we generate Italian content. Translations to other languages
    will be done manually or via translation services.
    """
    lines = []
    lines.append("# CLI commands translations")
    lines.append(f"# {locale.upper()}")
    lines.append("")

    # Process each command module
    for module_name, module_data in data.items():
        if module_name == "metadata":
            continue

        lines.append(f"## {module_name.upper()} Commands")
        lines.append("")

        # Help strings
        if "help_strings" in module_data:
            lines.append(f"### {module_name} - Help Texts")
            for item in module_data["help_strings"]:
                msg_id = item["id"]
                text = item["text"]
                lines.append(f"{msg_id} = {text}")
            lines.append("")

        # Console strings
        if "console_strings" in module_data:
            lines.append(f"### {module_name} - Console Output")
            for item in module_data["console_strings"]:
                msg_id = item["id"]
                # Get text, handling possible dict format
                if isinstance(item.get("text"), dict):
                    text = item["text"].get("text", "")
                else:
                    text = item.get("text", "")

                # Clean Rich markup for now (will be preserved in actual implementation)
                # Just keep the core text
                if text:
                    lines.append(f"{msg_id} = {text}")
            lines.append("")

        # Prompts
        if "prompts" in module_data:
            lines.append(f"### {module_name} - Prompts")
            for item in module_data["prompts"]:
                msg_id = item["id"]
                text = item.get("text", item.get("message", ""))
                if text:
                    lines.append(f"{msg_id} = {text}")
            lines.append("")

        # Table labels
        if "table_labels" in module_data:
            lines.append(f"### {module_name} - Table Labels")
            for item in module_data["table_labels"]:
                msg_id = item["id"]
                text = item.get("text", item.get("label", ""))
                if text:
                    lines.append(f"{msg_id} = {text}")
            lines.append("")

    return "\n".join(lines)


def main():
    """Generate all .ftl files."""
    print(f"Reading {JSON_FILE}...")

    if not JSON_FILE.exists():
        print(f"ERROR: {JSON_FILE} not found!")
        return 1

    with open(JSON_FILE) as f:
        data = json.load(f)

    print(
        f"Loaded {data['metadata']['total_strings']} strings from {len(data['metadata']['source_files'])} files"
    )

    # Generate for Italian first (reference implementation)
    for locale in ["it"]:  # Start with Italian only
        locale_dir = LOCALES_DIR / locale
        locale_dir.mkdir(parents=True, exist_ok=True)

        output_file = locale_dir / "cli.ftl"

        print(f"\nGenerating {output_file}...")
        content = generate_ftl_content(data, locale)

        output_file.write_text(content, encoding="utf-8")
        print(f"✅ Written {len(content.splitlines())} lines to {output_file}")

    print("\n✅ Italian CLI translations generated!")
    print("\nNext steps:")
    print("1. Review openfatture/i18n/locales/it/cli.ftl")
    print("2. Translate to EN, ES, FR, DE (manually or via translation service)")
    print("3. Start converting CLI code to use _()")

    return 0


if __name__ == "__main__":
    exit(main())
