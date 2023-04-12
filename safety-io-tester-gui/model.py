import serial
from serial import SerialException
import serial.tools.list_ports

import logging

logger = logging.getLogger("safety_io_logger")  # logger for all modules


BAUD_RATE = 115200

import time

import sys


class MockSerialPort:

    """Mock serial port for testing GUI without an Arduino"""

    def __init__(self):
        """
        Initialize the mock serial port
        """
        self.colcount = 0

    def write_data(self, data: bytes):
        """
        Write data to stdout instead of to a serial port

        data: bytes to write to stdout
        """
        sys.stdout.write(data)
        self.colcount += 1
        # simulated terminal width
        if self.colcount > 80:
            sys.stdout.write("\n")
            sys.colcount = 0
        sys.stdout.flush()


class ArduinoPort:

    """Serial port for communicating with the Arduino"""

    def __init__(self, port: str = None):
        """
        Initialize the serial port

        port (optional): Arduino's COM port to connect to
        """
        if port:
            self.serial = serial.Serial(port, BAUD_RATE)
        else:
            self.serial = None

    def get_arduino_port_list(self) -> list[str] | None:
        """
        Get port names of all connected Arduinos

        Returns:
            A list of ports (e.g. '/dev/ttyUSB0' or 'COM3'),
            None if no Arduino is connected
        """
        return [
            p.device
            for p in serial.tools.list_ports.comports()
            if p.vid
            in [0x2341, 0x2A03, 0x1B4F, 0x239A]  # list of typical Arduino vendor IDs
        ]

    def connect_to_arduino_port(self, port: str) -> None:
        """
        Connect to the Arduino over the serial COM port

        port: COM port to connect to
        """
        self.serial = serial.Serial(port, BAUD_RATE)

    def write_data(self, data: bytes) -> bool:
        """
        Send data to the connected Arduino over the serial COM port

        data: bytes to send to the Arduino

        Returns:
            True if the data was sent successfully, False otherwise
        """
        try:
            self.serial.write(data)
            return True
        except SerialException:
            self.serial.close()
            return False

    def read_data(self, message_size: int) -> bytes | None:
        """
        Read data from the connected Arduino over the serial COM port

        message_size: number of bytes to read from the Arduino

        Returns:
            bytes read from the Arduino,
            None if the serial port
        """
        try:
            return self.serial.read(message_size, timeout=0.1)
        except SerialException:
            self.serial.close()
            return None


class Model:
    def __init__(self) -> None:
        self.serial = None

    def connect_to_serial_port(self, port: str) -> None:
        # self.serial = MockSerialPort()
        # return

        if port:
            self.serial = ArduinoPort(port)
            return

        self.serial = ArduinoPort()
        ports = self.serial.get_arduino_port_list()

        # No Ardunio connected
        if not ports:
            logger.info(
                "Could not detect any accessible Arduino devices.\n \
                    \tTry using a different USB port or restarting the application."
            )
            return

        # Multiple Arduinos connected
        if len(ports) > 1:
            logger.info(
                "More than one Arduino is currently connected.\n \
                    \tThe Arduino with the lowest COM port ID has been selected."
            )

        # Connect to Arduino with the lowest COM port identifier
        logger.info(f"Arduino connected on: {ports[0]}")
        self.serial.connect_to_arduino(ports[0])

    def send_data(self, data: bytes) -> None:
        data_sent_successfully = self.serial.write_data(data)
        if not data_sent_successfully:
            logger.info("The Arduino was disconnected or has changed COM ports.")

    def get_output_pin_states(self) -> dict[str, tuple[bool]]:
        return {
            "mode1": (int(time.time()) % 2, False),
            "mode2": (False, True),
            "estop": (True, False),
            "stop": (False, True),
            "interlock": (True, False),
            "power": (True, False),
            "heartbeat": (True, False),
            "teach": (True, False),
        }

    def set_mode(self, mode: str) -> None:
        """
        Set the mode of the controller
        Index   Data byte
            0   M
            1   (0|1) Mode A1
            2   (0|1) Mode A2
            3   (0|1) Mode B1
            4   (0|1) Mode B2

        mode: must be one of ["Automatic", "Stop", "Manual", "Mute"]
        """
        match (mode):
            case "Automatic":
                self.send_data(b"M0110")
            case "Stop":
                self.send_data(b"M1010")
            case "Manual":
                self.send_data(b"M1001")
            case "Mute":
                self.send_data(b"M0101")


"""
Send (set):
    0   A
    1   Mode A1
    2   Mode A2
    3   E-Stop A
    4   Interlock A
    5   B
    6   Mode B1
    7   Mode B2
    8   E-Stop B
    9   Interlock B
    10  P
    11  Power
"""

"""
Send (read):
    0   R

Receive:
    0   Mode A1
    1   Mode A2
    2   E-Stop A
    3   Interlock A
    4   Stop A
    5   Teach Mode A
    6   Heartbeat A
    7   Mode B1
    8   Mode B2
    9   E-Stop B
    10  Interlock B
    11  Stop B
    12  Teach Mode B
    13  Heartbeat B
"""


"""
New proposed protocol:

Send (set mode):
    0   M
    1   Mode A1
    2   Mode A2
    3   Mode B1
    4   Mode B2

Send (set e-stop):
    0   E
    1   E-Stop A
    2   E-Stop B

Send (set interlock):
    0   I
    1   Interlock A
    2   Interlock B

Send (set power):
    0   P
    1   Power

Send (set all):
    0   A
    1   Mode A1
    2   Mode A2
    3   E-Stop A
    4   Interlock A
    5   B
    6   Mode B1
    7   Mode B2
    8   E-Stop B
    9   Interlock B
    10  P
    11  Power

Receive (for all set commands):
    0   O
    1   K
    2   \n

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Send (read all):
    0   R

Receive:
    0   Mode A1
    1   Mode A2
    2   E-Stop A
    3   Interlock A
    4   Stop A
    5   Teach Mode A
    6   Heartbeat A
    7   Mode B1
    8   Mode B2
    9   E-Stop B
    10  Interlock B
    11  Stop B
    12  Teach Mode B
    13  Heartbeat B
    14  \n


Send (read heartbeat):
    0   H

Receive:
    int number of hz
    \n

"""
