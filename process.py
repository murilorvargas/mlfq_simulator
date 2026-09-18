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
        self.name: str = name
        self.status: Optional[Literal["ready", "executing", "blocked", "finished"]] = None
        self.priority: int = priority
        self.program_counter: int = 0
        self.accumulator: int = 0
        self.data_memory: dict = data_memory
        self.instructions: List[Tuple[str, str]] = instructions
        self.labels: dict = labels
        self.memory_size: int = len(instructions) + len(data_memory)
        self.dwell_time: dict = {"ready": 0, "executing": 0, "blocked": 0}
        self.admission_time: Optional[int] = None
        self.finish_time: Optional[int] = None

    def track_dwell_time(self) -> None:
        if self.dwell_time.get(self.status) is not None:
            self.dwell_time[self.status] += 1
