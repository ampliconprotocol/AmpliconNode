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
from message_io_sink import MessageIoSink
from thread_pool_with_run_delay import ThreadPoolWithRunDelay


class Node(node_pb2_grpc.NodeServicer):
    def __init__(self, node_properties: node_pb2.NodeProperties):
        super().__init__()
        self.node_properties = node_properties
        self.node_info = node_properties.node_info
        self.node_secret = node_properties.node_secrets
        self.thread_lock = Lock()
        # This map contains info about the peers we have connected to.
        # The key is a node_has obtained by hashing the peer's node_info
        # The value is the actual node_info
        # This is used to look-up node_info s
        self.peer_node_hash_to_node_info = {}  # node_hash -> node_info
        # Similar to the above map, the following map contains info about the grpc channels we have
        # established with the peers. This is used to issue gRPC on the connected peer nodes.
        self.peer_node_hash_to_channel = {}  # node_hash -> grpc_channel
        self.listed_nodes_info = []
        self.is_ready_to_accept_connections = True
        # This is the main threadpool where all the slow work takes place. It also supports timed
        # (delayed) jobs.
        self.thread_pool = ThreadPoolWithRunDelay()
        self.message_center = message_center.MessageCenter(self.node_properties, self.thread_pool)
        self.max_connection_attempts_with_peer = 10
        self.wait_time_between_connection_attempts_with_peer_ns = common_utils.convert_seconds_to_ns(10)
        self.__connect_to_bootstrap_or_known_peers(node_properties.bootstrap_peers_list)

    def GetNodeInfo(self, request: node_pb2.GetNodeInfoRequest, context) -> node_pb2.GetNodeInfoResponse:
        logging.info(" Got a GetNodeInfo request from : %s at timestamp %d",
                     request.requesting_node.node_address,
                     request.request_utc_timestamp_nanos)
        if not common_utils.is_valid_node_info(request.requesting_node):
            return node_pb2.GetNodeInfoResponse(
                response_status=node_pb2.ResponseStatus(is_successful=False, status_text="Invalid requesting node."),
                response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

        return node_pb2.GetNodeInfoResponse(responding_node=self.node_info,
                                            response_status=node_pb2.ResponseStatus(is_successful=True),
                                            response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

    def GetPeersList(self, request: node_pb2.GetPeersListRequest, context) -> node_pb2.GetPeersListResponse:
        logging.info(" Got a GetPeerNodes request from : %s for %d peers at timestamp %d",
                     request.requesting_node.node_address,
                     request.max_desired_peers, request.request_utc_timestamp_nanos)
        if not common_utils.is_valid_node_info(request.requesting_node):
            return node_pb2.GetPeersListResponse(
                response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())
        with self.thread_lock:
            random.shuffle(self.listed_nodes_info)
            listed_nodes_to_return = self.listed_nodes_info[:request.max_desired_peers]

        return node_pb2.GetPeersListResponse(peers_list=listed_nodes_to_return,
                                             response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

    def AddNodeToPeersList(self, request: node_pb2.AddNodeToPeersListRequest,
                           context) -> node_pb2.AddNodeToPeersListResponse:
        logging.info(" Got a AddNodeToPeers request from : %s at timestamp %d",
                     request.requesting_node.node_address,
                     request.request_utc_timestamp_nanos)
        if not common_utils.is_valid_node_info(request.requesting_node):
            return node_pb2.AddNodeToPeersListResponse(response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

        with self.thread_lock:
            self.listed_nodes_info.append(request.requesting_node)
        return node_pb2.AddNodeToPeersListResponse(responding_node=self.node_info,
                                                   response_status=node_pb2.ResponseStatus(is_successful=True),
                                                   response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

    def ConnectAsPeer(self, request: node_pb2.ConnectAsPeerRequest, context) -> node_pb2.ConnectAsPeerResponse:
        if not common_utils.is_valid_node_info(request.requesting_node) or not self.__can_accept_connections():
            return node_pb2.ConnectAsPeerResponse(response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())
        node_hash = common_utils.get_node_hash(request.requesting_node)
        with self.thread_lock:
            self.peer_node_hash_to_channel[node_hash] = grpc.insecure_channel(request.requesting_node.node_address)
            self.peer_node_hash_to_node_info[node_hash] = request.requesting_node
        return node_pb2.ConnectAsPeerResponse(responding_node=self.node_info,
                                              response_status=node_pb2.ResponseStatus(is_successful=True),
                                              response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

    def IsNodeLive(self, request: node_pb2.IsNodeLiveRequest, context) -> node_pb2.IsNodeLiveResponse:
        if not common_utils.is_valid_node_info(request.requesting_node):
            return node_pb2.IsNodeLiveResponse(response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())
        return node_pb2.IsNodeLiveResponse(responding_node=self.node_info,
                                           is_live=self.__can_accept_connections(),
                                           response_status=node_pb2.ResponseStatus(is_successful=True),
                                           response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

    def EnqueueFindValidMessageDna(self, request: node_pb2.EnqueueFindValidMessageDnaRequest,
                                   context) -> node_pb2.EnqueueFindValidMessageDnaResponse:
        # We check whether the request is valid and generate a ResponseStatus message.
        checked_response_status = message_utils.check_enqueue_find_valid_message_dna_request_and_generate_response_status(
            request)
        if not checked_response_status.is_successful:
            return node_pb2.EnqueueFindValidMessageDnaResponse(
                response_status=checked_response_status,
                response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())
        request_id = common_utils.generate_uuid_string()
        self.message_center.enqueue_find_valid_message_dna_request(request_id, request,
                                                                   self.node_properties.max_candidates_per_request_for_valid_dna_search_for_forwarding_client)
        return node_pb2.EnqueueFindValidMessageDnaResponse(responding_node=self.node_info,
                                                           response_status=checked_response_status,
                                                           request_id=request_id,
                                                           estimated_wait_time_for_response_ms=1000,
                                                           response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

    def RelayMessage(self, request: node_pb2.RelayMessageRequest, context) -> node_pb2.RelayMessageResponse:
        if not common_utils.is_valid_node_info(request.requesting_node):
            return node_pb2.RelayMessageResponse(response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

        # We will simply return the successful status message regardless of internal processing.
        # This is to preserve the recipient node's anonymity.
        successful_response = node_pb2.RelayMessageResponse(
            status=node_pb2.ResponseStatus(is_successful=True),
            responding_node=self.node_info,
            response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

        # The bulk of the processing takes place in message_center.push_message_into_relay_queue
        # Briefly, we first check whether the message is meant for us [if yes we consume it]
        # If the message isn't meant for us, it is sent to all the connected peers.
        self.message_center.push_message_into_relay_queue(request.message)
        return successful_response

    def connect_to_peer(self, peer_node_info: node_pb2.NodeInfo):
        self.thread_pool.add_job(job_to_run=self.__connect_to_peer_with_retry, parameters=(peer_node_info))

    def connect_to_bootstrap_or_known_peers(self, peer_nodes_info: [node_pb2.NodeInfo]):
        if common_utils.is_empty_list(peer_nodes_info):
            return
        for peer_node_info in peer_nodes_info:
            self.connect_to_peer(peer_node_info)

    def add_message_sink_for_forwarded_public_key(self, public_key: str, message_sink: MessageIoSink):
        # TODO: Add the sink into the listening roster on MessageCenter
        pass

    def release_resources(self):
        self.thread_pool.release_resources()

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
        with self.thread_lock:
            self.peer_node_hash_to_channel[node_hash] = channel
            self.peer_node_hash_to_node_info[node_hash] = peer_node_info

    def __connect_to_bootstrap_or_known_peers(self, peers_node_info: [node_pb2.NodeInfo]):
        for peer_node_info in peers_node_info:
            self.connect_to_peer(peer_node_info)
