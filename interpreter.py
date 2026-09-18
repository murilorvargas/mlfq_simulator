from int_handlers import read_int
from process import Process, ProcessBlockedForInput, ProcessBlockedForOutput, ProcessHalted


class Interpreter:

    def __init__(self):
        self._arithmetic_operations = {
            "ADD": self._add,
            "SUB": self._sub,
            "MULT": self._mult,
            "DIV": self._div,
        }
        self._memory_operations = {
            "LOAD": self._load,
            "STORE": self._store,
        }
        self._jump_operations = {
            "BRANY": self._brany,
            "BRPOS": self._brpos,
            "BRZERO": self._brzero,
            "BRNEG": self._brneg,
        }
        self._system_operations = {
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

    def _add(self, accumulator: int, value: int) -> int:
        return accumulator + value

    def _sub(self, accumulator: int, value: int) -> int:
        return accumulator - value

    def _mult(self, accumulator: int, value: int) -> int:
        return accumulator * value

    def _div(self, accumulator: int, value: int) -> int:
        return int(accumulator / value)

    def _execute_arithmetic(self, process: Process, mnemonic: str, operand: str) -> None:
        if mnemonic not in self._arithmetic_operations:
            raise ValueError(f"Unknown arithmetic mnemonic: '{mnemonic}'")

        resolved_operand = self._resolve_operand(process, operand)
        operation_result = self._arithmetic_operations[mnemonic](process.accumulator, resolved_operand)
        process.accumulator = operation_result

    def _load(self, process: Process, operand: str) -> None:
        resolved_operand = self._resolve_operand(process, operand)
        process.accumulator = resolved_operand

    def _store(self, process: Process, operand: str) -> None:
        if operand.startswith("#"):
            raise ValueError(f"STORE does not support immediate addressing: '{operand}'")

        process.data_memory[operand] = process.accumulator

    def _execute_memory(self, process: Process, mnemonic: str, operand: str) -> None:
        if mnemonic not in self._memory_operations:
            raise ValueError(f"Unknown memory mnemonic: '{mnemonic}'")

        self._memory_operations[mnemonic](process, operand)

    def _brany(self, process: Process, label: str) -> bool:
        process.program_counter = process.labels[label]
        return True
    
    def _brpos(self, process: Process, label: str) -> bool:
        if process.accumulator > 0:
            process.program_counter = process.labels[label]
            return True

        return False
    
    def _brzero(self, process: Process, label: str) -> bool:
        if process.accumulator == 0:
            process.program_counter = process.labels[label]
            return True

        return False
    
    def _brneg(self, process: Process, label: str) -> bool:
        if process.accumulator < 0:
            process.program_counter = process.labels[label]
            return True

        return False

    def _execute_jump(self, process: Process,  mnemonic: str, label: str) -> bool:
        if mnemonic not in self._jump_operations:
            raise ValueError(f"Unknown jump mnemonic: '{mnemonic}'")

        return self._jump_operations[mnemonic](process, label)

    def _exit(self, process: Process) -> None:
        raise ProcessHalted(process)

    def _print(self, process: Process) -> None:
        print(f"[{process.name}] Impressão (SYSCALL 1): {process.accumulator}")
        raise ProcessBlockedForOutput(process)

    def _read(self, process: Process) -> None:
        process.accumulator = read_int(f"[{process.name}] Leitura (SYSCALL 2): ")
        raise ProcessBlockedForInput(process)

    def _execute_system(self, process: Process, mnemonic: str, operand: str) -> None:
        if mnemonic not in self._system_operations:
            raise ValueError(f"Unknown system mnemonic: '{mnemonic}'")

        if operand not in self._system_operations[mnemonic]:
            raise ValueError(f"Unknown SYSCALL operand: '{operand}'")

        self._system_operations[mnemonic][operand](process)

    def execute_instruction(self, process: Process) -> None:
        if process is None:
            raise RuntimeError("Cannot execute instruction: no process is currently executing")

        mnemonic, argument = process.instructions[process.program_counter]

        if mnemonic in self._arithmetic_operations:
            self._execute_arithmetic(process, mnemonic, argument)
            process.program_counter += 1
            return

        if mnemonic in self._memory_operations:
            self._execute_memory(process, mnemonic, argument)
            process.program_counter += 1
            return

        if mnemonic in self._jump_operations:
            executed = self._execute_jump(process, mnemonic, argument)
            if executed is False:
                process.program_counter += 1

            return

        if mnemonic in self._system_operations:
            try:
                self._execute_system(process, mnemonic, argument)
            except (ProcessBlockedForOutput, ProcessBlockedForInput) as exception:
                process.program_counter += 1
                raise exception
            return

        raise ValueError(f"Unknown instruction mnemonic: '{mnemonic}'")
