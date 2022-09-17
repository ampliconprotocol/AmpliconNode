import node_pb2
import node_pb2_grpc


class MessageCenter(object):
    def __init__(self):
        pass

    def add_message_hook(self):
        pass

    def remove_message_hook(self):
        pass

    def process_message(self, decrypted_message):
        pass

    def is_message_already_encountered(self, encrypted_message: node_pb2.EncryptedMessage) -> bool:
        return False

    def relay_message_to_connections(self, relay_message_request_original: node_pb2.RelayMessageRequest,
                                     current_node_info: node_pb2.NodeInfo, node_hash_to_channels: []):
        if self.is_message_already_encountered(relay_message_request_original.message):
            return
        for node_hash in node_hash_to_channels:
            channel = node_hash_to_channels[node_hash]
            stub = node_pb2_grpc.NodeStub(channel)
            relay_message_request_new = node_pb2.RelayMessageRequest(requesting_node=current_node_info,
                                                                     message=relay_message_request_original.message,
                                                                     destination_id=relay_message_request_original.destination_id,
                                                                     request_utc_timestamp_nanos=relay_message_request_original.request_utc_timestamp_nanos)
            relay_message_response = stub.RelayMessage(relay_message_request_new)
