from typing import List, Literal, Optional, Tuple

from process import Process
from queues import HighLevelQueue, LowLevelQueue


class Scheduler:
    HIGH_QUANTUM = 2
    LOW_QUANTUM = 4

    def __init__(self):
        self._admitted_processes: List[Process] = []
        self._high_level_queue = HighLevelQueue()
        self._low_level_queue = LowLevelQueue()
        self._executing_process: Optional[Process] = None
        self._executing_level: Optional[Literal["high", "low"]] = None
        self._blocked_processes: List[Process] = []
        self._quantum: int = 0
        self._preempted: Optional[Tuple[Process, int]] = None

    def _preempt(self, process_name: str) -> None:
        process = self._executing_process
        if process is not None and process.name == process_name:
            process.status = "ready"
            self._low_level_queue.enqueue_at_group_front(process)
            self._preempted = process, self._quantum
            self._executing_process = None
            return

        raise RuntimeError(f"Process not currently executing: '{process_name}'")

    def _run_high_level_queue(self) -> bool:
        ...

    def _run_low_level_queue(self) -> None:
        ...

    def admit(self, process: Process) -> None:
        for admitted_process in self._admitted_processes:
            if admitted_process.name == process.name:
                raise RuntimeError(f"Process already admitted: '{process.name}'")

        self._admitted_processes.append(process)
        process.status = "ready"
        self._high_level_queue.enqueue(process)

    def block(self, process_name: str) -> None:
        process = self._executing_process
        if process is not None and process.name == process_name:
            process.status = "blocked"
            self._blocked_processes.append(process)
            self._executing_process = None
            return

        raise RuntimeError(f"Process not currently executing: '{process_name}'")

    def unblock(self, process_name: str) -> None:
        for i, p in enumerate(self._blocked_processes):
            if p.name == process_name:
                process = self._blocked_processes.pop(i)
                process.status = "ready"
                self._high_level_queue.enqueue(process)
                return

        raise RuntimeError(f"Process not in the blocked list: '{process_name}'")

    def run(self) -> None:
        executed = self._run_high_level_queue()
        if executed is False:
            self._run_low_level_queue()
