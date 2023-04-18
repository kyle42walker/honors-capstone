from __future__ import annotations
from typing import Protocol
from model import Model
import logging

POLLING_RATE = 100  # [ms] polling rate for output pin states
logger = logging.getLogger("safety_io_logger")  # logger for all modules


class Model(Protocol):
    def detect_arduino_ports(self) -> list[str]:
        ...

    def connect_to_serial_port(self, port: str) -> bool:
        ...

    def disconnect_from_serial_port(self) -> None:
        ...

    def request_output_pin_states(self) -> dict[str, tuple[bool, bool]]:
        ...

    def set_mode(self, mode: str) -> bool:
        ...

    def toggle_mode_bit(self, bit_id: str) -> bool:
        ...

    def set_estop(
        self,
        e_stop_a: bool,
        e_stop_b: bool,
        first_channel: str = "",
        delay_ms: int = 0,
    ) -> bool:
        ...

    def set_interlock(
        self,
        interlock_a: bool,
        interlock_b: bool,
        first_channel: str = "",
        delay_ms: int = 0,
    ) -> bool:
        ...

    def toggle_power(self) -> bool:
        ...

    def request_heartbeat(self) -> tuple[int, int] | None:
        ...

    def set_echo_string(self, echo_string: str) -> bool:
        ...


class View(Protocol):
    def init_gui(self, presenter: Presenter) -> None:
        ...

    def set_output_pin_indicators(
        self, pin_states: dict[str, tuple[bool, bool]]
    ) -> None:
        ...

    def set_connection_status(self, status: str, port: str = None) -> None:
        ...

    def set_hearbeat_values(self, heartbeat_hz: tuple[int, int]) -> None:
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
        self.view.mainloop()

    def update_output_pin_indicators(self) -> None:
        """
        Update the output pin indicators in the GUI

        This function is called every POLLING_RATE ms
        """
        pin_states = self.model.request_output_pin_states()
        if not pin_states:
            self.failed_to_communicate()
            return
        self.view.set_output_pin_indicators(pin_states)

        # Poll again after POLLING_RATE ms
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
            self.view.set_connection_status("Connected", port=port)

            # Begin polling output pin states
            self.view.after(POLLING_RATE, self.update_output_pin_indicators)
        else:
            logger.error(f"Failed to connect to serial port '{port}'")
            self.view.set_connection_status("Disconnected")

    def disconnect_from_serial_port(self) -> None:
        """
        Disconnect from serial port
        """
        self.model.disconnect_from_serial_port()
        logger.info("Disconnected from serial port")
        self.view.set_connection_status("Disconnected")

    def failed_to_communicate(self) -> None:
        """
        Log a failed communication attempt
        """
        logger.error("Failed to communincate with serial device")
        self.model.disconnect_from_serial_port()
        self.view.set_connection_status("Disconnected")

    def set_mode(self, mode: str) -> None:
        """
        Set the mode of the controller

        mode: must be "Automatic", "Stop", "Manual", or "Mute"
        """
        if self.model.set_mode(mode):
            logger.debug(f"Mode set to '{mode}'")
        else:
            self.failed_to_communicate()

    def toggle_mode_bit(self, bit_id: str) -> None:
        """
        Toggle a single mode bit of the controller

        bit_id: must be "A1", "A2", "B1", or "B2"
        """
        if self.model.toggle_mode_bit(bit_id):
            logger.debug(f"Mode bit '{bit_id}' toggled")
        else:
            self.failed_to_communicate()

    def toggle_e_stop(self, trigger_state: int, delay_ms: str) -> None:
        """
        Toggle the e-stop bits of the controller

        trigger_state: must be "A and B", "A then B", "B then A", "A only", or "B only"
        delay_ms: delay between triggering A and B in milliseconds
        """
        communication_successful = False

        match trigger_state:
            case "A and B":
                if self.model.set_estop(True, True):
                    logger.debug(f"E-stops A and B")
                    communication_successful = True
            case "A then B":
                if self.model.set_estop(True, True, "A", int(delay_ms)):
                    logger.debug(f"E-stop A then B, {delay_ms} ms delay")
                    communication_successful = True
            case "B then A":
                if self.model.set_estop(True, True, "B", int(delay_ms)):
                    logger.debug(f"E-stop B then A, {delay_ms} ms delay")
                    communication_successful = True
            case "A only":
                if self.model.set_estop(True, False):
                    logger.debug(f"E-stop A only")
                    communication_successful = True
            case "B only":
                if self.model.set_estop(False, True):
                    logger.debug(f"E-stop B only")
                    communication_successful = True

        if not communication_successful:
            self.failed_to_communicate()

    def toggle_interlock(self, trigger_state: str, delay_ms: str) -> None:
        """
        Toggle the interlock bits of the controller

        trigger_state: must be "A and B", "A then B", "B then A", "A only", or "B only"
        delay_ms: delay between triggering A and B in milliseconds
        """
        communication_successful = False

        match trigger_state:
            case "A and B":
                if self.model.set_interlock(True, True):
                    logger.debug(f"Interlocks A and B")
                    communication_successful = True
            case "A then B":
                if self.model.set_interlock(True, True, "A", int(delay_ms)):
                    logger.debug(f"Interlock A then B, {delay_ms} ms delay")
                    communication_successful = True
            case "B then A":
                if self.model.set_interlock(True, True, "B", int(delay_ms)):
                    logger.debug(f"Interlock B then A, {delay_ms} ms delay")
                    communication_successful = True
            case "A only":
                if self.model.set_interlock(True, False):
                    logger.debug(f"Interlock A only")
                    communication_successful = True
            case "B only":
                if self.model.set_interlock(False, True):
                    logger.debug(f"Interlock B only")
                    communication_successful = True

        if not communication_successful:
            self.failed_to_communicate()

    def toggle_power(self) -> None:
        """
        Toggle the controller power
        """
        if self.model.toggle_power():
            logger.debug(f"Power toggled")
        else:
            self.failed_to_communicate()

    def measure_heartbeat(self) -> None:
        """
        Measure the heartbeat (A and B) of the controller and display the results
        """
        heartbeat_hz = self.model.request_heartbeat()
        if heartbeat_hz:
            logger.debug(
                f"Heartbeat A: {heartbeat_hz[0]}, Heartbeat B: {heartbeat_hz[1]}"
            )
            self.view.set_heartbeat_values(heartbeat_hz)
        else:
            self.failed_to_communicate()

    def echo_string(self, message: str) -> None:
        """
        Echo a string to be displayed on the Saftey IO Tester

        message: string to echo
        """
        if self.model.set_echo_string(message):
            logger.debug(f"Echo string: '{message}'")
        else:
            self.failed_to_communicate()

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
