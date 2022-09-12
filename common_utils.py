import hashlib
import re
import time

import node_pb2


def is_empty_object(input_object: object) -> bool:
    if not isinstance(input_object, object):
        raise ValueError("Input is not an object, an object type input was expected.")
    if input_object is None:
        return True
    return False


def is_empty_string(input_str: str) -> bool:
    if not isinstance(input_str, str):
        raise ValueError("Input is not a string, a string type input was expected.")
    if input_str is None or len(input_str) == 0:
        return True
    return False


def is_empty_bytes(input_bytes: bytes) -> bool:
    if not isinstance(input_bytes, bytes):
        raise ValueError("Input is not a bytes string, a bytes type input was expected.")
    if input_bytes is None or len(input_bytes) == 0:
        return True
    return False


def is_valid_hostname(hostname: str) -> bool:
    if len(hostname) > 255:
        return False
    if hostname[-1] == ".":
        hostname = hostname[:-1]  # strip exactly one dot from the right, if present
    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in hostname.split("."))


def is_valid_node_info(node_info: node_pb2.NodeInfo) -> bool:
    if is_empty_object(node_info):
        return False
    if is_empty_string(node_info.node_id):
        return False
    if not is_valid_hostname(node_info.node_address):
        return False
    return True


def get_node_hash(node_info: node_pb2.NodeInfo) -> str:
    if not is_valid_node_info(node_info):
        return ''
    return hashlib.sha1(node_info.node_address).hexdigest()


def has_valid_message_amplicon(message_dna: str, secret_node_primer: str, secret_node_amplicon_threshold: int) -> bool:
    first_index = message_dna.find(secret_node_primer)
    if first_index == -1:  # index not found
        return False
    last_index = message_dna.rfind(secret_node_primer)
    if last_index - first_index >= secret_node_amplicon_threshold:
        return True
    return False


def should_message_be_relayed(encrypted_message: node_pb2.EncryptedMessage,
                              current_node_properties: node_pb2.NodeProperties) -> bool:
    if is_empty_object(current_node_properties) or is_empty_object(current_node_properties.secrets) or is_empty_string(
            current_node_properties.secrets.secret_node_primer):
        raise ValueError("Invalid current node properties passed.")
    if is_empty_object(encrypted_message) or is_empty_string(encrypted_message.message_dna):
        raise ValueError("Invalid encrypted message passed.")

    if has_valid_message_amplicon(encrypted_message.message_dna, current_node_properties.secrets.secret_node_primer,
                                  current_node_properties.secrets.secret_amplicon_threshold):
        return True
    return False


def get_timestamp_now_ns() -> int:
    return time.time_ns()
