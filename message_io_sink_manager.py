from threading import Event
from threading import Lock

import common_utils
import message_io_sink
from thread_pool_with_run_delay import ThreadPoolWithRunDelay


class MessageIoSinkManager(object):
    def __init__(self, thread_pool_with_run_delay: ThreadPoolWithRunDelay, default_message_io_sink=None,
                 on_read_from_sink_callback=None):
        """
        :param thread_pool_with_run_delay: An externally specified ThreadPoolWithRunDelay object.
        :param default_message_io_sink: A MessageIoSink object that gets the messages when no sink_id is specified. Also
        this is the default (non-forwarded) sink.
        :param on_read_from_sink_callback: A function object that takes as input the
                                            (sink_id:str, message_payload:bytes)
        """
        self.sink_id_to_message_io_sink = {}
        self.sink_ids_being_listened_to = set()
        self.on_read_from_sink_callback = on_read_from_sink_callback
        self.is_shutting_down = Event()
        self.thread_pool_with_run_delay = thread_pool_with_run_delay
        self.default_message_io_sink = None
        self.lock = Lock()
        self.set_default_message_io_sink(default_message_io_sink)

    def is_active_sink_id(self, sink_id: str) -> bool:
        with self.lock:
            if sink_id in self.sink_id_to_message_io_sink:
                return True
        default_sink = self.get_default_message_io_sink()
        if not common_utils.is_empty_object(default_sink) and default_sink.get_id() == sink_id:
            return True
        return False

    def add_message_io_sink(self, sink: message_io_sink.MessageIoSink):
        if self.__is_message_io_sink_previously_added(sink):
            self.__remove_message_io_sink_read_ready_listener(sink)
        with self.lock:
            self.sink_id_to_message_io_sink[sink.get_id()] = sink
        self.__add_message_io_sink_read_ready_listener(sink)

    def remove_message_io_sink_by_id(self, sink_id: str):
        default_sink = self.get_default_message_io_sink()
        if not common_utils.is_empty_object(default_sink) and default_sink.get_id() == sink_id:
            self.set_default_message_io_sink(None)
            self.__remove_message_io_sink_read_ready_listener(default_sink)
            return
        with self.lock:
            if sink_id not in self.sink_id_to_message_io_sink:
                return
            sink = self.sink_id_to_message_io_sink[sink_id]
            del self.sink_id_to_message_io_sink[sink_id]
        self.__remove_message_io_sink_read_ready_listener(sink)

    def get_message_io_sink_by_id(self, sink_id: str = None) -> message_io_sink.MessageIoSink:
        """
        This method returns the message_io_sink object associated with the known sink_id.


        :param sink_id: When None or empty string "" this method returns the default message_io_sink object. In case
        sink_id is not found, while being a valid non-empty string this method returns None. Else it returns the
        corresponding message_io_sink.

        :return: default message_io_sink when sink_id = None/"", corresponding message_io_sink or None if sink not found.
        """
        default_sink = self.get_default_message_io_sink()
        if common_utils.is_empty_string(sink_id):
            return default_sink
        if not common_utils.is_empty_object(default_sink) and sink_id == default_sink.get_id():
            return default_sink
        with self.lock:
            if sink_id not in self.sink_id_to_message_io_sink:
                return None
            return self.sink_id_to_message_io_sink[sink_id]

    def set_default_message_io_sink(self, sink: message_io_sink.MessageIoSink):
        if common_utils.is_empty_object(sink) and common_utils.is_empty_object(self.get_default_message_io_sink()):
            return
        old_sink = self.get_default_message_io_sink()
        with self.lock:
            self.default_message_io_sink = sink
        if not common_utils.is_empty_object(old_sink):
            self.__remove_message_io_sink_read_ready_listener(old_sink)
        if not common_utils.is_empty_object(sink):
            self.__add_message_io_sink_read_ready_listener(sink)

    def get_default_message_io_sink(self) -> message_io_sink.MessageIoSink:
        with self.lock:
            return self.default_message_io_sink

    def write_to_sink(self, sink_id: str, message: bytes):
        sink = self.get_message_io_sink_by_id(sink_id)
        if common_utils.is_empty_object(sink):
            return

        def write():
            sink.write(message)

        self.thread_pool_with_run_delay.add_job(write)

    def release_resources(self):
        self.is_shutting_down.set()

    def __is_message_io_sink_previously_added(self, sink: message_io_sink.MessageIoSink) -> bool:
        sink_id = sink.get_id()
        if common_utils.is_empty_string(sink_id):
            raise ValueError("Invalid sink id specified.")
        with self.lock:
            if sink_id in self.sink_id_to_message_io_sink:
                return True
            return False

    def __remove_message_io_sink_read_ready_listener(self, sink: message_io_sink.MessageIoSink):
        with self.lock:
            if sink.get_id() in self.sink_ids_being_listened_to:
                self.sink_ids_being_listened_to.remove(sink.get_id())

    def __add_message_io_sink_read_ready_listener(self, sink: message_io_sink.MessageIoSink):
        with self.lock:
            self.sink_ids_being_listened_to.add(sink.get_id())
        self.thread_pool_with_run_delay.add_job(self.__listen_for_read_ready_event, (sink,))

    def __listen_for_read_ready_event(self, sink: message_io_sink.MessageIoSink):
        if self.is_shutting_down.is_set():
            return
        with self.lock:
            if sink.get_id() not in self.sink_ids_being_listened_to:
                return
        sink.read_is_ready.wait(timeout=0.01)
        while sink.is_read_ready():
            read_message = sink.read()
            if not common_utils.is_empty_bytes(read_message):
                with self.lock:
                    self.on_read_from_sink_callback(sink.get_id(), read_message)
        self.thread_pool_with_run_delay.add_job(self.__listen_for_read_ready_event, (sink,))
