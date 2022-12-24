from threading import Lock, Event

import grpc

import common_utils
import grpc_utils
import node_pb2
import node_pb2_grpc
import thread_pool_with_run_delay


def invoke_relay_message_rpc_on_peer_channel(request: node_pb2.RelayMessageRequest,
                                             channel: grpc.Channel):
    stub = node_pb2_grpc.NodeStub(channel)
    _ = stub.RelayMessage(request)


def get_grpc_channel(node_info: node_pb2.NodeInfo):
    return grpc.insecure_channel(node_info.node_address)


class PeerConnectionsManager(object):
    def __init__(self, thread_pool: thread_pool_with_run_delay.ThreadPoolWithRunDelay,
                 node_properties: node_pb2.NodeProperties, peers_list: [node_pb2.NodeInfo] = [],
                 periodicity_of_connections_check_active_seconds: int = 30):
        self.peer_node_info_hash_to_grpc_channel = {}
        self.peer_node_info_hash_to_node_info = {}
        self.active_peers_hash = set()  # set of node-info hashes of active peers
        self.periodicity_of_connections_check_active_seconds = periodicity_of_connections_check_active_seconds
        self.node_properties = node_properties
        self.thread_pool = thread_pool
        self.is_shutting_down = Event()
        self.lock = Lock()
        self.thread_pool.add_job(self.__periodic_check_if_connections_active)

        if common_utils.is_empty_list(peers_list):
            return
        for peer_node_info in peers_list:
            self.add_peer_node(peer_node_info)

    def add_peer_node(self, node_info: node_pb2.NodeInfo):
        node_info_hash = common_utils.get_node_hash(node_info)
        with self.lock:
            self.peer_node_info_hash_to_grpc_channel[node_info_hash] = get_grpc_channel(node_info)
            self.peer_node_info_hash_to_node_info[node_info_hash] = node_info

    def relay_amplicon_p2p_message_to_all_active_connections(self, message: node_pb2.AmpliconP2PRelayMessage):
        relay_message_request = node_pb2.RelayMessageRequest(message=message,
                                                             requesting_node=self.node_properties.node_info,
                                                             request_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())
        active_nodes_hash = self.get_active_peer_nodes_hash()
        for peer_node_hash in active_nodes_hash:
            self.thread_pool.add_job(invoke_relay_message_rpc_on_peer_channel,
                                     (relay_message_request,
                                      self.peer_node_info_hash_to_grpc_channel[peer_node_hash]))

    def get_active_peer_nodes_hash(self):
        with self.lock:
            active_nodes = self.active_peers_hash.copy()
            return active_nodes

    def get_peer_node_info_list(self):
        with self.lock:
            peer_nodes = []
            for k in sorted(self.peer_node_info_hash_to_node_info.keys()):
                peer_nodes.append(self.peer_node_info_hash_to_node_info[k])
            return peer_nodes

    def release_resources(self):
        self.is_shutting_down.set()

    def __periodic_check_if_connections_active(self):
        with self.lock:
            for peer_node_hash in self.peer_node_info_hash_to_node_info:
                node_info = self.peer_node_info_hash_to_node_info[peer_node_hash]
                self.thread_pool.add_job(self.__check_if_connection_is_active, (peer_node_hash, node_info))
        if self.is_shutting_down.is_set():
            return
        self.thread_pool.add_job(self.__periodic_check_if_connections_active,
                                 run_delay_from_now_ns=int(
                                     self.periodicity_of_connections_check_active_seconds * 1e9))

    def __check_if_connection_is_active(self, peer_node_hash: str, node_info: node_pb2.NodeInfo):
        is_active = grpc_utils.check_if_host_has_active_grpc_insecure_channel_server(node_info.node_address,
                                                                                     timeout_seconds=5)
        with self.lock:
            if is_active:
                self.active_peers_hash.add(peer_node_hash)
            elif peer_node_hash in self.active_peers_hash:
                self.active_peers_hash.remove(peer_node_hash)
