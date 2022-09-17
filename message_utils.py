import binascii

from nacl.public import PrivateKey, SealedBox
from nacl.exceptions import CryptoError

import common_utils
import node_pb2


def is_valid_encrypted_message(encrypted_message: node_pb2.EncryptedMessage) -> bool:
    if common_utils.is_empty_object(encrypted_message):
        return False
    if common_utils.is_empty_string(encrypted_message.message_id) or common_utils.is_empty_bytes(
            encrypted_message.encrypted_message_content):
        return False
    if common_utils.is_empty_string(encrypted_message.message_dna):
        return False
    return True


def get_sealed_box(node_secret: node_pb2.NodeSecret) -> SealedBox:
    private_key = PrivateKey(
        private_key=binascii.unhexlify(bytes(node_secret.secret_private_key, 'utf-8')))
    sealed_box = SealedBox(private_key)
    return sealed_box


def maybe_decrypt_message(encrypted_message: node_pb2.EncryptedMessage, node_secret: node_pb2.NodeSecret) -> bytes:
    '''
    Returns a decrypted bytes payload if message is meant for this node. Else returns None
    :param encrypted_message: The message payload to be decrypted
    :param node_secret: The node's secret
    :return: Decrypted bytes object if successful, else None
    '''
    if not is_valid_encrypted_message(encrypted_message):
        raise ValueError("Invalid encrypted message passed.")
    if common_utils.is_empty_object(node_secret):
        raise ValueError("Invalid node secret passed.")

    sealed_box = get_sealed_box(node_secret)
    try:
        decrypted_message = sealed_box.decrypt(encrypted_message.encrypted_message_content)
    except CryptoError as e:
        decrypted_message = None  # Message not meant for this node.
    return decrypted_message


def has_valid_message_amplicon(message_dna: str, secret_node_primer: str, secret_node_amplicon_threshold: int) -> bool:
    first_index = message_dna.find(secret_node_primer)
    if first_index == -1:  # index not found
        return False
    last_index = message_dna.rfind(secret_node_primer)
    if last_index - first_index >= secret_node_amplicon_threshold:
        return True
    return False


def should_message_be_relayed(encrypted_message: node_pb2.EncryptedMessage,
                              node_secret: node_pb2.NodeSecret) -> bool:
    if common_utils.is_empty_object(node_secret) or common_utils.is_empty_string(
            node_secret.secret_node_primer):
        raise ValueError("Invalid current node secret passed.")
    if not is_valid_encrypted_message(encrypted_message):
        raise ValueError("Invalid encrypted message passed.")

    if has_valid_message_amplicon(encrypted_message.message_dna, node_secret.secret_node_primer,
                                  node_secret.secret_amplicon_threshold):
        return True
    return False


