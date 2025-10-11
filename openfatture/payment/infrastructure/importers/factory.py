"""Factory for creating bank statement importers with auto-detection.

Implements the Factory pattern to abstract importer creation and provide
format auto-detection capabilities.
"""

import csv
from pathlib import Path
from typing import TYPE_CHECKING

from .base import BaseImporter, FileFormat

if TYPE_CHECKING:
    from .csv_importer import CSVConfig


class ImporterFactory:
    """Factory for creating importers with format auto-detection.

    Design Pattern: Factory Method + Registry Pattern
    SOLID Principle: Open/Closed (easy to add new formats)

    Features:
    - Auto-detect file format from extension and content
    - Load bank-specific presets
    - Registry for custom importer types
    - Validation of file before importer creation

    Example:
        >>> factory = ImporterFactory()
        >>> importer = factory.create_from_file(
        ...     Path("statement.csv"),
        ...     bank_preset="intesa"
        ... )
        >>> result = importer.import_transactions(account)
    """

    # Registry pattern: Format → Importer class mapping
    # Will be populated after importers are defined
    _registry: dict[FileFormat, type[BaseImporter]] = {}

    @classmethod
    def register(cls, format: FileFormat, importer_class: type[BaseImporter]) -> None:
        """Register a custom importer for a format.

        Allows extending the factory with custom importers.

        Args:
            format: File format to register for
            importer_class: Importer class to use for this format

        Example:
            >>> ImporterFactory.register(FileFormat.CSV, MyCustomCSVImporter)
        """
        cls._registry[format] = importer_class

    @staticmethod
    def detect_format(file_path: Path) -> FileFormat:
        """Auto-detect file format from extension and content.

        Detection Algorithm:
        1. Check file extension (.csv, .ofx, .qfx, .qif)
        2. Peek first 1KB of file content
        3. Look for format signatures:
           - OFX: <OFX> tag or OFXHEADER keyword
           - QIF: !Type: or !Account: headers
           - CSV: Detect delimiter with csv.Sniffer

        Args:
            file_path: Path to statement file

        Returns:
            Detected FileFormat or FileFormat.UNKNOWN

        Example:
            >>> format = ImporterFactory.detect_format(Path("statement.csv"))
            >>> assert format == FileFormat.CSV
        """
        if not file_path.exists():
            return FileFormat.UNKNOWN

        # Check extension first (fastest)
        extension = file_path.suffix.lower()
        extension_map = {
            ".csv": FileFormat.CSV,
            ".ofx": FileFormat.OFX,
            ".qfx": FileFormat.OFX,  # OFX variant
            ".qif": FileFormat.QIF,
        }

        if extension in extension_map:
            detected = extension_map[extension]

            if ImporterFactory._verify_format(file_path, detected):
                return detected

        # Fallback: Content-based detection
        return ImporterFactory._detect_from_content(file_path)

    @staticmethod
    def _verify_format(file_path: Path, expected_format: FileFormat) -> bool:
        """Verify format by peeking at file content.

        Args:
            file_path: Path to file
            expected_format: Format to verify

        Returns:
            True if content matches expected format
        """
        try:
            with open(file_path, "rb") as f:
                # Read first 1KB
                sample = f.read(1024).decode("utf-8", errors="ignore")

            if expected_format == FileFormat.OFX:
                return "<OFX>" in sample or "OFXHEADER" in sample

            elif expected_format == FileFormat.QIF:
                return "!Type:" in sample or "!Account:" in sample

            elif expected_format == FileFormat.CSV:
                # Try csv.Sniffer
                try:
                    dialect = csv.Sniffer().sniff(sample)
                    delimiter = getattr(dialect, "delimiter", ",")
                    if delimiter in {",", ";", "\t", "|"} and delimiter in sample:
                        return True
                    return False
                except csv.Error:
                    # Some CSV exports (e.g., Revolut) include localized headers
                    # that confuse Sniffer. Treat as CSV based on extension.
                    return True

        except Exception:
            return False

        return True

    @staticmethod
    def _detect_from_content(file_path: Path) -> FileFormat:
        """Detect format from file content when extension is ambiguous.

        Args:
            file_path: Path to file

        Returns:
            Detected FileFormat or FileFormat.UNKNOWN
        """
        try:
            with open(file_path, "rb") as f:
                sample = f.read(1024).decode("utf-8", errors="ignore")

            # Check for OFX signatures
            if "<OFX>" in sample or "OFXHEADER" in sample:
                return FileFormat.OFX

            # Check for QIF signatures
            if "!Type:" in sample or "!Account:" in sample:
                return FileFormat.QIF

            # Try CSV detection
            try:
                dialect = csv.Sniffer().sniff(sample)
                delimiter = getattr(dialect, "delimiter", ",")
                if delimiter in {",", ";", "\t", "|"} and delimiter in sample:
                    return FileFormat.CSV
            except csv.Error:
                pass

        except Exception:
            pass

        return FileFormat.UNKNOWN

    @classmethod
    def create_from_file(
        cls,
        file_path: Path,
        config: "dict | CSVConfig | None" = None,
        bank_preset: str | None = None,
        format: FileFormat | None = None,
    ) -> BaseImporter:
        """Create importer from file with optional configuration.

        Args:
            file_path: Path to statement file
            config: Optional configuration (CSV-specific)
            bank_preset: Optional bank preset name ('intesa', 'unicredit', 'banco_bpm')
            format: Optional explicit format (skips auto-detection)

        Returns:
            Configured BaseImporter instance

        Raises:
            ValueError: If format is unknown or unsupported
            FileNotFoundError: If file doesn't exist

        Example:
            >>> # Auto-detect with bank preset
            >>> importer = ImporterFactory.create_from_file(
            ...     Path("statement.csv"),
            ...     bank_preset="intesa"
            ... )
            >>>
            >>> # Explicit format
            >>> importer = ImporterFactory.create_from_file(
            ...     Path("data.txt"),
            ...     format=FileFormat.CSV
            ... )
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Detect format if not explicitly provided
        detected_format = format or cls.detect_format(file_path)

        if detected_format == FileFormat.UNKNOWN:
            extension = file_path.suffix.lower()
            if extension in {".ofx", ".qfx"}:
                detected_format = FileFormat.OFX
            elif extension == ".qif":
                detected_format = FileFormat.QIF
            else:
                raise ValueError(f"Unable to detect format for file: {file_path}")

        # Delegate to format-specific creator
        return cls.create(detected_format, file_path, config, bank_preset)

    @classmethod
    def create(
        cls,
        format: FileFormat,
        file_path: Path,
        config: "dict | CSVConfig | None" = None,
        bank_preset: str | None = None,
    ) -> BaseImporter:
        """Create importer for specific format.

        Args:
            format: File format
            file_path: Path to statement file
            config: Optional configuration
            bank_preset: Optional bank preset

        Returns:
            Configured BaseImporter instance

        Raises:
            ValueError: If format is unsupported
            ImportError: If importer module not available
        """
        if format == FileFormat.CSV:
            from .csv_importer import CSVConfig, CSVImporter

            # Load bank preset if specified
            if bank_preset:
                from .presets import BANK_PRESETS

                if bank_preset not in BANK_PRESETS:
                    raise ValueError(f"Unknown bank preset: {bank_preset}")
                config = BANK_PRESETS[bank_preset]

            # Use config or default
            if config is None:
                config = CSVConfig()
            elif isinstance(config, dict):
                config = CSVConfig(**config)

            return CSVImporter(file_path, config)

        elif format == FileFormat.OFX:
            from .ofx_importer import OFXImporter

            return OFXImporter(file_path)

        elif format == FileFormat.QIF:
            from .qif_importer import QIFImporter

            return QIFImporter(file_path)

        else:
            raise ValueError(f"Unsupported format: {format}")

    def __repr__(self) -> str:
        """Human-readable string representation."""
        formats = ", ".join(f.value for f in FileFormat if f != FileFormat.UNKNOWN)
        return f"<ImporterFactory(supported_formats=[{formats}])>"
