import random
import math
import matplotlib.pyplot as plt
import pandas as pd
from FabrikSolver import FabrikSolver2D
from MotionDataBase import MotionDataBase
import pyautogui
from scipy.interpolate import splprep, splev
import numpy as np


class MotionGenerator:
    """
    O objetivo do MotionGenerator é gerar movimentos realistas do mouse
    a partir de coordenadas iniciais e finais. Ele acessa uma base de
    dados de movimentos do cursor presentes na MotionDataBase e com base
    nesses dados ele é capaz de replicar um padrão humano de movimento do
    cursor.
    """
    # todo: se certificar de que os dados gerados da TrackCursor.py
    #  estejam em um formato adequado para rodar com essa classe.
    unidadetempo = 0.000000000008  # 0.00008 segundos
    xi, yi = 0, 0
    xf, yf = 0, 0
    dx = 0  # Distância entre xi e xf
    dy = 0  # Distância entre yi e yf
    distancia_min = 0
    subdb_escolhido = 0
    subdb_estatistica = 0
    focogerado = 0
    drealgerada = 0
    tempoescolhido = 0
    eixosescolhidos = 0
    eixosfinal = 0
    eixostamanhos = 0
    x_solved = 0
    y_solved = 0
    x_final = []
    y_final = []
    coordenadas = []
    coordenadasruido = []
    coordenadasfinal = []  # Com curvas adicionadas
    destinosvalidos = False
    coordenadasvalidas = bool
    coordenadascurvasvalidas = bool

    def __init__(self):
        self.solver = FabrikSolver2D(self.xi, self.yi, marginOfError=0.001)
        self.fontededados = MotionDataBase(195)
        self.database = self.fontededados.database
        self.subdatabases = {}
        self.gera_subdatabases()
        self.preenche_subdatabases()
        self.loop()

    def gera_subdatabases(self):
        """
        Cria várias subdatabases vazias, com base
        em faixas de distâncias mínimas p.ex: 0-100,
        400-500 ... 2100-2200.
        :return: Nada
        """
        self.subdatabases = {
            n: pd.DataFrame(columns=['Distancia min' + str(n * 100) + "-" + str(n * 100 + 100), 'Distancia real',
                                     'Foco', 'Tempo mov', 'Eixos'], data=[])
            for n in range(-1, 22)
        }

    def preenche_subdatabases(self):
        """
        Preenche as subdatabases com os dados
        contidos na Database principal, respeitando
        as faixas de distâncias mínimas.
        :return: Nada
        """
        # todo: até o momento não temos uma database separada para armazenas dados
        #  de eixos e tempo de movimento por faixa de distância mínima ou distânicia
        #  real por falta de dados. Após uma database mais robusta: adicionar essa
        #  diferenciação.
        for subdatabase in range(0, len(self.database)):
            distanciaminima = self.database['Distancia min'][subdatabase]
            indice = math.ceil(distanciaminima / 100)
            distanciareal = self.database["Distancia real"][subdatabase]
            foco = self.database["Foco"][subdatabase]
            tempodemovimento = self.database["Tempo mov"][subdatabase]
            listadeeixos = self.database["Eixos"][subdatabase]
            if indice == 23:
                indice -= 1
            else:
                pass
            self.subdatabases[indice - 1].loc[len(self.subdatabases[indice - 1])] = distanciaminima, distanciareal, foco, tempodemovimento, listadeeixos

    def teste_xyif(self):
        """
        Função usada para debugging do código
        no momento da escrita. Pode ser alterada
        para testar diversos valores iniciais e
        finais.
        :return: Nada
        """
        self.xi = 500
        self.yi = 500
        self.xf = 750
        self.yf = 800

    def solicita_xyif(self):
        """
        Função que pode ser usada para debugging
        com diferentes valores iniciais ou finais.
        Solicita xi,yi,xf e yf digitados em tempo
        real.
        :return: Nada
        """
        self.xi = int(input("Digite x inicial "))
        self.yi = int(input("Digite y inicial "))
        self.xf = int(input("Digite x final "))
        self.yf = int(input("Digite y final "))

    def gera_dxdy(self):
        """
        Calcula as distâncias entre xi e xf
        e yi e yf, para posteriormente o
        gerador de distância mínima gerar
        uma reta entre as coordenadas iniciais
        e finais.
        :return: Nada
        """
        xlista = [self.xi, self.xf]
        ylista = [self.yi, self.yf]
        xlista.sort(reverse=True)
        ylista.sort(reverse=True)
        self.dx = xlista[0] - xlista[1]
        self.dy = ylista[0] - ylista[1]

    def gera_distaciaminima(self):
        """
        Gera uma distãncia mínima entre as
        coordenadas iniciais e finais, ou seja,
        uma linha reta entre esses dois pontos.
        :return: Nada
        """
        self.distancia_min = math.sqrt(math.pow(self.dx, 2) + math.pow(self.dy, 2))

    @staticmethod
    def distanciaminina_static(xi, yi, xf, yf):
        """
        Gera uma distãncia mínima entre as
        coordenadas iniciais e finais, ou seja,
        uma linha reta entre esses dois pontos.
        :return: Nada
        """
        xlista = [xi, xf]
        ylista = [yi, yf]
        xlista.sort(reverse=True)
        ylista.sort(reverse=True)
        dx = xlista[0] - xlista[1]
        dy = ylista[0] - ylista[1]
        reta = math.sqrt(math.pow(dx, 2) + math.pow(dy, 2))
        return reta

    def escolhesubdatabase(self):
        """
        Usa a distância mínima para escolher
        uma subdatabase com dados respectivos
        à distância mínima em questão.
        :return: Nada
        """
        indice = math.ceil(self.distancia_min / 100)
        self.subdb_escolhido = self.subdatabases[indice - 1]

    def estatistica_subdatabase(self):
        """
        Extrai a estatística da subdatabase
        escolhida e armazena em uma variável
        para posteriormente gerar um valor de
        foco que respeite a distribuição do
        foco presente na database.
        :return: Nada
        """
        self.subdb_estatistica = self.subdb_escolhido.describe(include='all')

    @staticmethod
    def gera_numerosaleatorios(media, desvio, valormin, valormax):
        """
        Gera números aleatórios utilizando
        média, desvio padrão, valor mínimo
        e valor máximo.
        :return: O valor aleatório gerado
        """
        results = []
        while len(results) == 0:
            number = random.gauss(media, desvio)
            if valormin <= number <= valormax:
                results.append(number)
        return results[0]

    def gera_focoaleatorio(self):
        """
        Gera um valor de foco com base nas estatísticas
        do foco para o valor de distância no mínima no
        qual o movimento se enquadra utilizando o gerador
        de números aleatórios. Foco varia de 0-1
        :return: Nada
        """
        mediafoco = self.subdb_estatistica["Foco"]["mean"]
        desviofoco = self.subdb_estatistica["Foco"]["std"]
        self.focogerado = self.gera_numerosaleatorios(mediafoco, desviofoco, 0, 1)

    def gera_distanciareal(self):
        """
        Calcula o tamanho (distância real) que o movimento
        sintético terá.
        :return: Nada
        """
        self.drealgerada = self.distancia_min / self.focogerado

    def escolhe_eixos_e_tempo(self):
        """
        Escolhe um padrão de proporção de eixos para
        enquadrar o movimento sintético e ao mesmo tempo
        armazena o tempo do movimento em ut em uma variável.
        :return: Nada
        """
        indiceeixo = random.randint(0, len(self.subdb_escolhido['Eixos']) - 1)
        self.tempoescolhido = self.subdb_escolhido["Tempo mov"][indiceeixo]
        self.eixosescolhidos = self.subdb_escolhido["Eixos"][indiceeixo]
        if self.tempoescolhido == 1.0:
            self.drealgerada = self.distancia_min

    def add_variacaoeixos(self):
        """
        Adiciona variações sutis e aleatórias às proporções
        dos eixos para que uma proporção nunca seja exatamente
        igual a outra.
        :return: Nada
        """
        self.eixosfinal = []
        for eixos in range(0, len(self.eixosescolhidos)):
            self.eixosfinal.append(self.eixosescolhidos[eixos])
        if self.tempoescolhido != 1.0:
            for v in range(0, len(self.eixosfinal) - 1):
                change = random.uniform(-0.15, 0.15)
                total_change = round(self.eixosfinal[v] * change, 4)
                self.eixosfinal[v] += total_change
                value_to_add = round(-(float(total_change / (len(self.eixosfinal) - (v + 1)))), 4)
                for n in range(v + 1, len(self.eixosfinal)):
                    self.eixosfinal[n] = self.eixosfinal[n] + value_to_add
        else:
            pass

    def calcula_tamanhoeixos(self):
        """
        Calcula o tamanho real dos eixos a partir da
        proporção anteriormente definida. Isso é necessário
        porque a proporção foi armazenada na forma de % em
        relação ao tamanho total do movimento.
        :return: Nada
        """
        self.eixostamanhos = []
        for eixos in range(0, len(self.eixosfinal)):
            self.eixostamanhos.append(self.drealgerada * self.eixosfinal[eixos])

    @staticmethod
    def escolha_angulo(escolha):
        if escolha == 0:
            angle = 0
        elif escolha == 1:
            angle = 90
        elif escolha == 2:
            angle = 180
        else:
            angle = 270
        return angle

    def atualiza_solver(self):
        self.solver = FabrikSolver2D(self.xi, self.yi, marginOfError=0.001)

    def gera_trajetorias(self, xf, yf, eixos):
        """
        Adiciona os segmentos gerados ao IK Solver e
        os soluciona para gerar uma trajetória. Adicionei
        variabilidade ao ângulo do primeiro segmento para
        que as trajetórias tenham diferentes concavidades
        e direções.
        :return: Nada
        """
        escolha = random.randint(0, 3)
        angle = self.escolha_angulo(escolha)
        for v in range(0, len(eixos)):
            if v == 0:
                self.solver.addsegment(eixos[v], angle)
            else:
                self.solver.addsegment(eixos[v], 0)
        self.x_solved, self.y_solved = self.solver.compute(xf, yf)
        self.coordenadas = []
        ix, iy = self.solver.basePoint[0], self.solver.basePoint[1]
        self.coordenadas.append([ix, iy])
        for i in range(0, len(self.solver.segments)):
            [x, y] = [self.solver.segments[i].point[0], self.solver.segments[i].point[1]]
            self.coordenadas.append([x, y])

    def verifica_coordenadas(self):
        """
        Verifica se todas as coordenadas do movimento
        gerado estão contidas na tela do computador.
        :return: Nada
        """
        lista = []
        for i in range(0, len(self.solver.segments)):
            lista.append(0 < self.solver.segments[i].point[0] < 2560)
            lista.append(0 < self.solver.segments[i].point[1] < 1080)
        if all(lista):
            self.coordenadasvalidas = True
        else:
            self.coordenadasvalidas = False

    def varifica_destinos(self):
        """
        Verifica se o destino final coincide com o alvo
        determinado previamente em xf e yf. O Solver foi
        configurado para rodar 25 iterações até parar.
        Por conta desse motivo ele pode parar sem ter
        atingido seu destino.
        :return: Nada
        """
        xlista = [self.x_solved, self.xf]
        ylista = [self.y_solved, self.yf]
        xlista.sort(reverse=True)
        ylista.sort(reverse=True)
        xdif = xlista[0] - xlista[1]
        ydif = ylista[0] - ylista[1]
        if xdif <= 0.001 and ydif <= 0.001:
            self.destinosvalidos = True
        else:
            self.destinosvalidos = False

    def gera_trajetoruidoso(self):
        """
        Adiciona ruído à lista final de coordenadas
        após gerar as trajetórias com o IK Solver
        :return: Nada
        """
        distancias = []
        pontosintermediarios = []
        lista_numptsintermediarios = []
        self.coordenadasruido = []
        for i in range(len(self.coordenadas) - 1):
            distancias.clear()
            x1, y1 = self.coordenadas[i]
            x2, y2 = self.coordenadas[i + 1]
            distancia_ab = self.distanciaminina_static(x1, y1, x2, y2)
            distancias.append(distancia_ab)
            num_pontosruidosos = math.floor(distancia_ab/40)
            lista_numptsintermediarios.append(num_pontosruidosos)
            for j in range(num_pontosruidosos):
                while True:
                    magnitude = 100/num_pontosruidosos
                    media = magnitude * (j + 1) / 100
                    coeficiente = self.gera_numerosaleatorios(media=media, desvio=0.15, valormin=0.01, valormax=0.99)
                    x_intermediario = x1 + (x2 - x1) * coeficiente
                    y_intermediario = y1 + (y2 - y1) * coeficiente
                    x_noise, y_noise = x_intermediario * 0.01, y_intermediario * 0.011
                    x_intermediario += random.uniform(-x_noise, x_noise)
                    y_intermediario += random.uniform(-y_noise, y_noise)
                    distanciaatual = self.distanciaminina_static(x_intermediario, y_intermediario, x2, y2)
                    distancias.append(distanciaatual)
                    if distanciaatual == min(distancias):
                        break
                    else:
                        distancias.pop(len(distancias) - 1)
                pontosintermediarios.append([x_intermediario, y_intermediario])
        for i in range(0, len(self.coordenadas)):
            self.coordenadasruido.append(self.coordenadas[i])
            try:
                indice = lista_numptsintermediarios[i]
                self.coordenadasruido += pontosintermediarios[:indice]
                pontosintermediarios = pontosintermediarios[indice:]
            except:
                pass
        lista_numptsintermediarios.clear()

    def gera_curvas(self):
        """
        Utiliza a interpolação de Curvas de Bézier
        para interligar os pontos de forma curva.
        Gera 50 coordenadas adicionais que darão
        aspecto curvo ao movimento. Esse valor pode
        ser modificado.
        :return:
        """
        x = []
        y = []
        n_novos_pontos = 50
        for i in range(0, len(self.coordenadasruido)):
            x.append(self.coordenadasruido[i][0])
            y.append(self.coordenadasruido[i][1])
        tck, u = splprep([x, y])  # Método 1 para interpolação
        u_new = np.linspace(u.min(), u.max(), n_novos_pontos)  # Método 2 para interpolação
        x_new, y_new = splev(u_new, tck)  # Método 3 para interpolação (final)
        for i in range(0, len(x_new)):
            self.coordenadasfinal.append([x_new[i], y_new[i]])
            self.x_final.append(x_new[i])
            self.y_final.append(y_new[i])

    def segunda_verificacao(self):
        """
        Segunda verificação. Verifica se todas as
        coordenadas geradas após a geração de curvas
        situam-se dentro dos limites do monitor.
        :return: Nada
        """
        lista = []
        for i in range(0, len(self.coordenadasfinal)):
            lista.append(0 < self.coordenadasfinal[i][0] < 2560)
            lista.append(0 < self.coordenadasfinal[i][1] < 1080)
        if all(lista):
            self.coordenadascurvasvalidas = True
        else:
            self.coordenadascurvasvalidas = False

    def resumo_coordenadas(self):
        """
        Mostra na tela um resumo das coordenadas finais.
        :return: Nada
        """
        print("Resumo coordenadas: ")
        for i in range(0, len(self.coordenadasfinal)):
            print(self.coordenadasfinal[i])

    def plota_trajetoria(self):
        """
        Plota trajetória usando matplot.
        :return: Mostra o plot na tela.
        """
        plt.plot(self.x_final, self.y_final)
        plt.title("Trajeto final")
        plt.xlabel("Valores de x")
        plt.ylabel("Valores de y")
        plt.ylim(ymin=0, ymax=1080)
        plt.xlim(xmin=0, xmax=2560)
        ax = plt.gca()
        ax.invert_yaxis()
        plt.show()

    def limpa_solver(self):
        """
        Limpa a lista de segmentos do solver para
        que ele possa recomeçar sem dados das últimas
        simulações.
        :return: Nada
        """
        self.solver.segments = []
        self.solver.armLength = 0

    def limpa_coordenadas(self):
        """
        Limpa as listas que abrigam os dados das
        coordenadas para que a próxima trajetória
        possa ser gerada.
        :return: Nada
        """
        self.coordenadas.clear()
        self.coordenadasruido.clear()
        self.coordenadasfinal.clear()
        self.x_final.clear()
        self.y_final.clear()

    def movimenta_cursor(self):
        """
        Movimenta o cursor na tela usando pyautogui.
        :return: Nada
        """
        pyautogui.FAILSAFE = False
        pyautogui.moveTo(self.xi, self.yi, 0.5)
        for i in range(0, len(self.coordenadasfinal)):
            t = self.unidadetempo / 5
            x = self.coordenadasfinal[i][0]
            y = self.coordenadasfinal[i][1]
            pyautogui.moveTo(x, y, t)

    def loop(self):
        """
        Loop de execução.
        :return: Nada
        """
        for i in range(0, 50):
            self.destinosvalidos = False
            self.coordenadasvalidas = False
            while not self.destinosvalidos:
                self.teste_xyif()
                self.gera_dxdy()
                self.gera_distaciaminima()
                self.escolhesubdatabase()
                self.estatistica_subdatabase()
                self.gera_focoaleatorio()
                self.gera_distanciareal()
                self.escolhe_eixos_e_tempo()
                self.add_variacaoeixos()
                self.calcula_tamanhoeixos()
                self.atualiza_solver()
                self.gera_trajetorias(self.xf, self.yf, self.eixostamanhos)
                self.verifica_coordenadas()
                if self.coordenadasvalidas:
                    self.varifica_destinos()
                    if self.destinosvalidos:
                        self.gera_trajetoruidoso()
                        self.gera_curvas()
                        self.segunda_verificacao()
                        if self.coordenadascurvasvalidas:
                            self.resumo_coordenadas()
                            # self.movimenta_cursor()
                            self.plota_trajetoria()
                            self.limpa_solver()
                            self.limpa_coordenadas()
                            break
                        else:
                            self.limpa_solver()
                            self.limpa_coordenadas()
                            pass
                    else:
                        self.limpa_solver()
                        self.limpa_coordenadas()
                        pass
                else:
                    self.limpa_solver()
                    self.limpa_coordenadas()
                    pass


mg = MotionGenerator()
