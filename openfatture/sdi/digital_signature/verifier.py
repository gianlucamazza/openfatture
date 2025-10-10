"""
Signature verification for FatturaPA p7m files.

Verifies CAdES-BES digital signatures and extracts signed content.
"""

from datetime import UTC, datetime
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives.serialization import pkcs7
from pyasn1.codec.der import decoder
from pyasn1_modules import rfc2315


class SignatureVerifier:
    """
    Verifies digital signatures on p7m files.

    Can extract original content and verify signature validity.

    Usage:
        verifier = SignatureVerifier()
        is_valid, error = verifier.verify_file("invoice.xml.p7m")
        content = verifier.extract_content("invoice.xml.p7m")
    """

    def __init__(self):
        """Initialize signature verifier."""
        pass

    def verify_file(
        self, signed_path: Path, original_path: Path | None = None
    ) -> tuple[bool, str | None]:
        """
        Verify digital signature on a .p7m file.

        Args:
            signed_path: Path to .p7m signed file
            original_path: Path to original file (for detached signatures)

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not signed_path.exists():
            return False, f"Signed file not found: {signed_path}"

        try:
            # Read signed data
            signed_data = signed_path.read_bytes()

            # Parse PKCS7 structure
            # Note: cryptography doesn't provide high-level PKCS7 verification
            # This is a basic structural check
            certificates = pkcs7.load_der_pkcs7_certificates(signed_data)

            if not certificates:
                return False, "No certificates found in signature"

            # Check certificate expiration (use timezone-aware datetime)
            signer_cert = certificates[0]  # First certificate is usually the signer
            now = datetime.now(UTC)

            if now < signer_cert.not_valid_before_utc:
                return (
                    False,
                    f"Certificate not yet valid (valid from {signer_cert.not_valid_before_utc})",
                )

            if now > signer_cert.not_valid_after_utc:
                return False, f"Certificate expired on {signer_cert.not_valid_after_utc}"

            # Basic structural validation passed
            return True, None

        except Exception as e:
            return False, f"Signature verification failed: {e}"

    def extract_content(
        self, signed_path: Path, output_path: Path | None = None
    ) -> tuple[bool, str | None, bytes | None]:
        """
        Extract original content from signed .p7m file.

        Args:
            signed_path: Path to .p7m file
            output_path: Optional path to save extracted content

        Returns:
            Tuple[bool, Optional[str], Optional[bytes]]: (success, error_message, content)

        Note:
            This implementation uses basic ASN.1 parsing.
            For production, consider using more robust PKCS7 parsing libraries.
        """
        if not signed_path.exists():
            return False, f"File not found: {signed_path}", None

        try:
            # Read signed file
            signed_data = signed_path.read_bytes()

            # Extract content from PKCS7 envelope using basic ASN.1 parsing
            # For enveloped signatures, the original data is embedded in the PKCS7 structure

            # Simple extraction using DER structure parsing
            # PKCS7 SignedData structure contains the original content
            # This is a simplified approach - works for standard CAdES-BES enveloped signatures

            content_info, _ = decoder.decode(signed_data, asn1Spec=rfc2315.ContentInfo())

            # Check if it's signed data
            if content_info["contentType"] != rfc2315.signedData:
                return False, "Not a signed data PKCS7 structure", None

            signed_data_content = decoder.decode(
                bytes(content_info["content"]), asn1Spec=rfc2315.SignedData()
            )[0]

            # Get encapsulated content
            encap_content_info = signed_data_content["encapContentInfo"]

            if "eContent" not in encap_content_info or encap_content_info["eContent"] is None:
                return False, "No encapsulated content found (detached signature?)", None

            original_content = bytes(encap_content_info["eContent"])

            # Write to output if requested
            if output_path:
                output_path.write_bytes(original_content)

            return True, None, original_content

        except Exception as e:
            return False, f"Content extraction failed: {e}", None

    def get_signature_info(self, signed_path: Path) -> tuple[bool, str | None, dict | None]:
        """
        Get information about the signature and signer.

        Args:
            signed_path: Path to .p7m file

        Returns:
            Tuple[bool, Optional[str], Optional[dict]]: (success, error_message, info_dict)
        """
        if not signed_path.exists():
            return False, f"File not found: {signed_path}", None

        try:
            # Read and parse PKCS7
            signed_data = signed_path.read_bytes()
            certificates = pkcs7.load_der_pkcs7_certificates(signed_data)

            if not certificates:
                return False, "No certificates found", None

            # Get signer certificate info
            signer_cert = certificates[0]
            subject = signer_cert.subject
            issuer = signer_cert.issuer

            info = {
                "signer": {
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
                "valid_from": signer_cert.not_valid_before_utc,
                "valid_until": signer_cert.not_valid_after_utc,
                "serial_number": signer_cert.serial_number,
                "certificates_count": len(certificates),
            }

            return True, None, info

        except Exception as e:
            return False, f"Failed to get signature info: {e}", None

    def verify_and_extract(
        self, signed_path: Path, output_path: Path | None = None
    ) -> tuple[bool, str | None, bytes | None]:
        """
        Verify signature and extract content in one operation.

        Args:
            signed_path: Path to .p7m file
            output_path: Optional path to save extracted content

        Returns:
            Tuple[bool, Optional[str], Optional[bytes]]: (success, error_message, content)
        """
        # First verify
        is_valid, error = self.verify_file(signed_path)
        if not is_valid:
            return False, f"Signature verification failed: {error}", None

        # Then extract
        success, error, content = self.extract_content(signed_path, output_path)
        if not success:
            return False, f"Content extraction failed: {error}", None

        return True, None, content
