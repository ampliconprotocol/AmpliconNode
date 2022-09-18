import binascii
import configparser
import os

from nacl.public import PrivateKey

import common_utils
import node_pb2


class ConfigReader(object):
    AMPLICON_NODE_SECTION = 'AMPLICON_NODE'
    SOFTWARE_VERSION = '1.0.0alpha1'

    def __init__(self, config_file_path):
        if not os.path.exists(config_file_path) or not os.path.isfile(config_file_path):
            raise RuntimeError("Invalid config file path specified.")
        self.config_object = configparser.ConfigParser()
        self.config_object.read(config_file_path)

    def get_node_properties_object(self) -> node_pb2.NodeProperties:
        return node_pb2.NodeProperties(node_info=self.get_node_info(), node_secrets=self.get_node_secret(),
                                       max_peers=self.get_num_maximum_peers(),
                                       can_exceed_max_peers_if_destination_node_not_reachable=self.get_if_max_peers_can_be_exceeded_when_destination_is_unreachable(),
                                       max_time_to_wait_for_destination_node_response_ms=2000,
                                       non_local_forwarding_enabled=self.get_if_forwarding_enabled())

    def get_node_info(self) -> node_pb2.NodeInfo:
        return node_pb2.NodeInfo(node_address=self.get_listen_address_with_port(),
                                 software_version=self.SOFTWARE_VERSION,
                                 supported_communication_types=node_pb2.NodeSupportedCommunicationTypes.UNSECURE)

    def get_node_secret(self) -> node_pb2.NodeSecret:
        return node_pb2.NodeSecret(secret_private_key=self.load_or_initialize_private_key_from_file_path())

    def get_listen_address_with_port(self):
        listen_address_with_port = self.config_object[self.AMPLICON_NODE_SECTION]['listenaddress'] + ":" + \
                                   self.config_object[self.AMPLICON_NODE_SECTION][
                                       'listenport']
        return listen_address_with_port

    def get_num_maximum_peers(self):
        max_peers = self.config_object[self.AMPLICON_NODE_SECTION]['maxpeers']
        return max_peers

    def get_if_max_peers_can_be_exceeded_when_destination_is_unreachable(self) -> bool:
        output = self.config_object[self.AMPLICON_NODE_SECTION]['enableexceedmaxpeerswhendestinationnotfound']
        if int(output) == 0:
            return False
        return True

    def get_if_forwarding_enabled(self) -> bool:
        output = self.config_object[self.AMPLICON_NODE_SECTION]['enablenonlocalforwarding']
        if int(output) == 0:
            return False
        return True

    def get_private_key_file_path(self):
        private_key_file_path = self.config_object[self.AMPLICON_NODE_SECTION]['pathforprivatekeystorage']
        return private_key_file_path

    def load_or_initialize_private_key_from_file_path(self) -> str:
        private_key_file_path = self.get_private_key_file_path()
        private_key = self.__read_private_key_file(private_key_file_path)
        if self.__is_valid_private_key(private_key):
            return private_key
        private_key = self.__generate_private_key()
        self.__write_private_key_file(private_key_file_path, private_key)
        return private_key

    def __read_private_key_file(self, private_key_file_path) -> str:
        if not os.path.exists(private_key_file_path) or not os.path.isfile(private_key_file_path):
            return ''
        with open(private_key_file_path, 'rb') as infile:
            output = infile.read()
        return output

    def __is_valid_private_key(self, private_key) -> bool:
        if common_utils.is_empty_object(private_key) or common_utils.is_empty_string(private_key):
            return False
        return True

    def __write_private_key_file(self, private_key_file_path, private_key):
        with open(private_key_file_path, 'wb') as outfile:
            outfile.write(private_key)

    def __generate_private_key(self) -> str:
        temp_private_key = PrivateKey.generate()
        return binascii.hexlify(bytes(temp_private_key))
