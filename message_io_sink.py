import time
from threading import Event, Thread

import common_utils


class MessageIOSinkCallbackHandler(object):
    def __init__(self, event: Event, callback, max_messages_per_second: int = 10,
                 statistics_accumulation_window_seconds: int = 10,
                 wait_time_out_ms: int = 100):
        self.event = event
        self.callback = callback
        self.max_messages_per_second = max_messages_per_second
        self.statistics_accumulation_window_seconds = statistics_accumulation_window_seconds
        self.last_event_block_start_timestamp_ns = 0
        self.events_count_within_block = 0

        self.delete_object = Event()
        self.delete_object.clear()

        self.block_size_ns = self.statistics_accumulation_window_seconds * 1e9
        self.callback_handler_thread = Thread(target=self.__callback_handler_thread, args=(wait_time_out_ms,))
        self.callback_handler_thread.start()

    def release_resources(self):
        self.delete_object.set()
        self.callback_handler_thread.join()

    def __update_current_time_block_message_counts(self, current_timestamp_ns, messages_count=1):
        block_index = current_timestamp_ns // self.block_size_ns
        block_start_timestamp = block_index * self.block_size_ns

        if block_start_timestamp == self.last_event_block_start_timestamp_ns:
            self.events_count_within_block += messages_count
        else:
            self.last_event_block_start_timestamp_ns = block_start_timestamp
            self.events_count_within_block = messages_count

    def __is_messages_per_second_within_allowed_limit(self) -> bool:
        time_now_ns = common_utils.get_timestamp_now_ns()
        self.__update_current_time_block_message_counts(current_timestamp_ns=time_now_ns)
        block_start_timestamp_seconds = self.last_event_block_start_timestamp_ns / 1e9
        current_time_seconds = float(time_now_ns) / 1e9
        elapsed_block_time_seconds = current_time_seconds - block_start_timestamp_seconds
        if self.statistics_accumulation_window_seconds - 1 <= elapsed_block_time_seconds <= self.statistics_accumulation_window_seconds:
            average_mps = self.events_count_within_block / elapsed_block_time_seconds
            if average_mps > self.max_messages_per_second:
                return False
        return True

    def __callback_handler_thread(self, wait_time_out_ms):
        while not self.delete_object.is_set():
            self.event.wait(wait_time_out_ms / 1000.0)
            if self.event.is_set():
                if not self.__is_messages_per_second_within_allowed_limit():
                    time.sleep(0.5)
                    continue
                self.callback()

    def __del__(self):
        self.release_resources()


class MessageIoSink(object):
    def __init__(self, sink_id: str = '', event_timeout_ms: int = 1000, on_read_ready_callback=None,
                 on_write_ready_callback=None,
                 max_reads_per_second: int = 10, max_writes_per_second: int = 10,
                 statistics_accumulation_window_seconds: int = 10):
        if common_utils.is_empty_string(sink_id):
            sink_id = common_utils.generate_uuid_string()
        self.sink_id = sink_id
        self.read_is_ready = Event()
        self.write_is_ready = Event()
        self.is_delete_event_triggered = Event()
        self.event_timeout_ms = event_timeout_ms

        if not common_utils.is_empty_object(on_read_ready_callback):
            def read_ready_callback():
                on_read_ready_callback(self)

            self.on_read_ready_callback_handler = MessageIOSinkCallbackHandler(event=self.read_is_ready,
                                                                               callback=read_ready_callback,
                                                                               max_messages_per_second=max_reads_per_second,
                                                                               statistics_accumulation_window_seconds=statistics_accumulation_window_seconds)
        if not common_utils.is_empty_object(on_write_ready_callback):
            def write_ready_callback():
                on_write_ready_callback(self)

            self.on_write_ready_callback_handler = MessageIOSinkCallbackHandler(event=self.write_is_ready,
                                                                                callback=write_ready_callback,
                                                                                max_messages_per_second=max_writes_per_second,
                                                                                statistics_accumulation_window_seconds=statistics_accumulation_window_seconds)

    def get_id(self):
        return self.sink_id

    def read(self, *args, **kwargs):
        pass

    def read_immediately_or_fail(self, *args, **kwargs):
        if self.is_read_ready():
            return self.read(*args, **kwargs)
        raise RuntimeError("Could not read from Message IO Sink.")

    def is_read_ready(self) -> bool:
        return self.read_is_ready.is_set()

    def set_read_ready_event(self, read_is_ready=True):
        if read_is_ready:
            self.read_is_ready.set()
            return
        self.read_is_ready.clear()

    def wait_until_read_is_ready(self):
        while not self.is_delete_event_triggered.is_set():
            self.read_is_ready.wait(self.event_timeout_ms / 1000.0)
            if self.read_is_ready.is_set():
                return

    def blocking_read(self, *args, **kwargs):
        self.wait_until_read_is_ready()
        return self.read(*args, **kwargs)

    def write(self, *args, **kwargs):
        pass

    def write_immediately_or_fail(self, *args, **kwargs):
        if self.is_write_ready():
            return self.write(*args, **kwargs)
        raise RuntimeError("Could not write to Message IO Sink.")

    def is_write_ready(self):
        return self.write_is_ready.is_set()

    def set_write_ready_event(self, write_is_ready=True):
        if write_is_ready:
            self.write_is_ready.set()
            return
        self.write_is_ready.clear()

    def wait_until_write_is_ready(self):
        while not self.is_delete_event_triggered.is_set():
            self.write_is_ready.wait(self.event_timeout_ms / 1000.0)
            if self.write_is_ready.is_set():
                return

    def blocking_write(self, *args, **kwargs):
        self.wait_until_write_is_ready()
        return self.write(*args, **kwargs)

    def release_resources(self):
        self.is_delete_event_triggered.set()
        if hasattr(self, "on_read_ready_callback_handler"):
            self.on_read_ready_callback_handler.release_resources()
        if hasattr(self, "on_write_ready_callback_handler"):
            self.on_write_ready_callback_handler.release_resources()

    def __del__(self):
        self.release_resources()
