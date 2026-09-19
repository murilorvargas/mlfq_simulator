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
        # TODO (saída por UT — item 3 do enunciado): imprimir o monitoramento de uma unidade de tempo.
        #
        # Quando este método é chamado: uma unica vez por UT, a partir de _report_time_unit(), ANTES de
        # a instrução daquela UT ser executada. Ele também é chamado nas UTs ociosas (CPU parada, com
        # todos os processos bloqueados) e, nesse caso, self._executing_process é None.
        #
        # O enunciado pede três coisas a cada UT:
        #   1. Estado atual de cada processo (Pronto / Executando / Bloqueado / Finalizado): percorrer
        #      self._admitted_processes e ler process.status. Os valores internos são "ready",
        #      "executing", "blocked" e "finished" — traduzir na hora de imprimir.
        #   2. Ocupação da CPU (Diagrama de Gantt textual): imprimir a UT atual (parâmetro time) e quem
        #      está na CPU (self._executing_process). Aqui basta a linha da UT corrente; o diagrama
        #      completo é montado no fim por print_final_report().
        #   3. Conteúdo da Fila 0, da Fila 1 e da lista de bloqueados: self._high_level_queue.processes,
        #      self._low_level_queue.processes e self._blocked_processes. São listas de Process já na
        #      ordem de atendimento, então basta imprimir na ordem em que estão.
        #
        # Atenção: o processo que está na CPU JÁ FOI removido da sua fila, logo ele não aparece em
        # nenhuma das três listas acima. Imprimir self._executing_process separadamente.
        #
        # Sugestão: mostrar a prioridade junto do nome na Fila 1 (ex: "P2(prio 5), P1(prio 3)"), porque
        # a ordenação dela só faz sentido com esse dado à vista. A convenção do enunciado é MAIOR valor
        # = MAIOR prioridade (prioridade 5 passa na frente da 3), o contrário do 'nice' do Unix — sem
        # isso explícito a fila parece fora de ordem. Também ajuda imprimir self._executing_level
        # ("high"/"low") e self._quantum, que mostram de qual fila a CPU está sendo servida e qual UT
        # do quantum está sendo consumida.
        ...

    def _report_time_unit(self, time: int) -> None:
        self._track_dwell_time()
        self._cpu_timeline.append(self._executing_process)
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
        # TODO (estatísticas finais — item 3 do enunciado): imprimir o resumo ao fim da simulação.
        #
        # 1. Diagrama de Gantt completo: self._cpu_timeline tem um item por UT já simulada, na ordem
        #    (índice da lista = UT). Cada item é o Process que ocupou a CPU naquela UT, ou None quando
        #    a CPU ficou ociosa (acontece quando todos os processos estão bloqueados em I/O). Algo como:
        #        UT    0  1  2  3  4 ...
        #        CPU  P1 P1 P2 P2 P2 ...
        #    Vale imprimir junto a fila em que cada UT rodou (0 ou 1): sem isso o diagrama fica ambíguo.
        #    Ex.: na UT 2 do teste do professor a CPU está na Fila 0 (P2, que chegou na UT 1), e não na
        #    Fila 1 — o P1 acabou de ser rebaixado e fica esperando, porque enquanto houver processo
        #    pronto na Fila 0 a Fila 1 nem chega a ser consultada, independentemente da prioridade.
        #
        # 2. Turnaround individual = tempo total que o processo passou dentro do sistema, da chegada até
        #    terminar, somando tudo (executando + pronto + bloqueado):
        #        turnaround = process.finish_time + 1 - process.admission_time
        #    admission_time é a UT em que o processo foi admitido; finish_time é a UT em que ele executou
        #    o SYSCALL 0. O "+ 1" existe porque finish_time é o ÍNDICE da UT do halt e o processo ocupa
        #    essa UT por INTEIRO — ele só deixa o sistema no fim dela, ou seja, no instante finish_time+1.
        #    Essa é a única forma que satisfaz a identidade
        #        turnaround == dwell_time["executing"] + dwell_time["ready"] + dwell_time["blocked"]
        #    que vale para todo processo finalizado e serve como conferência do cálculo.
        #    No manual do usuário, apresentar como "instante de saída - instante de chegada" (sem "+ 1"
        #    aparente), explicando que o instante de saída é o FIM da UT do SYSCALL 0. Assim a fórmula
        #    do enunciado (fim - chegada) vale ao pé da letra e não sobra um "+ 1" sem explicação.
        #
        # 3. Tempo de Espera na Fila de Prontos de cada processo = process.dwell_time["ready"], que já
        #    vem MEDIDO UT a UT por _track_dwell_time(). Não recalcular por subtração. O Tempo Médio de
        #    Espera é a média desse valor entre os processos de self._admitted_processes.
        #
        # Valores de referência para conferir (teste do professor: P1 prio 3 chegando em t=0 e P2 prio 5
        # chegando em t=1) — P1: turnaround 12, CPU 5, bloqueado 3, espera 4; P2: turnaround 28, CPU 17,
        # bloqueado 9, espera 2; turnaround médio 20 e espera média 3. A simulação dura 29 UTs (0 a 28).
        # Os números do PDF divergem desses porque a linha do tempo do enunciado executa mais de uma
        # instrução na mesma UT e pula instruções, apesar de o próprio enunciado dizer que cada
        # instrução leva 1 UT. Ex.: o P2 executa 17 instruções (LOAD + 3 voltas do laço de 5 + SYSCALL
        # 0), mas o PDF afirma 8 UTs de CPU para ele; como são ainda 9 UTs bloqueado, o turnaround de
        # 17 UTs que o PDF apresenta é menor que o próprio tempo de CPU + I/O, ou seja, impossível.
        ...

    def run(self, time: int) -> None:
        executed = self._run_high_level_queue(time)
        if executed is False:
            self._run_low_level_queue(time)
