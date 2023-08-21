import time
import pyautogui
from pynput import mouse


class MouseDataMiner:
    """
    Esse código não consegue extrair informações do mouse quando ele está parado e nenhuma ação acontece.
    Isso ainda precisa ser corrigido para que o código possa ser usado.
    """
    mouse_x = int
    mouse_y = int
    press_click_x = int
    press_click_y = int
    release_click_x = int
    release_click_y = int
    time = float

    @staticmethod
    def filter_click_str(mouse_event):
        """
        Para extrair informações como click do mouse ou posição do curosr utilizamos funções prontas.
        As funções utilizadas são da biblioteca Events (.Click) e pyautogui.
        O problema é que essas funções devolvem um resultado no formato 'Point(x=1000, y=500)'.
        Esse formato tem seu tipo próprio, ex: "mouse.Events.Click", porém pode ser convertido para str.
        Essa função converte os resultados para str, remove caracteres desnecessários e devolve o resultado em int.
        :return: Posição do evento do click em int(x, y);
                 Qual dos botões do mouse foi pressionado em str;
                 Se o botão está pressionado ou não em bool.
        """
        mouse_event = str(mouse_event).replace('Click', '').replace('pressed=', '').replace('(', '').replace(')', '')
        mouse_event = mouse_event.replace('x=', '').replace('y=', '').replace('button=Button.', '')
        clcik_event_x, click_event_y, button, pressed = mouse_event.split(',')
        clcik_event_x, click_event_y = int(clcik_event_x), int(click_event_y)
        pressed = pressed.replace(' ', '')
        return clcik_event_x, click_event_y, button, pressed

    @staticmethod
    def filter_pos_str(mouse_position):
        """
        Para extrair informações como click do mouse ou posição do curosr utilizamos funções prontas.
        As funções utilizadas são da biblioteca Events (.Click) e pyautogui.
        O problema é que essas funções devolvem um resultado no formato 'Point(x=1000, y=500)'.
        Esse formato tem seu tipo próprio, ex: "mouse.Events.Click", porém pode ser convertido para str.
        Essa função converte os resultados para str, remove caracteres desnecessários e devolve o resultado em int.
        :return: Posição do mouse no tipo int.
        """
        mouse_position = str(mouse_position).replace('Point', '')
        mouse_position = mouse_position.replace('x=', '').replace('y=', '').replace('(', '').replace(')', '')
        pos_x, _, pos_y = mouse_position.partition(',')
        pos_x, pos_y = int(pos_x), int(pos_y)
        return pos_x, pos_y

    def mining_loop(self):
        """
        Esse loop pode ter ficado longo demais.
        Basicamente chama as funções e organiza sequência de execução em loop"
        """
        while True:
            with mouse.Events() as events:
                # Block at most one second
                event = events.get(10)
                if type(event) == mouse.Events.Click:
                    # Click position and information
                    click_ev_x, click_ev_y, button_click, pressed = self.filter_click_str(event)
                    if pressed == 'True':
                        self.press_click_x, self.press_click_y = click_ev_x, click_ev_y
                        print('Click at:', self.press_click_x, self.press_click_y)
                    elif pressed == 'False':
                        self.release_click_x, self.release_click_y = click_ev_x, click_ev_y
                        print('Release click at:', self.release_click_x, self.release_click_y)
                    # Mouse position
                    brute_position_mouse = pyautogui.position()
                    self.mouse_x, self.mouse_y = self.filter_pos_str(brute_position_mouse)
                    print("Mouse position:", self.mouse_x, self.mouse_y)
                else:
                    # Mouse position
                    brute_position_mouse = pyautogui.position()
                    self.mouse_x, self.mouse_y = self.filter_pos_str(brute_position_mouse)
                    print("Mouse position:", self.mouse_x, self.mouse_y)


mouse_data = MouseDataMiner()
mouse_data.mining_loop()





