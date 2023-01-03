from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AddNodeToPeersListRequest(_message.Message):
    __slots__ = ["request_utc_timestamp_nanos", "requesting_node"]
    REQUESTING_NODE_FIELD_NUMBER: _ClassVar[int]
    REQUEST_UTC_TIMESTAMP_NANOS_FIELD_NUMBER: _ClassVar[int]
    request_utc_timestamp_nanos: int
    requesting_node: NodeInfo
    def __init__(self, requesting_node: _Optional[_Union[NodeInfo, _Mapping]] = ..., request_utc_timestamp_nanos: _Optional[int] = ...) -> None: ...

class AddNodeToPeersListResponse(_message.Message):
    __slots__ = ["responding_node", "response_status", "response_utc_timestamp_nanos"]
    RESPONDING_NODE_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_STATUS_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_UTC_TIMESTAMP_NANOS_FIELD_NUMBER: _ClassVar[int]
    responding_node: NodeInfo
    response_status: ResponseStatus
    response_utc_timestamp_nanos: int
    def __init__(self, responding_node: _Optional[_Union[NodeInfo, _Mapping]] = ..., response_status: _Optional[_Union[ResponseStatus, _Mapping]] = ..., response_utc_timestamp_nanos: _Optional[int] = ...) -> None: ...

class AmpliconP2PRelayMessage(_message.Message):
    __slots__ = ["encrypted_message_core", "message_dna", "message_id"]
    ENCRYPTED_MESSAGE_CORE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_DNA_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    encrypted_message_core: EncryptedMessageCoreInformation
    message_dna: str
    message_id: str
    def __init__(self, message_id: _Optional[str] = ..., encrypted_message_core: _Optional[_Union[EncryptedMessageCoreInformation, _Mapping]] = ..., message_dna: _Optional[str] = ...) -> None: ...

class ConnectAsPeerRequest(_message.Message):
    __slots__ = ["request_utc_timestamp_nanos", "requesting_node"]
    REQUESTING_NODE_FIELD_NUMBER: _ClassVar[int]
    REQUEST_UTC_TIMESTAMP_NANOS_FIELD_NUMBER: _ClassVar[int]
    request_utc_timestamp_nanos: int
    requesting_node: NodeInfo
    def __init__(self, requesting_node: _Optional[_Union[NodeInfo, _Mapping]] = ..., request_utc_timestamp_nanos: _Optional[int] = ...) -> None: ...

class ConnectAsPeerResponse(_message.Message):
    __slots__ = ["responding_node", "response_status", "response_utc_timestamp_nanos"]
    RESPONDING_NODE_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_STATUS_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_UTC_TIMESTAMP_NANOS_FIELD_NUMBER: _ClassVar[int]
    responding_node: NodeInfo
    response_status: ResponseStatus
    response_utc_timestamp_nanos: int
    def __init__(self, responding_node: _Optional[_Union[NodeInfo, _Mapping]] = ..., response_status: _Optional[_Union[ResponseStatus, _Mapping]] = ..., response_utc_timestamp_nanos: _Optional[int] = ...) -> None: ...

class EncryptedMessageCoreInformation(_message.Message):
    __slots__ = ["encrypted_message_content"]
    ENCRYPTED_MESSAGE_CONTENT_FIELD_NUMBER: _ClassVar[int]
    encrypted_message_content: bytes
    def __init__(self, encrypted_message_content: _Optional[bytes] = ...) -> None: ...

class EnqueueFindValidMessageDnaRequest(_message.Message):
    __slots__ = ["destination_id", "dna_length", "encrypted_handshake_payload", "request_utc_timestamp_nanos", "requesting_node", "source_id"]
    DESTINATION_ID_FIELD_NUMBER: _ClassVar[int]
    DNA_LENGTH_FIELD_NUMBER: _ClassVar[int]
    ENCRYPTED_HANDSHAKE_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    REQUESTING_NODE_FIELD_NUMBER: _ClassVar[int]
    REQUEST_UTC_TIMESTAMP_NANOS_FIELD_NUMBER: _ClassVar[int]
    SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    destination_id: MessageEndpointId
    dna_length: int
    encrypted_handshake_payload: EncryptedMessageCoreInformation
    request_utc_timestamp_nanos: int
    requesting_node: NodeInfo
    source_id: MessageEndpointId
    def __init__(self, requesting_node: _Optional[_Union[NodeInfo, _Mapping]] = ..., dna_length: _Optional[int] = ..., destination_id: _Optional[_Union[MessageEndpointId, _Mapping]] = ..., source_id: _Optional[_Union[MessageEndpointId, _Mapping]] = ..., encrypted_handshake_payload: _Optional[_Union[EncryptedMessageCoreInformation, _Mapping]] = ..., request_utc_timestamp_nanos: _Optional[int] = ...) -> None: ...

