import binascii
import hashlib
import random
import sys
from random import choices, seed

from google.protobuf.message import DecodeError
from nacl.exceptions import CryptoError
from nacl.public import PrivateKey, SealedBox, PublicKey

import common_utils
import node_pb2


def is_valid_amplicon_p2p_relay_message(amplicon_p2p_relay_message: node_pb2.AmpliconP2PRelayMessage) -> bool:
    if common_utils.is_empty_object(amplicon_p2p_relay_message):
        return False
    if common_utils.is_empty_string(amplicon_p2p_relay_message.message_id) or common_utils.is_empty_bytes(
            amplicon_p2p_relay_message.encrypted_message_core.encrypted_message_content):
        return False
    if common_utils.is_empty_string(amplicon_p2p_relay_message.message_dna):
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


def maybe_decrypt_message(amplicon_p2p_relay_message: node_pb2.AmpliconP2PRelayMessage,
                          node_secret: node_pb2.NodeSecret) -> bytes:
    '''
    Returns a decrypted bytes payload if message is meant for this node. Else returns None
    :param amplicon_p2p_relay_message: The message payload to be decrypted
    :param node_secret: The node's secret
    :return: Decrypted bytes object if successful, else None
    '''
    if not is_valid_amplicon_p2p_relay_message(amplicon_p2p_relay_message):
        raise ValueError("Invalid Amplicon P2P Relay message passed.")
    if common_utils.is_empty_object(node_secret):
        raise ValueError("Invalid node secret passed.")

    sealed_box = get_sealed_box_for_private_key(node_secret)
    try:
        decrypted_message = sealed_box.decrypt(
            amplicon_p2p_relay_message.encrypted_message_core.encrypted_message_content)
    except CryptoError as e:
        decrypted_message = None  # Message not meant for this node.
    return decrypted_message


def encrypt_message_core_information(message_core_information: node_pb2.MessageCoreInformation,
                                     destination_public_key_hex_string: str) -> bytes:
    if common_utils.is_empty_string(destination_public_key_hex_string):
        raise ValueError("Invalid destination public key passed.")
    if common_utils.is_empty_object(message_core_information):
        raise ValueError("Invalid message core information passed.")
    sealed_box = get_sealed_box_for_public_key(destination_public_key_hex_string)
    raw_message_bytes = message_core_information.SerializeToString()
    output = sealed_box.encrypt(raw_message_bytes)
    return output


def is_valid_dna_length(dna_length: int) -> bool:
    if 15 <= dna_length <= 2048:
        return True
    return False


def is_valid_public_key(public_key: str, expected_public_key_length=64):
    if common_utils.is_empty_string(public_key):
        return False
    if len(public_key) != expected_public_key_length:
        return False
    return True


def is_valid_message_endpoint_id(message_endpoint_id: node_pb2.MessageEndpointId,
                                 expected_public_key_length: int = 64) -> bool:
    if not is_valid_public_key(message_endpoint_id.endpoint_public_key, expected_public_key_length):
        return False
    if not common_utils.is_empty_string(message_endpoint_id.forwarder_public_key) and not is_valid_public_key(
            message_endpoint_id.forwarder_public_key, expected_public_key_length):
        return False
    return True


def check_enqueue_find_valid_message_dna_request_and_generate_response_status(
        request: node_pb2.EnqueueFindValidMessageDnaRequest) -> node_pb2.ResponseStatus:
    if not common_utils.is_valid_node_info(request.requesting_node):
        return node_pb2.ResponseStatus(is_successful=False, status_text="Invalid requesting node info.")
    if not is_valid_dna_length(request.dna_length):
        return node_pb2.ResponseStatus(is_successful=False, status_text="Invalid DNA length requested.")
    if not is_valid_message_endpoint_id(request.source_id):
        return node_pb2.ResponseStatus(is_successful=False, status_text="Invalid source endpoint id provided.")
    if not is_valid_message_endpoint_id(request.destination_id) and common_utils.is_empty_bytes(
            request.encrypted_handshake_payload.encrypted_message_content):
        return node_pb2.ResponseStatus(is_successful=False,
                                       status_text="Neither destination endpoint id, nor encrypted handshake packet provided.")
    return node_pb2.ResponseStatus(is_successful=True)


