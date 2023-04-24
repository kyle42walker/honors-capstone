"""
File: main.py
Author: Kyle Walker
Date: 2023-04-24

This file is the entry point for the Safety IO Tester GUI application.
"""

from model import Model
from view import View
from presenter import Presenter


def main():
    model = Model()
    view = View()
    presenter = Presenter(model, view)
    presenter.run()


if __name__ == "__main__":
    main()
