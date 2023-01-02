import time
from concurrent import futures
from unittest import TestCase

import grpc

import common_utils
import node_pb2
import node_pb2_grpc
from node_mock import NodeMock
from peer_connections_manager import PeerConnectionsManager
from test_utils import get_free_port
from thread_pool_with_run_delay import ThreadPoolWithRunDelay


class TestPeerConnectionsManager(TestCase):
    def setUp(self) -> None:
        free_port = get_free_port()
        self.fake_remote_node_address = "localhost:{port}".format(port=free_port)
        self.fake_remote_node_info = self.__make_node_info(self.fake_remote_node_address)
        self.fake_remote_node_secrets = self.__make_node_secrets()
        self.fake_remote_node_properties = node_pb2.NodeProperties(node_info=self.fake_remote_node_info,
                                                                   node_secrets=self.fake_remote_node_secrets)
        self.fake_remote_node = NodeMock(node_properties=self.fake_remote_node_properties)
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))

        node_pb2_grpc.add_NodeServicer_to_server(self.fake_remote_node, self.server)
        self.server.add_insecure_port(self.fake_remote_node_address)
        self.server.start()
        # print("Server started on ", self.fake_remote_node_address)

        self.thread_pool = ThreadPoolWithRunDelay(num_threads=8)
        self.node_info = self.__make_node_info(node_address="11.12.13.14:1516")
        self.node_secrets = self.__make_node_secrets(index=1)
        self.node_properties = node_pb2.NodeProperties(node_info=self.node_info, node_secrets=self.node_secrets)
        self.peer_connections_manager = PeerConnectionsManager(thread_pool=self.thread_pool,
                                                               node_properties=self.node_properties,
                                                               periodicity_of_connections_check_active_seconds=10)
        self.non_existent_remote_node_info = self.__make_node_info("localhost:{port}".format(port=get_free_port()))

    def tearDown(self) -> None:
        self.server.stop(grace=40)
        self.peer_connections_manager.release_resources()
        self.thread_pool.release_resources()

    def test_add_peer_node(self):
        self.peer_connections_manager.add_peer_node(self.fake_remote_node_info)
        self.peer_connections_manager.add_peer_node(self.non_existent_remote_node_info)
        node_info_list = self.peer_connections_manager.get_peer_node_info_list()
        self.assertEqual(len(node_info_list), 2)
        address_list = [x.node_address for x in node_info_list]
        address_list = sorted(address_list)
        expected_list = sorted(
            [self.fake_remote_node_info.node_address, self.non_existent_remote_node_info.node_address])
        self.assertListEqual(address_list, expected_list)

    def test_relay_amplicon_p2p_message_to_all_active_connections(self):
        self.peer_connections_manager.add_peer_node(self.fake_remote_node_info)
        time.sleep(20)
        # Giving enough time for the periodic checks to run
        test_amplicon_p2p_relay_message = self.__make_amplicon_p2p_relay_message()
        self.peer_connections_manager.relay_amplicon_p2p_message_to_all_active_connections(
            test_amplicon_p2p_relay_message)
        # Allowing enough time for thread based relay to take effect
        time.sleep(1)
        received_request = self.fake_remote_node.pop_request_log()
        self.assertFalse(common_utils.is_empty_object(received_request))
        expected_request = node_pb2.RelayMessageRequest(message=test_amplicon_p2p_relay_message,
                                                        requesting_node=self.node_info,
                                                        request_utc_timestamp_nanos=received_request.request_utc_timestamp_nanos)

        self.assertEqual(received_request.SerializeToString(), expected_request.SerializeToString())

    def test_get_active_peer_nodes_hash(self):
        self.peer_connections_manager.add_peer_node(self.fake_remote_node_info)
        self.peer_connections_manager.add_peer_node(self.non_existent_remote_node_info)
        time.sleep(20)
        # Giving enough time for the periodic checks to run
        self.assertSetEqual(self.peer_connections_manager.get_active_peer_nodes_hash(),
                            {common_utils.get_node_hash(self.fake_remote_node_info), })

    def __make_node_info(self, node_address):
        software_version = node_pb2.Version(major_version=0, minor_version=1, is_release=True)
        supported_communication_types = node_pb2.NodeInfo.SECURE_AND_UNSECURE_STREAM
        return node_pb2.NodeInfo(node_address=node_address, software_version=software_version,
                                 supported_communication_types=supported_communication_types)

    def __make_node_secrets(self, index=0):
        node_secrets = [node_pb2.NodeSecret(
            secret_private_key="a2b740e7e7b828a4750cbe1ef3bbdb625328a528d0de188b378af82782a33c6c",
            secret_node_primer="AT", secret_amplicon_threshold=15),

            node_pb2.NodeSecret(
                secret_private_key="a2b740e7e7b828a4750cbe1ef3bbdb625328a528d0de188b378af82782a33c6c",
                secret_node_primer="GC", secret_amplicon_threshold=16)]
        return node_secrets[int(index) % len(node_secrets)]

    def __make_amplicon_p2p_relay_message(self):
        encrypted_message_core = node_pb2.EncryptedMessageCoreInformation(encrypted_message_content=b"fake message")
        return node_pb2.AmpliconP2PRelayMessage(message_id=common_utils.generate_uuid_string(),
                                                encrypted_message_core=encrypted_message_core, message_dna="ATGC")
