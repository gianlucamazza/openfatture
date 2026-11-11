"""AI tool adapters over `openfatture.sdi.application.signature_ops`."""

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolRisk
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
            risk=ToolRisk.MUTATE,
            description=(
                "Sign an invoice's FatturaPA XML with the PKCS#12 certificate, producing an "
                "enveloped CAdES-BES .p7m for SDI. By default it signs the XML recorded for "
                "the invoice by generate_invoice_xml and writes <xml file>.p7m next to it; "
                "an existing file at the output path is overwritten. On success the invoice "
                "records both paths, so a later signed submission sends the .p7m. Returns "
                "success, fattura_id, numero, xml_path, signed_path, file_size. Errors: "
                "invoice not found, no XML generated yet (call generate_invoice_xml first), "
                "XML file missing, certificate not configured or not found, a certificate "
                "that cannot be loaded (wrong password) or fails validation (expired, not "
                "yet valid, no signing usage). To check an existing .p7m use verify_signature; to "
                "check the certificate before signing use check_certificate_status."
            ),
            category="signature",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID whose XML is signed and whose signed path is recorded",
                    required=True,
                ),
                ToolParameter(
                    name="xml_path",
                    type=ToolParameterType.STRING,
                    description=(
                        "XML file to sign instead of the one recorded for the invoice; it "
                        "becomes the invoice's recorded XML"
                    ),
                    required=False,
                ),
                ToolParameter(
                    name="output_path",
                    type=ToolParameterType.STRING,
                    description="Path of the .p7m to write; defaults to the XML path plus .p7m",
                    required=False,
                ),
                ToolParameter(
                    name="certificate_path",
                    type=ToolParameterType.STRING,
                    description=(
                        "Path of a .pfx/.p12 file; defaults to the configured "
                        "signature_certificate_path"
                    ),
                    required=False,
                ),
                ToolParameter(
                    name="certificate_password",
                    type=ToolParameterType.STRING,
                    description=(
                        "Password of the certificate; defaults to the configured "
                        "signature_certificate_password"
                    ),
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
            risk=ToolRisk.READ,
            description=(
                "Check that a .p7m file is a well-formed DER PKCS#7 structure. It does not "
                "verify the signature cryptographically, the signer's certificate chain or "
                "that the content matches the XML, so is_valid=true means only that the "
                "file is structurally readable. Returns success, is_valid, file_path, "
                "file_size, or an error for a missing file, a non-.p7m extension or an "
                "invalid structure. It reads the file and changes nothing; a configured "
                "certificate that cannot be loaded also makes it fail. To create a .p7m use "
                "sign_invoice_xml."
            ),
            category="signature",
            parameters=[
                ToolParameter(
                    name="signed_file_path",
                    type=ToolParameterType.STRING,
                    description="Path of the signed .p7m file, such as signed_path from sign_invoice_xml",
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
            risk=ToolRisk.READ,
            description=(
                "Load the PKCS#12 signing certificate and report whether it can sign: "
                "is_valid with validation_error, expiration_status (valid, expiring_soon "
                "under 30 days, expired), expiration_warning, days_until_expiry, subject "
                "(common_name, organization, country), issuer, validity dates and "
                "serial_number. Read-only. Errors: certificate path not configured, file "
                "not found, or the file cannot be loaded (wrong password, not PKCS#12). Use "
                "it before sign_invoice_xml or when signing fails on the certificate."
            ),
            category="signature",
            parameters=[
                ToolParameter(
                    name="certificate_path",
                    type=ToolParameterType.STRING,
                    description=(
                        "Path of a .pfx/.p12 file; defaults to the configured "
                        "signature_certificate_path"
                    ),
                    required=False,
                ),
                ToolParameter(
                    name="certificate_password",
                    type=ToolParameterType.STRING,
                    description=(
                        "Password of the certificate; defaults to the configured "
                        "signature_certificate_password"
                    ),
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
