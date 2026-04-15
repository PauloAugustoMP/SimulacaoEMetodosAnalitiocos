class GeradorAleatorio:
    def __init__(self, semente):
        self.a = 1103515245
        self.c = 12345
        self.M = 2**31
        self.previous = semente
        self.usados = 0

    def next_random(self):
        if self.usados >= 100000:
            return None
        self.previous = (self.a * self.previous + self.c) % self.M
        self.usados += 1
        return self.previous / self.M


class Fila:
    def __init__(self, id_fila, servidores, capacidade, intervalo_servico, intervalo_chegada=None):
        self.id = id_fila
        self.servidores = servidores
        self.capacidade = capacidade
        self.intervalo_chegada = intervalo_chegada
        self.intervalo_servico = intervalo_servico

        self.estado_atual = 0
        self.perdas = 0
        self.tempos_estados = {i: 0.0 for i in range(capacidade + 1)}

    def registrar_tempo_estado(self, delta_tempo):
        self.tempos_estados[self.estado_atual] += delta_tempo


class RedeFilasSimulador:
    def __init__(self, config, semente):
        self.rng = GeradorAleatorio(semente)
        self.tempo_global = 0.0
        self.eventos = []

        self.filas = {}
        for id_fila, dados in config["filas"].items():
            self.filas[id_fila] = Fila(
                id_fila=id_fila,
                servidores=dados["servidores"],
                capacidade=dados["capacidade"],
                intervalo_servico=dados["servico"],
                intervalo_chegada=dados.get("chegada")
            )

        self.roteamento = config["roteamento"]

    def ordenar_eventos(self):
        prioridade = {"SAIDA": 0, "CHEGADA": 1}
        self.eventos.sort(key=lambda e: (e[0], prioridade[e[1]]))

    def agendar_evento(self, tempo, tipo, fila_id):
        self.eventos.append((tempo, tipo, fila_id))
        self.ordenar_eventos()

    def sortear_intervalo(self, minimo, maximo):
        rnd = self.rng.next_random()
        if rnd is None:
            return None
        return minimo + (maximo - minimo) * rnd

    def agendar_chegada_externa(self, fila_id):
        fila = self.filas[fila_id]
        if fila.intervalo_chegada is None:
            return

        intervalo = self.sortear_intervalo(*fila.intervalo_chegada)
        if intervalo is None:
            return

        novo_tempo = self.tempo_global + intervalo
        self.agendar_evento(novo_tempo, "CHEGADA", fila_id)

    def agendar_saida(self, fila_id):
        fila = self.filas[fila_id]

        tempo_servico = self.sortear_intervalo(*fila.intervalo_servico)
        if tempo_servico is None:
            return

        novo_tempo = self.tempo_global + tempo_servico
        self.agendar_evento(novo_tempo, "SAIDA", fila_id)

    def proximo_destino(self, fila_id):
        destinos = self.roteamento.get(fila_id, [])
        if not destinos:
            return None

        rnd = self.rng.next_random()
        if rnd is None:
            return None

        acumulado = 0.0
        for destino, prob in destinos:
            acumulado += prob
            if rnd <= acumulado:
                return destino

        return destinos[-1][0]

    def next_event(self):
        if self.eventos:
            return self.eventos.pop(0)
        return None

    def atualizar_estatisticas(self, novo_tempo):
        delta_tempo = novo_tempo - self.tempo_global
        for fila in self.filas.values():
            fila.registrar_tempo_estado(delta_tempo)
        self.tempo_global = novo_tempo

    def tratar_chegada(self, fila_id, gerar_proxima_externa=False):
        fila = self.filas[fila_id]

        if gerar_proxima_externa:
            self.agendar_chegada_externa(fila_id)

        if fila.estado_atual < fila.capacidade:
            fila.estado_atual += 1
            if fila.estado_atual <= fila.servidores:
                self.agendar_saida(fila_id)
        else:
            fila.perdas += 1

    def tratar_saida(self, fila_id):
        fila = self.filas[fila_id]

        if fila.estado_atual > 0:
            fila.estado_atual -= 1

        if fila.estado_atual >= fila.servidores:
            self.agendar_saida(fila_id)

        destino = self.proximo_destino(fila_id)
        if destino is not None:
            self.agendar_evento(self.tempo_global, "CHEGADA", destino)

    def executar(self, primeira_chegada_fila1=1.5):
        self.agendar_evento(primeira_chegada_fila1, "CHEGADA", 1)

        while self.eventos and self.rng.usados < 100000:
            evento = self.next_event()
            if evento is None:
                break

            tempo_evento, tipo_evento, fila_id = evento
            self.atualizar_estatisticas(tempo_evento)

            if tipo_evento == "CHEGADA":
                gerar_proxima_externa = (
                    fila_id == 1 and self.filas[fila_id].intervalo_chegada is not None
                )
                self.tratar_chegada(fila_id, gerar_proxima_externa=gerar_proxima_externa)

            elif tipo_evento == "SAIDA":
                self.tratar_saida(fila_id)

    def exibir_relatorio(self):
        print("=" * 50)
        print("RELATÓRIO DA REDE DE FILAS")
        print("=" * 50)

        for fila_id in sorted(self.filas.keys()):
            fila = self.filas[fila_id]
            print(f"\nFila {fila_id}: G/G/{fila.servidores}/{fila.capacidade}")
            print("-" * 40)
            print("Estado |   Tempo Total   | Probabilidade")

            tempo_total = sum(fila.tempos_estados.values())

            for estado in range(fila.capacidade + 1):
                tempo = fila.tempos_estados[estado]
                prob = (tempo / tempo_total) * 100 if tempo_total > 0 else 0
                print(f"  {estado}    | {tempo:15.4f} |  {prob:7.2f}%")

            print("-" * 40)
            print(f"Perdas da fila {fila_id}: {fila.perdas}")

        print("\n" + "=" * 50)
        print(f"Tempo global da simulação: {self.tempo_global:.4f}")
        print(f"Quantidade de aleatórios usados: {self.rng.usados}")
        print("=" * 50)


if __name__ == "__main__":
    config = {
        "filas": {
            1: {
                "servidores": 2,
                "capacidade": 3,
                "chegada": (1.0, 4.0),
                "servico": (3.0, 4.0)
            },
            2: {
                "servidores": 1,
                "capacidade": 5,
                "chegada": None,
                "servico": (2.0, 3.0)
            }
        },
        "roteamento": {
            1: [(2, 1.0)],
            2: [(None, 1.0)]
        }
    }

    simulador = RedeFilasSimulador(config=config, semente=42)
    simulador.executar(primeira_chegada_fila1=1.5)
    simulador.exibir_relatorio()
