from typing import List, Literal, Optional, Tuple

from process import Process
from queues import HighLevelQueue, LowLevelQueue


class Scheduler:
    HIGH_QUANTUM = 2
    LOW_QUANTUM = 4

    def __init__(self):
        self._admitted_processes: List[Process] = []
        self._high_level_queue = HighLevelQueue()
        self._low_level_queue = LowLevelQueue()
        self._executing_process: Optional[Process] = None
        self._executing_level: Optional[Literal["high", "low"]] = None
        self._blocked_processes: List[Process] = []
        self._quantum: int = 0
        self._preempted: Optional[Tuple[Process, int]] = None

    def _preempt(self, process_name: str) -> None:
        process = self._executing_process
        if process is not None and process.name == process_name:
            process.status = "ready"
            self._low_level_queue.enqueue_at_group_front(process)
            self._preempted = process, self._quantum
            self._executing_process = None
            return

        raise RuntimeError(f"Process not currently executing: '{process_name}'")

    def _run_high_level_queue(self) -> bool:
        continuing_high = (
            self._executing_process is not None
            and self._executing_level == "high"
        )

        if not continuing_high:
            if not self._high_level_queue.processes:
                return False

            if self._executing_process is not None:
                # A Fila 0 interrompe o processo que estava na Fila 1.
                self._preempt(self._executing_process.name)

            process = self._high_level_queue.dequeue_next()
            self._executing_process = process
            self._executing_level = "high"
            self._quantum = self.HIGH_QUANTUM
            process.status = "executing"

        # TODO: executar exatamente uma instrução com o Interpreter e descontar
        # uma UT de self._quantum, que representa o tempo restante.
        # TODO: tratar finalização e I/O, avançando o pc da syscall corretamente,
        # registrando o término ou agendando o desbloqueio após 3 UTs.
        # TODO: se continuar executável e o quantum acabar, marcar como ready,
        # inserir na Fila 1 e limpar o processo, nível e quantum da CPU.
        # TODO: contabilizar os estados durante a UT usando o relógio de run().
        # True reserva esta UT para a Fila 0; a execução ainda será conectada.
        return True

    def _run_low_level_queue(self) -> None:
        continuing_low = (
            self._executing_process is not None
            and self._executing_level == "low"
        )

        if not continuing_low:
            if not self._low_level_queue.processes:
                return

            process = self._low_level_queue.dequeue_next()
            self._executing_process = process
            self._executing_level = "low"
            process.status = "executing"

            if self._preempted is not None and self._preempted[0] is process:
                self._quantum = self._preempted[1]
                self._preempted = None
            else:
                self._quantum = self.LOW_QUANTUM

            # TODO: guardar quantum interrompido por processo, pois um único
            # _preempted pode ser sobrescrito por outra preempção antes da retomada.

        # TODO: compartilhar com a Fila 0 a execução de uma instrução por chamada,
        # o consumo de uma UT de quantum e o tratamento de finalização e I/O.
        # TODO: se continuar executável e o quantum acabar, marcar como ready,
        # reinserir no final do grupo de prioridade e limpar o estado da CPU.
        # TODO: contabilizar os estados durante a UT usando o relógio de run().

    def admit(self, process: Process, time: int) -> None:
        for admitted_process in self._admitted_processes:
            if admitted_process.name == process.name:
                raise RuntimeError(f"Process already admitted: '{process.name}'")

        self._admitted_processes.append(process)
        process.status = "ready"
        process.admission_time = time
        self._high_level_queue.enqueue(process)

    def block(self, process_name: str) -> None:
        process = self._executing_process
        if process is not None and process.name == process_name:
            process.status = "blocked"
            self._blocked_processes.append(process)
            self._executing_process = None
            return

        raise RuntimeError(f"Process not currently executing: '{process_name}'")

    def unblock(self, process_name: str) -> None:
        for i, p in enumerate(self._blocked_processes):
            if p.name == process_name:
                process = self._blocked_processes.pop(i)
                process.status = "ready"
                self._high_level_queue.enqueue(process)
                return

        raise RuntimeError(f"Process not in the blocked list: '{process_name}'")

    def print_periodic_report(self, time: int) -> None:
        # TODO: imprimir estado de cada processo admitido, a ocupação da CPU (Diagrama de Gantt textual,
        # com base em self._executing_process) e o conteúdo das Filas 0/1 e da lista de bloqueados
        ...

    def print_final_report(self) -> None:
        # TODO: calcular e imprimir Turnaround individual e Tempo Médio de Espera na Fila de Prontos
        ...

    def run(self, time: int) -> None:
        executed = self._run_high_level_queue()
        if executed is False:
            self._run_low_level_queue()
