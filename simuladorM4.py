# 1. GERADOR DE NÚMEROS PSEUDOALEATÓRIOS

class GeradorAleatorio:
    def __init__(self, semente):
        # Constantes padrão do método LCG (glibc)
        self.a = 1103515245
        self.c = 12345
        self.M = 2**31
        self.previous = semente

    def next_random(self):
        """
        Baseado na imagem:
        previous = ((a * previous) + c) % M;
        return (double) previous/M;
        """
        self.previous = (self.a * self.previous + self.c) % self.M
        return self.previous / self.M

# 2. SIMULADOR DE EVENTOS DISCRETOS

class FilaSimulador:
    def __init__(self, servidores, capacidade, min_chegada, max_chegada, min_servico, max_servico, semente):
        self.servidores = servidores
        self.capacidade = capacidade
        self.min_chegada = min_chegada
        self.max_chegada = max_chegada
        self.min_servico = min_servico
        self.max_servico = max_servico
        
        # Instancia o gerador baseado no LCG
        self.rng = GeradorAleatorio(semente)
        
        # Variáveis de Estado
        self.tempo_global = 0.0
        self.estado_atual = 0  # Clientes no sistema
        self.perdas = 0
        
        self.tempos_estados = {i: 0.0 for i in range(capacidade + 1)}
        
        self.eventos = []

    def agendar_chegada(self):
        rnd = self.rng.next_random()
        tempo_entre_chegadas = self.min_chegada + (self.max_chegada - self.min_chegada) * rnd
        novo_tempo = self.tempo_global + tempo_entre_chegadas
        self.eventos.append((novo_tempo, 'CHEGADA'))
        self.eventos.sort() # Mantém a lista ordenada pelo tempo (Priority Queue)

    def agendar_saida(self):
        rnd = self.rng.next_random()
        tempo_servico = self.min_servico + (self.max_servico - self.min_servico) * rnd
        novo_tempo = self.tempo_global + tempo_servico
        self.eventos.append((novo_tempo, 'SAIDA'))
        self.eventos.sort()

    def NextEvent(self):
        """Pega o próximo evento da lista."""
        if self.eventos:
            return self.eventos.pop(0)
        return None, None

    def executar(self, limite_eventos=100000, primeira_chegada=None):
        # Passo 1: Agendar a primeira chegada
        if primeira_chegada is not None:
            # Força a primeira chegada no tempo especificado
            self.eventos.append((primeira_chegada, 'CHEGADA'))
        else:
            # Sorteia a primeira chegada normalmente
            self.agendar_chegada()
        
        count = limite_eventos
        
        while count > 0 and len(self.eventos) > 0:
            # evento = NextEvent();
            tempo_evento, tipo_evento = self.NextEvent()
            
            # Coleta de estatísticas (contabiliza o tempo no estado anterior)
            delta_tempo = tempo_evento - self.tempo_global
            self.tempos_estados[self.estado_atual] += delta_tempo
            
            self.tempo_global = tempo_evento
            
            if tipo_evento == 'CHEGADA':
                self.tratar_chegada()
            elif tipo_evento == 'SAIDA':
                self.tratar_saida()
                
            count -= 1

    def tratar_chegada(self):
        self.agendar_chegada()
        
        if self.estado_atual < self.capacidade:
            self.estado_atual += 1
            if self.estado_atual <= self.servidores:
                self.agendar_saida()
        else:
            self.perdas += 1

    def tratar_saida(self):
        self.estado_atual -= 1
        if self.estado_atual >= self.servidores:
            self.agendar_saida()

    def exibir_relatorio(self):
        print(f"Fila: G/G/{self.servidores}/{self.capacidade}")
        print("-" * 40)
        print("Estado |   Tempo Total   | Probabilidade")
        
        tempo_total = sum(self.tempos_estados.values())
        
        for estado in range(self.capacidade + 1):
            tempo = self.tempos_estados[estado]
            probabilidade = (tempo / tempo_total) * 100 if tempo_total > 0 else 0
            print(f"  {estado}    | {tempo:15.4f} |  {probabilidade:7.2f}%")
            
        print("-" * 40)
        print(f"Número de perdas: {self.perdas}")
        print(f"Tempo total de simulação: {self.tempo_global:.4f}")
        print("="*40)


# 3. EXECUÇÃO

if __name__ == "__main__":
    # Configuração da Fila
    simulador = FilaSimulador(
        servidores=2,
        capacidade=5,
        min_chegada=2.0,
        max_chegada=5.0,
        min_servico=3.0,
        max_servico=5.0,
        semente=42 
    )

    # Executa a simulação para 100.000 eventos, forçando o primeiro a chegar no instante 2.0
    simulador.executar(limite_eventos=100000, primeira_chegada=2.0)
    
    # Imprime os resultados
    simulador.exibir_relatorio()
