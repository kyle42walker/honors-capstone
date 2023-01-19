import tkinter as tk


class Application(tk.Frame):

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

    def __init__(self, master=None, **kwargs):
        tk.LabelFrame.__init__(self, master, text='Mode Select', **kwargs)
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Mode:").grid(row=0, column=0, sticky="E")
        

def main():
    root = tk.Tk()
    root.title("Safety I/O Tester")
    root.iconphoto(False, tk.PhotoImage(file='Resource/Images/brooks_logo.png'))

    app = Application(root)
    app.mainloop()

if __name__ == '__main__': main()