from typing import List

from int_handlers import read_option, read_positive_int
from process import Process, ProcessBlockedForInput, ProcessBlockedForOutput, ProcessHalted
from programs.program_parser import ProgramParser
from scheduler import Scheduler


# TODO (item 4 do enunciado): criar 2 casos de teste próprios do grupo em programs/ e detalhar a
# simulação dos dois no manual do usuário (PDF). Os programas P1 e P2 são os de VALIDAÇÃO fornecidos
# pelo professor no item 5 e não contam como casos do grupo.
#
# Convenção de nome do arquivo: NOME-PRIOn-descricao.txt, onde NOME vira o nome do processo e n é a
# prioridade estática de 1 a 5 (ver ProgramParser._parse_filename). Lembrar que, no enunciado, MAIOR
# valor = MAIOR prioridade na Fila 1 (o contrário do 'nice' do Unix).
#
# Atenção ao rodar: ProgramParser.parse() carrega TODOS os .txt de programs/, em ordem alfabética.
# Assim que os 2 casos novos forem adicionados, toda execução vai carregar 4 processos e pedir o
# instante de carga de cada um. Para reproduzir o teste do professor isolado (só P1 e P2), tirar
# temporariamente os arquivos do grupo da pasta.
#
# O que P1 e P2 NÃO exercitam e que os 2 casos do grupo deveriam cobrir:
#   - preempção de um processo da Fila 1 por outro chegando na Fila 0 (por admissão e por retorno
#     de I/O), incluindo a retomada com o quantum restante;
#   - o caso em que, durante a preempção, um processo de prioridade MAIOR entra na Fila 1: ele passa
#     na frente do preemptado e recebe quantum novo, e o preemptado perde o tempo restante;
#   - estouro do quantum de 4 UTs da Fila 1, com retorno ao fim do próprio grupo de prioridade;
#   - empate de prioridade na Fila 1, para mostrar o desempate FIFO;
#   - SYSCALL 2 (leitura via teclado), que nenhum dos dois programas do professor usa;
#   - instruções não exercitadas por P1/P2: MULT, DIV, BRZERO, BRNEG, BRANY e imediato negativo.
#
# Como são só 2 casos, vale agrupar: um caso focado na Fila 1 (3 processos, prioridades 5/3/3, todos
# chegando em t=0, para mostrar ordenação por prioridade + desempate FIFO + estouro do quantum 4) e
# outro focado em preempção (1 processo longo de prioridade baixa começando em t=0 e outro de
# prioridade alta chegando no meio da execução dele, com SYSCALL 2 em algum ponto).
#
# A ordem de trabalho que funciona: primeiro escrever os dois programas, depois rodar a simulação e
# só então montar a linha do tempo UT a UT para o manual. Não dá para escrever a linha do tempo antes
# e conferir depois — qualquer instrução a mais ou a menos desloca todo o resto do escalonamento.
#
# O outro requisito do item 4 é o manual explicar como compilar e executar. Pontos a cobrir:
#   - Não há compilação: é Python interpretado, sem dependências externas. Requer Python 3.9 ou
#     superior (as anotações do tipo dict[int, List[Process]] em corpo de método são avaliadas em
#     tempo de execução e só passaram a ser válidas no 3.9).
#   - Comando: python3 mlfq_simulator_app.py. Pode ser chamado de qualquer diretório passando o
#     caminho do arquivo, sem precisar de cd: o Python coloca a pasta do script no sys.path e o
#     ProgramParser resolve a pasta programs/ a partir de __file__, não do diretório atual.
#   - Os programas em assembly hipotético precisam estar dentro de programs/, com extensão .txt e
#     nome no padrão NOME-PRIOn-descricao.txt. Não existe opção de linha de comando para apontar um
#     arquivo avulso nem para escolher quais carregar: parse() lê TODOS os .txt da pasta, em ordem
#     alfabética, e cria um processo para cada um. Para simular só um subconjunto, tirar os demais
#     da pasta. A ordem alfabética também define a ordem em que o simulador pergunta os instantes
#     de carga.
#   - O que o programa pergunta, nessa ordem: o modo de avanço do tempo (1 = automático, 2 = manual,
#     que espera um ENTER a cada UT) e, em seguida, o instante de carga de cada processo carregado.
#   - Explicar por que nome e prioridade NÃO são perguntados: eles vêm da convenção de nome do
#     arquivo. O enunciado lista nome, instante de carga, prioridade e arquivo como parâmetros de
#     entrada, mas aceita que a carga seja feita "via arquivo de configuração", que é o papel que a
#     convenção de nome cumpre aqui. Deixar isso escrito no manual para não parecer omissão.


class MLFQSimulator:
    IO_BLOCK_DURATION = 3

    def __init__(self, automatic_stepping: bool):
        self._automatic_stepping: bool = automatic_stepping
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

    def _tick(self) -> None:
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

    def schedule_arrival(self, process: Process, arrival_time: int) -> None:
        if self._arrivals.get(arrival_time) is None:
            self._arrivals[arrival_time] = []

        self._arrivals[arrival_time].append(process)

    def run(self) -> None:
        while self._arrivals or self._scheduler.has_pending_processes():
            if self._automatic_stepping is False:
                input(f"[UT {self._time}] Pressione ENTER para avançar: ")

            self._tick()

        self._scheduler.print_final_report()

def main() -> None:
    print("=== EXECUTANDO SIMULAÇÃO ===")

    program_parser = ProgramParser()

    try:
        processes = program_parser.parse()
    except ValueError as error:
        print(f"Erro ao carregar os programas: {error}")
        return

    stepping = read_option("Avanço do tempo: [1] automático | [2] manual: ", [1, 2])

    simulator = MLFQSimulator(stepping == 1)

    for process in processes:
        print(f"[{process.name}] Prioridade: {process.priority} | Memória: {process.memory_size} posições")
        arrival_time = read_positive_int(f"[{process.name}] Instante de carga (arrival time): ")
        simulator.schedule_arrival(process, arrival_time)

    try:
        simulator.run()
    except (ValueError, RuntimeError) as error:
        print(f"Erro de execução: {error}")

if __name__ == "__main__":
    main()
