#!/usr/bin/env python3
"""Monitor client creation and sync to external CRM.

DESCRIPTION: Sync new clients to external CRM system
TIMEOUT: 15

This hook is triggered when a new client is created.
Environment variables available:
    - OPENFATTURE_CLIENT_ID: Client database ID
    - OPENFATTURE_CLIENT_NAME: Client name/company name
    - OPENFATTURE_PARTITA_IVA: VAT number (if provided)
    - OPENFATTURE_CODICE_FISCALE: Tax code (if provided)
    - OPENFATTURE_CODICE_DESTINATARIO: SDI code (if provided)
    - OPENFATTURE_PEC: PEC email address (if provided)
"""

import json
import os
from datetime import datetime


def main():
    """Process client creation event."""
    # Extract event data from environment
    client_id = os.environ.get("OPENFATTURE_CLIENT_ID")
    client_name = os.environ.get("OPENFATTURE_CLIENT_NAME")
    partita_iva = os.environ.get("OPENFATTURE_PARTITA_IVA")
    codice_fiscale = os.environ.get("OPENFATTURE_CODICE_FISCALE")
    codice_destinatario = os.environ.get("OPENFATTURE_CODICE_DESTINATARIO")
    pec = os.environ.get("OPENFATTURE_PEC")

    print("👥 New Client Created")
    print("=" * 50)
    print(f"Client ID: {client_id}")
    print(f"Name: {client_name}")
    if partita_iva:
        print(f"P.IVA: {partita_iva}")
    if codice_fiscale:
        print(f"Codice Fiscale: {codice_fiscale}")
    if codice_destinatario:
        print(f"SDI Code: {codice_destinatario}")
    if pec:
        print(f"PEC: {pec}")
    print("=" * 50)

    # Example: Sync to external CRM
    client_data = {
        "id": client_id,
        "name": client_name,
        "vat_number": partita_iva,
        "tax_code": codice_fiscale,
        "sdi_code": codice_destinatario,
        "pec": pec,
        "created_at": datetime.now().isoformat(),
        "source": "OpenFatture",
    }

    # Uncomment to sync to external CRM
    # import requests
    # response = requests.post(
    #     "https://your-crm.com/api/clients",
    #     json=client_data,
    #     headers={"Authorization": f"Bearer {os.environ.get('CRM_API_KEY')}"}
    # )
    # if response.status_code == 201:
    #     print("✅ Client synced to CRM")
    # else:
    #     print(f"⚠️  CRM sync failed: {response.status_code}")

    # Log to file for audit trail
    log_file = os.path.expanduser("~/.openfatture/logs/client-events.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    log_entry = {
        "event": "client_created",
        "timestamp": datetime.now().isoformat(),
        "client_id": client_id,
        "client_name": client_name,
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    print("\n✅ Hook executed successfully")
    print(f"📝 Event logged to: {log_file}")


if __name__ == "__main__":
    main()
