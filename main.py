import configparser
import os
from concurrent import futures

import grpc

import node_pb2
import node_pb2_grpc
from node import Node

if __name__ == '__main__':
    config_path = os.path.join(os.path.dirname(__file__), "data", "node.config")
    config = configparser.ConfigParser()
    config.read(config_path)
    # print(config.sections())
    # for section in config.sections():
    #     for key in config[section]:
    #         print(section, key, config[section][key])

    listen_address_with_port = config['AMPLICON_NODE']['listenaddress'].strip() + ":" + config['AMPLICON_NODE'][
        'listenport'].strip()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
    node_properties = node_pb2.NodeProperties()
    node_pb2_grpc.add_NodeServicer_to_server(Node(node_properties), server)
    server.add_insecure_port(listen_address_with_port)
    server.start()
    server.wait_for_termination()
