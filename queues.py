from abc import ABC, abstractmethod
from typing import List

from process import Process


class BaseQueue(ABC):
    def __init__(self):
        self._processes: List[Process] = []

    @abstractmethod
    def enqueue(self, process: Process) -> None:
        ...

    def dequeue_next(self) -> Process:
        return self._processes.pop(0)


class HighLevelQueue(BaseQueue):

    def enqueue(self, process: Process) -> None:
        ...


class LowLevelQueue(BaseQueue):

    def enqueue(self, process: Process) -> None:
        ...

    def enqueue_at_group_front(self, process: Process) -> None:
        ...
