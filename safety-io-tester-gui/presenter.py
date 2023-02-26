from __future__ import annotations
from typing import Protocol
from model import Model


class View(Protocol):
    def init_gui(self, presenter: Presenter) -> None:
        ...

    def mainloop(self) -> None:
        ...


class Presenter:
    def __init__(self, model: Model, view: View) -> None:
        self.model = model
        self.view = view

    def set_mode(self, mode: str) -> None:
        print(mode)

    def toggle_mode_bit(self, bit_id: str) -> None:
        print(bit_id + ' toggled')
    
    def trigger_e_stop(self, trigger_selection: str, delay_ms: str):
        print(f'"{trigger_selection}" with delay of {delay_ms} ms')

    def run(self) -> None:
        self.view.init_gui(self)
        self.view.mainloop()