from typing import Union

from cryptography.hazmat.primitives.asymmetric import ed25519


def sign(secret: str, data: Union[str, bytes]) -> str:
    """QQ 开放平台签名算法"""
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(secret.encode())
    signature = private_key.sign(data.encode())
    return signature.hex()
