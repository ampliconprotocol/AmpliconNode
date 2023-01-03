from unittest import TestCase

import common_utils
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

    def test_encrypt_message_core_information_with_destination_id(self):
        test_message_core_no_forwarder = message_utils.get_message_core(
            message_type=node_pb2.MessageCoreInformation.BINARY_CONTENT, source_id=self.__get_endpoint_id(),
            destination_id=self.__get_endpoint_id(start_index=2), message_payload=b"Hello there!")
        encrypted_message = message_utils.encrypt_message_core_information_with_destination_id(
            test_message_core_no_forwarder)
        p2p_message = message_utils.get_amplicon_p2p_relay_message(encrypted_message, message_dna="ATGC")
        decrypted_message = message_utils.decrypt_encrypted_message_core_information_with_node_secret(
            amplicon_p2p_relay_message=p2p_message,
            node_secret=node_pb2.NodeSecret(secret_private_key=self.__get_test_private_key(key_instance=2)))
        self.assertEqual(test_message_core_no_forwarder, decrypted_message)
        # print(decrypted_message)
        test_message_core_with_forwarder = message_utils.get_message_core(
            message_type=node_pb2.MessageCoreInformation.HANDSHAKE, source_id=self.__get_endpoint_id(),
            destination_id=self.__get_endpoint_id(start_index=2, with_forwarder=True), message_payload=b"Hello there!")
        encrypted_message2 = message_utils.encrypt_message_core_information_with_destination_id(
            test_message_core_with_forwarder)
        p2p_message2 = message_utils.get_amplicon_p2p_relay_message(encrypted_message2, message_dna="ATGC")
        decrypted_message2 = message_utils.decrypt_encrypted_message_core_information_with_node_secret(
            amplicon_p2p_relay_message=p2p_message2,
            node_secret=node_pb2.NodeSecret(secret_private_key=self.__get_test_private_key(key_instance=3)))
        self.assertFalse(common_utils.is_empty_object(decrypted_message2))
        self.assertEqual(decrypted_message2.message_type, node_pb2.MessageCoreInformation.BINARY_CONTENT)
        self.assertEqual(decrypted_message2.destination_id.forwarder_public_key, self.__get_test_public_key(3))
        # print(decrypted_message2)


    def __get_test_public_key(self, key_instance=0) -> str:
        keys = ['f4837573e349fb626a51bae2b8562f3128193719c26e807a9432b1638516437a',
                '4511ed0489dd20682bd1fbfc9fa01a0e7740ca26fcb86729d00747f77061b43c',
                '25fc0a25ee8ef84507a52fbabf577a90ed4b50a7b070c6aff5ba32b8589c2d35',
                'b36cbf04dbbbf2e43805351d95ce824e3fd464d800afd6eeea7c95c28c5b5f17']
        return keys[key_instance % len(keys)]

    def __get_test_private_key(self, key_instance=0) -> str:
        keys = ['0fd2f07e461a5f16781581c924929459ae4a47e0c536ba7bbaf263493f153f8e',
                '96857c2293394fba31936c4fd5b0dd5f7a52a42e14e5eec72972c3029e410dfd',
                'f1ec219c246c08194c5d36b9658bacb155a7daafa40fa3e1eb5ba3f5b147664f',
                'a7ed4d6e3ffff9cdba4c168a02d164503a6c765958b437eecca217cbcd9e6594']
        return keys[key_instance % len(keys)]

    def __get_endpoint_id(self, with_forwarder=False, start_index=0):
        if with_forwarder:
            return node_pb2.MessageEndpointId(endpoint_public_key=self.__get_test_public_key(start_index),
                                              forwarder_public_key=self.__get_test_public_key(start_index + 1))
        return node_pb2.MessageEndpointId(endpoint_public_key=self.__get_test_public_key(start_index))
