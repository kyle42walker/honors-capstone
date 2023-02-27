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
        print(bit_id + " toggled")

    def trigger_e_stop(self, trigger_selection_index: int, delay_ms: str) -> None:
        match (trigger_selection_index):
            case 0:
                print("both e_stops triggered")
            case 1:
                print(f"e_stop a then b, {delay_ms} ms delay")
            case 2:
                print(f"e_stop b then a, {delay_ms} ms delay")
            case 3:
                print("e_stop a only")
            case 4:
                print("e_stop b only")

    def trigger_interlock(self, trigger_selection_index: int, delay_ms: str) -> None:
        match (trigger_selection_index):
            case 0:
                print("both interlocks triggered")
            case 1:
                print(f"interlock a then b, {delay_ms} ms delay")
            case 2:
                print(f"interlock b then a, {delay_ms} ms delay")
            case 3:
                print("interlock a only")
            case 4:
                print("interlock b only")

    def measure_heartbeat(self) -> None:
        print("measuring heartbeat...")

    def run(self) -> None:
        self.view.init_gui(self)
        self.view.mainloop()
