"""
Digital signature implementation for FatturaPA.

Implements CAdES-BES (PKCS#7) signatures for .p7m files.
"""

from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs7

from openfatture.sdi.digital_signature.certificate_manager import CertificateManager


class DigitalSigner:
    """
    Digital signer for FatturaPA XML files.

    Creates CAdES-BES compliant .p7m signed files compatible with SDI.

    Usage:
        signer = DigitalSigner(certificate_path, password)
        signer.sign_file("invoice.xml", "invoice.xml.p7m")
    """

    def __init__(
        self,
        certificate_path: Path | None = None,
        password: str | None = None,
        certificate_manager: CertificateManager | None = None,
    ):
        """
        Initialize digital signer.

        Args:
            certificate_path: Path to .pfx/.p12 certificate
            password: Certificate password
            certificate_manager: Pre-configured CertificateManager (overrides path/password)
        """
        if certificate_manager:
            self.cert_manager = certificate_manager
        else:
            self.cert_manager = CertificateManager(certificate_path, password)
            if certificate_path:
                self.cert_manager.load_certificate()

    def sign_file(
        self, input_path: Path, output_path: Path | None = None, detached: bool = False
    ) -> tuple[bool, str | None, Path | None]:
        """
        Sign a file with digital signature (CAdES-BES).

        Args:
            input_path: Path to file to sign (usually .xml)
            output_path: Path for signed output (usually .xml.p7m). If None, appends .p7m
            detached: If True, creates detached signature. If False, creates enveloped (default)

        Returns:
            Tuple[bool, Optional[str], Optional[Path]]: (success, error_message, output_path)
        """
        # Validate certificate
        is_valid, error = self.cert_manager.validate_certificate()
        if not is_valid:
            return False, f"Certificate validation failed: {error}", None

        # Check input file exists
        if not input_path.exists():
            return False, f"Input file not found: {input_path}", None

        # Determine output path
        if output_path is None:
            output_path = input_path.with_suffix(input_path.suffix + ".p7m")

        try:
            # Read input data
            input_data = input_path.read_bytes()

            # Create PKCS7 signature
            signed_data = self._create_pkcs7_signature(input_data, detached)

            # Write to output
            output_path.write_bytes(signed_data)

            return True, None, output_path

        except Exception as e:
            return False, f"Signature failed: {e}", None

    def sign_data(
        self, data: bytes, detached: bool = False
    ) -> tuple[bool, str | None, bytes | None]:
        """
        Sign data (in memory) with digital signature.

        Args:
            data: Data to sign
            detached: If True, creates detached signature. If False, creates enveloped

        Returns:
            Tuple[bool, Optional[str], Optional[bytes]]: (success, error_message, signed_data)
        """
        # Validate certificate
        is_valid, error = self.cert_manager.validate_certificate()
        if not is_valid:
            return False, f"Certificate validation failed: {error}", None

        try:
            # Create PKCS7 signature
            signed_data = self._create_pkcs7_signature(data, detached)
            return True, None, signed_data

        except Exception as e:
            return False, f"Signature failed: {e}", None

    def _create_pkcs7_signature(self, data: bytes, detached: bool = False) -> bytes:
        """
        Create PKCS#7 CAdES-BES signature.

        Args:
            data: Data to sign
            detached: Whether to create detached signature

        Returns:
            Signed data in PKCS#7/CMS format
        """
        certificate = self.cert_manager.certificate
        private_key = self.cert_manager.private_key

        if not certificate or not private_key:
            raise ValueError("Certificate and private key must be loaded")

        # Create PKCS7 signature using cryptography
        # For CAdES-BES, we use PKCS7 with SHA-256
        options = []
        if not detached:
            # Enveloped signature (default for FatturaPA)
            options = [pkcs7.PKCS7Options.Binary]
        else:
            # Detached signature
            options = [pkcs7.PKCS7Options.DetachedSignature]

        # Sign the data
        builder = (
            pkcs7.PKCS7SignatureBuilder()
            .set_data(data)
            .add_signer(certificate, private_key, hashes.SHA256())
        )

        # Serialize to DER format (binary)
        signed_data = builder.sign(serialization.Encoding.DER, options)

        return signed_data

    def verify_signature(self, signed_path: Path) -> tuple[bool, str | None]:
        """
        Verify a signed file (basic check).

        Args:
            signed_path: Path to .p7m file

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)

        Note:
            For full verification, use SignatureVerifier class.
        """
        if not signed_path.exists():
            return False, f"File not found: {signed_path}"

        try:
            # Read signed data
            signed_data = signed_path.read_bytes()

            # Try to load as PKCS7
            # This is a basic check - just verifying it's valid PKCS7 format
            from cryptography.hazmat.primitives.serialization import pkcs7

            # Load the PKCS7 structure
            # If this succeeds, the file is at least valid PKCS7
            pkcs7.load_der_pkcs7_certificates(signed_data)

            return True, None

        except Exception as e:
            return False, f"Invalid PKCS7/p7m file: {e}"

    def get_signer_info(self) -> dict:
        """
        Get information about the signing certificate.

        Returns:
            Dict with signer certificate information
        """
        if not self.cert_manager.certificate:
            raise ValueError("Certificate not loaded")

        return self.cert_manager.get_certificate_info()
