from abc import ABC, abstractmethod
from typing import List, Optional

from process import Process


class BaseQueue(ABC):
    def __init__(self):
        self.ready_processes: List[Process] = []
        self.executing_process: Optional[Process] = None
        self.blocked_processes: List[Process] = []
        self.finished_processes: List[Process] = []

    @abstractmethod
    def enqueue_ready(self, process: Process) -> None:
        ...

    def enqueue_blocked(self, process: Process) -> None:
        self.blocked_processes.append(process)

    def release_executing(self, process_name) -> Optional[Process]:
        process = self.executing_process
        if process is not None and process.name == process_name:
            self.executing_process = None
            return process

    def pop_blocked(self, process_name: str) -> Optional[Process]:
        for i, p in enumerate(self.blocked_processes):
            if p.name == process_name:
                return self.blocked_processes.pop(i)


class HighLevelQueue(BaseQueue):

    def enqueue_ready(self, process: Process) -> None:
        ...


class LowLevelQueue(BaseQueue):

    def enqueue_ready(self, process: Process) -> None:
        ...
