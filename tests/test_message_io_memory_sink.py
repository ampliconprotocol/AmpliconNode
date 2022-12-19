import time
from unittest import TestCase

import message_io_memory_sink


class TestMessageIoMemorySink(TestCase):
    def setUp(self) -> None:
        self.read_messages = []
        self.message_io_sink = message_io_memory_sink.MessageIoMemorySink(sink_id="fake_id",
                                                                     on_read_ready_callback=self.__read_callback)
    def tearDown(self) -> None:
        self.message_io_sink.release_resources()

    def test_add_message_to_read_ready_queue(self):
        self.message_io_sink.add_message_to_read_ready_queue("Test message 1")
        self.message_io_sink.add_message_to_read_ready_queue("Test message 2")
        self.message_io_sink.add_message_to_read_ready_queue("Test message 3")
        time.sleep(0.5)
        self.assertEqual(len(self.read_messages), 3)
        self.assertListEqual(self.read_messages, ["Test message 1", "Test message 2", "Test message 3"])


    def test_get_written_message(self):
        self.message_io_sink.write("Test message 1")
        self.message_io_sink.write("Test message 2")
        self.message_io_sink.write("Test message 3")
        time.sleep(0.5)
        self.assertEqual(self.message_io_sink.get_written_message(), "Test message 1")

    def __read_callback(self, message_sink: message_io_memory_sink.MessageIoMemorySink):
        while message_sink.is_read_ready():
            self.read_messages.append(message_sink.read())
