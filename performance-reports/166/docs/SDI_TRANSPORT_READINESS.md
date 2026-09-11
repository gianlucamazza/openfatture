# SDI Transport Readiness Guide

This document describes the infrastructure and configuration needed for live SDI (Sistema di Interscambio) and PEC (Posta Elettronica Certificata) transmission of FatturaPA invoices.

## ⚠️ IMPORTANT: No Live Transmission

**This implementation includes XML generation and validation only. Live SDI/PEC transmission is NOT implemented and requires additional security, legal, and infrastructure setup.**

## Prerequisites for Live Transmission

### 1. Digital Certificates

FatturaPA XML must be digitally signed before transmission to SDI.

**Certificate Directory Structure:**
```
data/
└── certs/
    ├── signing/
    │   ├── certificate.pem     # Your digital signature certificate
    │   ├── private_key.pem     # Private key (KEEP SECURE!)
    │   └── ca_chain.pem        # Certificate authority chain
    └── ssl/
        ├── client.crt          # SSL client certificate (for HTTPS)
        └── client.key          # SSL client key
```

**Certificate Requirements:**
- Certificate must be issued by a qualified trust service provider (TSP)
- Must be a QES (Qualified Electronic Signature) certificate
- Common providers: InfoCert, Aruba, Poste Italiane
- Certificate must be registered with the Agenzia delle Entrate

**Security Notes:**
- Store private keys securely (consider HSM for production)
- Set file permissions: `chmod 600 private_key.pem`
- Never commit certificates to version control
- Rotate certificates before expiration

### 2. PEC Configuration

For clients without a Codice Destinatario (using `0000000`), invoices are sent via PEC.

**SMTP Configuration (Environment Variables):**
```bash
# PEC SMTP Server
export OPENFATTURE_PEC_SMTP_SERVER="smtps.pec.aruba.it"
export OPENFATTURE_PEC_SMTP_PORT="465"
export OPENFATTURE_PEC_USERNAME="your-pec@pec.it"
export OPENFATTURE_PEC_PASSWORD="your-secure-password"

# Enable TLS/SSL
export OPENFATTURE_PEC_USE_TLS="true"

# Sender email (your PEC address)
export OPENFATTURE_PEC_FROM_ADDRESS="your-pec@pec.it"
```

**PEC Provider Examples:**
- **Aruba PEC:**
  - Server: `smtps.pec.aruba.it`
  - Port: `465` (SSL/TLS)
  
- **Aruba Business:**
  - Server: `smtps.aruba.it`
  - Port: `465` (SSL/TLS)

- **Poste Italiane:**
  - Server: `smtp.pec.aruba.it`
  - Port: `465` (SSL/TLS)

### 3. SDI Channel Configuration

There are three ways to transmit to SDI:

#### Option A: Direct Transmission (FTP/HTTPS)
- Requires registration with Agenzia delle Entrate
- FTP credentials provided after registration
- Endpoint: `https://sdi.fatturapa.gov.it` or FTP server

**Configuration:**
```bash
export OPENFATTURE_SDI_CHANNEL="direct"
export OPENFATTURE_SDI_USERNAME="your-sdi-username"
export OPENFATTURE_SDI_PASSWORD="your-sdi-password"
export OPENFATTURE_SDI_ENDPOINT="https://sdi.fatturapa.gov.it/SdiRiceviFile"
```

#### Option B: Intermediary Service
- Use certified intermediary (Aruba, TeamSystem, etc.)
- They handle SDI transmission, certificate management, and notifications
- API credentials provided by the service

**Example Configuration (Aruba):**
```bash
export OPENFATTURE_SDI_CHANNEL="aruba"
export OPENFATTURE_SDI_API_USERNAME="your-aruba-username"
export OPENFATTURE_SDI_API_PASSWORD="your-aruba-password"
export OPENFATTURE_SDI_API_ENDPOINT="https://ws.fatturapa.aruba.it/services"
```

#### Option C: PEC Only (No Direct SDI)
- Send signed XML via PEC to `sdi01@pec.fatturapa.it`
- Simpler setup, slower processing
- Still requires digital signature

**Configuration:**
```bash
export OPENFATTURE_SDI_CHANNEL="pec"
export OPENFATTURE_SDI_PEC_ADDRESS="sdi01@pec.fatturapa.it"
```

## Implementation Checklist

Before enabling live transmission, ensure:

### Legal & Compliance
- [ ] Company registered for electronic invoicing with Agenzia delle Entrate
- [ ] VAT number and fiscal code verified
- [ ] Legal representative identified
- [ ] Privacy policy updated for electronic invoicing data

### Technical Setup
- [ ] Digital signature certificate obtained and installed
- [ ] Certificate registered with Agenzia delle Entrate
- [ ] PEC account activated and tested
- [ ] Certificate directory structure created with secure permissions
- [ ] Environment variables configured
- [ ] XML signature library integrated (e.g., `xmlsec`)

