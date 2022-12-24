import hashlib
import re
import time
import uuid

import node_pb2


def is_empty_integer(input_int: int, return_empty_if_zero=False) -> bool:
    if not isinstance(input_int, int) and input_int is not None:
        return True
    if input_int is None:
        return True
    if input_int == 0 and return_empty_if_zero:
        return True
    return False


def is_empty_object(input_object: object) -> bool:
    if not isinstance(input_object, object):
        raise ValueError("Input is not an object, an object type input was expected.")
    if input_object is None:
        return True
    return False


def is_empty_string(input_str: str) -> bool:
    if not isinstance(input_str, str) and input_str is not None:
        raise ValueError("Input is not a string, a string type input was expected.")
    if input_str is None or len(input_str) == 0:
        return True
    return False


def is_empty_list(input_list) -> bool:
    if input_list is None:
        return True
    if not isinstance(input_list, list):
        raise ValueError("Input is not a list, a list type object was expected.")
    if len(input_list) == 0:
        return True
    return False


def is_empty_bytes(input_bytes: bytes) -> bool:
    if not isinstance(input_bytes, bytes) and input_bytes is not None:
        raise ValueError("Input is not a bytes string, a bytes type input was expected.")
    if input_bytes is None or len(input_bytes) == 0:
        return True
    return False


def get_num_digits_in_int(input_num: int) -> bool:
    if input_num == 0:
        return 1
    output = 0
    input_num = abs(input_num)
    while input_num > 0:
        output += 1
        input_num //= 10
    return output


def is_valid_ip_v4(input_str: str) -> bool:
    pattern = "^([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})$"
    matcher = re.compile(pattern)
    result = matcher.match(input_str)
    if result is None:
        return False
    digits_count = 0
    for i in result.groups():
        digits_count += get_num_digits_in_int(int(i))
    if len(input_str) != (digits_count + 3):
        return False
    return True


def is_valid_domain_name(input_str: str) -> bool:
    pattern = "^([a-z0-9_\-]+)(\.?[a-z0-9_\-]+)?(\.?[a-z0-9_\-]+)?$"
    matcher = re.compile(pattern, re.IGNORECASE)
    result = matcher.match(input_str)
    if result is None:
        return False
    return True


def is_valid_hostname(hostname: str) -> bool:
    if len(hostname) > 255:
        return False
    pattern = "^([^:]+)(:[0-9]{1,5})?$"
    matcher = re.compile(pattern)
    result = matcher.match(hostname)
    if result is None:
        return False
    first_part = result.group(1)
    if is_valid_ip_v4(first_part):
        return True
    if is_valid_domain_name(first_part):
        return True
    return False


def is_valid_node_info(node_info: node_pb2.NodeInfo) -> bool:
    if is_empty_object(node_info):
        return False
    if not is_valid_hostname(node_info.node_address):
        return False
    return True


def make_encoded_str(input_str: str) -> bytes:
    if isinstance(input_str, str):
        return input_str.encode('utf-8')
    if isinstance(input_str, bytes):
        return input_str
    return b''


def get_node_hash(node_info: node_pb2.NodeInfo) -> str:
    if not is_valid_node_info(node_info):
        return ''
    encoded_string = make_encoded_str(node_info.node_address)
    return hashlib.sha1(encoded_string).hexdigest()


def get_timestamp_now_ns() -> int:
    return time.time_ns()


def convert_seconds_to_ns(seconds: float) -> int:
    return int(seconds * 10 ** 9)


def generate_uuid_string():
    uuid4_hex_string = str(uuid.uuid4().hex)
    return uuid4_hex_string
