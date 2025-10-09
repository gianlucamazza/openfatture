"""XSD validator for FatturaPA XML."""

from pathlib import Path

from lxml import etree


class FatturaPAValidator:
    """
    Validator for FatturaPA XML against official XSD schema.

    The XSD schema should be downloaded from:
    https://www.fatturapa.gov.it/export/documenti/fatturapa/v1.2.2/Schema_del_file_xml_FatturaPA_v1.2.2.xsd
    """

    def __init__(self, xsd_path: Path | None = None):
        """
        Initialize validator.

        Args:
            xsd_path: Path to FatturaPA XSD schema file.
                     If not provided, looks in data directory.
        """
        self.xsd_path = xsd_path or self._get_default_xsd_path()
        self._schema: etree.XMLSchema | None = None

    @staticmethod
    def _get_default_xsd_path() -> Path:
        """Get default XSD path in data directory."""
        from openfatture.utils.config import get_settings

        settings = get_settings()
        return settings.data_dir / "schemas" / "FatturaPA_v1.2.2.xsd"

    def load_schema(self) -> None:
        """
        Load XSD schema from file.

        Raises:
            FileNotFoundError: If XSD file doesn't exist
            etree.XMLSchemaParseError: If XSD is invalid
        """
        if not self.xsd_path.exists():
            raise FileNotFoundError(
                f"XSD schema not found at: {self.xsd_path}\n"
                "Download from: "
                "https://www.fatturapa.gov.it/export/documenti/fatturapa/v1.2.2/"
                "Schema_del_file_xml_FatturaPA_v1.2.2.xsd"
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

        # Parse XML
        try:
            xml_doc = etree.fromstring(xml_content.encode("utf-8"))
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


def download_xsd_schema(auto_download: bool = False) -> Path:
    """
    Download official FatturaPA XSD schema.

    Args:
        auto_download: If True, automatically downloads the schema if missing.
                      If False, raises FileNotFoundError with instructions.

    Returns:
        Path: Path to downloaded schema

    Raises:
        FileNotFoundError: If schema not found and auto_download is False
        urllib.error.URLError: If download fails (network error, timeout)
        IOError: If file write fails

    Note:
        Downloads from official FatturaPA government source.
        For production, consider bundling the XSD with the package instead.
    """
    import urllib.request

    from openfatture.utils.config import get_settings

    settings = get_settings()
    schema_dir = settings.data_dir / "schemas"
    schema_dir.mkdir(parents=True, exist_ok=True)

    schema_path = schema_dir / "FatturaPA_v1.2.2.xsd"

    # If schema already exists, return it
    if schema_path.exists():
        return schema_path

    # If auto_download is disabled, provide manual instructions
    if not auto_download:
        raise FileNotFoundError(
            f"XSD schema not found at: {schema_path}\n\n"
            "Please download manually from:\n"
            "https://www.fatturapa.gov.it/export/documenti/fatturapa/v1.2.2/"
            "Schema_del_file_xml_FatturaPA_v1.2.2.xsd\n\n"
            f"And save it to: {schema_path}\n\n"
            "Or call download_xsd_schema(auto_download=True) to download automatically."
        )

    # Download the schema
    schema_url = (
        "https://www.fatturapa.gov.it/export/documenti/fatturapa/v1.2.2/"
        "Schema_del_file_xml_FatturaPA_v1.2.2.xsd"
    )

    try:
        # Download with timeout
        with urllib.request.urlopen(schema_url, timeout=30) as response:
            schema_content = response.read()

        # Write to file
        schema_path.write_bytes(schema_content)

        return schema_path

    except urllib.error.URLError as e:
        raise urllib.error.URLError(
            f"Failed to download XSD schema from {schema_url}\n"
            f"Error: {e}\n"
            "Please check your internet connection or download manually."
        ) from e
    except OSError as e:
        raise OSError(
            f"Failed to write XSD schema to {schema_path}\n"
            f"Error: {e}\n"
            "Please check file permissions."
        ) from e
