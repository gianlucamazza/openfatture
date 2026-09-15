"""XSD validator for FatturaPA XML."""

from importlib.resources import files
from pathlib import Path

from lxml import etree


class LocalSchemaResolver(etree.Resolver):
    """
    Custom resolver for loading local XSD schemas.

    Resolves schema imports from the bundled schemas directory,
    enabling offline validation without network access.
    """

    def __init__(self, schema_dir: Path):
        """
        Initialize resolver.

        Args:
            schema_dir: Directory containing the schema files
        """
        super().__init__()
        self.schema_dir = schema_dir

    def resolve(self, url: str, id: str, context: etree._ResolverContext) -> etree.Resolver:
        """
        Resolve schema URL to local file.

        Args:
            url: Schema URL or filename
            id: Schema identifier
            context: Resolution context

        Returns:
            Resolver for the local file
        """
        # Extract filename from URL if it's a full URL
        if "/" in url:
            filename = url.split("/")[-1]
        else:
            filename = url

        # Try to read from bundled schemas using importlib.resources
        try:
            schema_files = files("openfatture.sdi.schemas")
            schema_bytes = (schema_files / filename).read_bytes()
            return self.resolve_string(schema_bytes, context)
        except (FileNotFoundError, AttributeError):
            # Fall back to filesystem if not in package resources
            local_path = self.schema_dir / filename
            if local_path.exists():
                return self.resolve_filename(str(local_path), context)

        # If not found locally, let lxml handle it (may fail for HTTP URLs)
        return None


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

    @staticmethod
    def _get_bundled_schema_path() -> Path:
        """Get path to bundled FatturaPA XSD schema."""
        schema_files = files("openfatture.sdi.schemas")
        schema_file = schema_files / "FatturaPA_v1.2.2.xsd"
        # Convert to Path - for Python 3.9+ this is a Traversable, need to get actual path
        if hasattr(schema_file, "__fspath__"):
            return Path(schema_file)
        # For older versions or zip imports, we need to extract
        return Path(str(schema_file))

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
            schema_files = files("openfatture.sdi.schemas")
            schema_bytes = (schema_files / "FatturaPA_v1.2.2.xsd").read_bytes()

            # Parse with a custom resolver to handle the local xmldsig import
            schema_dir = Path(str(schema_files))
            parser = etree.XMLParser()
            parser.resolvers.add(LocalSchemaResolver(schema_dir))

            schema_doc = etree.fromstring(schema_bytes, parser)
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
    Download official FatturaPA XSD schema to data directory.

    Note: FatturaPAValidator now uses bundled schemas by default (no download needed).
    This function is retained for backward compatibility and custom workflows that
    need schemas in the data directory.

    Args:
        auto_download: If True, automatically downloads the schema if missing.
                      If False, raises FileNotFoundError with instructions.

    Returns:
        Path: Path to downloaded schema

    Raises:
        FileNotFoundError: If schema not found and auto_download is False
        urllib.error.URLError: If download fails (network error, timeout)
        IOError: If file write fails
    """
    import urllib.request

    from openfatture.platform.config import get_settings

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
