# FatturaPA XSD Schemas

This directory contains the official XSD schemas required for validating FatturaPA electronic invoices.

## Files

### FatturaPA_v1.2.2.xsd
- **Source**: Agenzia delle Entrate - Fatturazione Elettronica
- **Original URL**: https://www.fatturapa.gov.it/export/documenti/fatturapa/v1.2.2/Schema_del_file_xml_FatturaPA_v1.2.2.xsd
- **Version**: 1.2.2
- **Modified**: The `xs:import` schemaLocation for xmldsig has been changed from the HTTP URL to a local file reference (`xmldsig-core-schema.xsd`) to enable offline validation.

### xmldsig-core-schema.xsd
- **Source**: W3C XML Signature Syntax and Processing
- **Original URL**: http://www.w3.org/TR/2002/REC-xmldsig-core-20020212/xmldsig-core-schema.xsd
- **Version**: 2002-02-12 (W3C Recommendation)
- **Purpose**: Defines the XML Digital Signature elements referenced by the FatturaPA schema.

## Why Bundle Schemas?

The official FatturaPA XSD imports the W3C xmldsig schema via an HTTP URL. By default, lxml's `XMLSchema` does not resolve remote imports, causing validation to fail. Bundling both schemas as package resources and using a local `schemaLocation` allows:

1. **Offline validation**: No network access required
2. **CI/CD reliability**: Tests and validation work in isolated environments
3. **Deterministic behavior**: No dependency on external server availability

## License Notes

- **FatturaPA XSD**: Published by the Italian Revenue Agency (Agenzia delle Entrate) for public use in electronic invoicing compliance.
- **xmldsig-core-schema.xsd**: W3C document, freely redistributable per W3C document license.
