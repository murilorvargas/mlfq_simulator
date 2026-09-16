from typing import List

from int_handlers import read_int
from process import Process
from programs.program_parser import ProgramParser
from scheduler import Scheduler


class MLFQSimulator:

    def __init__(self):
        self.time: int = 0
        self.scheduler: Scheduler = Scheduler()
        self.arrivals: dict[int, List[Process]] = {}
        self.unblocks: dict[int, List[Process]] = {}

    def _admit_arrivals(self) -> None:
        processes = self.arrivals[self.time]
        for process in processes:
            self.scheduler.admit(process)

        del self.arrivals[self.time]

    def _unblock_processes(self) -> None:
        processes = self.unblocks[self.time]
        for process in processes:
            self.scheduler.unblock(process.name)

        del self.unblocks[self.time]

    def schedule_arrival(self, process: Process, arrival_time: int) -> None:
        if arrival_time not in self.arrivals:
            self.arrivals[arrival_time] = []

        self.arrivals[arrival_time].append(process)

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

    program_parser = ProgramParser()

    processes = program_parser.parse()

    simulator = MLFQSimulator()

    for process in processes:
        arrival_time = read_int(f"[{process.name}] Instante de carga (arrival time): ")
        simulator.schedule_arrival(process, arrival_time)

    simulator.run()

if __name__ == "__main__":
    main()
