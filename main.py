import logging
import os
from concurrent import futures

import grpc

import node_pb2
import node_pb2_grpc
from config_reader import ConfigReader
from node import Node

if __name__ == '__main__':
    config_file_path = os.path.join(os.path.dirname(__file__), "data", "node.config")
    config_reader = ConfigReader(config_file_path)
    print(config_reader.get_node_properties())
    logging.info("Starting server on address : %s ", config_reader.get_listen_address_with_port())
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
    node_properties = node_pb2.NodeProperties()
    node_pb2_grpc.add_NodeServicer_to_server(Node(node_properties), server)
    server.add_insecure_port(config_reader.get_listen_address_with_port())
    server.start()
    logging.info("Server successfully started")
    server.wait_for_termination()
