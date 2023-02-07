from model import Model
from view import Safety_IO_Tester_GUI
from presenter import Presenter

def main():
    model = Model()
    view = Safety_IO_Tester_GUI()
    presenter = Presenter(model, view)
    presenter.run()


if __name__ == '__main__': main()


# https://github.com/ArjanCodes/2022-gui/tree/main/mvp