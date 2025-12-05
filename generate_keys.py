from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

def generate_rsa_keypair(key_size: int = 4096):
    """
    Generate 4096-bit RSA key pair with exponent 65537.
    Returns private_key, public_key objects.
    """

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size
    )

    public_key = private_key.public_key()

    return private_key, public_key


def save_keys():
    private_key, public_key = generate_rsa_keypair()

    # Save PRIVATE key → PEM
    with open("student_private.pem", "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
        )

    # Save PUBLIC key → PEM
    with open("student_public.pem", "wb") as f:
        f.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )

    print("Keys generated successfully:")
    print("- student_private.pem")
    print("- student_public.pem")


if __name__ == "__main__":
    save_keys()