"""AI tool adapters over `openfatture.sdi.application.signature_ops`."""

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
from openfatture.sdi.application.signature_ops import (
    check_certificate_status,
    sign_invoice_xml,
    verify_signature,
)


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
