import logging
import random
from threading import Lock

import grpc

import common_utils
import node_pb2
import node_pb2_grpc


class Node(node_pb2_grpc.NodeServicer):
    def __init__(self, node_properties: node_pb2.NodeProperties):
        self.node_properties = node_properties
        self.node_info = node_properties.info
        self.thread_lock = Lock()
        self.peer_node_hash_to_node_info = {}  # node_hash -> node_info
        self.peer_node_hash_to_channel = {}  # node_hash -> grpc_channel
        self.peer_node_hash_to_lock = {}  # node_hash -> Lock
        self.listed_nodes_info = []
        self.is_ready_to_accept_connections = True
        super().__init__()

    def __can_accept_connections(self) -> bool:
        if self.is_ready_to_accept_connections:
            return True
        return False

    def GetPeerNodes(self, request: node_pb2.GetPeersListRequest, context) -> node_pb2.GetPeersListResponse:
        logging.info(" Got a GetPeerNodes request from : %s for %d peers at timestamp %d",
                     request.requesting_node.node_id,
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
                           context) -> node_pb2.AddNodeToPeersResponse:
        logging.info(" Got a AddNodeToPeers request from : %s with listing %s at timestamp %d",
                     request.requesting_node.node_id,
                     'enabled' if request.list_node else 'disabled', request.request_utc_timestamp_nanos)
        if not common_utils.is_valid_node_info(request.requesting_node):
            return node_pb2.AddNodeToPeersListResponse(response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())
        node_hash = common_utils.get_node_hash(request.requesting_node)
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
        self.peer_node_hash_to_lock[node_hash] = Lock()
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
        # Check if message is meant for us
        # Check if we have seen message-id + hash before
        # If not pass on to peers