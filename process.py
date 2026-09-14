from typing import List, Optional, Tuple


class ProcessHalted(Exception):
    pass

class ProcessBlockedForOutput(Exception):
    pass

class ProcessBlockedForInput(Exception):
    pass

class Process:

    def __init__(
        self,
        name: str,
        priority: int,
        data_memory: dict,
        instructions: List[Tuple[str, str]],
        labels: dict,
    ) -> None:
        self.name: str = name
        self.priority: int = priority
        self.program_counter: int = 0
        self.accumulator: Optional[int] = None
        self.data_memory: dict = data_memory
        self.instructions: List[Tuple[str, str]] = instructions
        self.labels: dict = labels
