from queue import Queue
from threading import Lock

import message_io_sink


class MessageIoMemorySink(message_io_sink.MessageIoSink):
    def __init__(self, sink_id='', on_read_ready_callback=None):
        self.read_ready_messages_queue = Queue()
        self.written_messages_queue = Queue()
        super(MessageIoMemorySink, self).__init__(sink_id=sink_id, on_read_ready_callback=on_read_ready_callback)
        self.set_write_ready_event(write_is_ready=True)
        self.lock = Lock()

    def read(self):
        with self.lock:
            if self.read_ready_messages_queue.empty():
                return None
            if self.read_ready_messages_queue.qsize() == 1:
                self.set_read_ready_event(read_is_ready=False)
            return self.read_ready_messages_queue.get()

    def write(self, message):
        with self.lock:
            self.written_messages_queue.put(message)

    def get_written_message(self):
        with self.lock:
            if self.written_messages_queue.empty():
                return None
            return self.written_messages_queue.get()

    def add_message_to_read_ready_queue(self, message):
        with self.lock:
            self.read_ready_messages_queue.put(message)
            self.set_read_ready_event(read_is_ready=True)