class EnqueueFindValidMessageDnaResponse(_message.Message):
    __slots__ = ["estimated_wait_time_for_response_ms", "request_id", "responding_node", "response_status", "response_utc_timestamp_nanos"]
    ESTIMATED_WAIT_TIME_FOR_RESPONSE_MS_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    RESPONDING_NODE_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_STATUS_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_UTC_TIMESTAMP_NANOS_FIELD_NUMBER: _ClassVar[int]
    estimated_wait_time_for_response_ms: int
    request_id: str
    responding_node: NodeInfo
    response_status: ResponseStatus
    response_utc_timestamp_nanos: int
    def __init__(self, responding_node: _Optional[_Union[NodeInfo, _Mapping]] = ..., request_id: _Optional[str] = ..., estimated_wait_time_for_response_ms: _Optional[int] = ..., response_status: _Optional[_Union[ResponseStatus, _Mapping]] = ..., response_utc_timestamp_nanos: _Optional[int] = ...) -> None: ...

class GetFoundMessageDnaRequest(_message.Message):
    __slots__ = ["request_id", "request_utc_timestamp_nanos", "requesting_node"]
    REQUESTING_NODE_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    REQUEST_UTC_TIMESTAMP_NANOS_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    request_utc_timestamp_nanos: int
    requesting_node: NodeInfo
    def __init__(self, requesting_node: _Optional[_Union[NodeInfo, _Mapping]] = ..., request_id: _Optional[str] = ..., request_utc_timestamp_nanos: _Optional[int] = ...) -> None: ...

class GetFoundMessageDnaResponse(_message.Message):
    __slots__ = ["found_message_dna", "request_id", "responding_node", "response_status", "response_utc_timestamp_nanos"]
    FOUND_MESSAGE_DNA_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    RESPONDING_NODE_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_STATUS_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_UTC_TIMESTAMP_NANOS_FIELD_NUMBER: _ClassVar[int]
    found_message_dna: _containers.RepeatedScalarFieldContainer[str]
    request_id: str
    responding_node: NodeInfo
    response_status: ResponseStatus
    response_utc_timestamp_nanos: int
    def __init__(self, responding_node: _Optional[_Union[NodeInfo, _Mapping]] = ..., request_id: _Optional[str] = ..., found_message_dna: _Optional[_Iterable[str]] = ..., response_status: _Optional[_Union[ResponseStatus, _Mapping]] = ..., response_utc_timestamp_nanos: _Optional[int] = ...) -> None: ...

class GetNodeInfoRequest(_message.Message):
    __slots__ = ["request_utc_timestamp_nanos", "requesting_node"]
    REQUESTING_NODE_FIELD_NUMBER: _ClassVar[int]
    REQUEST_UTC_TIMESTAMP_NANOS_FIELD_NUMBER: _ClassVar[int]
    request_utc_timestamp_nanos: int
    requesting_node: NodeInfo
    def __init__(self, requesting_node: _Optional[_Union[NodeInfo, _Mapping]] = ..., request_utc_timestamp_nanos: _Optional[int] = ...) -> None: ...

class GetNodeInfoResponse(_message.Message):
    __slots__ = ["responding_node", "response_status", "response_utc_timestamp_nanos"]
    RESPONDING_NODE_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_STATUS_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_UTC_TIMESTAMP_NANOS_FIELD_NUMBER: _ClassVar[int]
    responding_node: NodeInfo
    response_status: ResponseStatus
    response_utc_timestamp_nanos: int
    def __init__(self, responding_node: _Optional[_Union[NodeInfo, _Mapping]] = ..., response_status: _Optional[_Union[ResponseStatus, _Mapping]] = ..., response_utc_timestamp_nanos: _Optional[int] = ...) -> None: ...

class GetPeersListRequest(_message.Message):
    __slots__ = ["max_desired_peers", "request_utc_timestamp_nanos", "requesting_node"]
    MAX_DESIRED_PEERS_FIELD_NUMBER: _ClassVar[int]
    REQUESTING_NODE_FIELD_NUMBER: _ClassVar[int]
    REQUEST_UTC_TIMESTAMP_NANOS_FIELD_NUMBER: _ClassVar[int]
    max_desired_peers: int
    request_utc_timestamp_nanos: int
    requesting_node: NodeInfo
    def __init__(self, requesting_node: _Optional[_Union[NodeInfo, _Mapping]] = ..., max_desired_peers: _Optional[int] = ..., request_utc_timestamp_nanos: _Optional[int] = ...) -> None: ...

