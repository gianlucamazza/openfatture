"""Tools for digital signature management (PKCS#12 certificates)."""

from pathlib import Path
from typing import Any

from pydantic import validate_call

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
from openfatture.sdi.digital_signature.certificate_manager import CertificateManager
from openfatture.sdi.digital_signature.signer import DigitalSigner
from openfatture.storage.database.base import get_session
from openfatture.storage.database.models import Fattura
from openfatture.utils.config import get_settings
from openfatture.utils.logging import get_logger
from openfatture.utils.security import validate_integer_input

logger = get_logger(__name__)


# =============================================================================
# Digital Signature Tools
# =============================================================================


@validate_call
def sign_invoice_xml(
    fattura_id: int,
    xml_path: str | None = None,
    output_path: str | None = None,
    certificate_path: str | None = None,
    certificate_password: str | None = None,
) -> dict[str, Any]:
    """
    Digitally sign invoice XML file with PKCS#12 certificate (CAdES-BES).

    Creates .p7m signed file compatible with SDI requirements.

    Args:
        fattura_id: Invoice ID to sign
        xml_path: Path to XML file (optional, auto-detects if None)
        output_path: Output path for signed .p7m file (optional, auto-generates if None)
        certificate_path: Path to .pfx/.p12 certificate (optional, uses config if None)
        certificate_password: Certificate password (optional, uses config if None)

    Returns:
        Dictionary with signing result and output path
    """
    # Validate input
    fattura_id = validate_integer_input(fattura_id, min_value=1)

    db = get_session()
    try:
        # Get invoice
        fattura = db.query(Fattura).filter(Fattura.id == fattura_id).first()

        if not fattura:
            return {"success": False, "error": f"Fattura {fattura_id} not found"}

        # Load certificate configuration
        settings = get_settings()

        cert_path_str = certificate_path or getattr(settings, "signature_certificate_path", None)
        cert_password = certificate_password or getattr(
            settings, "signature_certificate_password", None
        )

        if not cert_path_str:
            return {
                "success": False,
                "error": "Certificate path not provided. Set SIGNATURE_CERTIFICATE_PATH in .env or provide certificate_path parameter.",
            }

        cert_path = Path(cert_path_str)
        if not cert_path.exists():
            return {"success": False, "error": f"Certificate file not found: {cert_path}"}

        # Determine XML path
        if xml_path:
            xml_file = Path(xml_path)
        else:
            # Auto-detect XML file (common locations)
            possible_paths = [
                Path(f"fattura_{fattura.numero}_{fattura.anno}.xml"),
                Path(f"IT{settings.cedente_partita_iva}_{fattura.numero:05d}.xml"),
                Path("output") / f"fattura_{fattura.numero}_{fattura.anno}.xml",
            ]

            xml_file = None
            for p in possible_paths:
                if p.exists():
                    xml_file = p
                    break

            if not xml_file:
                return {
                    "success": False,
                    "error": f"XML file not found. Tried: {[str(p) for p in possible_paths]}. Please provide xml_path parameter.",
                }

        # At this point xml_file is guaranteed to be non-None
        assert xml_file is not None, "xml_file should be set by now"

        if not xml_file.exists():
            return {"success": False, "error": f"XML file not found: {xml_file}"}

        # Create signer
        try:
            signer = DigitalSigner(certificate_path=cert_path, password=cert_password)
        except Exception as e:
            return {"success": False, "error": f"Failed to load certificate: {e}"}

        # Sign file
        output_file = Path(output_path) if output_path else None
        success, error, signed_path = signer.sign_file(xml_file, output_file, detached=False)

        if not success:
            return {"success": False, "error": error}

        logger.info(
            "invoice_xml_signed",
            fattura_id=fattura_id,
            numero=f"{fattura.numero}/{fattura.anno}",
            xml_path=str(xml_file),
            signed_path=str(signed_path),
        )

        return {
            "success": True,
            "fattura_id": fattura_id,
            "numero": f"{fattura.numero}/{fattura.anno}",
            "xml_path": str(xml_file.absolute()),
            "signed_path": str(signed_path.absolute()) if signed_path else None,
            "file_size": signed_path.stat().st_size if signed_path else 0,
            "message": f"XML firmato digitalmente: {signed_path.name if signed_path else 'unknown'}",
        }

    except Exception as e:
        logger.error("sign_invoice_xml_failed", fattura_id=fattura_id, error=str(e))
        return {"success": False, "error": str(e)}
    finally:
        db.close()


