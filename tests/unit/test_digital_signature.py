"""Unit tests for digital signature module."""

from datetime import UTC, datetime, timedelta

import pytest
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from openfatture.sdi.digital_signature import CertificateManager, DigitalSigner, SignatureVerifier

pytestmark = pytest.mark.unit


@pytest.fixture
def temp_certificate(tmp_path):
    """Create a temporary self-signed certificate for testing."""
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    # Create certificate
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "IT"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Company"),
            x509.NameAttribute(NameOID.COMMON_NAME, "Test Certificate"),
        ]
    )

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(UTC) - timedelta(days=1))
        .not_valid_after(datetime.now(UTC) + timedelta(days=365))
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(private_key, hashes.SHA256(), backend=default_backend())
    )

    # Save as PKCS12
    from cryptography.hazmat.primitives.serialization import pkcs12

    p12_data = pkcs12.serialize_key_and_certificates(
        name=b"test",
        key=private_key,
        cert=cert,
        cas=None,
        encryption_algorithm=serialization.BestAvailableEncryption(b"test1234"),
    )

    cert_path = tmp_path / "test_cert.pfx"
    cert_path.write_bytes(p12_data)

    return {
        "path": cert_path,
        "password": "test1234",
        "private_key": private_key,
        "certificate": cert,
    }


class TestCertificateManager:
    """Tests for CertificateManager."""

    def test_init_with_path_and_password(self, temp_certificate):
        """Test initialization with path and password."""
        manager = CertificateManager(temp_certificate["path"], temp_certificate["password"])

        assert manager.certificate_path == temp_certificate["path"]

    def test_load_certificate_success(self, temp_certificate):
        """Test loading valid certificate."""
        manager = CertificateManager()
        manager.load_certificate(temp_certificate["path"], temp_certificate["password"])

        assert manager.certificate is not None
        assert manager.private_key is not None

    def test_load_certificate_file_not_found(self, tmp_path):
        """Test loading non-existent certificate."""
        manager = CertificateManager()
        non_existent = tmp_path / "nonexistent.pfx"

        with pytest.raises(FileNotFoundError):
            manager.load_certificate(non_existent, "password")

    def test_load_certificate_wrong_password(self, temp_certificate):
        """Test loading with wrong password."""
        manager = CertificateManager()

        with pytest.raises(ValueError, match="Failed to load certificate"):
            manager.load_certificate(temp_certificate["path"], "wrongpassword")

    def test_validate_certificate_success(self, temp_certificate):
        """Test validating valid certificate."""
        manager = CertificateManager(temp_certificate["path"], temp_certificate["password"])
        manager.load_certificate()

        is_valid, error = manager.validate_certificate()

        assert is_valid is True
        assert error is None

    def test_validate_certificate_not_loaded(self):
        """Test validating when certificate not loaded."""
        manager = CertificateManager()

        is_valid, error = manager.validate_certificate()

        assert is_valid is False
        assert "not loaded" in error

    def test_get_certificate_info(self, temp_certificate):
        """Test getting certificate information."""
        manager = CertificateManager(temp_certificate["path"], temp_certificate["password"])
        manager.load_certificate()

        info = manager.get_certificate_info()

        assert info["subject"]["common_name"] == "Test Certificate"
        assert info["subject"]["organization"] == "Test Company"
        assert info["subject"]["country"] == "IT"
        assert "valid_from" in info
        assert "valid_until" in info

    def test_export_public_certificate(self, temp_certificate, tmp_path):
        """Test exporting public certificate."""
        manager = CertificateManager(temp_certificate["path"], temp_certificate["password"])
        manager.load_certificate()

        output_path = tmp_path / "public_cert.pem"
        manager.export_public_certificate(output_path)

        assert output_path.exists()
        # Verify it's valid PEM
        content = output_path.read_text()
        assert "BEGIN CERTIFICATE" in content


class TestDigitalSigner:
    """Tests for DigitalSigner."""

    def test_init_with_certificate_path(self, temp_certificate):
        """Test initialization with certificate path."""
        signer = DigitalSigner(temp_certificate["path"], temp_certificate["password"])

        assert signer.cert_manager.certificate is not None

    def test_init_with_certificate_manager(self, temp_certificate):
        """Test initialization with CertificateManager."""
        manager = CertificateManager(temp_certificate["path"], temp_certificate["password"])
        manager.load_certificate()

        signer = DigitalSigner(certificate_manager=manager)

        assert signer.cert_manager == manager

    def test_sign_file_success(self, temp_certificate, tmp_path):
        """Test signing a file."""
        signer = DigitalSigner(temp_certificate["path"], temp_certificate["password"])

        # Create test XML file
        xml_file = tmp_path / "test.xml"
        xml_file.write_text('<?xml version="1.0"?><root>test</root>')

        output_file = tmp_path / "test.xml.p7m"

        success, error, result_path = signer.sign_file(xml_file, output_file)

        assert success is True
        assert error is None
        assert result_path == output_file
        assert output_file.exists()

    def test_sign_file_auto_output_path(self, temp_certificate, tmp_path):
        """Test signing with automatic output path."""
        signer = DigitalSigner(temp_certificate["path"], temp_certificate["password"])

        xml_file = tmp_path / "test.xml"
        xml_file.write_text('<?xml version="1.0"?><root>test</root>')

        success, error, result_path = signer.sign_file(xml_file)

        assert success is True
        assert result_path == tmp_path / "test.xml.p7m"
        assert result_path.exists()

    def test_sign_file_not_found(self, temp_certificate, tmp_path):
        """Test signing non-existent file."""
        signer = DigitalSigner(temp_certificate["path"], temp_certificate["password"])

        non_existent = tmp_path / "nonexistent.xml"

        success, error, result_path = signer.sign_file(non_existent)

        assert success is False
        assert "not found" in error

    def test_sign_data_success(self, temp_certificate):
        """Test signing data in memory."""
        signer = DigitalSigner(temp_certificate["path"], temp_certificate["password"])

        data = b'<?xml version="1.0"?><root>test</root>'

        success, error, signed_data = signer.sign_data(data)

        assert success is True
        assert error is None
        assert signed_data is not None
        assert len(signed_data) > 0

    def test_get_signer_info(self, temp_certificate):
        """Test getting signer certificate info."""
        signer = DigitalSigner(temp_certificate["path"], temp_certificate["password"])

        info = signer.get_signer_info()

        assert info["subject"]["common_name"] == "Test Certificate"
        assert info["subject"]["organization"] == "Test Company"