class GetPeersListResponse(_message.Message):
    __slots__ = ["peers_list", "response_utc_timestamp_nanos"]
    PEERS_LIST_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_UTC_TIMESTAMP_NANOS_FIELD_NUMBER: _ClassVar[int]
    peers_list: _containers.RepeatedCompositeFieldContainer[NodeInfo]
    response_utc_timestamp_nanos: int
    def __init__(self, peers_list: _Optional[_Iterable[_Union[NodeInfo, _Mapping]]] = ..., response_utc_timestamp_nanos: _Optional[int] = ...) -> None: ...

class HandShakePayload(_message.Message):
    __slots__ = ["request_id"]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    def __init__(self, request_id: _Optional[str] = ...) -> None: ...

class IsNodeLiveRequest(_message.Message):
    __slots__ = ["request_utc_timestamp_nanos", "requesting_node"]
    REQUESTING_NODE_FIELD_NUMBER: _ClassVar[int]
    REQUEST_UTC_TIMESTAMP_NANOS_FIELD_NUMBER: _ClassVar[int]
    request_utc_timestamp_nanos: int
    requesting_node: NodeInfo
    def __init__(self, requesting_node: _Optional[_Union[NodeInfo, _Mapping]] = ..., request_utc_timestamp_nanos: _Optional[int] = ...) -> None: ...

class IsNodeLiveResponse(_message.Message):
    __slots__ = ["is_live", "responding_node", "response_status", "response_utc_timestamp_nanos"]
    IS_LIVE_FIELD_NUMBER: _ClassVar[int]
    RESPONDING_NODE_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_STATUS_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_UTC_TIMESTAMP_NANOS_FIELD_NUMBER: _ClassVar[int]
    is_live: bool
    responding_node: NodeInfo
    response_status: ResponseStatus
    response_utc_timestamp_nanos: int
    def __init__(self, responding_node: _Optional[_Union[NodeInfo, _Mapping]] = ..., is_live: bool = ..., response_status: _Optional[_Union[ResponseStatus, _Mapping]] = ..., response_utc_timestamp_nanos: _Optional[int] = ...) -> None: ...

class MessageCoreInformation(_message.Message):
    __slots__ = ["destination_id", "message_hash", "message_payload", "message_type", "nonce", "source_id"]
    class MessageType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    ACKNOWLEDGEMENT_BINARY_CONTENT: MessageCoreInformation.MessageType
    ACKNOWLEDGEMENT_HANDSHAKE: MessageCoreInformation.MessageType
    BINARY_CONTENT: MessageCoreInformation.MessageType
    DESTINATION_ID_FIELD_NUMBER: _ClassVar[int]
    HANDSHAKE: MessageCoreInformation.MessageType
    MESSAGE_HASH_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_TYPE_FIELD_NUMBER: _ClassVar[int]
    NONCE_FIELD_NUMBER: _ClassVar[int]
    SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    UNSPECIFIED: MessageCoreInformation.MessageType
    destination_id: MessageEndpointId
    message_hash: str
    message_payload: bytes
    message_type: MessageCoreInformation.MessageType
    nonce: int
    source_id: MessageEndpointId
    def __init__(self, message_type: _Optional[_Union[MessageCoreInformation.MessageType, str]] = ..., message_payload: _Optional[bytes] = ..., source_id: _Optional[_Union[MessageEndpointId, _Mapping]] = ..., destination_id: _Optional[_Union[MessageEndpointId, _Mapping]] = ..., nonce: _Optional[int] = ..., message_hash: _Optional[str] = ...) -> None: ...

class MessageEndpointId(_message.Message):
    __slots__ = ["endpoint_public_key", "forwarder_public_key"]
    ENDPOINT_PUBLIC_KEY_FIELD_NUMBER: _ClassVar[int]
    FORWARDER_PUBLIC_KEY_FIELD_NUMBER: _ClassVar[int]
    endpoint_public_key: str
    forwarder_public_key: str
    def __init__(self, endpoint_public_key: _Optional[str] = ..., forwarder_public_key: _Optional[str] = ...) -> None: ...

