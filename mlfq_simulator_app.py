from typing import List

from int_handlers import read_int
from process import Process
from programs.program_parser import ProgramParser
from scheduler import Scheduler


class MLFQSimulator:

    def __init__(self):
        self._time: int = 0
        self._scheduler: Scheduler = Scheduler()
        self._arrivals: dict[int, List[Process]] = {}
        self._unblocks: dict[int, List[Process]] = {}

    def _admit_arrivals(self) -> None:
        processes = self._arrivals[self._time]
        for process in processes:
            self._scheduler.admit(process, self._time)

        del self._arrivals[self._time]

    def _unblock_processes(self) -> None:
        processes = self._unblocks[self._time]
        for process in processes:
            self._scheduler.unblock(process.name)

        del self._unblocks[self._time]

    def _print_periodic_report(self) -> None:
        # TODO: imprimir o tempo global (t=self._time) e chamar self._scheduler.print_periodic_report(self._time)
        ...

    def _print_final_report(self) -> None:
        # TODO: chamar self._scheduler.print_final_report()
        ...

    def schedule_arrival(self, process: Process, arrival_time: int) -> None:
        if arrival_time not in self._arrivals:
            self._arrivals[arrival_time] = []

        self._arrivals[arrival_time].append(process)

    def tick(self) -> None:
        self._admit_arrivals()
        self._unblock_processes()

        self._scheduler.run(self._time)

        self._time += 1

    def run(self) -> None:
        while self._arrivals or self._unblocks:
            self.tick()

def main() -> None:
    print("Running mlfq simulator app!")

    program_parser = ProgramParser()

    processes = program_parser.parse()

    simulator = MLFQSimulator()

    for process in processes:
        arrival_time = read_int(f"[{process.name}] Instante de carga (arrival time): ")
        simulator.schedule_arrival(process, arrival_time)

    simulator.run()

if __name__ == "__main__":
    main()
