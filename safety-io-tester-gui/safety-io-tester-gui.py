import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass, field
from typing import List, Callable


class Application(ttk.Frame):

    ''' The main GUI frame '''

    def __init__(self, master):
        tk.Frame.__init__(self, master, padx=5, pady=5)
        self.mainloop = master.mainloop
        # self.arduino = ArduinoPort()
        
        self.create_panels()
        self.grid()

    def create_panels(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        # self.columnconfigure(2, weight=1)
        
        lbl_mode_select = ttk.Label(self, text='Mode Select', relief='groove', borderwidth=2)
        pnl_mode_select_simple = Panel_Mode_Select_Simple(self, relief='groove', borderwidth=2)
        pnl_mode_select_advanced = Panel_Mode_Select_Advanced(self, relief='groove', borderwidth=2)

        lbl_mode_select.grid(row=0, column=0, columnspan=2, sticky='NESW')
        pnl_mode_select_simple.grid(row=1, column=0, sticky='NESW')
        pnl_mode_select_advanced.grid(row=1, column=1, sticky='NESW')


class Panel_Mode_Select_Simple(ttk.Frame):

    ''' Simplified Mode Selection Panel '''

    def __init__(self, master, **kwargs):
        ttk.Frame.__init__(self, master, **kwargs)
        self.modes = [
            'Automatic',
            'Stop',
            'Manual',
            'Mute',
        ]
        self.mode_selection = tk.StringVar(self)
        self.create_widgets()
        self.update_mode()

    def create_widgets(self):
        ttk.Label(self, text='Mode:').grid(row=0, column=0, sticky='E')
        mode_dropdown = ttk.OptionMenu(
            self,
            self.mode_selection,
            self.modes[0],
            *self.modes,
            command=self.update_mode
        )
        mode_dropdown.config(width=10)
        mode_dropdown.grid(row=0, column=1, sticky='E')

    def update_mode(self, *args):
        print(self.mode_selection.get())
        # TODO: Send command to Arduino


class Panel_Mode_Select_Advanced(ttk.Frame):

    ''' Advanced Mode Selection Panel '''

    def __init__(self, master, **kwargs):
        ttk.Frame.__init__(self, master, **kwargs)
        self.bit_toggling_enabled = tk.IntVar(self)
        self.create_widgets()
        # self.mode_updated()

    def create_widgets(self):
        # ttk.Label(self, text='Enable Mode Bit Toggling:').grid(row=0, column=0, sticky='E')
        ttk.Checkbutton(
            self,
            text='Enable Mode Bit Toggling',
            variable=self.bit_toggling_enabled,
            onvalue=1,
            offvalue=0,
        ).grid(row=0, column=1)
        

    # def mode_updated(self, *args):
    #     print(self.mode_selection.get())
    #     # TODO: Send command to Arduino
    

def main():
    root = tk.Tk()
    root.title('Safety I/O Tester')
    root.iconphoto(False, tk.PhotoImage(file='Resource/Images/brooks_logo.png'))

    app = Application(root)
    app.mainloop()

if __name__ == '__main__': main()