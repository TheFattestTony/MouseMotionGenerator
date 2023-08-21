import numpy as np
import pickle
import pandas as pd
import math


class MotionDataBase:
    """
    O objetivo é extrair dados salvos em um arquivo
    e organizá-los para fornecê-los ao MotionGenerator
    """

    def __init__(self, dbsize):
        """
        Inicializa extraindo as informações salvas
        previamente em um documento (.pkl normalmente)
        A motionfile é a inicialização do arquivo .pkl
        que usaremos no futuro. O motiondataset é um array
        com as mesmas dimensões do array armazenado na .pkl
        porém vazio, pronto para receber os dados da pkl file.
        O dbsize é o número de dados abrigados no arquivo,
        no caso do exemplo teste: dbsize = 195
        """
        self.dbsize = dbsize
        self.unidadetempo = 0.25  # Segundos
        self.motionfile = open("motion_file.pkl", "rb")
        self.motiondataset = np.resize(np.array([[]]), (50, 3))
        self.motiondataset = np.expand_dims(self.motiondataset, 0)
        self.eixosdataset = []  # Tabela com listas completas de eixos, incluindo zeros
        self.carregardados()
        # A estrutura de dados final em formato tabela
        self.database = self.iniciadatabase()
        self.preenchedatabase()

    def carregardados(self):
        """
        Carrega os dados da pickle file.
        Joga os dados na motiondataset.
        A estrutura de try e excpet foi escolhida por conta
        de algumas exceções incômodas que podem surgir no
        processo de carregamento dos dados.
        :return: Nada
        """
        try:
            for i in range(0, self.dbsize):
                motiondata = pickle.load(self.motionfile)
                motiondata = np.expand_dims(motiondata, 0)
                self.motiondataset = np.append(self.motiondataset, motiondata, axis=0)
            # Na .pkl teste os dados vieram em 3D, [:, :, 0:2] transforma em 2D
            # Pode ser apagado no futuro com dados real bem filtrados
            self.motiondataset = self.motiondataset[:, :, 0:2]
        except:
            print('Ocorreu um erro durante o carregamento de dados da .pkl file')

    def iniciadatabase(self):
        self.database = pd.DataFrame(columns=['Distancia min', 'Distancia real', 'Foco', 'Tempo mov', 'Eixos'])
        return self.database

    def preenchedatabase(self):
        for movimento in range(0, len(self.motiondataset), 1):  # Percorre a lista de movimentos
            x1, y1 = self.motiondataset[movimento][len(self.motiondataset[movimento]) - 1]
            x2, y2 = self.motiondataset[movimento][0]
            listx, listy = [x1, x2], [y1, y2]
            listx.sort(reverse=True), listy.sort(reverse=True)
            dx, dy = listx[0] - listx[1], listy[0] - listy[1]
            distanciaminima = round(math.sqrt(math.pow(dx, 2) + math.pow(dy, 2)), 3)
            distanciareal = 0
            listaeixos = np.linspace(0, 0, 0, dtype=float)  # Lista com eixos > zero
            listaeixos_ = []  # Lista com todos os eixos incluindo zero
            for fracao in range(0, len(self.motiondataset[movimento]) - 1):  # Percorre as etapas de cada movimento
                ax, ay = self.motiondataset[movimento][fracao]
                bx, by = self.motiondataset[movimento][fracao + 1]
                xlist, ylist = [ax, bx], [ay, by]
                xlist.sort(reverse=True), ylist.sort(reverse=True)
                dx2, dy2 = xlist[0] - xlist[1], ylist[0] - ylist[1]
                distanciamicro = np.array(math.sqrt(math.pow(dx2, 2) + math.pow(dy2, 2)))
                distanciamicro_ = round(math.sqrt(math.pow(dx2, 2) + math.pow(dy2, 2)), 3)
                listaeixos = np.append(listaeixos, distanciamicro)
                listaeixos_.append(distanciamicro_)
                distanciareal = round(distanciareal + distanciamicro, 3)

            self.eixosdataset.append(listaeixos_)
            listaeixos_naozero = np.nonzero(listaeixos)
            elementos_naozero = listaeixos[listaeixos_naozero]
            tempomovendo = len(elementos_naozero)

            for eixo in range(len(elementos_naozero)):  # Tranforma os valores dos eixos em % em relação ao movimento
                try:
                    if distanciareal > 0.001:
                        elementos_naozero[eixo] = round(np.divide(elementos_naozero[eixo], distanciareal), 3)
                    else:
                        pass
                except ZeroDivisionError:
                    "Ocorreu um erro de divisão por zero durante a transformação dos eixos em %"

            if distanciareal > 0:
                foco = round(distanciaminima / distanciareal, 3)
            else:
                foco = round(0, 3)

            self.database.loc[movimento] = distanciaminima, distanciareal, foco, tempomovendo, elementos_naozero
            self.database.sort_values(by='Distancia min', inplace=True)
            self.database.reset_index(drop=True, inplace=True)

    @staticmethod
    def info():
        print("A Distância Mínima é a menor distância entre os pontos inicial e final,"
              "A Distância Real é a distância total que foi de fato percorrida,"
              "Foco é igual a Distância mínima/Distância real,"
              "Tempo Movendo é o número de eixos com valor > 0,"
              "Elementos não zero é uma lista dos eixos diferentes de zero em %")
