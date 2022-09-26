import logging
import random
from threading import Lock

import grpc

import common_utils
import grpc_utils
import message_center
import message_utils
import node_pb2
import node_pb2_grpc
from thread_pool_with_run_delay import ThreadPoolWithRunDelay


class Node(node_pb2_grpc.NodeServicer):
    def __init__(self, node_properties: node_pb2.NodeProperties):
        super().__init__()
        self.node_info = node_properties.node_info
        self.node_secret = node_properties.node_secrets
        self.thread_lock = Lock()
        self.peer_node_hash_to_node_info = {}  # node_hash -> node_info
        self.peer_node_hash_to_channel = {}  # node_hash -> grpc_channel

        self.listed_nodes_info = []
        self.is_ready_to_accept_connections = True
        self.message_center = message_center.MessageCenter()
        self.thread_pool = ThreadPoolWithRunDelay()
        self.max_connection_attempts_with_peer = 10
        self.wait_time_between_connection_attempts_with_peer_ns = common_utils.convert_seconds_to_ns(10)
        self.__connect_to_bootstrap_or_known_peers(node_properties.bootstrap_peers_list)

    def GetPeersList(self, request: node_pb2.GetPeersListRequest, context) -> node_pb2.GetPeersListResponse:
        logging.info(" Got a GetPeerNodes request from : %s for %d peers at timestamp %d",
                     request.requesting_node.node_address,
                     request.max_desired_peers, request.request_utc_timestamp_nanos)
        if not common_utils.is_valid_node_info(request.requesting_node):
            return node_pb2.GetPeersListResponse(
                response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())
        self.thread_lock.acquire()
        random.shuffle(self.listed_nodes)
        listed_nodes_to_return = self.listed_nodes[:request.max_desired_peers]
        self.thread_lock.release()
        return node_pb2.GetPeersListResponse(peers_list=listed_nodes_to_return,
                                             response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

    def AddNodeToPeersList(self, request: node_pb2.AddNodeToPeersListRequest,
                           context) -> node_pb2.AddNodeToPeersListResponse:
        logging.info(" Got a AddNodeToPeers request from : %s with listing %s at timestamp %d",
                     request.requesting_node.node_address,
                     'enabled' if request.list_node else 'disabled', request.request_utc_timestamp_nanos)
        if not common_utils.is_valid_node_info(request.requesting_node):
            return node_pb2.AddNodeToPeersListResponse(response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

        self.thread_lock.acquire()
        self.listed_nodes_info.append(request.requesting_node)
        self.thread_lock.release()
        return node_pb2.AddNodeToPeersListResponse(responding_node=self.node_info,
                                                   response_status=node_pb2.ResponseStatus(is_successful=True),
                                                   response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

    def ConnectAsPeer(self, request: node_pb2.ConnectAsPeerRequest, context) -> node_pb2.ConnectAsPeerResponse:
        if not common_utils.is_valid_node_info(request.requesting_node) or not self.__can_accept_connections():
            return node_pb2.ConnectAsPeerResponse(response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())
        node_hash = common_utils.get_node_hash(request.requesting_node)
        self.thread_lock.acquire()
        self.peer_node_hash_to_channel[node_hash] = grpc.insecure_channel(request.requesting_node.node_address)
        self.peer_node_hash_to_node_info[node_hash] = request.requesting_node
        self.thread_lock.release()
        return node_pb2.ConnectAsPeerResponse(responding_node=self.node_info,
                                              response_status=node_pb2.ResponseStatus(is_successful=True),
                                              response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

    def IsNodeLive(self, request: node_pb2.IsNodeLiveRequest, context) -> node_pb2.IsNodeLiveResponse:
        if not common_utils.is_valid_node_info(request.requesting_node):
            return node_pb2.IsNodeLiveResponse(response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())
        return node_pb2.IsNodeLiveResponse(responding_node=self.node_info,
                                           is_live=self.__can_accept_connections(),
                                           response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

    def RelayMessage(self, request: node_pb2.RelayMessageRequest, context) -> node_pb2.RelayMessageResponse:
        if not common_utils.is_valid_node_info(request.requesting_node):
            return node_pb2.RelayMessageResponse(response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

        # We will simply return the successful status message regardless of internal processing.
        # This is to preserve the recipient node's anonymity.
        successful_response = node_pb2.RelayMessageResponse(
            status=node_pb2.ResponseStatus(is_successful=True),
            responding_node=self.node_info,
            message_id=request.message.message_id,
            response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())
        decrypted_message = message_utils.maybe_decrypt_message(request.message, self.node_secret)
        if not common_utils.is_empty_bytes(decrypted_message):
            # Message is meant for us
            self.message_center.process_message(decrypted_message)
            return successful_response
        if not message_utils.should_message_be_relayed(request.message, self.node_secret):
            return successful_response
        self.thread_lock.acquire()
        self.message_center.relay_message_to_connections(request, self.node_info, self.peer_node_hash_to_channel)
        self.thread_lock.release()
        return successful_response

    def connect_to_peer(self, peer_node_info: node_pb2.NodeInfo):
        self.thread_pool.add_job(job_to_run=self.__connect_to_peer_with_retry, parameters=(peer_node_info, 0))

    def connect_to_bootstrap_or_known_peers(self, peer_nodes_info: [node_pb2.NodeInfo]):
        if common_utils.is_empty_list(peer_nodes_info):
            return
        for peer_node_info in peer_nodes_info:
            self.connect_to_peer(peer_node_info)

    def __can_accept_connections(self) -> bool:
        if self.is_ready_to_accept_connections:
            return True
        return False

    def __connect_to_peer_with_retry(self, peer_node_info: node_pb2.NodeInfo, try_count=0):
        if not grpc_utils.check_if_host_has_active_grpc_insecure_channel_server(peer_node_info.node_address):
            if try_count + 1 < self.max_connection_attempts_with_peer:
                self.thread_pool.add_job(job_to_run=self.__connect_to_peer_with_retry,
                                         parameters=(peer_node_info, try_count + 1),
                                         run_delay_from_now_ns=self.wait_time_between_connection_attempts_with_peer_ns)
            return
        channel = grpc.insecure_channel(peer_node_info.node_address)
        node_hash = common_utils.get_node_hash(peer_node_info)
        stub = node_pb2_grpc.NodeStub(channel)
        _ = stub.ConnectAsPeer(
            node_pb2.ConnectAsPeerRequest(requesting_node=self.node_info,
                                          request_utc_timestamp_nanos=common_utils.get_timestamp_now_ns()))
        self.thread_lock.acquire()
        self.peer_node_hash_to_channel[node_hash] = channel
        self.peer_node_hash_to_node_info[node_hash] = peer_node_info
        self.thread_lock.release()
        return

    def __connect_to_bootstrap_or_known_peers(self, peers_node_info:[node_pb2.NodeInfo]):
        for peer_node_info in peers_node_info:
            self.connect_to_peer(peer_node_info)