### Testing
- [ ] Generated XML validates against official XSD schema
- [ ] Test invoices validated with [FatturaPA Validator](https://sdi.fatturapa.gov.it/SdI2FatturaPAWeb/AccediAlServizioAction.do?pagina=Verifica_File_Xml)
- [ ] Digital signature applied and verified
- [ ] PEC sending tested (with test recipient)
- [ ] SDI test environment used (if direct transmission)

### Production Readiness
- [ ] Backup and recovery procedures in place
- [ ] Monitoring and alerting configured
- [ ] Log retention policy defined
- [ ] Error handling and retry logic implemented
- [ ] SDI notification handling implemented (RC, NS, MC, NE, DT, AT, EC)

## Hard Gates

The following are HARD REQUIREMENTS before any live transmission:

1. **Digital Signature**: XML must be signed with a qualified certificate
2. **XSD Validation**: XML must validate against FatturaPA_v1.2.2.xsd
3. **Test Mode First**: Use SDI test environment before production
4. **Legal Authorization**: Only authorized personnel can enable transmission

## Code Integration Points

When implementing transmission, these areas need attention:

### XML Signature
```python
# Example integration point (NOT IMPLEMENTED)
from openfatture.sdi.signature import sign_xml


def prepare_for_sdi(fattura: Fattura) -> Path:
    """Prepare invoice for SDI transmission."""
    # 1. Generate XML
    xml_content = builder.build(fattura)

    # 2. Validate against XSD
    is_valid, error = validator.validate(xml_content)
    if not is_valid:
        raise ValueError(f"Invalid XML: {error}")

    # 3. Sign XML (REQUIRES IMPLEMENTATION)
    signed_xml = sign_xml(
        xml_content=xml_content,
        certificate_path=settings.cert_path,
        private_key_path=settings.key_path,
    )

    # 4. Save signed XML
    signed_path = settings.invoices_dir / f"{fattura.numero}_signed.xml"
    signed_path.write_text(signed_xml)

    return signed_path
```

### PEC Transmission
```python
# Example integration point (NOT IMPLEMENTED)
from openfatture.sdi.transport import send_via_pec


def send_to_pec(fattura: Fattura, signed_xml_path: Path):
    """Send invoice via PEC."""
    # Requires PEC SMTP configuration
    send_via_pec(
        recipient=fattura.cliente.pec or settings.sdi_pec_address,
        subject=f"Fattura {fattura.numero}/{fattura.anno}",
        attachment=signed_xml_path,
        smtp_config=settings.pec_smtp_config,
    )
```

### SDI Notification Handling
```python
# Example integration point (NOT IMPLEMENTED)
from openfatture.sdi.notifications import process_sdi_notification


def handle_sdi_response(notification_xml: str):
    """Process SDI notification (RC, NS, MC, etc.)."""
    notification = process_sdi_notification(notification_xml)

    # Update invoice status based on notification type
    if notification.tipo == "NS":  # Notifica Scarto
        # Invoice rejected
        update_invoice_status(notification.fattura_id, StatoFattura.SCARTATA)
    elif notification.tipo == "RC":  # Ricevuta Consegna
        # Invoice delivered
        update_invoice_status(notification.fattura_id, StatoFattura.CONSEGNATA)
```

## Security Considerations

1. **Private Key Protection**: Never expose private keys in logs, errors, or version control
2. **Credential Storage**: Use environment variables or secret management (not hardcoded)
3. **Access Control**: Limit who can trigger SDI transmission
4. **Audit Logging**: Log all transmission attempts and outcomes
5. **Network Security**: Use TLS/SSL for all external communication
6. **Data Retention**: Follow legal requirements for invoice archival (10+ years)

## Testing Resources

- **Official SDI Validator**: https://sdi.fatturapa.gov.it/SdI2FatturaPAWeb/
- **Test Environment**: Available through Agenzia delle Entrate registration
- **Sample Invoices**: https://www.fatturapa.gov.it/export/documenti/fatturapa/v1.2.2/
- **XSD Schema**: Included in `data/schemas/FatturaPA_v1.2.2.xsd`

## Support & Resources

- **Agenzia delle Entrate**: https://www.agenziaentrate.gov.it/
- **FatturaPA Portal**: https://www.fatturapa.gov.it/
- **Technical Specifications**: https://www.fatturapa.gov.it/en/norme-e-regole/documentazione-fattura-elettronica/
- **Community Forum**: https://forum.italia.it/c/fattura-pa/

---

**Remember**: This is infrastructure documentation only. Implementation requires qualified professionals familiar with Italian fiscal law, digital signatures, and secure system design.
