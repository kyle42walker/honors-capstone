from __future__ import annotations
from typing import Protocol
from model import Model
import logging


POLLING_RATE = 100  # [ms] polling rate for output pin states
logger = logging.getLogger("safety_io_logger")  # logger for all modules


class Model(Protocol):
    def get_output_pin_states(self) -> dict[str, tuple[bool]]:
        ...


class View(Protocol):
    def init_gui(self, presenter: Presenter) -> None:
        ...

    def set_output_pin_indicators(self, pin_states: dict[str, tuple[bool]]) -> None:
        ...

    def log(self, message: str) -> None:
        ...

    def after(self, ms: int, func: callable) -> None:
        ...

    def mainloop(self) -> None:
        ...


class Presenter:
    def __init__(self, model: Model, view: View) -> None:
        self.model = model
        self.view = view

    def set_mode(self, mode: str) -> None:
        logger.debug(f"mode set to {mode}")

    def toggle_mode_bit(self, bit_id: str) -> None:
        logger.debug(f"mode bit {bit_id} toggled")

    def toggle_e_stop(self, trigger_selection_index: int, delay_ms: str) -> None:
        match (trigger_selection_index):
            case 0:
                logger.debug(f"both e_stops triggered")
            case 1:
                logger.debug(f"e_stop a then b, {delay_ms} ms delay")
            case 2:
                logger.debug(f"e_stop b then a, {delay_ms} ms delay")
            case 3:
                logger.debug(f"e_stop a only")
            case 4:
                logger.debug(f"e_stop b only")

    def toggle_interlock(self, trigger_selection_index: int, delay_ms: str) -> None:
        match (trigger_selection_index):
            case 0:
                logger.debug(f"both interlocks triggered")
            case 1:
                logger.debug(f"interlock a then b, {delay_ms} ms delay")
            case 2:
                logger.debug(f"interlock b then a, {delay_ms} ms delay")
            case 3:
                logger.debug(f"interlock a only")
            case 4:
                logger.debug(f"interlock b only")

    def toggle_power(self) -> None:
        logger.debug(f"power toggled")

    def measure_heartbeat(self) -> None:
        logger.debug(f"heartbeat measured")

    def echo_string(self, message: str) -> None:
        logger.debug(f"echo: {message}")

    def run(self) -> None:
        # initialize GUI
        self.view.init_gui(self)

        # start logging
        self.start_logger()

        # connect to saftey IO board
        # self.model.connect_to_arduino()

        # start gui
        self.view.after(POLLING_RATE, self.update_output_pin_indicators)
        self.view.mainloop()

    def update_output_pin_indicators(self) -> None:
        # update indicators in GUI by polling output pin states every POLLING_RATE ms
        self.view.set_output_pin_indicators(self.model.get_output_pin_states())
        self.view.after(POLLING_RATE, self.update_output_pin_indicators)

    def start_logger(self) -> None:
        # configure logger
        logger.setLevel(logging.DEBUG)
        self.log_formatter = logging.Formatter("%(asctime)s - %(message)s")

        # start console logging
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(self.log_formatter)
        logger.addHandler(console_handler)

        # start GUI logging
        gui_handler = Gui_Log_Handler(self.view)
        gui_handler.setLevel(logging.INFO)
        gui_handler.setFormatter(self.log_formatter)
        logger.addHandler(gui_handler)

    def start_logging_to_file(self, file_path: str) -> None:
        logger.info(f"logging started to {file_path}")

        file_handler = logging.FileHandler(file_path, mode="w")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(self.log_formatter)
        logger.addHandler(file_handler)

    def stop_logging_to_file(self) -> None:
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                logger.removeHandler(handler)

        logger.info(f"logging to file stopped")


class Gui_Log_Handler(logging.Handler):

    """Handler for logging to GUI"""

    def __init__(self, view: View):
        super().__init__()
        self.view = view

    def emit(self, record: logging.LogRecord):
        msg = self.format(record)
        self.view.log(msg)
