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
    if not is_valid_hostname(node_info.node_address):
        return False
    return True


def get_node_hash(node_info: node_pb2.NodeInfo) -> str:
    if not is_valid_node_info(node_info):
        return ''
    return hashlib.sha1(node_info.node_address).hexdigest()





def get_timestamp_now_ns() -> int:
    return time.time_ns()
