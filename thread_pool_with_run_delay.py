import multiprocessing
import threading
import time
from queue import PriorityQueue, Full, Queue

import common_utils


class ThreadWorker(object):
    def __init__(self, job_queue: Queue, shutdown_event: threading.Event):
        self.job_queue = job_queue
        self.shutdown_event = shutdown_event
        self.thread = threading.Thread(target=self.__wait_on_queue_and_execute_job)
        self.thread.start()

    def join(self):
        self.thread.join()

    def __wait_on_queue_and_execute_job(self):
        while not self.shutdown_event.is_set():
            job_to_run, parameters = self.job_queue.get()
            if common_utils.is_empty_object(job_to_run):
                continue
            try:
                job_to_run(*parameters)
            except Exception as e:
                pass
            self.job_queue.task_done()


class ThreadDelayCoordinator(object):
    def __init__(self, job_queue_with_delay: PriorityQueue, job_queue: Queue, shutdown_event: threading.Event,
                 sleep_time_ms=100):
        self.job_queue_with_delay = job_queue_with_delay
        self.job_queue = job_queue
        self.shutdown_event = shutdown_event
        self.sleep_time_ms = sleep_time_ms
        self.all_tasks_assigned_workers = threading.Event()
        self.thread = threading.Thread(target=self.__wait_on_delay_queue_and_post_job_to_worker_queue)
        self.thread.start()

    def wait_until_queued_tasks_are_assigned_workers(self):
        self.all_tasks_assigned_workers.wait()

    def join(self):
        self.thread.join()

    def __wait_on_delay_queue_and_post_job_to_worker_queue(self):
        while not self.shutdown_event.is_set():
            run_at_utc_timestamp_nsec, (job_to_run, parameters) = self.job_queue_with_delay.get()
            if self.shutdown_event.is_set():
                return
            if common_utils.is_empty_object(job_to_run):
                continue
            if common_utils.get_timestamp_now_ns() < run_at_utc_timestamp_nsec:
                self.job_queue_with_delay.put((run_at_utc_timestamp_nsec, (job_to_run, parameters)))
                time.sleep(self.sleep_time_ms / 1000.0)
                continue
            self.job_queue.put((job_to_run, parameters))
            if self.job_queue_with_delay.qsize() == 0:
                self.all_tasks_assigned_workers.set()


class ThreadPoolWithRunDelay(object):
    def __init__(self, num_threads=None, max_queue_size=1000000):
        self.job_queue_with_delay = PriorityQueue(maxsize=max_queue_size)
        self.job_queue = Queue(maxsize=max_queue_size)
        self.shutdown_event = threading.Event()
        if num_threads is None:
            num_threads = self.__get_num_threads()
        self.worker_threads = []
        for _ in range(num_threads):
            self.worker_threads.append(ThreadWorker(self.job_queue, self.shutdown_event))
        self.coordinator_thread = ThreadDelayCoordinator(self.job_queue_with_delay, self.job_queue, self.shutdown_event)

    def add_job(self, job_to_run, parameters=(), run_at_utc_timestamp_ns: int = 0, run_delay_from_now_ns: int = 0):
        if run_at_utc_timestamp_ns <= 0 < run_delay_from_now_ns:
            run_at_utc_timestamp_ns = common_utils.get_timestamp_now_ns()
            run_at_utc_timestamp_ns += run_delay_from_now_ns
        if run_at_utc_timestamp_ns == 0:
            # If there is no delay specified avoid the priority queue
            try:
                self.job_queue.put_nowait((job_to_run, parameters))
            except Full as e:
                # Silently discard message
                pass
            return
        try:
            # Delay specified use the priority queue
            self.job_queue_with_delay.put_nowait((run_at_utc_timestamp_ns, (job_to_run, parameters)))
        except Full as e:
            # Silently discard message
            pass

    def wait_for_jobs_completion_and_shut_down(self):
        def stop():
            return

        # We need to add a dummy job with delay, so that the priority queue awakens the coordinator thread
        self.add_job(stop, run_delay_from_now_ns=100)
        self.coordinator_thread.wait_until_queued_tasks_are_assigned_workers()
        self.job_queue.join()
        self.shutdown_event.set()
        for _ in range(len(self.worker_threads)):
            self.job_queue.put((stop, ()))
        for thread in self.worker_threads:
            thread.join()
        self.job_queue_with_delay.put((0, (stop, ())))
        self.coordinator_thread.join()

    def release_resources(self):
        self.wait_for_jobs_completion_and_shut_down()

    def __get_num_threads(self):
        num_threads = multiprocessing.cpu_count() // 2
        if num_threads == 0:
            num_threads = 1
        return num_threads

    # def __del__(self):
    #     self.release_resources()
