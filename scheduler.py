from typing import List, Literal, Optional, Tuple

from interpreter import Interpreter
from process import Process, ProcessBlockedForInput, ProcessBlockedForOutput, ProcessHalted
from queues import HighLevelQueue, LowLevelQueue


class Scheduler:
    HIGH_QUANTUM = 2
    LOW_QUANTUM = 4

    def __init__(self):
        self._interpreter = Interpreter()

        self._admitted_processes: List[Process] = []
        self._high_level_queue = HighLevelQueue()
        self._low_level_queue = LowLevelQueue()
        self._executing_process: Optional[Process] = None
        self._executing_level: Optional[Literal["high", "low"]] = None
        self._blocked_processes: List[Process] = []
        self._quantum: Optional[int] = None
        self._preempted: Optional[Tuple[Process, int]] = None
        self._cpu_timeline: List[Optional[Process]] = []
        self._level_timeline: List[Optional[Literal["high", "low"]]] = []

    def _track_dwell_time(self) -> None:
        for process in self._high_level_queue.processes:
            process.track_dwell_time()

        for process in self._low_level_queue.processes:
            process.track_dwell_time()

        if self._executing_process is not None:
            self._executing_process.track_dwell_time()

        for process in self._blocked_processes:
            process.track_dwell_time()

    def _print_periodic_report(self, time: int) -> None:
        status_labels = {
            "ready": "Pronto",
            "executing": "Executando",
            "blocked": "Bloqueado",
            "finished": "Finalizado",
        }

        print(f"\n[UT {time}] Estado dos processos:")
        if not self._admitted_processes:
            print("  Nenhum processo admitido.")

        for process in self._admitted_processes:
            print(f"  {process.name}: {status_labels[process.status]}")

        if self._executing_process is None:
            print(f"  CPU [UT {time}]: Ociosa")
        else:
            level = 0 if self._executing_level == "high" else 1
            print(
                f"  CPU [UT {time}]: {self._executing_process.name} "
                f"(Fila {level}, quantum: {self._quantum} UT)"
            )

        high_queue = ", ".join(process.name for process in self._high_level_queue.processes)
        low_queue = ", ".join(
            f"{process.name}(prio {process.priority})"
            for process in self._low_level_queue.processes
        )
        blocked = ", ".join(process.name for process in self._blocked_processes)

        print(f"  Fila 0: {high_queue or 'Vazia'}")
        print(f"  Fila 1 (maior valor = maior prioridade): {low_queue or 'Vazia'}")
        print(f"  Bloqueados: {blocked or 'Nenhum'}")

    def _report_time_unit(self, time: int) -> None:
        self._track_dwell_time()
        self._cpu_timeline.append(self._executing_process)
        self._level_timeline.append(self._executing_level)
        self._print_periodic_report(time)

    def _requeue(self, process_name: str) -> None:
        process = self._executing_process
        if process is not None and process.name == process_name:
            process.status = "ready"
            self._executing_process = None
            self._executing_level = None
            self._low_level_queue.enqueue(process)
            self._quantum = None
            return

        raise RuntimeError(f"Process not currently executing: '{process_name}'")

    def _preempt(self, process_name: str) -> None:
        process = self._executing_process
        if process is not None and process.name == process_name:
            if self._quantum == self.LOW_QUANTUM:
                self._requeue(process_name)
                return

            process.status = "ready"
            self._low_level_queue.enqueue_at_group_front(process)
            self._preempted = process, self._quantum
            self._executing_process = None
            self._executing_level = None
            self._quantum = None
            return

        raise RuntimeError(f"Process not currently executing: '{process_name}'")

    def _demote(self, process_name: str) -> None:
        if self._executing_level != "high":
            raise RuntimeError(f"Process not currently executing in Fila 0: '{process_name}'")

        self._requeue(process_name)

    def _block(self, process_name: str) -> None:
        process = self._executing_process
        if process is not None and process.name == process_name:
            process.status = "blocked"
            self._blocked_processes.append(process)
            self._executing_process = None
            self._executing_level = None
            self._quantum = None
            return

        raise RuntimeError(f"Process not currently executing: '{process_name}'")

    def _finish(self, process_name: str, time: int) -> None:
        process = self._executing_process
        if process is not None and process.name == process_name:
            process.status = "finished"
            process.finish_time = time
            self._executing_process = None
            self._executing_level = None
            self._quantum = None
            return

        raise RuntimeError(f"Process not currently executing: '{process_name}'")

    def _execute(self, process: Process, level: Literal["high", "low"]) -> None:
        if self._executing_process is not None:
            raise RuntimeError(f"Process already executing: '{self._executing_process.name}'")

        process.status = "executing"
        self._executing_process = process
        self._executing_level = level
        self._quantum = 1

    def _run_interpreter(self, time: int) -> None:
        self._report_time_unit(time)

        try:
            self._interpreter.run_instruction(self._executing_process)
        except (ProcessBlockedForOutput, ProcessBlockedForInput) as exception:
            process: Process = exception.args[0]
            self._block(process.name)
            raise exception
        except ProcessHalted as exception:
            process: Process = exception.args[0]
            self._finish(process.name, time)

    def _run_high_level_queue(self, time: int) -> bool:
        if self._executing_level != "high":
            if self._high_level_queue.has_processes() is False:
                return False

            if self._executing_process is not None:
                self._preempt(self._executing_process.name)

            process = self._high_level_queue.dequeue_next()
            self._execute(process, "high")
        else:
            if self._quantum == self.HIGH_QUANTUM:
                self._demote(self._executing_process.name)

                if self._high_level_queue.has_processes() is False:
                    return False

                process = self._high_level_queue.dequeue_next()
                self._execute(process, "high")
            else:
                self._quantum += 1

        self._run_interpreter(time)
        return True

    def _run_low_level_queue(self, time: int) -> None:
        if self._executing_level != "low":
            if self._low_level_queue.has_processes() is False:
                self._report_time_unit(time)
                return

            process = self._low_level_queue.dequeue_next()
            self._execute(process, "low")

            if self._preempted is not None and self._preempted[0] is process:
                self._quantum = self._preempted[1] + 1

            self._preempted = None
        else:
            if self._quantum == self.LOW_QUANTUM:
                self._requeue(self._executing_process.name)

                process = self._low_level_queue.dequeue_next()
                self._execute(process, "low")
            else:
                self._quantum += 1

        self._run_interpreter(time)

    def admit(self, process: Process, time: int) -> None:
        for admitted_process in self._admitted_processes:
            if admitted_process.name == process.name:
                raise RuntimeError(f"Process already admitted: '{process.name}'")

        self._admitted_processes.append(process)
        process.status = "ready"
        process.admission_time = time
        self._high_level_queue.enqueue(process)

    def unblock(self, process_name: str) -> None:
        for index, blocked_process in enumerate(self._blocked_processes):
            if blocked_process.name == process_name:
                process = self._blocked_processes.pop(index)
                process.status = "ready"
                self._high_level_queue.enqueue(process)
                return

        raise RuntimeError(f"Process not in the blocked list: '{process_name}'")

    def has_pending_processes(self) -> bool:
        for process in self._admitted_processes:
            if process.status != "finished":
                return True
        return False

    def print_final_report(self) -> None:
        print("\n=== RELATÓRIO FINAL ===")
        print("\nDiagrama de Gantt:")

        if not self._cpu_timeline:
            print("  Nenhuma UT simulada.")
        else:
            times = []
            cpu = []
            levels = []
            for time, process in enumerate(self._cpu_timeline):
                name = process.name if process is not None else "Ociosa"
                level = self._level_timeline[time]
                queue = "-" if level is None else ("0" if level == "high" else "1")
                width = max(len(str(time)), len(name))
                times.append(f"{time:>{width}}")
                cpu.append(f"{name:>{width}}")
                levels.append(f"{queue:>{width}}")

            print("  UT   | " + " | ".join(times))
            print("  CPU  | " + " | ".join(cpu))
            print("  Fila | " + " | ".join(levels))

        if not self._admitted_processes:
            print("\n  Nenhum processo admitido.")
            return

        print("\nEstatísticas por processo (UT):")
        total_turnaround = 0
        total_waiting = 0
        for process in self._admitted_processes:
            # O processo sai do sistema ao fim da UT em que executa o halt.
            turnaround = process.finish_time + 1 - process.admission_time
            waiting = process.dwell_time["ready"]
            total_turnaround += turnaround
            total_waiting += waiting
            print(
                f"  {process.name}: Turnaround = {turnaround} | "
                f"CPU = {process.dwell_time['executing']} | "
                f"Bloqueado = {process.dwell_time['blocked']} | Espera = {waiting}"
            )

        count = len(self._admitted_processes)
        print(f"\n  Turnaround médio: {total_turnaround / count:.2f} UT")
        print(f"  Tempo médio de espera: {total_waiting / count:.2f} UT")

    def run(self, time: int) -> None:
        executed = self._run_high_level_queue(time)
        if executed is False:
            self._run_low_level_queue(time)
