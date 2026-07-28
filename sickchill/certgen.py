# Certificate generation helpers for SickChill.
#
# This module previously used the classic pyOpenSSL example
# It has been rewritten to use
# the cryptography library because the mutable OpenSSL.crypto.X509
# and X509Req APIs were deprecated/removed in pyOpenSSL 26.x.
#
# The new implementation is intentionally a clean rewrite and is
# not a derivative of the original pyOpenSSL example code.

from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

TYPE_RSA = "RSA"  # kept for API compatibility
TYPE_DSA = "DSA"  # not used by SickChill


def createKeyPair(type, bits):
    """Return a cryptography private key (RSA only – what SickChill uses)."""
    if type != TYPE_RSA:
        raise ValueError("Only RSA is supported")
    return rsa.generate_private_key(public_exponent=65537, key_size=bits)


def createCertRequest(pkey, digest="sha256", **name):
    """
    Build a CertificateSigningRequest.
    `digest` is accepted for compatibility but ignored (we always use SHA-256).
    """
    name_attrs = []
    mapping = {
        "C": NameOID.COUNTRY_NAME,
        "ST": NameOID.STATE_OR_PROVINCE_NAME,
        "L": NameOID.LOCALITY_NAME,
        "O": NameOID.ORGANIZATION_NAME,
        "OU": NameOID.ORGANIZATIONAL_UNIT_NAME,
        "CN": NameOID.COMMON_NAME,
        "emailAddress": NameOID.EMAIL_ADDRESS,
    }
    for k, v in name.items():
        if k in mapping:
            name_attrs.append(x509.NameAttribute(mapping[k], v))

    builder = x509.CertificateSigningRequestBuilder().subject_name(x509.Name(name_attrs))
    return builder.sign(pkey, hashes.SHA256())


def createCertificate(req, issuerCert, issuerKey, serial, notBefore, notAfter, digest="sha256"):
    """
    Create a certificate from a CSR.
    notBefore / notAfter are relative seconds from now (matching the old pyOpenSSL helpers).
    """
    now = datetime.now(timezone.utc)
    subject = req.subject
    # When creating the CA itself the original code passed the request as issuerCert.
    # We treat that case specially.
    if hasattr(issuerCert, "subject"):
        issuer = issuerCert.subject
    else:
        issuer = subject

    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(req.public_key())
        .serial_number(serial)
        .not_valid_before(now + timedelta(seconds=notBefore))
        .not_valid_after(now + timedelta(seconds=notAfter))
    )
    return builder.sign(issuerKey, hashes.SHA256())