def encrypt_message_core_information_with_destination_id(
        message_core_information: node_pb2.MessageCoreInformation) -> node_pb2.EncryptedMessageCoreInformation:
    if not is_valid_message_endpoint_id(message_core_information.destination_id):
        return node_pb2.EncryptedMessageCoreInformation()
    if common_utils.is_empty_string(message_core_information.destination_id.forwarder_public_key):
        return node_pb2.EncryptedMessageCoreInformation(
            encrypted_message_content=encrypt_message_core_information(
                message_core_information,
                message_core_information.destination_id.endpoint_public_key))
    encrypted_for_final_endpoint = encrypt_message_core_information(message_core_information,
                                                                    message_core_information.destination_id.endpoint_public_key)
    message_core_information_for_forwarder = node_pb2.MessageCoreInformation(
        message_type=node_pb2.MessageCoreInformation.BINARY_CONTENT, message_payload=encrypted_for_final_endpoint,
        destination_id=message_core_information.destination_id)
    return node_pb2.EncryptedMessageCoreInformation(
        encrypted_message_content=encrypt_message_core_information(
            message_core_information_for_forwarder,
            message_core_information.destination_id.forwarder_public_key))


def decrypt_encrypted_message_core_information_with_node_secret(
        amplicon_p2p_relay_message: node_pb2.AmpliconP2PRelayMessage,
        node_secret: node_pb2.NodeSecret) -> node_pb2.MessageCoreInformation:
    sealed_box = get_sealed_box_for_private_key(node_secret)
    try:
        decrypted_message = sealed_box.decrypt(
            amplicon_p2p_relay_message.encrypted_message_core.encrypted_message_content)
    except CryptoError as e1:
        decrypted_message = None  # Message not meant for this node.
    if decrypted_message is None:
        return None
    output = node_pb2.MessageCoreInformation()
    try:
        output.ParseFromString(decrypted_message)
    except DecodeError as e2:
        output = None
    return output


def has_valid_message_amplicon(message_dna: str, secret_node_primer: str, secret_node_amplicon_threshold: int) -> bool:
    first_index = message_dna.find(secret_node_primer)
    if first_index == -1:  # index not found
        return False
    last_index = message_dna.rfind(secret_node_primer)
    if last_index - first_index >= secret_node_amplicon_threshold:
        return True
    return False


def should_message_be_relayed(amplicon_p2p_relay_message: node_pb2.AmpliconP2PRelayMessage,
                              node_secret: node_pb2.NodeSecret) -> bool:
    if common_utils.is_empty_object(node_secret) or common_utils.is_empty_string(
            node_secret.secret_node_primer):
        raise ValueError("Invalid current node secret passed.")
    if not is_valid_amplicon_p2p_relay_message(amplicon_p2p_relay_message):
        raise ValueError("Invalid encrypted message passed.")

    if has_valid_message_amplicon(amplicon_p2p_relay_message.message_dna, node_secret.secret_node_primer,
                                  node_secret.secret_amplicon_threshold):
        return True
    return False


