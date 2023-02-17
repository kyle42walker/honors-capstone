import tkinter as tk
from tkinter import ttk
from typing import Protocol


TITLE = 'Safety I/O Tester'
BROOKS_LOGO_PATH = 'Resource/Images/brooks_logo.png'


class Presenter(Protocol):
    def get_output_pin_states(self) -> None:
        ...

    def set_mode(self, mode: str) -> None:
        ...

    def toggle_mode_bit(self, bit: str) -> None:
        ...


class View(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(TITLE)
        self.iconphoto(False, tk.PhotoImage(file=BROOKS_LOGO_PATH))


    def init_gui(self, presenter: Presenter) -> None:
        self.frm_interactive = Interactive_Frame(self, presenter)
        # self.frm_display = Display_Panel(self, presenter)
        # self.frm_log = Log_Panel(self, presenter)

        self.frm_interactive.grid(row=0, column=0)
        # self.frm_display.grid(row=0, column=1)
        # self.frm_log.grid(row=1, column=0, columnspan=2)


class Interactive_Frame(ttk.Frame):

    ''' GUI frame containing all user-interactive widgets '''

    def __init__(self, parent, presenter, **kwargs) -> None:
        super().__init__(parent, **kwargs)
        self.presenter = presenter
        self.create_panels()


    def create_panels(self) -> None:
        self.grid_row = tk.IntVar(self, 0)
        self.pnl_mode_select = Mode_Selection_Panel(self, self.presenter, self.grid_row)
        self.pnl_emergency_stop = Emergency_Stop_Panel(self, self.presenter, self.grid_row)

        ttk.Separator(self, orient='vertical').grid(row=0, column=2, rowspan=self.grid_row.get()+1, sticky='NS')


    def increment_grid_row(self):
        self.grid_row.set(self.grid_row.get() + 1)


class Mode_Selection_Panel():

    ''' Mode selection controls '''

    def __init__(self, frame, presenter, grid_row):
        self.presenter = presenter
        self.grid_row = grid_row
        self.frame = frame

        self.modes = [
            'Automatic',
            'Stop',
            'Manual',
            'Mute',
        ]
        self.mode_selection = tk.StringVar(self.frame)

        self.bit_toggling_enabled = tk.BooleanVar(self.frame)

        self.create_widgets()


    def create_widgets(self):
        # Mode selection via dropdown menu
        lbl_mode = ttk.Label(self.frame, text='Mode:')
        lbl_mode.grid(row=self.grid_row.get(), column=0, sticky='E')

        self.opt_mode_dropdown = ttk.OptionMenu(
            self.frame,
            self.mode_selection,
            self.modes[0],
            *self.modes,
            command=self.presenter.set_mode
        )
        self.opt_mode_dropdown.config(width=10)
        self.opt_mode_dropdown.grid(row=self.grid_row.get(), column=1, sticky='E')
        self.presenter.set_mode(self.modes[0])

        # Advanced bit toggling to set mode
        chk_mode_bit_toggle = ttk.Checkbutton(
            self.frame,
            text='Enable Mode Bit Toggling',
            variable=self.bit_toggling_enabled,
            command=self.chk_mode_bit_toggled
        )
        chk_mode_bit_toggle.grid(row=self.grid_row.get(), column=3, columnspan=4)
        self.frame.increment_grid_row()

        # Buttons to toggle mode bits (A1, A2, B1, B2)
        self.btn_a1_mode_bit = ttk.Button(
            self.frame,
            text = 'A1',
            state = tk.DISABLED,
            command = lambda: self.presenter.toggle_mode_bit('A1')
        )
        self.btn_a1_mode_bit.grid(row=self.grid_row.get(), column=3)
        
        self.btn_a2_mode_bit = ttk.Button(
            self.frame,
            text = 'A2',
            state = tk.DISABLED,
            command = lambda: self.presenter.toggle_mode_bit('A2')
        )
        self.btn_a2_mode_bit.grid(row=self.grid_row.get(), column=4)
        
        self.btn_b1_mode_bit = ttk.Button(
            self.frame,
            text = 'B1',
            state = tk.DISABLED,
            command = lambda: self.presenter.toggle_mode_bit('B1')
        )
        self.btn_b1_mode_bit.grid(row=self.grid_row.get(), column=5)
        
        self.btn_b2_mode_bit =  ttk.Button(
            self.frame,
            text = 'B2',
            state = tk.DISABLED,
            command = lambda: self.presenter.toggle_mode_bit('B2')
        )
        self.btn_b2_mode_bit.grid(row=self.grid_row.get(), column=6)


    def chk_mode_bit_toggled(self):
        if self.bit_toggling_enabled.get():
            self.opt_mode_dropdown['state'] = tk.DISABLED
            self.btn_a1_mode_bit['state'] = tk.NORMAL
            self.btn_a2_mode_bit['state'] = tk.NORMAL
            self.btn_b1_mode_bit['state'] = tk.NORMAL
            self.btn_b2_mode_bit['state'] = tk.NORMAL
        else:
            self.opt_mode_dropdown['state'] = tk.NORMAL
            self.btn_a1_mode_bit['state'] = tk.DISABLED
            self.btn_a2_mode_bit['state'] = tk.DISABLED
            self.btn_b1_mode_bit['state'] = tk.DISABLED
            self.btn_b2_mode_bit['state'] = tk.DISABLED

class Emergency_Stop_Panel():

    ''' Emergency stop controls '''

    def __init__(self, frame, presenter, grid_row):
        self.presenter = presenter
        self.grid_row = grid_row
        self.frame = frame
        self.create_widgets()

    def create_widgets(self):
        pass