class NodeInfo(_message.Message):
    __slots__ = ["forwarding_public_key", "is_forwarding_enabled", "node_address", "node_type", "software_version", "supported_communication_types"]
    class NodeSupportedCommunicationTypes(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    class NodeType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    CLIENT_ONLY: NodeInfo.NodeType
    FORWARDING_PUBLIC_KEY_FIELD_NUMBER: _ClassVar[int]
    IS_FORWARDING_ENABLED_FIELD_NUMBER: _ClassVar[int]
    NODE_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    NODE_TYPE_FIELD_NUMBER: _ClassVar[int]
    SECURE: NodeInfo.NodeSupportedCommunicationTypes
    SECURE_AND_UNSECURE: NodeInfo.NodeSupportedCommunicationTypes
    SECURE_AND_UNSECURE_STREAM: NodeInfo.NodeSupportedCommunicationTypes
    SECURE_STREAM: NodeInfo.NodeSupportedCommunicationTypes
    SERVER_AND_CLIENT: NodeInfo.NodeType
    SOFTWARE_VERSION_FIELD_NUMBER: _ClassVar[int]
    SUPPORTED_COMMUNICATION_TYPES_FIELD_NUMBER: _ClassVar[int]
    UNKNOWN: NodeInfo.NodeSupportedCommunicationTypes
    UNKNOWN_NODE_TYPE: NodeInfo.NodeType
    UNSECURE: NodeInfo.NodeSupportedCommunicationTypes
    UNSECURE_STREAM: NodeInfo.NodeSupportedCommunicationTypes
    forwarding_public_key: str
    is_forwarding_enabled: bool
    node_address: str
    node_type: NodeInfo.NodeType
    software_version: Version
    supported_communication_types: NodeInfo.NodeSupportedCommunicationTypes
    def __init__(self, node_address: _Optional[str] = ..., node_type: _Optional[_Union[NodeInfo.NodeType, str]] = ..., software_version: _Optional[_Union[Version, _Mapping]] = ..., supported_communication_types: _Optional[_Union[NodeInfo.NodeSupportedCommunicationTypes, str]] = ..., is_forwarding_enabled: bool = ..., forwarding_public_key: _Optional[str] = ...) -> None: ...

class NodeProperties(_message.Message):
    __slots__ = ["bootstrap_peers_list", "can_exceed_max_peers_if_destination_node_not_reachable", "enable_forwarding_server", "max_candidates_per_request_for_valid_dna_search_for_forwarding_client", "max_peers", "max_relays_per_message_id", "max_time_to_wait_for_destination_node_response_ms", "node_info", "node_secrets"]
    BOOTSTRAP_PEERS_LIST_FIELD_NUMBER: _ClassVar[int]
    CAN_EXCEED_MAX_PEERS_IF_DESTINATION_NODE_NOT_REACHABLE_FIELD_NUMBER: _ClassVar[int]
    ENABLE_FORWARDING_SERVER_FIELD_NUMBER: _ClassVar[int]
    MAX_CANDIDATES_PER_REQUEST_FOR_VALID_DNA_SEARCH_FOR_FORWARDING_CLIENT_FIELD_NUMBER: _ClassVar[int]
    MAX_PEERS_FIELD_NUMBER: _ClassVar[int]
    MAX_RELAYS_PER_MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    MAX_TIME_TO_WAIT_FOR_DESTINATION_NODE_RESPONSE_MS_FIELD_NUMBER: _ClassVar[int]
    NODE_INFO_FIELD_NUMBER: _ClassVar[int]
    NODE_SECRETS_FIELD_NUMBER: _ClassVar[int]
    bootstrap_peers_list: _containers.RepeatedCompositeFieldContainer[NodeInfo]
    can_exceed_max_peers_if_destination_node_not_reachable: bool
    enable_forwarding_server: bool
    max_candidates_per_request_for_valid_dna_search_for_forwarding_client: int
    max_peers: int
    max_relays_per_message_id: int
    max_time_to_wait_for_destination_node_response_ms: int
    node_info: NodeInfo
    node_secrets: NodeSecret
    def __init__(self, node_info: _Optional[_Union[NodeInfo, _Mapping]] = ..., node_secrets: _Optional[_Union[NodeSecret, _Mapping]] = ..., max_peers: _Optional[int] = ..., can_exceed_max_peers_if_destination_node_not_reachable: bool = ..., max_time_to_wait_for_destination_node_response_ms: _Optional[int] = ..., max_relays_per_message_id: _Optional[int] = ..., enable_forwarding_server: bool = ..., max_candidates_per_request_for_valid_dna_search_for_forwarding_client: _Optional[int] = ..., bootstrap_peers_list: _Optional[_Iterable[_Union[NodeInfo, _Mapping]]] = ...) -> None: ...

class NodeSecret(_message.Message):
    __slots__ = ["secret_amplicon_threshold", "secret_node_primer", "secret_private_key"]
    SECRET_AMPLICON_THRESHOLD_FIELD_NUMBER: _ClassVar[int]
    SECRET_NODE_PRIMER_FIELD_NUMBER: _ClassVar[int]
    SECRET_PRIVATE_KEY_FIELD_NUMBER: _ClassVar[int]
    secret_amplicon_threshold: int
    secret_node_primer: str
    secret_private_key: str
    def __init__(self, secret_private_key: _Optional[str] = ..., secret_node_primer: _Optional[str] = ..., secret_amplicon_threshold: _Optional[int] = ...) -> None: ...

class PackableRelayMessageInfo(_message.Message):
    __slots__ = ["decrypted_message_core", "encrypted_relay_message"]
    DECRYPTED_MESSAGE_CORE_FIELD_NUMBER: _ClassVar[int]
    ENCRYPTED_RELAY_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    decrypted_message_core: MessageCoreInformation
    encrypted_relay_message: AmpliconP2PRelayMessage
    def __init__(self, encrypted_relay_message: _Optional[_Union[AmpliconP2PRelayMessage, _Mapping]] = ..., decrypted_message_core: _Optional[_Union[MessageCoreInformation, _Mapping]] = ...) -> None: ...

class RelayMessageRequest(_message.Message):
    __slots__ = ["message", "request_utc_timestamp_nanos", "requesting_node"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    REQUESTING_NODE_FIELD_NUMBER: _ClassVar[int]
    REQUEST_UTC_TIMESTAMP_NANOS_FIELD_NUMBER: _ClassVar[int]
    message: AmpliconP2PRelayMessage
    request_utc_timestamp_nanos: int
    requesting_node: NodeInfo
    def __init__(self, message: _Optional[_Union[AmpliconP2PRelayMessage, _Mapping]] = ..., requesting_node: _Optional[_Union[NodeInfo, _Mapping]] = ..., request_utc_timestamp_nanos: _Optional[int] = ...) -> None: ...

class RelayMessageResponse(_message.Message):
    __slots__ = ["responding_node", "response_utc_timestamp_nanos", "status"]
    RESPONDING_NODE_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_UTC_TIMESTAMP_NANOS_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    responding_node: NodeInfo
    response_utc_timestamp_nanos: int
    status: ResponseStatus
    def __init__(self, responding_node: _Optional[_Union[NodeInfo, _Mapping]] = ..., status: _Optional[_Union[ResponseStatus, _Mapping]] = ..., response_utc_timestamp_nanos: _Optional[int] = ...) -> None: ...

class ResponseStatus(_message.Message):
    __slots__ = ["is_pending", "is_successful", "status_text"]
    IS_PENDING_FIELD_NUMBER: _ClassVar[int]
    IS_SUCCESSFUL_FIELD_NUMBER: _ClassVar[int]
    STATUS_TEXT_FIELD_NUMBER: _ClassVar[int]
    is_pending: bool
    is_successful: bool
    status_text: str
    def __init__(self, is_successful: bool = ..., is_pending: bool = ..., status_text: _Optional[str] = ...) -> None: ...

class Version(_message.Message):
    __slots__ = ["is_alpha", "is_beta", "is_release", "is_release_candidate", "major_version", "minor_version"]
    IS_ALPHA_FIELD_NUMBER: _ClassVar[int]
    IS_BETA_FIELD_NUMBER: _ClassVar[int]
    IS_RELEASE_CANDIDATE_FIELD_NUMBER: _ClassVar[int]
    IS_RELEASE_FIELD_NUMBER: _ClassVar[int]
    MAJOR_VERSION_FIELD_NUMBER: _ClassVar[int]
    MINOR_VERSION_FIELD_NUMBER: _ClassVar[int]
    is_alpha: bool
    is_beta: bool
    is_release: bool
    is_release_candidate: bool
    major_version: int
    minor_version: int
    def __init__(self, major_version: _Optional[int] = ..., minor_version: _Optional[int] = ..., is_alpha: bool = ..., is_beta: bool = ..., is_release_candidate: bool = ..., is_release: bool = ...) -> None: ...
