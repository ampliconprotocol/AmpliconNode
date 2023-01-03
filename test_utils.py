import binascii
import socket
from contextlib import closing

from nacl.public import PrivateKey


def get_free_port(host='localhost') -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind((host, 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]
    return -1


def generate_public_and_private_keys() -> (str, str):
    """

    :return: A tuple of (private_key, public_key)
    """
    key_pair = PrivateKey.generate()
    private_key = binascii.hexlify(bytes(key_pair)).decode("utf-8")
    public_key = binascii.hexlify(bytes(key_pair.public_key)).decode("utf-8")
    return (private_key, public_key)

print(generate_public_and_private_keys())
print(generate_public_and_private_keys())
print(generate_public_and_private_keys())
print(generate_public_and_private_keys())