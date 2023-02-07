import tkinter as tk
from tkinter import ttk
from typing import Protocol

class Presenter(Protocol):
    def get_output_pin_states(self) -> None:
        ...

    def update_mode(self, mode: str) -> None:
        ...

    

class Safety_IO_Tester_GUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title('Safety I/O Tester')
        self.iconphoto(False, tk.PhotoImage(file='Resource/Images/brooks_logo.png'))

    def init_ui(self, presenter: Presenter) -> None:
        self.input_panels = ttk.Frame(self, padx=10, pady=10)








class Application(tk.Tk):

    ''' The main GUI frame '''

    def __init__(self, master):
        tk.Frame.__init__(self, master, padx=5, pady=5)
        self.mainloop = master.mainloop
        # self.arduino = ArduinoPort()
        
        self.create_panels()
        self.grid()

    def create_panels(self):
        pnl_mode_select = Panel_Mode_Select(self, padx=50, pady=50)

        pnl_mode_select.grid(row=0, column=0)


class Panel_Mode_Select(tk.LabelFrame):

    '''  '''

    def __init__(self, master, **kwargs):
        tk.LabelFrame.__init__(self, master, text='Mode Select', **kwargs)
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text='Mode:').grid(row=0, column=0, sticky='E')
        ttk.Separator(self, orient='vertical').grid(row=0, column=1, pady=10, ipady=100)
        tk.Label(self, text='Mode:').grid(row=0, column=2, sticky='E')