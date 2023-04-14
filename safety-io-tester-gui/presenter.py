from __future__ import annotations
from typing import Protocol
from model import Model
import logging


POLLING_RATE = 100  # [ms] polling rate for output pin states
logger = logging.getLogger("safety_io_logger")  # logger for all modules


class Model(Protocol):
    def read_output_pin_states(self) -> dict[str, tuple[bool]]:
        ...

    def write_mode(self, mode: str) -> bool:
        ...

    def write_mode_bit(self, bit_id: str) -> bool:
        ...

    def detect_arduino_ports(self) -> list[str]:
        ...

    def connect_to_serial_port(self, port: str) -> bool:
        ...


class View(Protocol):
    def init_gui(self, presenter: Presenter) -> None:
        ...

    def connect(self) -> None:
        ...

    def disconnect(self) -> None:
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
        """
        Initialize the presenter
        """
        self.model = model
        self.view = view

    def run(self) -> None:
        """
        Run the application
        """
        # Initialize GUI
        self.view.init_gui(self)

        # Start logging
        self.start_logger()

        # Start GUI
        self.view.after(POLLING_RATE, self.update_output_pin_indicators)
        self.view.mainloop()

    def update_output_pin_indicators(self) -> None:
        """
        Update the output pin indicators in the GUI

        This function is called every POLLING_RATE ms
        """
        self.view.set_output_pin_indicators(self.model.read_output_pin_states())
        self.view.after(POLLING_RATE, self.update_output_pin_indicators)

    def connect_to_serial_port(self, port: str) -> None:
        """
        Connect to serial port

        port: port to connect to. If None, try to detect Arduino port automatically
        """
        # If no port is specified, try to detect one
        if not port:
            port_list = self.model.detect_arduino_ports()

            # If no port is detected, return
            if not port_list:
                logger.error("No compatible Arduino devices detected")
                return

            # If multiple ports are detected, select the lexicographically lowest ID
            if len(port_list) > 1:
                logger.info("Multiple devices detected - Selecting the lowest port ID")
            port = port_list[0]

        # Attempt to connect to serial port
        if self.model.connect_to_serial_port(port):
            logger.info(f"Successfully connected to serial port '{port}'")
            self.view.connect()
        else:
            logger.error(f"Failed to connect to serial port '{port}'")
            self.view.disconnect()

    def set_mode(self, mode: str) -> None:
        """
        Set the mode of the controller

        mode: must be "Automatic", "Stop", "Manual", or "Mute"
        """
        if self.model.write_mode(mode):
            logger.debug(f"Mode set to '{mode}'")
        else:
            logger.error("Failed to communincate with serial device")
            self.view.disconnect()

    def toggle_mode_bit(self, bit_id: str) -> None:
        """
        Toggle a single mode bit of the controller

        bit_id: must be "A1", "A2", "B1", or "B2"
        """
        if self.model.write_mode_bit(bit_id):
            logger.debug(f"Mode bit '{bit_id}' toggled")
        else:
            logger.error("Failed to communincate with serial device")
            self.view.disconnect()

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

    def start_logger(self) -> None:
        """
        Start the console and GUI loggers
        """
        # Configure logger
        logger.setLevel(logging.DEBUG)
        self.log_formatter = logging.Formatter("%(asctime)s - %(message)s")

        # Start console logging
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(self.log_formatter)
        logger.addHandler(console_handler)

        # Start GUI logging
        gui_handler = Gui_Log_Handler(self.view)
        gui_handler.setLevel(logging.INFO)
        gui_handler.setFormatter(self.log_formatter)
        logger.addHandler(gui_handler)

    def start_logging_to_file(self, file_path: str) -> None:
        """
        Start logging to file

        file_path: path to log file
        """
        logger.info(f"Logging started to '{file_path}'")

        # Open file and start logging
        file_handler = logging.FileHandler(file_path, mode="w")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(self.log_formatter)
        logger.addHandler(file_handler)

    def stop_logging_to_file(self) -> None:
        """
        Stop logging to any file started by start_logging_to_file()
        """
        # Remove any logging file handlers
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                logger.removeHandler(handler)

        logger.info(f"Logging to file stopped")


class Gui_Log_Handler(logging.Handler):

    """Handler for logging to GUI"""

    def __init__(self, view: View):
        super().__init__()
        self.view = view

    def emit(self, record: logging.LogRecord):
        """
        Emit a log message by displaying it in the GUI

        record: log record
        """
        msg = self.format(record)
        self.view.log(msg)
