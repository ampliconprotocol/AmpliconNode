import time
from concurrent import futures
from unittest import TestCase

import grpc

import common_utils
import node_pb2
from node_mock import NodeMock
from peer_connections_manager import PeerConnectionsManager
from test_utils import get_free_port, generate_public_and_private_keys
from thread_pool_with_run_delay import ThreadPoolWithRunDelay
from message_center import MessageCenter
from message_io_memory_sink import MessageIoMemorySink
from queue import Queue
import message_utils


class TestMessageCenter(TestCase):
    def setUp(self) -> None:
        self.read_messages = Queue(maxsize=100)
        self.thread_pool = ThreadPoolWithRunDelay(num_threads=8)

        self.node_info = self.__make_node_info(node_address="11.12.13.14:1516")
        self.node_secrets = self.__make_node_secrets(index=1)
        self.node_properties = node_pb2.NodeProperties(node_info=self.node_info, node_secrets=self.node_secrets,
                                                       max_relays_per_message_id=3)
        self.peer_connections_manager = PeerConnectionsManager(thread_pool=self.thread_pool,
                                                               node_properties=self.node_properties,
                                                               periodicity_of_connections_check_active_seconds=10)
        self.__start_fake_remote_server()
        self.peer_connections_manager.add_peer_node(self.fake_remote_node_info)
        self.message_center = MessageCenter(node_properties=self.node_properties,
                                            peer_connections_manager=self.peer_connections_manager,
                                            thread_pool_with_run_delay_instance=self.thread_pool)
        self.public_keys = []
        self.private_keys = []

    def tearDown(self) -> None:
        self.server.stop(grace=40)
        self.message_center.release_resources()
        self.peer_connections_manager.release_resources()
        self.thread_pool.release_resources()

    def test_add_message_sink_for_forwarded_public_key_and_send_message_to_sink_by_public_key(self):
        self.__generate_key_pairs()
        message_io_memory_sink = MessageIoMemorySink(
            sink_id=self.public_keys[-1])
        self.message_center.add_message_sink_for_forwarded_public_key(message_io_memory_sink)

        test_message_core = self.__get_decrypted_message_core(self.public_keys[-1])
        test_amplicon_p2p_message = self.__get_encrypted_amplicon_p2p_message(test_message_core, message_dna="ATGCATGC")
        self.message_center.send_message_to_sink_by_public_key(self.public_keys[-1], test_amplicon_p2p_message,
                                                               test_message_core)
        time.sleep(2)
        received_bytes_message = message_io_memory_sink.get_written_message()
        packed_message = node_pb2.PackableRelayMessageInfo.FromString(received_bytes_message)
        self.assertEqual(packed_message.decrypted_message_core, test_message_core)
        self.assertEqual(packed_message.encrypted_relay_message, test_amplicon_p2p_message)

    def test_is_message_relayed_max_allowed_times_and_increment_message_relay_count(self):
        self.__generate_key_pairs()
        test_message_core = self.__get_decrypted_message_core(self.public_keys[-1])
        test_amplicon_p2p_message = self.__get_encrypted_amplicon_p2p_message(test_message_core, message_dna="ATGCATGC")
        for i in range(self.node_properties.max_relays_per_message_id):
            self.message_center.push_message_into_relay_queue(test_amplicon_p2p_message)
            time.sleep(2)
            print(i)
            if i < self.node_properties.max_relays_per_message_id - 1:
                self.assertFalse(self.message_center.is_message_relayed_max_allowed_times(test_amplicon_p2p_message))
            else:
                self.assertTrue(self.message_center.is_message_relayed_max_allowed_times(test_amplicon_p2p_message))

    def test_is_message_core_received_before(self):
        self.fail()

    def test_mark_message_core_as_received(self):
        self.fail()

    def test_enqueue_find_valid_message_dna_request(self):
        self.fail()

    def test_get_enqueue_find_message_dna_request_results(self):
        self.fail()

    def test_push_message_into_relay_queue(self):
        self.fail()

    def test_maybe_decrypt_encrypted_message(self):
        self.fail()

    def test_process_received_amplicon_p2p_relay_message(self):
        self.fail()

    def test_consume_received_amplicon_p2p_relay_message(self):
        self.fail()

    def test_respond_to_handshake_message(self):
        self.fail()

    def test_process_handshake_acknowledgement_message(self):
        self.fail()

    def test_respond_to_binary_content_message(self):
        self.fail()

    def test_process_binary_content_acknowledgement_message(self):
        self.fail()

    def __make_node_info(self, node_address):
        software_version = node_pb2.Version(major_version=0, minor_version=1, is_release=True)
        supported_communication_types = node_pb2.NodeInfo.SECURE_AND_UNSECURE_STREAM
        return node_pb2.NodeInfo(node_address=node_address, software_version=software_version,
                                 supported_communication_types=supported_communication_types)

    def __make_node_secrets(self, index=0):
        node_secrets = [node_pb2.NodeSecret(
            secret_private_key="489ec54938e491145035a468cbcf2a7c97017c57e1510fe85167345b94685f8f",
            secret_node_primer="AT", secret_amplicon_threshold=15),

            node_pb2.NodeSecret(
                secret_private_key="dee960fa17370daafe1447eccb11a1990d8564e5cda6925ad2ee2a7d50fda0ed",
                secret_node_primer="GC", secret_amplicon_threshold=16)]
        return node_secrets[int(index) % len(node_secrets)]

    def __start_fake_remote_server(self):
        free_port = get_free_port()
        self.fake_remote_node_address = "localhost:{port}".format(port=free_port)
        self.fake_remote_node_info = self.__make_node_info(self.fake_remote_node_address)
        self.fake_remote_node_secrets = self.__make_node_secrets()
        self.fake_remote_node_properties = node_pb2.NodeProperties(node_info=self.fake_remote_node_info,
                                                                   node_secrets=self.fake_remote_node_secrets)
        self.fake_remote_node = NodeMock(node_properties=self.fake_remote_node_properties)
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))

    def __read_callback(self, message_sink: MessageIoMemorySink):
        while message_sink.is_read_ready():
            self.read_messages.put(message_sink.read())

    def __get_endpoint_id(self, public_key: str, forwarder_public_key: str = None):
        if common_utils.is_empty_string(forwarder_public_key):
            return node_pb2.MessageEndpointId(endpoint_public_key=public_key)
        return node_pb2.MessageEndpointId(endpoint_public_key=public_key, forwarder_public_key=forwarder_public_key)

    def __get_decrypted_message_core(self, destination_endpoint_public_key: str):
        destination_endpoint_id = self.__get_endpoint_id(public_key=destination_endpoint_public_key,
                                                         forwarder_public_key='e7e09cbd1cbbf9d871a21e6a3e724f7badb96e8aa71754e7df101ae04e211248')
        source_endpoint_id = self.__get_endpoint_id(
            public_key='a104d469a3cdfe5cd79763e00773f92819fef0a9707affc76a01f05a39c0ae2a')
        return message_utils.get_message_core(message_type=node_pb2.MessageCoreInformation.BINARY_CONTENT,
                                              source_id=source_endpoint_id, destination_id=destination_endpoint_id,
                                              message_payload=b"Just testing")

    def __get_encrypted_amplicon_p2p_message(self, message_core: node_pb2.MessageCoreInformation, message_dna: str):
        encrypted_core = message_utils.encrypt_message_core_information_with_destination_id(message_core)
        return message_utils.get_amplicon_p2p_relay_message(encrypted_core, message_dna)

    def __generate_key_pairs(self, count=1):
        for i in range(count):
            key_pair = generate_public_and_private_keys()
            self.private_keys.append(key_pair[0])
            self.public_keys.append(key_pair[1])
