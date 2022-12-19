from threading import Lock

import common_utils
import message_utils
import node_pb2
import node_pb2_grpc
from message_io_sink import MessageIoSink
from message_io_sink_manager import MessageIoSinkManager
from thread_pool_with_run_delay import ThreadPoolWithRunDelay


def relay_request_to_single_connection(channel, relay_message_request_original, requesting_node_info):
    stub = node_pb2_grpc.NodeStub(channel)
    relay_message_request_new = node_pb2.RelayMessageRequest(requesting_node=requesting_node_info,
                                                             message=relay_message_request_original.message,
                                                             destination_id=relay_message_request_original.destination_id,
                                                             request_utc_timestamp_nanos=relay_message_request_original.request_utc_timestamp_nanos)
    _ = stub.RelayMessage(relay_message_request_new)


class MessageCenter(object):
    def __init__(self, node_properties: node_pb2.NodeProperties,
                 thread_pool_with_run_delay_instance: ThreadPoolWithRunDelay):
        self.thread_pool_with_run_delay_instance = thread_pool_with_run_delay_instance
        self.node_info = node_properties.node_info
        self.node_secret = node_properties.node_secrets
        self.node_properties = node_properties
        self.source_id = node_pb2.MessageEndpointId(
            endpoint_public_key=message_utils.get_public_key_string_from_private_key_string(
                self.node_secret.secret_private_key))

        self.forwarded_public_key_to_message_io_sink = {}

        self.relayed_message_ids = set()
        self.request_id_to_working_dna_list = {}
        self.request_id_to_request_proto = {}
        self.message_id_to_encrypted_core = {}  # {str: node_pb2.EncryptedMessageCoreInformation}
        self.message_id_to_acknowledgment_status = {}  # {str:bool}

        self.message_core_hash_to_serialized_source_id = {}  # {str: source_id:str}
        self.lock = Lock()
        self.message_io_sink_manager = MessageIoSinkManager(
            thread_pool_with_run_delay=self.thread_pool_with_run_delay_instance,
            on_read_from_sink_callback=self.__on_read_from_message_io_sink_callback)

    def send_message_to_sink_by_public_key(self, public_key: str, message: bytes):
        self.message_io_sink_manager.write_to_sink(public_key, message)

    def add_message_sink_for_forwarded_public_key(self, message_sink: MessageIoSink):
        public_key = message_sink.get_id()
        if not message_utils.is_valid_public_key(public_key) or common_utils.is_empty_object(message_sink):
            return
        self.message_io_sink_manager.add_message_io_sink(sink=message_sink)

    def is_message_relayed_before(self, message: node_pb2.AmpliconP2PRelayMessage) -> bool:
        with self.lock:
            if message.message_id in self.relayed_message_ids:
                return True
        return False

    def mark_message_as_relayed(self, message: node_pb2.AmpliconP2PRelayMessage):
        with self.lock:
            self.relayed_message_ids.add(message.message_id)

    def is_message_core_received_before(self,
                                        decrypted_message_core: node_pb2.MessageCoreInformation):
        message_core_hash = message_utils.get_message_core_hash(decrypted_message_core)
        source_id_serialized_string = decrypted_message_core.source_id.SerializeToString()
        with self.lock:
            if message_core_hash in self.message_core_hash_to_serialized_source_id and source_id_serialized_string in \
                    self.message_core_hash_to_serialized_source_id[message_core_hash]:
                return True
        return False

    def mark_message_core_as_received(self,
                                      decrypted_message_core: node_pb2.MessageCoreInformation):
        message_core_hash = message_utils.get_message_core_hash(decrypted_message_core)
        source_id_serialized_string = decrypted_message_core.source_id.SerializeToString()
        with self.lock:
            if message_core_hash not in self.message_core_hash_to_serialized_source_id:
                self.message_core_hash_to_serialized_source_id[message_core_hash] = set()
            self.message_core_hash_to_serialized_source_id[message_core_hash].add(source_id_serialized_string)

    def enqueue_find_valid_message_dna_request(self, request_id: str,
                                               request: node_pb2.EnqueueFindValidMessageDnaRequest,
                                               num_candidates_to_check: int = 100):
        dna_candidates_pool = message_utils.generate_message_dna_candidates(message_dna_length=request.dna_length,
                                                                            num_candidates_to_generate=num_candidates_to_check)
        encrypted_handshake_message_core = self.__prepare_handshake_message_from_enqueue_find_valid_message_dna_request(
            request_id, request)
        handshake_message_list = message_utils.get_amplicon_p2p_relay_messages_with_different_message_dna(
            encrypted_handshake_message_core, dna_candidates_pool)
        if common_utils.is_empty_bytes(request.encrypted_handshake_payload.encrypted_message_content):
            # We only listen for response to the EnqueueFindValidMessageDnaRequest request if the forwarding client
            # doesn't want to handle the response. (Which is indicated by providing an encrypted Handshake packet
            # or asking the forwarding server to take care of the handshake packet creation).
            with self.lock:
                self.request_id_to_request_proto[request_id] = request
        self.thread_pool_with_run_delay_instance.add_job(self.__push_message_batch_into_relay_queue,
                                                         (handshake_message_list,))

    def get_enqueue_find_message_dna_request_status(self, request_id: str):
        pass

    def push_message_into_relay_queue(self, amplicon_p2p_relay_message: node_pb2.AmpliconP2PRelayMessage):
        self.thread_pool_with_run_delay_instance.add_job(self.process_received_amplicon_p2p_relay_message,
                                                         (amplicon_p2p_relay_message,))

    def maybe_decrypt_encrypted_message(self,
                                        message: node_pb2.AmpliconP2PRelayMessage) -> node_pb2.MessageCoreInformation:
        return message_utils.decrypt_encrypted_message_core_information_with_node_secret(message, self.node_secret)

    def process_received_amplicon_p2p_relay_message(self, message: node_pb2.AmpliconP2PRelayMessage):
        if not message_utils.is_valid_amplicon_p2p_relay_message(message):
            return
        if self.is_message_relayed_before(message):
            return
        self.mark_message_as_relayed(message)
        message_core = self.maybe_decrypt_encrypted_message(message)
        if common_utils.is_empty_object(message_core):
            # Message could not be decrypted, it is not meant for us
            self.thread_pool_with_run_delay_instance.add_job(self.__send_message_to_connections, (message,))
            return
        self.consume_received_amplicon_p2p_relay_message(original_message=message, decrypted_message_core=message_core)

    def consume_received_amplicon_p2p_relay_message(self, original_message: node_pb2.AmpliconP2PRelayMessage,
                                                    decrypted_message_core: node_pb2.MessageCoreInformation):
        if self.is_message_core_received_before(decrypted_message_core):
            return
        self.mark_message_core_as_received(decrypted_message_core)
        if message_utils.is_handshake_message(decrypted_message_core):
            return self.respond_to_handshake_message(original_message, decrypted_message_core)
        if message_utils.is_handshake_acknowledgement_message(decrypted_message_core):
            return self.process_handshake_acknowledgement_message(original_message, decrypted_message_core)
        if message_utils.is_binary_content_message(decrypted_message_core):
            return self.respond_to_binary_content_message(original_message, decrypted_message_core)
        if message_utils.is_binary_content_acknowledgement_message(decrypted_message_core):
            return self.respond_to_binary_content_message(original_message, decrypted_message_core)
        return

    def respond_to_handshake_message(self, original_message: node_pb2.AmpliconP2PRelayMessage,
                                     decrypted_message_core: node_pb2.MessageCoreInformation):
        acknowledgement_core_message = message_utils.get_message_core(
            message_type=node_pb2.MessageCoreInformation.ACKNOWLEDGEMENT_HANDSHAKE,
            source_id=self.source_id,
            destination_id=decrypted_message_core.source_id, message_payload=decrypted_message_core.message_payload)

        acknowledgement_p2p_relay_message = self.__encrypt_message_core_and_get_relay_message(
            acknowledgement_core_message,
            original_message.message_dna)

        self.thread_pool_with_run_delay_instance.add_job(self.push_message_into_relay_queue,
                                                         (acknowledgement_p2p_relay_message,))

    def process_handshake_acknowledgement_message(self, original_message: node_pb2.AmpliconP2PRelayMessage,
                                                  decrypted_message_core: node_pb2.MessageCoreInformation):
        handshake_packet = node_pb2.HandShakePayload.FromString(decrypted_message_core.message_payload)
        if common_utils.is_empty_string(handshake_packet.request_id):
            return
        request_id = handshake_packet.request_id
        with self.lock:
            if request_id not in self.request_id_to_request_proto:
                return
            if request_id not in self.request_id_to_working_dna_list:
                self.request_id_to_working_dna_list[request_id] = set()
            self.request_id_to_working_dna_list[request_id].add(original_message.message_dna)

    def respond_to_binary_content_message(self, original_message: node_pb2.AmpliconP2PRelayMessage,
                                          decrypted_message_core: node_pb2.MessageCoreInformation):
        self.__acknowledge_receipt_of_binary_content_message(original_message, decrypted_message_core)
        if self.__is_message_meant_for_a_forwarded_public_key(decrypted_message_core):
            public_key_of_forwarded_message_sink = decrypted_message_core.destination_id.endpoint_public_key
            self.thread_pool_with_run_delay_instance.add_job(self.__write_to_message_sink,
                                                             (public_key_of_forwarded_message_sink, original_message,
                                                              decrypted_message_core))
            return
        self.binary_content_message_sink(original_message, decrypted_message_core)

    def process_binary_content_acknowledgement_message(self, original_message: node_pb2.AmpliconP2PRelayMessage,
                                                       decrypted_message_core: node_pb2.MessageCoreInformation):
        pass

    def pack_and_send_message_to_sink_by_public_key(self, public_key: str,
                                                    original_message: node_pb2.AmpliconP2PRelayMessage,
                                                    decrypted_message_core: node_pb2.MessageCoreInformation):
        packable_message = node_pb2.PackableRelayMessageInfo(original_message=original_message,
                                                             decrypted_message=decrypted_message_core)
        self.message_io_sink_manager.write_to_sink(sink_id=public_key, message=packable_message.SerializeToString())

    def __send_message_to_connections(self, message: node_pb2.AmpliconP2PRelayMessage):
        pass

    def __prepare_handshake_message_from_enqueue_find_valid_message_dna_request(self, request_id: str,
                                                                                request: node_pb2.EnqueueFindValidMessageDnaRequest) -> node_pb2.EncryptedMessageCoreInformation:
        """
        This internal method prepares a {@code node_pb2.EnqueueFindValidMessageDnaRequest} object. It checks if
        an encrypted HANDSHAKE packet exists. If not, it creates a HANDSHAKE packet (encrypted with
        {@code destination_id}) and adds it to the request object.
        :param request_id: The request-id associated with the DNA search request for which the HANDSHAKE packet is
        being prepared.
        :param request: The actual contents of the search request as passed by the client.
        :return: A prepared node_pb2.EncryptedMessageCoreInformation object (a HANDSHAKE packet).
        """
        if not common_utils.is_empty_bytes(request.encrypted_handshake_payload.encrypted_message_content):
            return request.encrypted_handshake_payload
        # Handshake packet is not provided. We have to create one.
        # We replace the source id with our source id, so that we can decrypt the acknowledgement response
        # without burdening the forwarding client.
        handshake_packet = node_pb2.HandShakePayload(request_id=request_id)
        message_core_information = message_utils.get_message_core(
            message_type=node_pb2.MessageCoreInformation.HANDSHAKE, source_id=self.source_id,
            message_payload=handshake_packet.SerializeToString(),
            destination_id=request.destination_id)
        return message_utils.encrypt_message_core_information_with_destination_id(message_core_information)

    def __push_message_batch_into_relay_queue(self, amplicon_p2p_relay_messages: []):
        for message in amplicon_p2p_relay_messages:
            self.thread_pool_with_run_delay_instance.add_job(self.push_message_into_relay_queue, (message,))

    def __send_message_to_connections(self, amplicon_p2p_relay_message: node_pb2.AmpliconP2PRelayMessage):
        pass

    def __write_to_message_sink(self, public_key_of_forwarded_message_sink: str,
                                original_message: node_pb2.AmpliconP2PRelayMessage,
                                decrypted_message_core: node_pb2.MessageCoreInformation):
        with self.lock:
            if public_key_of_forwarded_message_sink not in self.forwarded_public_key_to_message_io_sink:
                return
            message_io_sink = self.forwarded_public_key_to_message_io_sink[public_key_of_forwarded_message_sink]
            if message_io_sink.is_write_ready():
                message_io_sink.write(original_message, decrypted_message_core)
                return
            # Sink was not ready to receive the write request. Requeue the write request with a 100ms delay.
            self.thread_pool_with_run_delay_instance.add_job(self.__write_to_message_sink,
                                                             (public_key_of_forwarded_message_sink, original_message,
                                                              decrypted_message_core),
                                                             run_delay_from_now_ns=100000)

    def __is_message_meant_for_a_forwarded_public_key(self,
                                                      decrypted_message_core: node_pb2.MessageCoreInformation) -> bool:
        endpoint_public_key = decrypted_message_core.destination_id.endpoint_public_key
        if not message_utils.is_valid_public_key(
                endpoint_public_key) or endpoint_public_key not in self.forwarded_public_key_to_message_io_sink:
            return False
        return True

    def __encrypt_message_core_and_get_relay_message(self, message_core_information: node_pb2.MessageCoreInformation,
                                                     message_dna: str) -> node_pb2.AmpliconP2PRelayMessage:
        encrypted_message_core = message_utils.encrypt_message_core_information_with_destination_id(
            message_core_information)
        return message_utils.get_amplicon_p2p_relay_message(encrypted_message_core=encrypted_message_core,
                                                            message_dna=message_dna)

    def __acknowledge_receipt_of_binary_content_message(self, original_message: node_pb2.AmpliconP2PRelayMessage,
                                                        decrypted_message_core: node_pb2.MessageCoreInformation):
        acknowledgement_core_message = message_utils.get_message_core(
            message_type=node_pb2.MessageCoreInformation.ACKNOWLEDGEMENT_BINARY_CONTENT,
            source_id=decrypted_message_core.destination_id,
            destination_id=decrypted_message_core.source_id)

        acknowledgement_p2p_relay_message = self.__encrypt_message_core_and_get_relay_message(
            acknowledgement_core_message,
            original_message.message_dna)
        self.thread_pool_with_run_delay_instance.add_job(self.push_message_into_relay_queue,
                                                         (acknowledgement_p2p_relay_message,))

    def __on_read_from_message_io_sink_callback(self, sink_id: str, message: bytes):
        pass