class TestSignatureVerifier:
    """Tests for SignatureVerifier."""

    def test_verify_file_with_valid_signature(self, temp_certificate, tmp_path):
        """Test verifying a valid signed file."""
        # Create signed file
        signer = DigitalSigner(temp_certificate["path"], temp_certificate["password"])
        xml_file = tmp_path / "test.xml"
        xml_file.write_text('<?xml version="1.0"?><root>test</root>')
        signed_file = tmp_path / "test.xml.p7m"
        signer.sign_file(xml_file, signed_file)

        # Verify
        verifier = SignatureVerifier()
        is_valid, error = verifier.verify_file(signed_file)

        assert is_valid is True
        assert error is None

    def test_verify_file_not_found(self, tmp_path):
        """Test verifying non-existent file."""
        verifier = SignatureVerifier()
        non_existent = tmp_path / "nonexistent.p7m"

        is_valid, error = verifier.verify_file(non_existent)

        assert is_valid is False
        assert "not found" in error

    @pytest.mark.skip(reason="Content extraction requires pyasn1 - optional dependency")
    def test_extract_content_success(self, temp_certificate, tmp_path):
        """Test extracting content from signed file."""
        # Create signed file
        signer = DigitalSigner(temp_certificate["path"], temp_certificate["password"])
        xml_file = tmp_path / "test.xml"
        original_content = b'<?xml version="1.0"?><root>test</root>'
        xml_file.write_bytes(original_content)
        signed_file = tmp_path / "test.xml.p7m"
        signer.sign_file(xml_file, signed_file)

        # Extract
        verifier = SignatureVerifier()
        success, error, content = verifier.extract_content(signed_file)

        assert success is True
        assert error is None
        assert content == original_content

    @pytest.mark.skip(reason="Content extraction requires pyasn1 - optional dependency")
    def test_extract_content_with_output_path(self, temp_certificate, tmp_path):
        """Test extracting content to output file."""
        # Create signed file
        signer = DigitalSigner(temp_certificate["path"], temp_certificate["password"])
        xml_file = tmp_path / "test.xml"
        original_content = b'<?xml version="1.0"?><root>test</root>'
        xml_file.write_bytes(original_content)
        signed_file = tmp_path / "test.xml.p7m"
        signer.sign_file(xml_file, signed_file)

        # Extract to file
        verifier = SignatureVerifier()
        output_file = tmp_path / "extracted.xml"
        success, error, content = verifier.extract_content(signed_file, output_file)

        assert success is True
        assert output_file.exists()
        assert output_file.read_bytes() == original_content

    def test_get_signature_info(self, temp_certificate, tmp_path):
        """Test getting signature information."""
        # Create signed file
        signer = DigitalSigner(temp_certificate["path"], temp_certificate["password"])
        xml_file = tmp_path / "test.xml"
        xml_file.write_text('<?xml version="1.0"?><root>test</root>')
        signed_file = tmp_path / "test.xml.p7m"
        signer.sign_file(xml_file, signed_file)

        # Get info
        verifier = SignatureVerifier()
        success, error, info = verifier.get_signature_info(signed_file)

        assert success is True
        assert error is None
        assert info["signer"]["common_name"] == "Test Certificate"
        assert info["signer"]["organization"] == "Test Company"
        assert "valid_from" in info
        assert "valid_until" in info

    @pytest.mark.skip(reason="Content extraction requires pyasn1 - optional dependency")
    def test_verify_and_extract(self, temp_certificate, tmp_path):
        """Test combined verify and extract operation."""
        # Create signed file
        signer = DigitalSigner(temp_certificate["path"], temp_certificate["password"])
        xml_file = tmp_path / "test.xml"
        original_content = b'<?xml version="1.0"?><root>test</root>'
        xml_file.write_bytes(original_content)
        signed_file = tmp_path / "test.xml.p7m"
        signer.sign_file(xml_file, signed_file)

        # Verify and extract
        verifier = SignatureVerifier()
        success, error, content = verifier.verify_and_extract(signed_file)

        assert success is True
        assert error is None
        assert content == original_content