def generate_primer_or_dna_string(desired_length, allowed_characters="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                                  random_seed=0):
    if random_seed != 0:
        seed(random_seed)
    output = ''.join(choices(allowed_characters, k=desired_length))
    return output


def generate_message_dna_candidates(message_dna_length=128, num_candidates_to_generate=100) -> [str]:
    output = set()
    for i in range(num_candidates_to_generate):
        output.add(generate_primer_or_dna_string(desired_length=message_dna_length))
    return list(output)


def get_amplicon_p2p_relay_message(encrypted_message_core: node_pb2.EncryptedMessageCoreInformation, message_dna: str):
    return node_pb2.AmpliconP2PRelayMessage(message_id=common_utils.generate_uuid_string(),
                                            encrypted_message_core=encrypted_message_core, message_dna=message_dna)


def get_amplicon_p2p_relay_messages_with_different_message_dna(
        encrypted_message_core: node_pb2.EncryptedMessageCoreInformation, message_dna_list: [str]):
    output = []
    for dna in message_dna_list:
        output.append(get_amplicon_p2p_relay_message(encrypted_message_core=encrypted_message_core, message_dna=dna))
    return output


def get_modified_relay_request(relay_request_original: node_pb2.RelayMessageRequest, message_dna: str = None):
    if common_utils.is_empty_object(relay_request_original):
        raise ValueError("Invalid relay request provided.")
    if common_utils.is_empty_string(message_dna):
        return relay_request_original
    message = node_pb2.EncryptedMessage(message_id=relay_request_original.message.message_id,
                                        encrypted_message_content=relay_request_original.message.encrypted_message_content,
                                        message_dna=message_dna)
    return node_pb2.RelayMessageRequest(message=message, requesting_node=relay_request_original.requesting_node,
                                        destination_id=relay_request_original.destination_id,
                                        request_utc_timestamp_nanos=relay_request_original.request_utc_timestamp_nanos)


def get_public_key_string_from_private_key_string(secret_private_key: str) -> str:
    private_key = PrivateKey(
        private_key=binascii.unhexlify(common_utils.make_encoded_str(secret_private_key)))
    public_key = binascii.hexlify(bytes(private_key.public_key))
    return public_key.decode("utf-8")


def get_message_core_hash(message_core: node_pb2.MessageCoreInformation) -> str:
    message_core_without_hash = node_pb2.MessageCoreInformation(message_type=message_core.message_type,
                                                                message_payload=message_core.message_payload,
                                                                source_id=message_core.source_id,
                                                                destination_id=message_core.destination_id,
                                                                nonce=message_core.nonce)
    sha1_hash = hashlib.sha1(message_core_without_hash.SerializeToString()).hexdigest()
    return sha1_hash


def get_message_core(message_type: node_pb2.MessageCoreInformation.MessageType,
                     source_id: node_pb2.MessageEndpointId, destination_id: node_pb2.MessageEndpointId,
                     message_payload: bytes = None, nonce: int = None) -> node_pb2.MessageCoreInformation:
    if nonce is None:
        nonce = random.randint(0, sys.maxsize)
    temp_message_core = node_pb2.MessageCoreInformation(message_type=message_type, message_payload=message_payload,
                                                        source_id=source_id, destination_id=destination_id,
                                                        nonce=nonce)
    message_hash = get_message_core_hash(temp_message_core)
    return node_pb2.MessageCoreInformation(message_type=message_type, message_payload=message_payload,
                                           source_id=source_id, destination_id=destination_id, nonce=nonce,
                                           message_hash=message_hash)


def is_handshake_message(message_core: node_pb2.MessageCoreInformation) -> bool:
    if message_core.message_type == node_pb2.MessageCoreInformation.HANDSHAKE:
        return True
    return False


def is_handshake_acknowledgement_message(message_core: node_pb2.MessageCoreInformation) -> bool:
    if message_core.message_type == node_pb2.MessageCoreInformation.ACKNOWLEDGEMENT_HANDSHAKE:
        return True
    return False


def is_binary_content_message(message_core: node_pb2.MessageCoreInformation) -> bool:
    if message_core.message_type == node_pb2.MessageCoreInformation.BINARY_CONTENT:
        return True
    return False


def is_binary_content_acknowledgement_message(message_core: node_pb2.MessageCoreInformation) -> bool:
    if message_core.message_type == node_pb2.MessageCoreInformation.ACKNOWLEDGEMENT_BINARY_CONTENT:
        return True
    return False

def make_serialized_packable_relay_message(encrypted_p2p_relay_message:node_pb2.AmpliconP2PRelayMessage, decrypted_message_core:node_pb2.MessageCoreInformation) -> bytes:
    packable_relay_message = node_pb2.PackableRelayMessageInfo(encrypted_relay_message=encrypted_p2p_relay_message, decrypted_message_core=decrypted_message_core)
    return packable_relay_message.SerializeToString()

def maybe_get_destination_endpoint_from_packable_relay_message(
        message: node_pb2.PackableRelayMessageInfo) -> node_pb2.MessageEndpointId:
    if not is_valid_message_endpoint_id(message.decrypted_message_core.destination_id):
        return None
    return message.decrypted_message_core.destination_id


def maybe_make_encrypted_p2p_relay_message_from_packable_relay_message(message: node_pb2.PackableRelayMessageInfo,
                                                                       message_dna: str = None):
    pass


def make_string_tuple_from_message_endpoint_id(endpoint_id: node_pb2.MessageEndpointId):
    if common_utils.is_empty_string(endpoint_id.forwarder_public_key):
        return endpoint_id.endpoint_public_key, ''
    return endpoint_id.endpoint_public_key, endpoint_id.forwarder_public_key


def maybe_get_source_and_destination_endpoint_id_tuple_from_enqueue_find_valid_message_dna_request(
        request: node_pb2.EnqueueFindValidMessageDnaRequest) -> (str, str, str, str):
    if not is_valid_message_endpoint_id(request.source_id) or not is_valid_message_endpoint_id(request.destination_id):
        return None
    output = []
    output.extend(make_string_tuple_from_message_endpoint_id(request.source_id))
    output.extend(make_string_tuple_from_message_endpoint_id(request.destination_id))
    return tuple(output)

def get_sink_id_from_endpoint_id(endpoint_id:node_pb2.MessageEndpointId, node_public_key:str = None):
    if not common_utils.is_empty_string(node_public_key) and endpoint_id.forwarder_public_key != node_public_key:
        return None
    if not is_valid_public_key(endpoint_id.endpoint_public_key):
        return None
    return endpoint_id.endpoint_public_key