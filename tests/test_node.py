from unittest import TestCase

from grpc import StatusCode
from grpc_testing import server_from_dictionary, strict_real_time

import common_utils
import message_utils
import node_pb2
from node import Node


class TestNode(TestCase):

    def setUp(self) -> None:
        self.fake_remote_node_address = "11.0.0.2:4041"
        self.fake_remote_node_info = self.__make_node_info(self.fake_remote_node_address)
        self.fake_remote_node_secret = self.__make_fake_remote_node_secret()
        self.fake_remote_node_properties = node_pb2.NodeProperties(node_info=self.fake_remote_node_info,
                                                                   node_secrets=self.fake_remote_node_secret)
        node_servicer = Node(node_properties=self.fake_remote_node_properties)
        servicers = {
            node_pb2.DESCRIPTOR.services_by_name['Node']: node_servicer
        }
        self.test_server = server_from_dictionary(
            servicers, strict_real_time())

        self.fake_client_node_address = "11.0.0.1:4040"
        self.fake_client_node_info = self.__make_node_info(self.fake_client_node_address)

    def test_get_node_info(self):
        get_node_info_request_valid = node_pb2.GetNodeInfoRequest(
            requesting_node=self.fake_client_node_info, request_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())
        get_node_info_request_invalid = node_pb2.GetNodeInfoRequest(
            request_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

        for index, request in enumerate([get_node_info_request_valid, get_node_info_request_invalid]):
            method = self.test_server.invoke_unary_unary(
                method_descriptor=(node_pb2.DESCRIPTOR
                .services_by_name['Node']
                .methods_by_name['GetNodeInfo']),
                invocation_metadata={},
                request=request, timeout=1)
            response, metadata, code, details = method.termination()
            self.assertEqual(code, StatusCode.OK)
            self.assertFalse(common_utils.is_empty_object(response))

            if index == 0:
                self.assertEqual(response.response_status, node_pb2.ResponseStatus(is_successful=True))
                self.assertEqual(response.responding_node, self.fake_remote_node_info)
            if index == 1:
                self.assertEqual(response.response_status,
                                 node_pb2.ResponseStatus(is_successful=False, status_text="Invalid requesting node."))

                self.assertTrue(common_utils.is_empty_string(response.responding_node.node_address))

    def test_add_node_to_peers_list(self):
        add_client_node_to_peers_list_request = node_pb2.AddNodeToPeersListRequest(
            requesting_node=self.fake_client_node_info, request_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

        method = self.test_server.invoke_unary_unary(
            method_descriptor=(node_pb2.DESCRIPTOR
            .services_by_name['Node']
            .methods_by_name['AddNodeToPeersList']),
            invocation_metadata={},
            request=add_client_node_to_peers_list_request, timeout=1)
        response, metadata, code, details = method.termination()
        self.assertEqual(code, StatusCode.OK)
        self.assertFalse(common_utils.is_empty_object(response))
        print(response)
        self.assertEqual(response.response_status, node_pb2.ResponseStatus(is_successful=True))
        self.assertEqual(response.responding_node, self.fake_remote_node_info)

    def test_get_peers_list(self):
        get_peers_list_request = node_pb2.GetPeersListRequest(requesting_node=self.fake_client_node_info,
                                                              max_desired_peers=10,
                                                              request_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())
        for tries in range(2):
            method = self.test_server.invoke_unary_unary(
                method_descriptor=(node_pb2.DESCRIPTOR
                .services_by_name['Node']
                .methods_by_name['GetPeersList']),
                invocation_metadata={},
                request=get_peers_list_request, timeout=1)
            response, metadata, code, details = method.termination()
            self.assertEqual(code, StatusCode.OK)
            self.assertFalse(common_utils.is_empty_object(response))
            if tries == 0:
                # In the first run we expect the server to return an empty list
                self.assertEqual(len(response.peers_list), 0)
            else:
                # In the second run (since we added a fake peer) we expect the list
                # to contain the fake peer's info.
                self.assertEqual(len(response.peers_list), 1)
                self.assertEqual(response.peers_list[0], self.fake_peer_node1_info)

            if tries == 0:
                # We issue a AddNodeToPeersList request in the second run
                _ = self.__add_fake_node_to_peers_list()

    def test_connect_as_peer(self):
        connect_as_peer_request = node_pb2.ConnectAsPeerRequest(requesting_node=self.fake_client_node_info,
                                                                request_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

        method = self.test_server.invoke_unary_unary(
            method_descriptor=(node_pb2.DESCRIPTOR
            .services_by_name['Node']
            .methods_by_name['ConnectAsPeer']),
            invocation_metadata={},
            request=connect_as_peer_request, timeout=1)
        response, metadata, code, details = method.termination()
        self.assertEqual(code, StatusCode.OK)
        self.assertFalse(common_utils.is_empty_object(response))
        self.assertEqual(response.response_status, node_pb2.ResponseStatus(is_successful=True))
        self.assertEqual(response.responding_node, self.fake_remote_node_info)

    def test_is_node_live(self):
        is_node_live_request = node_pb2.IsNodeLiveRequest(requesting_node=self.fake_client_node_info,
                                                          request_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())
        method = self.test_server.invoke_unary_unary(
            method_descriptor=(node_pb2.DESCRIPTOR
            .services_by_name['Node']
            .methods_by_name['IsNodeLive']),
            invocation_metadata={},
            request=is_node_live_request, timeout=1)
        response, metadata, code, details = method.termination()
        self.assertEqual(code, StatusCode.OK)
        self.assertFalse(common_utils.is_empty_object(response))
        self.assertTrue(response.is_live)
        self.assertEqual(response.responding_node, self.fake_remote_node_info)

    def test_enqueue_find_valid_message_dna(self):
        # We did not specify destination_id or handshake packet hence it's an invalid request.
        invalid_request = node_pb2.EnqueueFindValidMessageDnaRequest(
            requesting_node=self.fake_client_node_info,
            dna_length=64,
            request_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())
        valid_request_with_destination_id = node_pb2.EnqueueFindValidMessageDnaRequest(
            requesting_node=self.fake_client_node_info,
            dna_length=64,
            source_id=self.__get_endpoint_id(),
            destination_id=self.__get_endpoint_id(start_index=2),
            request_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())
        valid_request_with_encrypted_handshake_packet = node_pb2.EnqueueFindValidMessageDnaRequest(
            requesting_node=self.fake_client_node_info,
            dna_length=64,
            source_id=self.__get_endpoint_id(),
            encrypted_handshake_payload=self.__get_encrypted_test_handshake_packet(),
            request_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

        for index, request in enumerate(
                [invalid_request, valid_request_with_destination_id, valid_request_with_encrypted_handshake_packet]):
            method = self.test_server.invoke_unary_unary(
                method_descriptor=(node_pb2.DESCRIPTOR
                .services_by_name['Node']
                .methods_by_name['EnqueueFindValidMessageDna']),
                invocation_metadata={},
                request=request, timeout=1)
            response, metadata, code, details = method.termination()

            self.assertEqual(code, StatusCode.OK)
            self.assertFalse(common_utils.is_empty_object(response))
            if index == 0:
                self.assertFalse(response.response_status.is_successful)
                self.assertTrue(common_utils.is_empty_string(response.responding_node.node_address))
                self.assertTrue(common_utils.is_empty_string(response.request_id))
                self.assertEqual(response.estimated_wait_time_for_response_ms, 0)
            else:
                self.assertTrue(response.response_status.is_successful)
                self.assertFalse(common_utils.is_empty_string(response.responding_node.node_address))
                self.assertFalse(common_utils.is_empty_string(response.request_id))
                self.assertGreater(response.estimated_wait_time_for_response_ms, 0)

    def test_relay_message(self):
        # self.fail()
        self.assertTrue(True)

    def test_connect_to_peer(self):
        # self.fail()
        self.assertTrue(True)

    def test_connect_to_bootstrap_or_known_peers(self):
        # self.fail()
        self.assertTrue(True)

    def __make_node_info(self, node_address):
        software_version = node_pb2.Version(major_version=0, minor_version=1, is_release=True)
        supported_communication_types = node_pb2.NodeInfo.SECURE_AND_UNSECURE_STREAM
        return node_pb2.NodeInfo(node_address=node_address, software_version=software_version,
                                 supported_communication_types=supported_communication_types)

    def __make_fake_remote_node_secret(self):
        return node_pb2.NodeSecret(secret_private_key="", secret_node_primer="AT", secret_amplicon_threshold=15)

    def __add_fake_node_to_peers_list(self):
        self.fake_peer_node1_address = "12.0.0.1:3939"
        self.fake_peer_node1_info = self.__make_node_info(self.fake_peer_node1_address)

        add_fake_peer_node1_to_peers_list_request = node_pb2.AddNodeToPeersListRequest(
            requesting_node=self.fake_peer_node1_info, request_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

        method = self.test_server.invoke_unary_unary(
            method_descriptor=(node_pb2.DESCRIPTOR
            .services_by_name['Node']
            .methods_by_name['AddNodeToPeersList']),
            invocation_metadata={},
            request=add_fake_peer_node1_to_peers_list_request, timeout=1)
        response, metadata, code, details = method.termination()
        return response, metadata, code, details

    def __get_test_public_key(self, key_instance=0) -> str:
        keys = ['9efb28f789332dc8c08ac0fa9c48eb9e76b1b151721021fc590924738bed8c35',
                '33200b6d5e6518e8a0a917771691767fd02df2389be35fc19b8b0a6cda60c53f',
                '9e4b2e2f03bb713bda308fc4decbfb04f0e49bdde5c3be996d8c7f330c6cac22',
                '15d95bbe253447f175ea090c75b7707beb9dba8087738d5959fae4dcedac2328']
        return keys[key_instance % len(keys)]

    def __get_endpoint_id(self, with_forwarder=False, start_index=0):
        if with_forwarder:
            return node_pb2.MessageEndpointId(endpoint_public_key=self.__get_test_public_key(start_index),
                                              forwarder_public_key=self.__get_test_public_key(start_index + 1))
        return node_pb2.MessageEndpointId(endpoint_public_key=self.__get_test_public_key(start_index))

    def __get_encrypted_test_handshake_packet(self,
                                              destination_has_forwarder=False) -> node_pb2.EncryptedMessageCoreInformation:
        if destination_has_forwarder:
            source_id = node_pb2.MessageEndpointId(endpoint_public_key=self.__get_test_public_key(0),
                                                   forwarder_public_key=self.__get_test_public_key(1))
            destination_id = node_pb2.MessageEndpointId(endpoint_public_key=self.__get_test_public_key(2),
                                                        forwarder_public_key=self.__get_test_public_key(3))
        else:
            source_id = node_pb2.MessageEndpointId(endpoint_public_key=self.__get_test_public_key(0))
            destination_id = node_pb2.MessageEndpointId(endpoint_public_key=self.__get_test_public_key(2))
        handshake_packet = node_pb2.MessageCoreInformation(message_type=node_pb2.MessageCoreInformation.HANDSHAKE,
                                                           source_id=source_id,
                                                           destination_id=destination_id)
        return message_utils.encrypt_message_core_information_with_destination_id(handshake_packet)
