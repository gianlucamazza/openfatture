# XSD Validation in OpenFatture

OpenFatture includes offline XSD validation for FatturaPA electronic invoices using bundled official schemas.

## Quick Start

```python
from openfatture.sdi.validator.xsd_validator import FatturaPAValidator

# Initialize validator (uses bundled schemas by default)
validator = FatturaPAValidator()

# Validate XML string
is_valid, error = validator.validate(xml_content)
if is_valid:
    print("✓ Invoice is valid")
else:
    print(f"✗ Validation error: {error}")

# Or validate a file
is_valid, error = validator.validate_file(Path("invoice.xml"))
```

## Bundled Schemas

Starting from version 2.3.1, OpenFatture bundles the official XSD schemas as package resources, enabling:

- **Offline validation**: No network access required
- **CI/CD compatibility**: Works in isolated build environments
- **Deterministic behavior**: No dependency on external server availability

### Included Schemas

The package includes two schemas in `openfatture/sdi/schemas/`:

1. **FatturaPA_v1.2.2.xsd**
   - Source: Agenzia delle Entrate
   - URL: https://www.fatturapa.gov.it/export/documenti/fatturapa/v1.2.2/Schema_del_file_xml_FatturaPA_v1.2.2.xsd
   - Version: 1.2.2
   - Modified: `xs:import` schemaLocation changed to local reference

2. **xmldsig-core-schema.xsd**
   - Source: W3C XML Signature Recommendation
   - URL: http://www.w3.org/TR/2002/REC-xmldsig-core-20020212/xmldsig-core-schema.xsd
   - Version: 2002-02-12
   - Purpose: Defines XML Digital Signature elements

See `openfatture/sdi/schemas/README.md` for complete schema documentation.

## Why Bundle Schemas?

### The Problem

The official FatturaPA XSD imports the W3C xmldsig schema via HTTP:

```xml
<xs:import namespace="http://www.w3.org/2000/09/xmldsig#" 
           schemaLocation="http://www.w3.org/TR/2002/REC-xmldsig-core-20020212/xmldsig-core-schema.xsd" />
```

By default, lxml's `XMLSchema` does **not** resolve remote HTTP imports, causing:
- Schema load failures ("QName 'Signature' does not resolve")
- Validation always fails even for valid invoices
- Network dependency for what should be offline validation

### The Solution

OpenFatture bundles both schemas and uses a custom `LocalSchemaResolver` that:
1. Resolves imports from package resources (via `importlib.resources`)
2. Falls back to filesystem if needed
3. Never requires network access

The bundled FatturaPA schema has been modified to use a local schemaLocation:

```xml
<xs:import namespace="http://www.w3.org/2000/09/xmldsig#" 
           schemaLocation="xmldsig-core-schema.xsd" />
```

## API Reference

### FatturaPAValidator

```python
class FatturaPAValidator:
    def __init__(self, xsd_path: Path | None = None):
        """
        Initialize validator.
        
        Args:
            xsd_path: Optional custom XSD path. If None (default), 
                     uses bundled schemas.
        """
    
    def validate(self, xml_content: str) -> tuple[bool, str | None]:
        """
        Validate XML string.
        
        Returns:
            (is_valid, error_message) tuple
        """
    
    def validate_file(self, xml_path: Path) -> tuple[bool, str | None]:
        """
        Validate XML file.
        
        Returns:
            (is_valid, error_message) tuple
        """
```

### Custom Schema Path (Optional)

For backward compatibility or custom workflows, you can provide your own schema:

```python
validator = FatturaPAValidator(xsd_path=Path("/path/to/custom.xsd"))
```

## Testing

The test suite includes:

- `test_bundled_schema_loads_successfully`: Verifies schema loads without errors
- `test_validate_minimal_fatturapa_xml`: Validates a minimal FatturaPA fixture
- `test_bundled_schema_resolves_xmldsig_offline`: Confirms xmldsig resolves locally

Run validation tests:

```bash
uv run python -m pytest tests/unit/test_xsd_validator.py::TestBundledSchemas -v
```

## Integration with OpenFatture Cloud

OpenFatture Cloud can now assert real XSD validation success instead of softening failures as "namespace quirks":

1. Pin to openfatture >= 2.3.1 in Cloud dependencies
2. Use `FatturaPAValidator` directly (no schema downloads)
3. Assert `is_valid is True` for happy-path validation

No need to vendor schemas into openfatture-cloud; the fix is in the OSS package.

## Schema Updates

To update schemas in the future:

1. Download new schemas from official sources (see `schemas/README.md`)
2. Modify FatturaPA XSD to use local xmldsig schemaLocation
3. Place in `openfatture/sdi/schemas/`
4. Update version references in docs
5. Test with `tests/fixtures/minimal_fatturapa.xml`

## References

- [FatturaPA Official Site](https://www.fatturapa.gov.it/)
- [W3C XML Signature](https://www.w3.org/TR/xmldsig-core/)
- [lxml XMLSchema documentation](https://lxml.de/validation.html#xmlschema)
- Package schema source: `openfatture/sdi/schemas/README.md`
