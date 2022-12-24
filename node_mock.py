from queue import Queue

import common_utils
import message_utils
import node_pb2
import node_pb2_grpc


class NodeMock(node_pb2_grpc.NodeServicer):
    def __init__(self, node_properties: node_pb2.NodeProperties):
        super().__init__()
        self.node_properties = node_properties
        self.node_info = node_properties.node_info
        self.node_secret = node_properties.node_secrets
        self.request_logs = Queue()

    def GetNodeInfo(self, request: node_pb2.GetNodeInfoRequest, context) -> node_pb2.GetNodeInfoResponse:
        self.request_logs.put(request)
        if not common_utils.is_valid_node_info(request.requesting_node):
            return node_pb2.GetNodeInfoResponse(
                response_status=node_pb2.ResponseStatus(is_successful=False, status_text="Invalid requesting node."),
                response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

        return node_pb2.GetNodeInfoResponse(responding_node=self.node_info,
                                            response_status=node_pb2.ResponseStatus(is_successful=True),
                                            response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

    def GetPeersList(self, request: node_pb2.GetPeersListRequest, context) -> node_pb2.GetPeersListResponse:
        self.request_logs.put(request)
        if not common_utils.is_valid_node_info(request.requesting_node):
            return node_pb2.GetPeersListResponse(
                response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

        return node_pb2.GetPeersListResponse(peers_list=[],
                                             response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

    def AddNodeToPeersList(self, request: node_pb2.AddNodeToPeersListRequest,
                           context) -> node_pb2.AddNodeToPeersListResponse:
        self.request_logs.put(request)
        if not common_utils.is_valid_node_info(request.requesting_node):
            return node_pb2.AddNodeToPeersListResponse(response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())
        return node_pb2.AddNodeToPeersListResponse(responding_node=self.node_info,
                                                   response_status=node_pb2.ResponseStatus(is_successful=True),
                                                   response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

    def ConnectAsPeer(self, request: node_pb2.ConnectAsPeerRequest, context) -> node_pb2.ConnectAsPeerResponse:
        self.request_logs.put(request)
        if not common_utils.is_valid_node_info(request.requesting_node):
            return node_pb2.ConnectAsPeerResponse(response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())
        return node_pb2.ConnectAsPeerResponse(responding_node=self.node_info,
                                              response_status=node_pb2.ResponseStatus(is_successful=True),
                                              response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

    def IsNodeLive(self, request: node_pb2.IsNodeLiveRequest, context) -> node_pb2.IsNodeLiveResponse:
        self.request_logs.put(request)
        if not common_utils.is_valid_node_info(request.requesting_node):
            return node_pb2.IsNodeLiveResponse(response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())
        return node_pb2.IsNodeLiveResponse(responding_node=self.node_info,
                                           is_live=True,
                                           response_status=node_pb2.ResponseStatus(is_successful=True),
                                           response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

    def EnqueueFindValidMessageDna(self, request: node_pb2.EnqueueFindValidMessageDnaRequest,
                                   context) -> node_pb2.EnqueueFindValidMessageDnaResponse:
        self.request_logs.put(request)
        # We check whether the request is valid and generate a ResponseStatus message.
        checked_response_status = message_utils.check_enqueue_find_valid_message_dna_request_and_generate_response_status(
            request)
        if not checked_response_status.is_successful:
            return node_pb2.EnqueueFindValidMessageDnaResponse(
                response_status=checked_response_status,
                response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())
        request_id = common_utils.generate_uuid_string()
        return node_pb2.EnqueueFindValidMessageDnaResponse(responding_node=self.node_info,
                                                           response_status=checked_response_status,
                                                           request_id=request_id,
                                                           estimated_wait_time_for_response_ms=1000,
                                                           response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

    def RelayMessage(self, request: node_pb2.RelayMessageRequest, context) -> node_pb2.RelayMessageResponse:
        self.request_logs.put(request)
        if not common_utils.is_valid_node_info(request.requesting_node):
            return node_pb2.RelayMessageResponse(response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())

        # We will simply return the successful status message regardless of internal processing.
        # This is to preserve the recipient node's anonymity.
        successful_response = node_pb2.RelayMessageResponse(
            status=node_pb2.ResponseStatus(is_successful=True),
            responding_node=self.node_info,
            response_utc_timestamp_nanos=common_utils.get_timestamp_now_ns())
        return successful_response

    def pop_request_log(self):
        if not self.request_logs.empty():
            return self.request_logs.get()
        return None
