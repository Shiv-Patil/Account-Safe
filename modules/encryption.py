from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
import base64

def generate_key(salt: bytes, password: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt(key: bytes, to_encrypt: str) -> str:
    return Fernet(key).encrypt(to_encrypt.encode()).decode('ascii')

def decrypt(key: bytes, to_decrypt: str) -> str:
    return Fernet(key).decrypt(to_decrypt.encode()).decode('ascii')
