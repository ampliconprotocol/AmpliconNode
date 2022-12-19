from unittest import TestCase

import message_utils
import node_pb2


class Test(TestCase):
    def test_get_message_core_hash(self):
        message_core = node_pb2.MessageCoreInformation(message_type=node_pb2.MessageCoreInformation.BINARY_CONTENT,
                                                       source_id=self.__get_endpoint_id(with_forwarder=True),
                                                       destination_id=self.__get_endpoint_id(with_forwarder=False,
                                                                                             start_index=2),
                                                       nonce=123456789)
        expected_message_hash = '05a6cdda6e321b7c9f7e0bd9d73f062b481e4d4b'
        self.assertEqual(message_utils.get_message_core_hash(message_core), expected_message_hash)

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
