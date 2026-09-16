from typing import List, Literal, Optional, Tuple

from process import Process
from queues import HighLevelQueue, LowLevelQueue


class Scheduler:
    HIGH_QUANTUM = 2
    LOW_QUANTUM = 4

    def __init__(self):
        self.admitted_processes: List[str] = []
        self.high_level_queue = HighLevelQueue()
        self.low_level_queue = LowLevelQueue()
        self.executing_process: Optional[Process] = None
        self.executing_level: Optional[Literal["high", "low"]] = None
        self.blocked_processes: List[Process] = []
        self.quantum: int = 0
        self.preempted: Optional[Tuple[str, int]] = None

    def _preempt(self, process_name: str) -> None:
        process = self.executing_process
        if process is not None and process.name == process_name:
            process.status = "ready"
            self.low_level_queue.enqueue_at_group_front(process)
            self.preempted = process_name, self.quantum
            self.executing_process = None
            return

        raise RuntimeError(f"Process not currently executing: '{process_name}'")

    def admit(self, process: Process) -> None:
        for admitted_process in self.admitted_processes:
            if admitted_process == process.name:
                raise RuntimeError(f"Process already admitted: '{process.name}'")

        self.admitted_processes.append(process.name)
        process.status = "ready"
        self.high_level_queue.enqueue(process)

    def block(self, process_name: str) -> None:
        process = self.executing_process
        if process is not None and process.name == process_name:
            process.status = "blocked"
            self.blocked_processes.append(process)
            self.executing_process = None
            return

        raise RuntimeError(f"Process not currently executing: '{process_name}'")

    def unblock(self, process_name: str) -> None:
        for i, p in enumerate(self.blocked_processes):
            if p.name == process_name:
                process = self.blocked_processes.pop(i)
                process.status = "ready"
                self.high_level_queue.enqueue(process)
                return

        raise RuntimeError(f"Process not in the blocked list: '{process_name}'")

    def run(self) -> None:
        ...
