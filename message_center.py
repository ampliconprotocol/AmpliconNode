import logging
from threading import Lock

import common_utils
import message_utils
import node_pb2
import node_pb2_grpc
from thread_pool_with_run_delay import ThreadPoolWithRunDelay


def relay_request_to_single_connection(channel, relay_message_request_original, requesting_node_info):
    stub = node_pb2_grpc.NodeStub(channel)
    relay_message_request_new = node_pb2.RelayMessageRequest(requesting_node=requesting_node_info,
                                                             message=relay_message_request_original.message,
                                                             destination_id=relay_message_request_original.destination_id,
                                                             request_utc_timestamp_nanos=relay_message_request_original.request_utc_timestamp_nanos)
    _ = stub.RelayMessage(relay_message_request_new)


class MessageCenter(object):
    def __init__(self, node_info: node_pb2.NodeInfo, node_secret: node_pb2.NodeSecret,
                 thread_pool_with_run_delay_instance: ThreadPoolWithRunDelay):
        self.thread_pool_with_run_delay_instance = thread_pool_with_run_delay_instance
        self.node_info = node_info
        self.node_secret = node_secret
        # Contains the following tuple associated with each topic_id key:
        # (message_time_stamp_nanos, to_topic_id, to_public_key, message_dna)
        self.destination_id_to_working_dna_candidates = {}
        self.known_message_ids = set()
        self.lock = Lock()

    def consume_message(self, decrypted_message: node_pb2.MessageCoreInformation,
                        original_relay_request: node_pb2.RelayMessageRequest):
        """

        :param decrypted_message:
        :param original_relay_request:
        :return:
        """
        if common_utils.is_empty_object(decrypted_message):
            # Message is not meant for us
            return
        if common_utils.is_empty_object(original_relay_request):
            # We don't have sufficient data to respond
            return

        logging.info("Got the following message addressed to current node : %s",
                     decrypted_message.SerializeToString().decode('utf-8'))
        if decrypted_message.message_type == node_pb2.ACKNOWLEDGEMENT:
            return self.process_acknowledgement_message(decrypted_message, original_relay_request)
        # TODO: Handle discrete packet and stream types.

    def is_message_already_encountered(self, amplicon_p2p_relay_message: node_pb2.AmpliconP2PRelayMessage,
                                       mark_message_as_encountered=True) -> bool:
        output = False
        with self.lock:
            if amplicon_p2p_relay_message.message_id in self.known_message_ids:
                output = True
            if mark_message_as_encountered:
                self.known_message_ids.add(amplicon_p2p_relay_message.message_id)
        return output

    def relay_message_to_connections(self, relay_message_request_original: node_pb2.RelayMessageRequest,
                                     node_hash_to_channels: {}):
        """

        :param relay_message_request_original:
        :param node_hash_to_channels:
        :return:
        """
        if self.is_message_already_encountered(relay_message_request_original.message):
            return
        for node_hash in node_hash_to_channels:
            channel = node_hash_to_channels[node_hash]
            self.thread_pool_with_run_delay_instance.add_job(relay_request_to_single_connection,
                                                             (channel, relay_message_request_original, self.node_info))

    def find_dna_to_reach_destination(self, relay_message_request: node_pb2.RelayMessageRequest,
                                      peer_node_hash_to_channels: {},
                                      topic_id: str, message_dna_length: int = 128, wait_time_out_ms: int = 2000,
                                      on_success=None, on_failure=None):
        """
        :param relay_message_request:
        :param peer_node_hash_to_channels:
        :param topic_id:
        :param message_dna_length:
        :param wait_time_out_ms:
        :param on_success: A function that takes the topic_id and a list of
        (message_time_stamp_nanos, to_topic_id, to_public_key, message_dna)
        :param on_failure: A function that just consumes the topic_id
        :return: None
        """
        with self.lock:
            if topic_id in self.destination_id_to_working_dna_candidates:
                del self.destination_id_to_working_dna_candidates[topic_id]

        dna_to_try = message_utils.get_message_dna_candidates_for_95_pct_reachability(message_dna_length)

        for message_dna_candidate in dna_to_try:
            relay_request_new = message_utils.get_modified_relay_request(relay_message_request, message_dna_candidate)
            self.relay_message_to_connections(relay_request_new, peer_node_hash_to_channels)

        self.thread_pool_with_run_delay_instance.add_job(self.__check_if_working_dna_is_found,
                                                         (topic_id, on_success, on_failure),
                                                         run_delay_from_now_ns=wait_time_out_ms * 1000)

    def process_acknowledgement_message(self, decrypted_message: node_pb2.MessageCoreInformation,
                                        original_relay_request: node_pb2.RelayMessageRequest):
        """

        :param decrypted_message:
        :param original_relay_request:
        :return:
        """
        if decrypted_message.message_type != node_pb2.ACKNOWLEDGEMENT or common_utils.is_empty_object(
                decrypted_message.acknowledgement_message):
            return
        to_topic_id = decrypted_message.acknowledgement_message.send_destination_id
        to_public_key = decrypted_message.acknowledgement_message.send_public_key
        message_dna = original_relay_request.message.message_dna
        message_time_stamp_nanos = original_relay_request.request_utc_timestamp_nanos
        from_topic_id = original_relay_request.destination_id

        with self.lock:
            if from_topic_id not in self.destination_id_to_working_dna_candidates:
                self.destination_id_to_working_dna_candidates[from_topic_id] = []
            self.destination_id_to_working_dna_candidates[from_topic_id].append(
                (message_time_stamp_nanos, to_topic_id, to_public_key, message_dna))

    # def __create_handshake_encrypted_message(self, destination_node_public_key_hex_str: str, return_destination_id,
    #                                          return_public_key=None) -> bytes:
    #     """
    #
    #     :param destination_node_public_key_hex_str:
    #     :param return_destination_id:
    #     :param return_public_key:
    #     :return:
    #     """
    #     if common_utils.is_empty_string(destination_node_public_key_hex_str):
    #         raise ValueError("Invalid destination_node_public_key_hex_str passed.")
    #     if common_utils.is_empty_string(return_public_key):
    #         return_public_key = message_utils.get_public_key_hex_str(self.node_secret)
    #     # unencrypted_output = node_pb2.RawMessage(message_type=node_pb2.HANDSHAKE,
    #     #                                          handshake_message=node_pb2.HandShakeMessage(
    #     #                                              return_destination_id=return_destination_id,
    #     #                                              return_public_key=return_public_key))
    #     unencrypted_output = node_pb2.MessageCoreInformation(message_type=node_pb2.MessageCoreInformation.HANDSHAKE, source=)
    #     return message_utils.encrypt_message_core_information(unencrypted_output, destination_node_public_key_hex_str)

    def encrypt_message_core_information_for_destination_endpoint_id(self,
                                                                     message_core_information: node_pb2.MessageCoreInformation) -> node_pb2.AmpliconP2PRelayMessage:
        pass

    def enqueue_find_message_dna_request(self):
        pass

    def get_enqueue_find_message_dna_request_status(self):
        pass

    def __prepare_enqueue_find_message_dna_request(self,
                                                   request: node_pb2.EnqueueFindValidMessageDnaRequest) -> node_pb2.EnqueueFindValidMessageDnaRequest:
        """
        This internal method prepares a {@code node_pb2.EnqueueFindValidMessageDnaRequest} object. It checks if
        an encrypted HANDSHAKE packet exists. If not, it creates a HANDSHAKE packet (encrypted with
        {@code destination_id}) and adds it to the request object.
        :param request:
        :return: A prepared node_pb2.EnqueueFindValidMessageDnaRequest object with the proper HANDSHAKE packet.
        """
        if not common_utils.is_empty_bytes(request.encrypted_handshake_payload):
            return request
        pass

    def __check_if_working_dna_is_found(self, topic_id, on_success, on_failure):
        with self.lock:
            if topic_id not in self.destination_id_to_working_dna_candidates or len(
                    self.destination_id_to_working_dna_candidates[topic_id]) == 0:
                if not common_utils.is_empty_object(on_failure):
                    return on_failure(topic_id)
            elif not common_utils.is_empty_object(on_success):
                return on_success(topic_id, self.destination_id_to_working_dna_candidates[topic_id])
