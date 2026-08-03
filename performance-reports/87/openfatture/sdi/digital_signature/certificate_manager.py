"""
Certificate management for digital signatures.

Handles loading and validating .pfx/.p12 certificates for FatturaPA signing.
"""

from datetime import UTC, datetime
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import (
    dh,
    dsa,
    ec,
    rsa,
    x448,
    x25519,
)
from cryptography.hazmat.primitives.asymmetric.ed448 import Ed448PrivateKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.x509 import Certificate

type PrivateKeyType = (
    rsa.RSAPrivateKey
    | dsa.DSAPrivateKey
    | ec.EllipticCurvePrivateKey
    | dh.DHPrivateKey
    | Ed25519PrivateKey
    | Ed448PrivateKey
    | x25519.X25519PrivateKey
    | x448.X448PrivateKey
)


class CertificateManager:
    """
    Manages digital certificates for invoice signing.

    Supports:
    - Loading .pfx/.p12 certificates
    - Validating certificate expiration
    - Extracting certificate information
    """

    def __init__(self, certificate_path: Path | None = None, password: str | None = None):
        """
        Initialize certificate manager.

        Args:
            certificate_path: Path to .pfx or .p12 certificate file
            password: Certificate password (if encrypted)
        """
        self.certificate_path = certificate_path
        self._password = password.encode() if password else None
        self._certificate: Certificate | None = None
        self._private_key: PrivateKeyType | None = None

    def load_certificate(
        self, certificate_path: Path | None = None, password: str | None = None
    ) -> None:
        """
        Load certificate from .pfx/.p12 file.

        Args:
            certificate_path: Path to certificate file (overrides __init__)
            password: Certificate password (overrides __init__)

        Raises:
            FileNotFoundError: If certificate file doesn't exist
            ValueError: If password is incorrect or certificate is invalid
        """
        cert_path = certificate_path or self.certificate_path
        cert_password = password.encode() if password else self._password

        if not cert_path:
            raise ValueError("Certificate path must be provided")

        if not cert_path.exists():
            raise FileNotFoundError(f"Certificate not found: {cert_path}")

        # Load PKCS12 certificate
        try:
            with open(cert_path, "rb") as f:
                cert_data = f.read()

            # Parse PKCS12
            from cryptography.hazmat.primitives.serialization import pkcs12

            private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
                cert_data, cert_password, backend=default_backend()
            )

            if not certificate:
                raise ValueError("No certificate found in .pfx/.p12 file")

            if not private_key:
                raise ValueError("No private key found in .pfx/.p12 file")

            self._certificate = certificate
            self._private_key = private_key
            self.certificate_path = cert_path

        except Exception as e:
            raise ValueError(f"Failed to load certificate: {e}") from e

    def validate_certificate(self) -> tuple[bool, str | None]:
        """
        Validate certificate is usable for signing.

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not self._certificate:
            return False, "Certificate not loaded"

        # Check expiration (use timezone-aware datetime)
        now = datetime.now(UTC)
        not_before = self._certificate.not_valid_before_utc
        not_after = self._certificate.not_valid_after_utc

        if now < not_before:
            return False, f"Certificate not yet valid (valid from {not_before})"

        if now > not_after:
            return False, f"Certificate expired on {not_after}"

        # Check key usage (should allow digital signature)
        try:
            key_usage = self._certificate.extensions.get_extension_for_class(x509.KeyUsage)
            if not key_usage.value.digital_signature:
                return False, "Certificate does not allow digital signatures"
        except x509.ExtensionNotFound:
            # Key usage extension not found - warning but not blocking
            pass

        return True, None

    def get_certificate_info(self) -> dict:
        """
        Get certificate information for display.

        Returns:
            Dict with certificate details
        """
        if not self._certificate:
            raise ValueError("Certificate not loaded")

        subject = self._certificate.subject
        issuer = self._certificate.issuer

        return {
            "subject": {
                "common_name": (
                    subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0].value
                    if subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)
                    else None
                ),
                "organization": (
                    subject.get_attributes_for_oid(x509.oid.NameOID.ORGANIZATION_NAME)[0].value
                    if subject.get_attributes_for_oid(x509.oid.NameOID.ORGANIZATION_NAME)
                    else None
                ),
                "country": (
                    subject.get_attributes_for_oid(x509.oid.NameOID.COUNTRY_NAME)[0].value
                    if subject.get_attributes_for_oid(x509.oid.NameOID.COUNTRY_NAME)
                    else None
                ),
            },
            "issuer": {
                "common_name": (
                    issuer.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0].value
                    if issuer.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)
                    else None
                ),
                "organization": (
                    issuer.get_attributes_for_oid(x509.oid.NameOID.ORGANIZATION_NAME)[0].value
                    if issuer.get_attributes_for_oid(x509.oid.NameOID.ORGANIZATION_NAME)
                    else None
                ),
            },
            "valid_from": self._certificate.not_valid_before_utc,
            "valid_until": self._certificate.not_valid_after_utc,
            "serial_number": self._certificate.serial_number,
        }

    @property
    def certificate(self) -> Certificate | None:
        """Get loaded certificate."""
        return self._certificate

    @property
    def private_key(self) -> PrivateKeyType | None:
        """Get loaded private key."""
        return self._private_key

    def export_public_certificate(self, output_path: Path) -> None:
        """
        Export public certificate (without private key) to PEM format.

        Args:
            output_path: Path to save certificate (.pem)
        """
        if not self._certificate:
            raise ValueError("Certificate not loaded")

        pem_data = self._certificate.public_bytes(serialization.Encoding.PEM)
        output_path.write_bytes(pem_data)
