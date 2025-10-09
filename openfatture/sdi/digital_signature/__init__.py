"""
Digital signature module for FatturaPA.

Supports CAdES-BES (p7m) digital signatures for Italian electronic invoicing.
"""

from openfatture.sdi.digital_signature.certificate_manager import CertificateManager
from openfatture.sdi.digital_signature.signer import DigitalSigner
from openfatture.sdi.digital_signature.verifier import SignatureVerifier

__all__ = [
    "DigitalSigner",
    "SignatureVerifier",
    "CertificateManager",
]
