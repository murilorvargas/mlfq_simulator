from typing import List

from process import Process
from queues import HighLevelQueue, LowLevelQueue


class Scheduler:

    def __init__(self):
        self.admitted_processes: List[str] = []
        self.high_level_queue = HighLevelQueue()
        self.low_level_queue = LowLevelQueue()
        self.quantum: int = 0

    def admit(self, process: Process) -> None:
        for admitted_process in self.admitted_processes:
            if admitted_process == process.name:
                raise ValueError(f"Process name already admitted: {process.name}")

        self.admitted_processes.append(process.name)
        self.high_level_queue.enqueue_ready(process)

    def block(self, process_name: str) -> None:
        process = self.high_level_queue.release_executing(process_name)
        if process is not None:
            self.high_level_queue.enqueue_blocked(process)
            return

        process = self.low_level_queue.release_executing(process_name)
        if process is not None:
            self.low_level_queue.enqueue_blocked(process)
            return

        raise ValueError(f"Process not found in executing processes: {process_name}")

    def unblock(self, process_name: str) -> None:
        process = self.high_level_queue.pop_blocked(process_name)
        if process is not None:
            self.high_level_queue.enqueue_ready(process)
            return

        process = self.low_level_queue.pop_blocked(process_name)
        if process is not None:
            self.high_level_queue.enqueue_ready(process)
            return

        raise ValueError(f"Process not found in blocked processes: {process_name}")

    def run(self) -> None:
        ...
