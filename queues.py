from abc import ABC, abstractmethod
from typing import List

from process import Process


class BaseQueue(ABC):
    def __init__(self):
        self.processes: List[Process] = []

    @abstractmethod
    def enqueue(self, process: Process) -> None:
        ...

    def dequeue_next(self) -> Process:
        return self.processes.pop(0)


class HighLevelQueue(BaseQueue):

    def enqueue(self, process: Process) -> None:
        # TODO: implementar entrada FIFO no final da Fila 0
        ...


class LowLevelQueue(BaseQueue):

    def enqueue(self, process: Process) -> None:
        # TODO: implementar inserção ordenada por prioridade (com desempate FIFO) na Fila 1
        ...

    def enqueue_at_group_front(self, process: Process) -> None:
        # TODO: implementar reinserção no topo do grupo de prioridade do processo
        ...
