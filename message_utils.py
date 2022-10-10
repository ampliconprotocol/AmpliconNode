import binascii
from random import choices, seed

from nacl.exceptions import CryptoError
from nacl.public import PrivateKey, SealedBox, PublicKey

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


def get_sealed_box_for_private_key(node_secret: node_pb2.NodeSecret) -> SealedBox:
    private_key = PrivateKey(
        private_key=binascii.unhexlify(bytes(node_secret.secret_private_key, 'utf-8')))
    sealed_box = SealedBox(private_key)
    return sealed_box


def get_sealed_box_for_public_key(public_key_hex_string: str) -> SealedBox:
    public_key = PublicKey(public_key=binascii.unhexlify(bytes(public_key_hex_string, 'utf-8')))
    sealed_box = SealedBox(public_key)
    return sealed_box


def get_public_key_hex_str(node_secret: node_pb2.NodeSecret) -> str:
    private_key = PrivateKey(
        private_key=binascii.unhexlify(bytes(node_secret.secret_private_key, 'utf-8')))
    output = binascii.hexlify(bytes(private_key.public_key)).decode('utf-8')
    return output


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

    sealed_box = get_sealed_box_for_private_key(node_secret)
    try:
        decrypted_message = sealed_box.decrypt(encrypted_message.encrypted_message_content)
    except CryptoError as e:
        decrypted_message = None  # Message not meant for this node.
    return decrypted_message


def encrypt_raw_message(raw_message: node_pb2.RawMessage, destination_public_key_hex_string: str) -> bytes:
    if common_utils.is_empty_string(destination_public_key_hex_string):
        raise ValueError("Invalid destination public key passed.")
    if common_utils.is_empty_object(raw_message):
        raise ValueError("Invalid raw message passed.")
    sealed_box = get_sealed_box_for_public_key(destination_public_key_hex_string)
    raw_message_bytes = raw_message.SerializeToString()
    output = sealed_box.encrypt(raw_message_bytes)
    return output


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


def generate_primer_or_dna_string(desired_length, allowed_characters="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                                  random_seed=0):
    if random_seed != 0:
        seed(random_seed)
    output = ''.join(choices(allowed_characters, k=desired_length))
    return output


def get_message_dna_candidates_for_95_pct_reachability(message_dna_length=128):
    num_candidates_to_generate = 5000
    output = []
    for i in range(num_candidates_to_generate):
        output.append(generate_primer_or_dna_string(desired_length=message_dna_length))
    return output
