import cv2
import time
import numpy as np
import serial


class MouseDataMiner:
    prev_frame_time = 0
    color = [0, 0, 0]
    color_clck = [251, 49, 255]
    xx = 0
    yy = 0
    need_to_start_clock = True
    start_time = float
    click_occured = False
    look_full_screen = True
    click_seq = [0, 0]
    click_btn_state = 'relesead'

    def __init__(self):
        self.serial_port = serial.Serial(port='COM6', baudrate=9600)
        self.start_serial()
        capture = cv2.VideoCapture(0 + cv2.CAP_DSHOW)
        capture.set(3, 1900)
        capture.set(4, 1080)
        cv2.namedWindow("Video", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Video", 1920, 1080)
        self.track_cursor(capture)
        self.data = 0
        self.data_set = np.resize(np.array([[]]), (1, 3))

    def start_serial(self):
        time.sleep(2)  # Wait for grbl to initialize
        self.serial_port.flushInput()  # Flush startup text in serial input
        print('Starting click button serial...')

    def get_click(self):
        click_response = self.serial_port.read()
        if click_response:
            if click_response.decode() == '1':
                self.click_occured = True
                self.click_seq.append(1)
                self.click_seq.pop(0)
            elif click_response.decode() == '0':
                self.click_occured = False
                self.click_seq.append(0)
                self.click_seq.pop(0)
        else:
            self.click_occured = False
        self.serial_port.flushInput()
        return self.click_occured

    def update_clk_btn_state(self):
        """
        Retorna o estado do botão do mouse.
        :return: 'relesead', 'release', 'press', 'pressed'
        """
        if self.click_seq == [0, 0]:
            self.click_btn_state = 'relesead'
        elif self.click_seq == [0, 1]:
            self.click_btn_state = 'press'
        elif self.click_seq == [1, 0]:
            self.click_btn_state = 'release'
        elif self.click_seq == [1, 1]:
            self.click_btn_state = 'pressed'
        return self.click_btn_state

    def get_last_coordinates(self):
        last_coordinates = (self.xx, self.yy)
        return last_coordinates

    @staticmethod
    def prepare_screen_frames(capture):
        """
        Prepara as imagens para o TemplateMatching.
        A primeira imagem é a tela do computador, armazenada na variável frame e convertida para grayscale.
        :return: frame, frame_gray
        """
        ret, frame = capture.read()
        frame_gray = None
        if frame is not None:
            frame = cv2.resize(frame, dsize=(1920, 1080))
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            pass

        return frame, frame_gray

    @staticmethod
    def prepare_cursor_frames():
        """
        A segunda e terceira imagem são duas máscaras criadas a partir da imagem do cursor.
        Uma das máscaras é preparada para TemplateMatching em fundo claro e outra em fundo escuro.
        hh e ww são o shape da matrix do cursor e precisam ser retornados para cálculos futuros.
        :return: cursor_mask_bs, cursor_mask_ws, hh, ww
        """
        cursor = cv2.imread('cursor.png', cv2.IMREAD_UNCHANGED)
        hh, ww = cursor.shape[:2]

        # extract template mask as grayscale from alpha channel and make 3 channels
        cursor_mask_bs = cursor[:, :, 2]
        cursor_mask_ws = cursor[:, :, 1]

        return cursor_mask_bs, cursor_mask_ws, hh, ww

    def get_roi_coordinates(self):
        """
        Calcula as coordenadas de uma ROI próxima aos últimos x e y do mouse.
        Otimiza o template matching do opencv.
        :return: Coordenadas da ROI
        """
        xmin, xmax, ymin, ymax = 0, 1920, 0, 1080
        last_x, last_y = self.get_last_coordinates()
        y1 = last_y - 135
        y2 = last_y + 135
        x1 = last_x - 240
        x2 = last_x + 240
        if y1 < ymin:
            while y1 != ymin:
                y1 += 1
                y2 += 1
        if y2 > ymax:
            while y2 != ymax:
                y1 -= 1
                y2 -= 1
        if x1 < ymin:
            while x1 != ymin:
                x1 += 1
                x2 += 1
        if x2 > ymax:
            while x2 != ymax:
                x1 -= 1
                x2 -= 1
        roi_frame_coordinates = x1, x2, y1, y2
        return roi_frame_coordinates

    def estimate_fps(self, frame):
        """
        Estima o FPS.
        Escreve no canto superior esquerdo do vídeo o valor do FPS.
        :return: No momento nada.
        """
        font = cv2.FONT_HERSHEY_SIMPLEX
        new_frame_time = time.time()
        fps = 1 / (new_frame_time - self.prev_frame_time)
        self.prev_frame_time = new_frame_time
        fps = int(fps)
        fps = str(fps)
        cv2.putText(frame, fps, (7, 70), font, 3, (100, 255, 0), 3, cv2.LINE_AA)

    @staticmethod
    def perceive_click(color_actual, color_click):
        color_comparison = color_actual - color_click
        click_occured = False
        if np.all(color_comparison >= -8):
            if np.all(color_comparison <= 8):
                click_occured = True
        elif np.all(color_comparison <= 8):
            if np.all(color_comparison >= -8):
                click_occured = True
        else:
            click_occured = False
        return click_occured

    @staticmethod
    def get_click_coordinates(x, y):
        return x, y

    def click_time_control(self):
        """
        Extrai informações relativas ao click do mouse.
        Inclui posições e tempos.
        :return: por enquanto nada.
        """
        if self.click_btn_state == 'press':
            self.get_click_coordinates(self.xx, self.yy)
            press_time = time.time()
            final_press_time = press_time - self.start_time
            print('Press occured at:', self.xx, self.yy, 'at time:', final_press_time)
        if self.click_btn_state == 'release':
            self.get_click_coordinates(self.xx, self.yy)
            end_time = time.time()
            final_mov_time = end_time - self.start_time
            print('Motion duration was', final_mov_time, "seconds")
            mouse_clk_time = final_mov_time
            print("Click occured at:", self.xx, self.yy, "at time:", mouse_clk_time)
            self.need_to_start_clock = True
            self.click_occured = False

    def cursor_matching(self, capture):
        """
        Lida com toda o processo de template matching do cursor.
        Está demasiadamente grande e redundante, porém funcional.
        :param capture: é a própria imagem que vem da placa de captura.
        :return: frame, para que o código possa usá-lo em sequência.
        """
        if self.need_to_start_clock:
            self.start_time = time.time()
            self.need_to_start_clock = False
        frame, gray_frame = self.prepare_screen_frames(capture)
        cursor_mask_bs, cursor_mask_ws, hh, ww = self.prepare_cursor_frames()
        if not self.look_full_screen:
            x1, x2, y1, y2 = self.get_roi_coordinates()
        else:
            x1, x2, y1, y2 = 0, 1920, 0, 1080
        result = cv2.matchTemplate(gray_frame[y1:y2, x1:x2], cursor_mask_bs, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= 0.70:
            mark_time = time.time()
            self.xx = max_loc[0] + x1
            self.yy = max_loc[1] + y1
            pt1 = (self.xx, self.yy)
            pt2 = (self.xx + ww, self.yy + hh)
            cv2.rectangle(frame, pt1, pt2, (0, 0, 255), 1)
            self.color = frame[self.yy - 10, self.xx]
            actual_time = mark_time - self.start_time
            self.look_full_screen = False
            print(actual_time)
            print(self.xx, self.yy)
        else:
            alt_cursor = cv2.imread("cursor_2.png")
            alt_cursor_gray = cv2.cvtColor(alt_cursor, cv2.COLOR_BGR2GRAY)
            result = cv2.matchTemplate(gray_frame[y1:y2, x1:x2], alt_cursor_gray, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            if max_val >= 0.70:
                mark_time = time.time()
                self.xx = max_loc[0] + x1
                self.yy = max_loc[1] + y1
                pt1 = (self.xx, self.yy)
                pt2 = (self.xx + ww, self.yy + hh)
                cv2.rectangle(frame, pt1, pt2, (0, 0, 255), 1)
                self.color = frame[self.yy - 10, self.xx]
                actual_time = mark_time - self.start_time
                self.look_full_screen = False
                print(actual_time)
                print(self.xx, self.yy)
            else:
                result = cv2.matchTemplate(gray_frame[y1:y2, x1:x2], cursor_mask_ws, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                if max_val >= 0.70:
                    mark_time = time.time()
                    self.xx = max_loc[0] + x1
                    self.yy = max_loc[1] + y1
                    pt1 = (self.xx, self.yy)
                    pt2 = (self.xx + ww, self.yy + hh)
                    cv2.rectangle(frame, pt1, pt2, (0, 0, 255), 1)
                    self.color = frame[self.yy - 10, self.xx]
                    actual_time = mark_time - self.start_time
                    self.look_full_screen = False
                    print(self.xx, self.yy)
                    print(actual_time)
                else:
                    print('nao achei')
                    self.look_full_screen = True
        return frame

    def track_cursor(self, capture):
        """
        Tem como primeiro objetivo organizar o fluxo de execução das funções até então criadas.
        O segundo objetivo é retornar adequadamente as coordenadas atualizadas do cursor na tela do notebook.
        O terceiro objetivo é desenhar um retângulo ao redor do cursor para facilitar vizualização.
        Ao pressionar 'Esc' a execução é interrompida
        :return: nada.
        """
        while 1:
            frame = self.cursor_matching(capture)
            self.get_click()
            self.update_clk_btn_state()
            self.click_time_control()
            self.estimate_fps(frame)
            cv2.imshow("Video", frame)

            k = cv2.waitKey(30) & 0xff
            if k == 27:
                capture.release()
                cv2.destroyAllWindows()
                break


mouse = MouseDataMiner()
