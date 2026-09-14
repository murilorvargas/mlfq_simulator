from typing import List, Literal, Optional, Tuple

from programs.program_parser import ProgramParser


# TODO: decidir se as transições de estado (halt/bloqueio) serão sinalizadas
# via exceções ou por outro mecanismo (ex: retorno de estado, flag no Process)
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
        self.status: Literal["ready", "executing", "blocked", "finished"] = "ready"
        self.program_counter: int = 0
        self.accumulator: Optional[int] = None
        self.data_memory: dict = data_memory
        self.instructions: List[Tuple[str, str]] = instructions
        self.labels: dict = labels

class Interpreter:

    def __init__(self):
        self.arithmetic_operations = {
            "ADD": self._add,
            "SUB": self._sub,
            "MULT": self._mult,
            "DIV": self._div,
        }
        self.memory_operations = {
            "LOAD": self._load,
            "STORE": self._store,
        }
        self.jump_operations = {
            "BRANY": self._brany,
            "BRPOS": self._brpos,
            "BRZERO": self._brzero,
            "BRNEG": self._brneg,
        }
        self.system_operations = {
            "SYSCALL": {
                "0": self._exit,
                "1": self._print,
                "2": self._read,
            }
        }

    def _resolve_operand(self, process: Process, operand: str) -> int:
        if operand.startswith("#"):
            return int(operand[1:])

        return process.data_memory[operand]

    # --------- ARITHMETIC OPERATIONS ---------

    def _add(self, accumulator: int, value: int) -> int:
        return accumulator + value

    def _sub(self, accumulator: int, value: int) -> int:
        return accumulator - value

    def _mult(self, accumulator: int, value: int) -> int:
        return accumulator * value

    def _div(self, accumulator: int, value: int) -> int:
        return int(accumulator / value)

    def _execute_arithmetic(self, process: Process, mnemonic: str, operand: str) -> None:
        if mnemonic not in self.arithmetic_operations:
            raise ValueError(f"Invalid arithmetic mnemonic: {mnemonic}")

        resolved_operand = self._resolve_operand(process, operand)
        operation_result = self.arithmetic_operations[mnemonic](process.accumulator, resolved_operand)
        process.accumulator = operation_result

    # --------- MEMORY OPERATIONS ---------

    def _load(self, process: Process, operand: str) -> None:
        resolved_operand = self._resolve_operand(process, operand)
        process.accumulator = resolved_operand

    def _store(self, process: Process, operand: str) -> None:
        process.data_memory[operand] = process.accumulator

    def _execute_memory(self, process: Process, mnemonic: str, operand: str) -> None:
        if mnemonic not in self.memory_operations:
            raise ValueError(f"Invalid memory mnemonic: {mnemonic}")

        self.memory_operations[mnemonic](process, operand)

    # --------- JUMP OPERATIONS ---------

    def _brany(self, process: Process, label: str) -> None:
        process.program_counter = process.labels[label]

    def _brpos(self, process: Process, label: str) -> None:
        if process.accumulator > 0:
            process.program_counter = process.labels[label]

    def _brzero(self, process: Process, label: str) -> None:
        if process.accumulator == 0:
            process.program_counter = process.labels[label]

    def _brneg(self, process: Process, label: str) -> None:
        if process.accumulator < 0:
            process.program_counter = process.labels[label]

    def _execute_jump(self, process: Process,  mnemonic: str, label: str) -> None:
        if mnemonic not in self.jump_operations:
            raise ValueError(f"Invalid jump mnemonic: {mnemonic}")

        self.jump_operations[mnemonic](process, label)

    # --------- SYSTEM OPERATIONS ---------

    def _exit(self, process: Process) -> None:
        ...
        # raise ProcessHalted(process)

    def _print(self, process: Process) -> None:
        print(f"[{process.name}] Impressão (SYSCALL 1): {process.accumulator}")
        # raise ProcessBlockedForOutput(process)

    def _read(self, process: Process) -> None:
        process.accumulator = int(input(f"[{process.name}] Leitura (SYSCALL 2): "))
        # raise ProcessBlockedForInput(process)

    def _execute_system(self, process: Process, mnemonic: str, operand: str) -> None:
        if mnemonic not in self.system_operations:
            raise ValueError(f"Invalid system mnemonic: {mnemonic}")

        if operand not in self.system_operations[self.memory_operations]:
            raise ValueError(f"Invalid system operand: {operand}")

        self.system_operations[self.system_operations][operand](process)

    # ---------  ---------

    def execute_instruction(self, process: Process) -> None:
        ...

class HighPriorityQueue:

    def __init__(self):
        self.ready_processes: List[Process] = []
        self.executing_processes: List[Process] = []
        self.blocked_processes: List[Process] = []
        self.finished_processes: List[Process] = []

class LowPriorityQueue:

    def __init__(self):
        self.ready_processes: List[Process] = []
        self.executing_processes: List[Process] = []
        self.blocked_processes: List[Process] = []
        self.finished_processes: List[Process] = []

class Scheduler:

    def __init__(self):
        self.high_priority_queue = HighPriorityQueue()
        self.low_priority_queue = LowPriorityQueue()

    def admit(self, process: Process) -> None:
        if process.status != "ready":
            raise ValueError(f"Invalid process status for admit: {process.status}")

        self.high_priority_queue.ready_processes.append(process)

    def run(self) -> None:
        ...

class MLFQSimulator:

    def __init__(self):
        self.time: int = 0
        self.scheduler: Scheduler = Scheduler()
        self.arrivals: dict[int, List[Process]] = {}
        self.unblocks: dict[int, List[Process]] = {}

    def schedule_arrival(self, process: Process, arrival_time: int) -> None:
        if arrival_time not in self.arrivals:
            self.arrivals[arrival_time] = []

        self.arrivals[arrival_time].append(process)

    def _admit_arrivals(self) -> None:
        ...

    def _unblock_processes(self) -> None:
        ...

    def tick(self) -> None:
        self._admit_arrivals()
        self._unblock_processes()

        self.scheduler.run()

        self.time += 1

    def run(self) -> None:
        while self.arrivals or self.unblocks:
            self.tick()

def main() -> None:
    print("Running mlfq simulator app!")

    parser = ProgramParser()

    processes = parser.parse_programs()

    simulator = MLFQSimulator()

    for process in processes:
        arrival_time = int(input(f"[{process.name}] Instante de carga (arrival time): "))
        simulator.schedule_arrival(process, arrival_time)

    simulator.run()

if __name__ == "__main__":
    main()