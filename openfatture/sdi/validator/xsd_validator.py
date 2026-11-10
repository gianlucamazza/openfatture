"""XSD validator for FatturaPA XML."""

from importlib.resources import as_file, files
from pathlib import Path

from lxml import etree

from openfatture.sdi.safe_xml import parse_untrusted


class FatturaPAValidator:
    """
    Validator for FatturaPA XML against official XSD schema.

    The validator uses bundled XSD schemas (FatturaPA v1.2.2 and W3C xmldsig)
    for offline validation. Schemas are included as package resources.
    """

    def __init__(self, xsd_path: Path | None = None):
        """
        Initialize validator.

        Args:
            xsd_path: Path to FatturaPA XSD schema file.
                     If not provided, uses bundled schema from package resources.
        """
        self.xsd_path = xsd_path
        self._schema: etree.XMLSchema | None = None
        self._use_bundled = xsd_path is None

    def load_schema(self) -> None:
        """
        Load XSD schema from file.

        Uses bundled schemas by default. The bundled FatturaPA schema references
        the xmldsig-core-schema.xsd with a local schemaLocation, enabling offline
        validation without network access.

        Raises:
            FileNotFoundError: If XSD file doesn't exist (custom path only)
            etree.XMLSchemaParseError: If XSD is invalid
        """
        if self._use_bundled:
            # Use bundled schemas from package resources
            # as_file() extracts to a real filesystem path where lxml can resolve local imports
            schema_files = files("openfatture.sdi.schemas")
            with as_file(schema_files / "FatturaPA_v1.2.2.xsd") as schema_path:
                with open(schema_path, "rb") as f:
                    schema_doc = etree.parse(f)
                    self._schema = etree.XMLSchema(schema_doc)
        else:
            # Use custom path (backward compatibility)
            if self.xsd_path is None or not self.xsd_path.exists():
                raise FileNotFoundError(
                    f"XSD schema not found at: {self.xsd_path}\n"
                    "Either use the bundled schema (default) or provide a valid path."
                )

            with open(self.xsd_path, "rb") as f:
                schema_doc = etree.parse(f)
                self._schema = etree.XMLSchema(schema_doc)

    def validate(self, xml_content: str) -> tuple[bool, str | None]:
        """
        Validate XML content against FatturaPA XSD.

        Args:
            xml_content: XML string to validate

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Load schema if not already loaded
        if self._schema is None:
            try:
                self.load_schema()
            except FileNotFoundError as e:
                return False, str(e)
            if self._schema is None:
                return False, "XSD schema not available for validation."

        # Parse XML
        try:
            xml_doc = parse_untrusted(xml_content)
        except etree.XMLSyntaxError as e:
            return False, f"XML syntax error: {e}"

        # Validate against schema
        try:
            self._schema.assertValid(xml_doc)
            return True, None
        except etree.DocumentInvalid as e:
            return False, f"Validation error: {e}"

    def validate_file(self, xml_path: Path) -> tuple[bool, str | None]:
        """
        Validate XML file.

        Args:
            xml_path: Path to XML file

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not xml_path.exists():
            return False, f"File not found: {xml_path}"

        xml_content = xml_path.read_text(encoding="utf-8")
        return self.validate(xml_content)
