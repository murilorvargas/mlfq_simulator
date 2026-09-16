from typing import List, Literal, Optional, Tuple


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
        self._priority: int = priority
        self.name: str = name
        self.status: Optional[Literal["ready", "executing", "blocked", "finished"]] = None
        self.program_counter: int = 0
        self.accumulator: Optional[int] = None
        self.data_memory: dict = data_memory
        self.instructions: List[Tuple[str, str]] = instructions
        self.labels: dict = labels
