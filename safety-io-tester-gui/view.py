import tkinter as tk
from tkinter import ttk
from typing import Protocol
from abc import ABC, abstractmethod


TITLE = 'Safety I/O Tester'
BROOKS_LOGO_PATH = 'Resource/Images/brooks_logo.png'


class Presenter(Protocol):
    # def get_output_pin_states(self) -> None:
    #     ...

    def set_mode(self, mode: str) -> None:
        ...

    def toggle_mode_bit(self, bit_id: str) -> None:
        ...
        
    def trigger_e_stop(self, trigger_selection: str, delay_ms: str) -> None:
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

        # TODO: use tk.after() function to start polling controller state
        # -- The polling function will call tk.after() at the end to repeat


class Interactive_Frame(ttk.Frame):

    ''' GUI frame containing all user-interactive widgets '''

    def __init__(self, parent, presenter, **kwargs) -> None:
        super().__init__(parent, **kwargs)
        self.presenter = presenter
        self.create_panels()


    def create_panels(self) -> None:
        grid_row = tk.IntVar(self, 0)
        self.pnl_mode_select = Mode_Selection_Panel(self, self.presenter, grid_row=grid_row)
        self.pnl_emergency_stop = Emergency_Stop_Panel(self, self.presenter, grid_row=grid_row)

        ttk.Separator(self, orient='vertical').grid(row=0, column=1, rowspan=grid_row.get() + 1, sticky='NS')


class Interactive_Split_Panel(ABC):

    ''' ABC for left-right split interactive panels '''

    def __init__(self, parent, presenter, grid_row):
        self.presenter = presenter

        padx = 10
        pady = 10

        frm_left = ttk.Frame(parent)
        frm_left.grid(row=grid_row.get(), column=0, padx=padx, pady=pady)
        frm_right = ttk.Frame(parent)
        frm_right.grid(row=grid_row.get(), column=2, padx=padx, pady=pady)
        grid_row.set(grid_row.get() + 1)

        ttk.Separator(parent, orient='horizontal').grid(row=grid_row.get(), column=0, columnspan=3, sticky='EW')
        grid_row.set(grid_row.get() + 1)

        self.create_left_widgets(frm_left)
        self.create_right_widgets(frm_right)


    @abstractmethod
    def create_left_widgets(self, frame):
        pass


    @abstractmethod
    def create_right_widgets(self, frame):
        pass


class Mode_Selection_Panel(Interactive_Split_Panel):

    ''' Mode selection controls '''

    def __init__(self, parent, presenter, grid_row):
        super().__init__(parent, presenter, grid_row)


    def create_left_widgets(self, frame):
        # Mode selection via dropdown menu
        lbl_mode = ttk.Label(frame, text='Mode:')
        lbl_mode.grid(row=0, column=0, sticky='NW')

        self.valid_modes = [
            'Automatic',
            'Stop',
            'Manual',
            'Mute',
        ]
        self.mode_selection = tk.StringVar(frame)

        self.opt_mode_dropdown = ttk.OptionMenu(
            frame,
            self.mode_selection,
            self.valid_modes[0],
            *self.valid_modes,
            command=self.presenter.set_mode
        )
        self.opt_mode_dropdown.config(width=10)
        self.opt_mode_dropdown.grid(row=1, column=0)
        self.presenter.set_mode(self.valid_modes[0])


    def create_right_widgets(self, frame):
        # Advanced bit toggling to set mode
        self.bit_toggling_enabled = tk.BooleanVar(frame)

        chk_mode_bit_toggle = ttk.Checkbutton(
            frame,
            text='Enable Mode Bit Toggling',
            variable=self.bit_toggling_enabled,
            command=self.chk_mode_bit_toggled
        )
        chk_mode_bit_toggle.grid(row=0, column=0, columnspan=4)

        # Buttons to toggle mode bits (A1, A2, B1, B2)
        self.btn_a1_mode_bit = ttk.Button(
            frame,
            text = 'A1',
            command = lambda: self.presenter.toggle_mode_bit('A1')
        )
        self.btn_a1_mode_bit.grid(row=1, column=0)
        
        self.btn_a2_mode_bit = ttk.Button(
            frame,
            text = 'A2',
            command = lambda: self.presenter.toggle_mode_bit('A2')
        )
        self.btn_a2_mode_bit.grid(row=1, column=1)
        
        self.btn_b1_mode_bit = ttk.Button(
            frame,
            text = 'B1',
            command = lambda: self.presenter.toggle_mode_bit('B1')
        )
        self.btn_b1_mode_bit.grid(row=1, column=2)
        
        self.btn_b2_mode_bit =  ttk.Button(
            frame,
            text = 'B2',
            command = lambda: self.presenter.toggle_mode_bit('B2')
        )
        self.btn_b2_mode_bit.grid(row=1, column=3)

        # Set initial button states
        self.chk_mode_bit_toggled()


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


class Emergency_Stop_Panel(Interactive_Split_Panel):

    ''' Emergency stop controls '''

    def __init__(self, parent, presenter, grid_row):
        super().__init__(parent, presenter, grid_row)


    def create_left_widgets(self, frame):
        lbl_e_stop = ttk.Label(frame, text='E-Stop:')
        lbl_e_stop.grid(row=0, column=0, sticky='NW')
        
        # TODO: Use image (big red circle/polygon) for e-stop button
        self.btn_e_stop = ttk.Button(
            frame,
            text='E-Stop',
            command=lambda: self.presenter.trigger_e_stop(
                self.e_stop_trigger_selection.get(), 
                self.e_stop_delay_ms.get()
            )
        )
        self.btn_e_stop.grid(row=1, column=0)


    def create_right_widgets(self, frame):
        self.dual_channel_trigger_states = [
            'A and B on simultaneously',
            'A on after B by [Delay] ms',
            'B on after A by [Delay] ms',
            'A on and B off',
            'B on and A off',
        ]
        self.e_stop_trigger_selection = tk.StringVar(frame)

        self.opt_e_stop_dropdown = ttk.OptionMenu(
            frame,
            self.e_stop_trigger_selection,
            self.dual_channel_trigger_states[0],
            *self.dual_channel_trigger_states,
            command=self.toggle_delay_entry_state,
        )
        self.opt_e_stop_dropdown.config(width=25)
        self.opt_e_stop_dropdown.grid(row=0, column=0, columnspan=3)

        self.e_stop_delay_ms = tk.StringVar(frame, '')

        ttk.Label(frame, text='Delay: ').grid(row=1, column=0, sticky='E')

        vcmd = (frame.register(self.validate_delay_entry), '%P')
        self.ent_e_stop_delay = ttk.Entry(
            frame,
            width=2,
            justify='right',
            textvariable=self.e_stop_delay_ms,
            state=tk.DISABLED,
            validate='key',
            validatecommand=vcmd
        )
        self.ent_e_stop_delay.grid(row=1, column=1, sticky='EW')

        ttk.Label(frame, text='ms').grid(row=1, column=2, sticky='W')


    def toggle_delay_entry_state(self, trigger_selection: str):
        if 'ms' in trigger_selection:
            self.e_stop_delay_ms.set('0')
            self.ent_e_stop_delay['state'] = tk.NORMAL
            self.ent_e_stop_delay.selection_range(0, tk.END)
            self.ent_e_stop_delay.icursor('end')
            self.ent_e_stop_delay.focus_set()
        else:
            self.e_stop_delay_ms.set('')
            self.ent_e_stop_delay['state'] = tk.DISABLED


    def validate_delay_entry(self, value: str):
        if value:
            try:
                int(value)
                return True
            except ValueError:
                return False
        return True
