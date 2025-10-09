"""Invoice service layer with business logic."""

from pathlib import Path

from openfatture.sdi.validator.xsd_validator import FatturaPAValidator
from openfatture.sdi.xml_builder.fatturapa import FatturaPABuilder, generate_filename
from openfatture.storage.database.models import Fattura
from openfatture.utils.config import Settings


class InvoiceService:
    """Service for invoice operations."""

    def __init__(self, settings: Settings):
        """Initialize service."""
        self.settings = settings
        self.xml_builder = FatturaPABuilder(settings)
        self.validator = FatturaPAValidator()

    def generate_xml(self, fattura: Fattura, validate: bool = True) -> tuple[str, str | None]:
        """
        Generate FatturaPA XML for invoice.

        Args:
            fattura: Invoice model
            validate: Whether to validate against XSD (default: True)

        Returns:
            tuple[str, Optional[str]]: (xml_content, error_message)
        """
        try:
            # Generate filename
            filename = generate_filename(fattura, self.settings)
            output_path = self.settings.archivio_dir / "xml" / filename

            # Build XML
            xml_content = self.xml_builder.build(fattura, output_path)

            # Validate if requested
            if validate:
                is_valid, error = self.validator.validate(xml_content)
                if not is_valid:
                    return xml_content, f"Validation failed: {error}"

            # Update fattura record
            fattura.xml_path = str(output_path)

            return xml_content, None

        except Exception as e:
            return "", f"Error generating XML: {e}"

    def get_xml_path(self, fattura: Fattura) -> Path:
        """Get path where XML would be saved."""
        filename = generate_filename(fattura, self.settings)
        return self.settings.archivio_dir / "xml" / filename
