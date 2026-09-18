from typing import List

from int_handlers import read_int
from process import Process, ProcessBlockedForInput, ProcessBlockedForOutput, ProcessHalted
from programs.program_parser import ProgramParser
from scheduler import Scheduler


class MLFQSimulator:
    IO_BLOCK_DURATION = 3

    def __init__(self):
        self._time: int = 0
        self._scheduler: Scheduler = Scheduler()
        self._arrivals: dict[int, List[Process]] = {}
        self._unblocks: dict[int, List[Process]] = {}

    def _admit_arrivals(self) -> None:
        if self._arrivals.get(self._time) is not None:
            processes = self._arrivals[self._time]
            for process in processes:
                self._scheduler.admit(process, self._time)

            del self._arrivals[self._time]

    def _unblock_processes(self) -> None:
        if self._unblocks.get(self._time) is not None:
            processes = self._unblocks[self._time]
            for process in processes:
                self._scheduler.unblock(process.name)

            del self._unblocks[self._time]

    def schedule_arrival(self, process: Process, arrival_time: int) -> None:
        if self._arrivals.get(arrival_time) is None:
            self._arrivals[arrival_time] = []

        self._arrivals[arrival_time].append(process)

    def tick(self) -> None:
        self._admit_arrivals()
        self._unblock_processes()

        try:
            self._scheduler.run(self._time)
        except (ProcessBlockedForOutput, ProcessBlockedForInput) as exception:
            process: Process = exception.args[0]
            unblock_time = self._time + 1 + self.IO_BLOCK_DURATION
            if self._unblocks.get(unblock_time) is None:
                self._unblocks[unblock_time] = []

            self._unblocks[unblock_time].append(process)
        except ProcessHalted:
            ...

        self._time += 1

    def run(self) -> None:
        while self._arrivals or self._scheduler.has_pending_processes():
            self.tick()

        self._scheduler.print_final_report()

def main() -> None:
    print("=== EXECUTANDO SIMULAÇÃO ===")

    program_parser = ProgramParser()

    try:
        processes = program_parser.parse()
    except ValueError as error:
        print(f"Erro ao carregar os programas: {error}")
        return

    simulator = MLFQSimulator()

    for process in processes:
        print(f"[{process.name}] Prioridade: {process.priority} | Memória: {process.memory_size} posições")
        arrival_time = read_int(f"[{process.name}] Instante de carga (arrival time): ")
        simulator.schedule_arrival(process, arrival_time)

    try:
        simulator.run()
    except (ValueError, RuntimeError) as error:
        print(f"Erro de execução: {error}")

if __name__ == "__main__":
    main()
