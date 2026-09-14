from typing import List, Literal, Optional

from process import Process


class Queue:

    def __init__(self, level: Literal["high", "low"]):
        self.level: Literal["high", "low"] = level
        self.ready_processes: List[Process] = []
        self.executing_process: Optional[Process] = None
        self.blocked_processes: List[Process] = []
        self.finished_processes: List[Process] = []

class Scheduler:

    def __init__(self):
        self.admitted_processes: List[str] = []
        self.high_level_queue = Queue("high")
        self.low_level_queue = Queue("low")
        self.quantum: int = 0

    def admit(self, process: Process) -> None:
        for admitted_process in self.admitted_processes:
            if admitted_process == process.name:
                raise ValueError(f"Process name already admitted: {process.name}")

        self.admitted_processes.append(process.name)
        self.high_level_queue.ready_processes.append(process)

    def block(self, process_name: str) -> None:
        process = self.high_level_queue.executing_process
        if process is not None and process.name == process_name:
            self.high_level_queue.executing_process = None
            self.high_level_queue.blocked_processes.append(process)
            return

        process = self.low_level_queue.executing_process
        if process is not None and process.name == process_name:
            self.low_level_queue.executing_process = None
            self.low_level_queue.blocked_processes.append(process)
            return

        raise ValueError(f"Process not found in executing processes: {process_name}")

    def unblock(self, process_name: str) -> None:
        for i, p in enumerate(self.high_level_queue.blocked_processes):
            if p.name == process_name:
                process = self.high_level_queue.blocked_processes.pop(i)
                self.high_level_queue.ready_processes.append(process)
                return

        for i, p in enumerate(self.low_level_queue.blocked_processes):
            if p.name == process_name:
                process = self.low_level_queue.blocked_processes.pop(i)
                self.high_level_queue.ready_processes.append(process)
                return

        raise ValueError(f"Process not found in blocked processes: {process_name}")

    def run(self) -> None:
        ...
