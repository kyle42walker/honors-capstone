import tkinter as tk
from tkinter import ttk


class Application(ttk.Frame):

    ''' The main GUI frame '''

    def __init__(self, master):
        tk.Frame.__init__(self, master, padx=5, pady=5)
        self.mainloop = master.mainloop
        # self.arduino = ArduinoPort()
        
        self.create_panels()
        self.grid()

    def create_panels(self):
        pnl_mode_select_simple = Panel_Mode_Select_Simple(self, padx=50, pady=50)
        pnl_mode_select_advanced = Panel_Mode_Select_Advanced(self, padx=50, pady=50)


        pnl_mode_select_simple.grid(row=0, column=0)
        pnl_mode_select_advanced.grid(row=0, column=1)


class Panel_Mode_Select_Simple(tk.LabelFrame):

    ''' Simplified Mode Selection Panel '''

    def __init__(self, master, **kwargs):
        tk.LabelFrame.__init__(self, master, text='Mode Select', **kwargs)
        self.modes = [
            'Automatic',
            'Stop',
            'Manual',
            'Mute',
        ]
        self.mode_selection = tk.StringVar(self)
        self.create_widgets()
        self.mode_updated()

    def create_widgets(self):
        tk.Label(self, text='Mode:').grid(row=0, column=0, sticky='E')
        mode_selector = ttk.OptionMenu(
            self,
            self.mode_selection,
            self.modes[0],
            *self.modes,
            command=self.mode_updated
        )
        mode_selector.config(width=10)
        mode_selector.grid(row=0, column=1, sticky='E')

    def mode_updated(self, *args):
        print(self.mode_selection.get())
        # TODO: Send command to Arduino


class Panel_Mode_Select_Advanced(tk.LabelFrame):

    ''' Advanced Mode Selection Panel '''

    def __init__(self, master, **kwargs):
        tk.LabelFrame.__init__(self, master, text='Advanced', **kwargs)
        self.create_widgets()
        self.mode_updated()

    # def create_widgets(self):
    #     tk.Label(self, text='Mode Sel:').grid(row=0, column=0, sticky='E')
    #     mode_selector = ttk.OptionMenu(
    #         self,
    #         self.mode_selection,
    #         self.modes[0],
    #         *self.modes,
    #         command=self.mode_updated
    #     )
    #     mode_selector.config(width=10)
    #     mode_selector.grid(row=0, column=1, sticky='E')

    # def mode_updated(self, *args):
    #     print(self.mode_selection.get())
    #     # TODO: Send command to Arduino


def main():
    root = tk.Tk()
    root.title('Safety I/O Tester')
    # root.iconphoto(False, tk.PhotoImage(file='Resource/Images/brooks_logo.png'))

    app = Application(root)
    app.mainloop()

if __name__ == '__main__': main()