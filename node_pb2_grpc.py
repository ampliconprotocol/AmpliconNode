# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import node_pb2 as node__pb2


class NodeStub(object):
    """The RPC for a node are defined below.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetNodeInfo = channel.unary_unary(
                '/node.Node/GetNodeInfo',
                request_serializer=node__pb2.GetNodeInfoRequest.SerializeToString,
                response_deserializer=node__pb2.GetNodeInfoResponse.FromString,
                )
        self.GetPeersList = channel.unary_unary(
                '/node.Node/GetPeersList',
                request_serializer=node__pb2.GetPeersListRequest.SerializeToString,
                response_deserializer=node__pb2.GetPeersListResponse.FromString,
                )
        self.AddNodeToPeersList = channel.unary_unary(
                '/node.Node/AddNodeToPeersList',
                request_serializer=node__pb2.AddNodeToPeersListRequest.SerializeToString,
                response_deserializer=node__pb2.AddNodeToPeersListResponse.FromString,
                )
        self.ConnectAsPeer = channel.unary_unary(
                '/node.Node/ConnectAsPeer',
                request_serializer=node__pb2.ConnectAsPeerRequest.SerializeToString,
                response_deserializer=node__pb2.ConnectAsPeerResponse.FromString,
                )
        self.IsNodeLive = channel.unary_unary(
                '/node.Node/IsNodeLive',
                request_serializer=node__pb2.IsNodeLiveRequest.SerializeToString,
                response_deserializer=node__pb2.IsNodeLiveResponse.FromString,
                )
        self.EnqueueFindValidMessageDna = channel.unary_unary(
                '/node.Node/EnqueueFindValidMessageDna',
                request_serializer=node__pb2.EnqueueFindValidMessageDnaRequest.SerializeToString,
                response_deserializer=node__pb2.EnqueueFindValidMessageDnaResponse.FromString,
                )
        self.GetFoundMessageDna = channel.unary_unary(
                '/node.Node/GetFoundMessageDna',
                request_serializer=node__pb2.GetFoundMessageDnaRequest.SerializeToString,
                response_deserializer=node__pb2.GetFoundMessageDnaResponse.FromString,
                )
        self.RelayMessage = channel.unary_unary(
                '/node.Node/RelayMessage',
                request_serializer=node__pb2.RelayMessageRequest.SerializeToString,
                response_deserializer=node__pb2.RelayMessageResponse.FromString,
                )


class NodeServicer(object):
    """The RPC for a node are defined below.
    """

    def GetNodeInfo(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetPeersList(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def AddNodeToPeersList(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ConnectAsPeer(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def IsNodeLive(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def EnqueueFindValidMessageDna(self, request, context):
        """The following RPC issues a search for a valid message DNA. The return is a proto containing the
        request id (as acknowledged by the Node) and the time-to-wait (before asking for a
        response ) and the time-to-live (for the request's info).
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetFoundMessageDna(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RelayMessage(self, request, context):
        """The following RPC method consumes a  RelayMessageRequest which has an encrypted message payload.
        If the message is meant for the current node, this node can successfully decrypt it.
        If successfully decrypted the current node can choose to relay this (with a certain statistical probability) just
        to feign ignorance of the end-point. (Thus preserving its anonymity).
        If not decrypted, the current node then tries to find an amplicon (using its primer and the message's DNA).
        If an amplicon is found and it exceeds the current node's amplicon threshold, the message is relayed to its
        connections. Else the message is dropped.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_NodeServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'GetNodeInfo': grpc.unary_unary_rpc_method_handler(
                    servicer.GetNodeInfo,
                    request_deserializer=node__pb2.GetNodeInfoRequest.FromString,
                    response_serializer=node__pb2.GetNodeInfoResponse.SerializeToString,
            ),
            'GetPeersList': grpc.unary_unary_rpc_method_handler(
                    servicer.GetPeersList,
                    request_deserializer=node__pb2.GetPeersListRequest.FromString,
                    response_serializer=node__pb2.GetPeersListResponse.SerializeToString,
            ),
            'AddNodeToPeersList': grpc.unary_unary_rpc_method_handler(
                    servicer.AddNodeToPeersList,
                    request_deserializer=node__pb2.AddNodeToPeersListRequest.FromString,
                    response_serializer=node__pb2.AddNodeToPeersListResponse.SerializeToString,
            ),
            'ConnectAsPeer': grpc.unary_unary_rpc_method_handler(
                    servicer.ConnectAsPeer,
                    request_deserializer=node__pb2.ConnectAsPeerRequest.FromString,
                    response_serializer=node__pb2.ConnectAsPeerResponse.SerializeToString,
            ),
            'IsNodeLive': grpc.unary_unary_rpc_method_handler(
                    servicer.IsNodeLive,
                    request_deserializer=node__pb2.IsNodeLiveRequest.FromString,
                    response_serializer=node__pb2.IsNodeLiveResponse.SerializeToString,
            ),
            'EnqueueFindValidMessageDna': grpc.unary_unary_rpc_method_handler(
                    servicer.EnqueueFindValidMessageDna,
                    request_deserializer=node__pb2.EnqueueFindValidMessageDnaRequest.FromString,
                    response_serializer=node__pb2.EnqueueFindValidMessageDnaResponse.SerializeToString,
            ),
            'GetFoundMessageDna': grpc.unary_unary_rpc_method_handler(
                    servicer.GetFoundMessageDna,
                    request_deserializer=node__pb2.GetFoundMessageDnaRequest.FromString,
                    response_serializer=node__pb2.GetFoundMessageDnaResponse.SerializeToString,
            ),
            'RelayMessage': grpc.unary_unary_rpc_method_handler(
                    servicer.RelayMessage,
                    request_deserializer=node__pb2.RelayMessageRequest.FromString,
                    response_serializer=node__pb2.RelayMessageResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'node.Node', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Node(object):
    """The RPC for a node are defined below.
    """

    @staticmethod
    def GetNodeInfo(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/node.Node/GetNodeInfo',
            node__pb2.GetNodeInfoRequest.SerializeToString,
            node__pb2.GetNodeInfoResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetPeersList(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/node.Node/GetPeersList',
            node__pb2.GetPeersListRequest.SerializeToString,
            node__pb2.GetPeersListResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def AddNodeToPeersList(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/node.Node/AddNodeToPeersList',
            node__pb2.AddNodeToPeersListRequest.SerializeToString,
            node__pb2.AddNodeToPeersListResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def ConnectAsPeer(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/node.Node/ConnectAsPeer',
            node__pb2.ConnectAsPeerRequest.SerializeToString,
            node__pb2.ConnectAsPeerResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def IsNodeLive(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/node.Node/IsNodeLive',
            node__pb2.IsNodeLiveRequest.SerializeToString,
            node__pb2.IsNodeLiveResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def EnqueueFindValidMessageDna(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/node.Node/EnqueueFindValidMessageDna',
            node__pb2.EnqueueFindValidMessageDnaRequest.SerializeToString,
            node__pb2.EnqueueFindValidMessageDnaResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetFoundMessageDna(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/node.Node/GetFoundMessageDna',
            node__pb2.GetFoundMessageDnaRequest.SerializeToString,
            node__pb2.GetFoundMessageDnaResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def RelayMessage(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/node.Node/RelayMessage',
            node__pb2.RelayMessageRequest.SerializeToString,
            node__pb2.RelayMessageResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