@validate_call
def verify_signature(
    signed_file_path: str,
) -> dict[str, Any]:
    """
    Verify digital signature on a .p7m file.

    Performs basic PKCS#7 validation to check if signature is structurally valid.

    Args:
        signed_file_path: Path to .p7m signed file

    Returns:
        Dictionary with verification result
    """
    signed_path = Path(signed_file_path)

    if not signed_path.exists():
        return {"success": False, "error": f"File not found: {signed_file_path}"}

    if not signed_path.suffix.lower() == ".p7m":
        return {
            "success": False,
            "error": f"File must be .p7m format (got: {signed_path.suffix})",
        }

    try:
        # Load certificate configuration (for signer initialization)
        settings = get_settings()
        cert_path_str = getattr(settings, "signature_certificate_path", None)
        cert_password = getattr(settings, "signature_certificate_password", None)

        # Create signer (even for verification, to access verify_signature method)
        cert_path = Path(cert_path_str) if cert_path_str else None
        signer = DigitalSigner(certificate_path=cert_path, password=cert_password)

        # Verify signature
        is_valid, error = signer.verify_signature(signed_path)

        if not is_valid:
            logger.warning(
                "signature_verification_failed",
                signed_path=str(signed_path),
                error=error,
            )
            return {
                "success": False,
                "is_valid": False,
                "error": error,
                "file_path": str(signed_path.absolute()),
            }

        logger.info(
            "signature_verified",
            signed_path=str(signed_path),
            file_size=signed_path.stat().st_size,
        )

        return {
            "success": True,
            "is_valid": True,
            "file_path": str(signed_path.absolute()),
            "file_size": signed_path.stat().st_size,
            "message": "Digital signature is valid (PKCS#7 structure verified)",
        }

    except Exception as e:
        logger.error("verify_signature_failed", signed_path=str(signed_path), error=str(e))
        return {"success": False, "is_valid": False, "error": str(e)}


@validate_call
def check_certificate_status(
    certificate_path: str | None = None,
    certificate_password: str | None = None,
) -> dict[str, Any]:
    """
    Check PKCS#12 certificate status and information.

    Returns certificate details, validity dates, and expiration warnings.

    Args:
        certificate_path: Path to .pfx/.p12 certificate (optional, uses config if None)
        certificate_password: Certificate password (optional, uses config if None)

    Returns:
        Dictionary with certificate information and status
    """
    try:
        # Load certificate configuration
        settings = get_settings()

        cert_path_str = certificate_path or getattr(settings, "signature_certificate_path", None)
        cert_password = certificate_password or getattr(
            settings, "signature_certificate_password", None
        )

        if not cert_path_str:
            return {
                "success": False,
                "error": "Certificate path not provided. Set SIGNATURE_CERTIFICATE_PATH in .env or provide certificate_path parameter.",
            }

        cert_path = Path(cert_path_str)
        if not cert_path.exists():
            return {"success": False, "error": f"Certificate file not found: {cert_path}"}

        # Load certificate
        try:
            cert_manager = CertificateManager(certificate_path=cert_path, password=cert_password)
            cert_manager.load_certificate()
        except Exception as e:
            return {"success": False, "error": f"Failed to load certificate: {e}"}

        # Validate certificate
        is_valid, validation_error = cert_manager.validate_certificate()

        # Get certificate info
        cert_info = cert_manager.get_certificate_info()

        # Calculate expiration details
        from datetime import UTC, datetime

        now = datetime.now(UTC)
        valid_until = cert_info["valid_until"]
        days_until_expiry = (valid_until - now).days

        # Determine expiration status
        if days_until_expiry < 0:
            expiration_status = "expired"
            expiration_warning = f"EXPIRED {abs(days_until_expiry)} days ago"
        elif days_until_expiry < 30:
            expiration_status = "expiring_soon"
            expiration_warning = f"Expires in {days_until_expiry} days - RENEW SOON"
        elif days_until_expiry < 90:
            expiration_status = "valid"
            expiration_warning = f"Expires in {days_until_expiry} days"
        else:
            expiration_status = "valid"
            expiration_warning = None

        logger.info(
            "certificate_status_checked",
            cert_path=str(cert_path),
            is_valid=is_valid,
            days_until_expiry=days_until_expiry,
        )

        return {
            "success": True,
            "certificate_path": str(cert_path.absolute()),
            "is_valid": is_valid,
            "validation_error": validation_error,
            "expiration_status": expiration_status,
            "expiration_warning": expiration_warning,
            "days_until_expiry": days_until_expiry,
            "subject": {
                "common_name": cert_info["subject"]["common_name"],
                "organization": cert_info["subject"]["organization"],
                "country": cert_info["subject"]["country"],
            },
            "issuer": {
                "common_name": cert_info["issuer"]["common_name"],
                "organization": cert_info["issuer"]["organization"],
            },
            "validity": {
                "valid_from": cert_info["valid_from"].isoformat(),
                "valid_until": cert_info["valid_until"].isoformat(),
            },
            "serial_number": str(cert_info["serial_number"]),
        }

    except Exception as e:
        logger.error("check_certificate_status_failed", error=str(e))
        return {"success": False, "error": str(e)}


