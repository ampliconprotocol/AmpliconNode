import time
from threading import Lock
from unittest import TestCase

from message_io_memory_sink import MessageIoMemorySink
from message_io_sink import MessageIoSink
from message_io_sink_manager import MessageIoSinkManager
from thread_pool_with_run_delay import ThreadPoolWithRunDelay


class TestMessageIoSinkManager(TestCase):
    def setUp(self) -> None:
        self.thread_pool = ThreadPoolWithRunDelay(num_threads=8)
        self.sink_manager = MessageIoSinkManager(thread_pool_with_run_delay=self.thread_pool,
                                                 on_read_from_sink_callback=self.__on_read_callback)
        self.lock = Lock()
        self.sink_id_to_read_messages = {}

    def tearDown(self) -> None:
        self.sink_manager.release_resources()
        self.thread_pool.release_resources()

    def test_add_message_io_sink(self):
        sink1 = MessageIoSink()
        self.sink_manager.add_message_io_sink(sink1)
        self.assertIs(sink1, self.sink_manager.get_message_io_sink_by_id(sink_id=sink1.get_id()))
        sink2 = MessageIoSink(sink_id=sink1.get_id())
        self.sink_manager.add_message_io_sink(sink2)
        self.assertIs(sink2, self.sink_manager.get_message_io_sink_by_id(sink_id=sink1.get_id()))
        self.assertIs(None, self.sink_manager.get_message_io_sink_by_id(sink_id="non_existent_id"))

    def test_remove_message_io_sink_by_id(self):
        sink1 = MessageIoSink()
        self.sink_manager.add_message_io_sink(sink1)
        self.sink_manager.remove_message_io_sink_by_id(sink_id=sink1.get_id())
        self.assertIs(None, self.sink_manager.get_message_io_sink_by_id(sink_id=sink1.get_id()))
        default_sink = MessageIoSink()
        self.sink_manager.set_default_message_io_sink(default_sink)
        self.sink_manager.remove_message_io_sink_by_id(sink_id=default_sink.get_id())
        self.assertIs(None, self.sink_manager.get_default_message_io_sink())

    def test_get_message_io_sink_by_id(self):
        sink1 = MessageIoSink()
        self.sink_manager.add_message_io_sink(sink1)
        self.assertIs(sink1, self.sink_manager.get_message_io_sink_by_id(sink_id=sink1.get_id()))
        self.assertIs(None, self.sink_manager.get_message_io_sink_by_id(sink_id="non_existent_id"))

    def test_set_default_message_io_sink(self):
        default_sink = MessageIoSink()
        self.sink_manager.set_default_message_io_sink(default_sink)
        self.assertIs(default_sink, self.sink_manager.get_default_message_io_sink())

    def test_get_default_message_io_sink(self):
        self.assertIs(None, self.sink_manager.get_default_message_io_sink())
        default_sink = MessageIoSink()
        self.sink_manager.set_default_message_io_sink(default_sink)
        self.assertIs(default_sink, self.sink_manager.get_default_message_io_sink())
        self.assertEqual(default_sink.get_id(), self.sink_manager.get_default_message_io_sink().get_id())
        default_sink2 = MessageIoSink()
        self.sink_manager.set_default_message_io_sink(default_sink2)
        self.assertEqual(default_sink2.get_id(), self.sink_manager.get_default_message_io_sink().get_id())

    def test_write_to_sink(self):
        sink1 = MessageIoMemorySink()
        sink2 = MessageIoMemorySink()
        default_sink = MessageIoMemorySink()
        self.sink_manager.add_message_io_sink(sink1)
        self.sink_manager.add_message_io_sink(sink2)
        self.sink_manager.set_default_message_io_sink(default_sink)
        self.sink_manager.write_to_sink(sink_id=sink1.get_id(), message=b"Hello Clarice!")
        self.sink_manager.write_to_sink(sink_id=sink2.get_id(), message=b"Good morning, Dr. Lecter!")
        self.sink_manager.write_to_sink(sink_id="", message=b"Tell me about the ranch Clarice.")
        time.sleep(0.5)
        self.assertEqual(sink1.get_written_message(), b"Hello Clarice!")
        self.assertEqual(sink2.get_written_message(), b"Good morning, Dr. Lecter!")
        self.assertEqual(default_sink.get_written_message(), b"Tell me about the ranch Clarice.")

    def test_read_from_sinks(self):
        sink1 = MessageIoMemorySink()
        sink2 = MessageIoMemorySink()
        default_sink = MessageIoMemorySink()
        self.sink_manager.add_message_io_sink(sink1)
        self.sink_manager.add_message_io_sink(sink2)
        self.sink_manager.set_default_message_io_sink(default_sink)
        sink1.add_message_to_read_ready_queue(b"Master Pain! Master Pain! What do we do?")
        sink1.add_message_to_read_ready_queue(b"He is the chosen one!")
        sink2.add_message_to_read_ready_queue(b"My son, my son, what have ye done?")
        default_sink.add_message_to_read_ready_queue(
            b"Stand in the ashes of a trillion dead souls, and ask the ghosts if honor matters.")
        default_sink.add_message_to_read_ready_queue(
            b"The silence will be your answer.")
        time.sleep(1)
        self.lock.acquire()
        self.assertEqual(self.sink_id_to_read_messages[sink1.get_id()],
                         [b"Master Pain! Master Pain! What do we do?", b"He is the chosen one!"])
        self.assertEqual(self.sink_id_to_read_messages[sink2.get_id()], [b"My son, my son, what have ye done?"])
        self.assertEqual(self.sink_id_to_read_messages[default_sink.get_id()],
                         [b"Stand in the ashes of a trillion dead souls, and ask the ghosts if honor matters.",
                          b"The silence will be your answer."])
        self.lock.release()

    def test_is_active_sink_id(self):
        sink1 = MessageIoSink()
        sink2 = MessageIoSink()
        default_sink = MessageIoSink()
        self.sink_manager.add_message_io_sink(sink1)
        self.sink_manager.add_message_io_sink(sink2)
        self.sink_manager.set_default_message_io_sink(default_sink)
        self.assertTrue(self.sink_manager.is_active_sink_id(sink1.get_id()))
        self.assertTrue(self.sink_manager.is_active_sink_id(sink2.get_id()))
        self.assertTrue(self.sink_manager.is_active_sink_id(default_sink.get_id()))
        self.sink_manager.remove_message_io_sink_by_id(sink1.get_id())
        self.sink_manager.remove_message_io_sink_by_id(default_sink.get_id())
        self.assertFalse(self.sink_manager.is_active_sink_id(sink1.get_id()))
        self.assertTrue(self.sink_manager.is_active_sink_id(sink2.get_id()))
        self.assertFalse(self.sink_manager.is_active_sink_id(default_sink.get_id()))

    def __on_read_callback(self, sink_id, message):
        with self.lock:
            if sink_id not in self.sink_id_to_read_messages:
                self.sink_id_to_read_messages[sink_id] = []
            self.sink_id_to_read_messages[sink_id].append(message)