# =============================================================================
# Tool Definitions
# =============================================================================


def get_signature_tools() -> list[Tool]:
    """
    Get all digital signature tools.

    Returns:
        List of Tool instances
    """
    return [
        Tool(
            name="sign_invoice_xml",
            description="Digitally sign invoice XML with PKCS#12 certificate (creates .p7m file for SDI)",
            category="signature",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID to sign",
                    required=True,
                ),
                ToolParameter(
                    name="xml_path",
                    type=ToolParameterType.STRING,
                    description="Path to XML file (optional, auto-detects if None)",
                    required=False,
                ),
                ToolParameter(
                    name="output_path",
                    type=ToolParameterType.STRING,
                    description="Output path for signed .p7m file (optional)",
                    required=False,
                ),
                ToolParameter(
                    name="certificate_path",
                    type=ToolParameterType.STRING,
                    description="Path to .pfx/.p12 certificate (optional, uses config)",
                    required=False,
                ),
                ToolParameter(
                    name="certificate_password",
                    type=ToolParameterType.STRING,
                    description="Certificate password (optional, uses config)",
                    required=False,
                ),
            ],
            func=sign_invoice_xml,
            requires_confirmation=True,
            examples=[
                "sign_invoice_xml(fattura_id=123)",
                "sign_invoice_xml(fattura_id=456, xml_path='fattura_001_2025.xml')",
            ],
            tags=["signature", "sign", "invoice", "write"],
        ),
        Tool(
            name="verify_signature",
            description="Verify digital signature on .p7m file (PKCS#7 validation)",
            category="signature",
            parameters=[
                ToolParameter(
                    name="signed_file_path",
                    type=ToolParameterType.STRING,
                    description="Path to .p7m signed file",
                    required=True,
                ),
            ],
            func=verify_signature,
            examples=[
                "verify_signature(signed_file_path='fattura_001_2025.xml.p7m')",
            ],
            tags=["signature", "verify", "validation"],
        ),
        Tool(
            name="check_certificate_status",
            description="Check PKCS#12 certificate status, validity, and expiration info",
            category="signature",
            parameters=[
                ToolParameter(
                    name="certificate_path",
                    type=ToolParameterType.STRING,
                    description="Path to .pfx/.p12 certificate (optional, uses config)",
                    required=False,
                ),
                ToolParameter(
                    name="certificate_password",
                    type=ToolParameterType.STRING,
                    description="Certificate password (optional, uses config)",
                    required=False,
                ),
            ],
            func=check_certificate_status,
            examples=[
                "check_certificate_status()",
                "check_certificate_status(certificate_path='my_cert.pfx', certificate_password='secret')",
            ],
            tags=["signature", "certificate", "status", "info"],
        ),
    ]
