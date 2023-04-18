import serial
from serial import SerialException, SerialTimeoutException
import serial.tools.list_ports
import logging
import sys

logger = logging.getLogger("safety_io_logger")  # logger for all modules


BAUD_RATE = 115200

import time


class Model:
    def __init__(self) -> None:
        self.serial = MockSerialPort()  # for testing without Arduino
        # self.serial = serial.Serial()
        self.serial.baudrate = BAUD_RATE
        self.serial.timeout = 1  # timeout for read operations (in seconds)
        self.serial.write_timeout = 1  # timeout for write operations (in seconds)

    def detect_arduino_ports(self) -> list[str]:
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

    def connect_to_serial_port(self, port: str) -> bool:
        """
        Connect to the serial device over the specified port

        port: COM port to connect to

        Returns:
            True if the connection was successful, False otherwise
        """
        try:
            self.serial.port = port
            self.serial.open()
            return True
        except SerialException:
            self.disconnect_from_serial_port()
            return False

    def disconnect_from_serial_port(self) -> None:
        """
        Disconnect from the serial device
        """
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()
        self.serial.close()

    def write_data(self, data: bytes) -> bool:
        """
        Send data to the connected serial device

        data: bytes to send to the serial device

        Returns:
            True if the data was sent successfully, False otherwise
        """
        try:
            self.serial.write(data)
            logger.info(f"Sent data: '{data.decode()}'")
            if self.read_response_OK():
                return True
            logger.warning("Did not recieve 'OK' response from Safety IO Tester")
            self.disconnect_from_serial_port()
            return False

        except (SerialException, SerialTimeoutException):
            self.disconnect_from_serial_port()
            return False

    def read_response_OK(self) -> bool:
        """
        Read the response from the serial device

        Returns:
            True if the response was "OK", False otherwise

        Raises:
            SerialException: if there is an error reading from the serial device
        """
        response = self.serial.read(3).decode().strip()
        logger.info(f"Response: '{response}'")
        return response == "OK"

    def request_output_pin_states(self) -> dict[str, tuple[bool, bool]]:
        return {
            "mode1": (int(time.time()) % 2, False),
            "mode2": (False, True),
            "estop": (True, False),
            "stop": (False, True),
            "interlock": (True, False),
            "power": (int(time.time()) % 2, int(time.time()) % 3),
            "heartbeat": (True, False),
            "teach": (True, False),
        }

    def set_mode(self, mode_str: str) -> bool:
        """
        Set the mode of the controller

        Send data to the serial device in the following format:
        Index   Data byte
            0   M
            1   (0|1) - Mode A1
            2   (0|1) - Mode A2
            3   (0|1) - Mode B1
            4   (0|1) - Mode B2

        e.g. "M1001" sets bits A1 and B2, setting the controller to "Manual" mode

        mode_str: must be one of ["Automatic", "Stop", "Manual", "Mute"]

        Returns:
            True if the data was sent successfully, False otherwise
        """
        # Convert mode string to corresponding mode bits
        match (mode_str):
            case "Automatic":
                mode_bits = ["0", "1", "1", "0"]
            case "Stop":
                mode_bits = ["1", "0", "1", "0"]
            case "Manual":
                mode_bits = ["1", "0", "0", "1"]
            case "Mute":
                mode_bits = ["0", "1", "0", "1"]

        # Send mode bits to the serial device
        data = bytearray([ord("M")] + [ord(b) for b in mode_bits])
        return self.write_data(data)

    def toggle_mode_bit(self, mode_bit: str) -> bool:
        """
        Toggle the specified mode bit.
        Values for nontoggled bits are read from the controller.

        Send data to the serial device in the following format:
        Index   Data byte
            0   M
            1   (0|1) - Mode A1
            2   (0|1) - Mode A2
            3   (0|1) - Mode B1
            4   (0|1) - Mode B2

        e.g. "M1001" sets bits A1 and B2, setting the controller to "Manual" mode

        mode_bit: must be one of ["A1", "A2", "B1", "B2"]

        Returns:
            True if the data was sent successfully, False otherwise
        """
        # Get current mode bits
        pin_states = self.request_output_pin_states()
        mode_ab1, mode_ab2 = [pin_states[key] for key in ["mode1", "mode2"]]
        mode_bits = [
            str(int(mode_ab1[0])),  # A1
            str(int(mode_ab2[0])),  # A2
            str(int(mode_ab1[1])),  # B1
            str(int(mode_ab2[1])),  # B2
        ]

        # Toggle the specified mode bit
        match mode_bit:
            case "A1":
                mode_bits[0] = "1" if mode_bits[0] == "0" else "0"
            case "A2":
                mode_bits[1] = "1" if mode_bits[1] == "0" else "0"
            case "B1":
                mode_bits[2] = "1" if mode_bits[2] == "0" else "0"
            case "B2":
                mode_bits[3] = "1" if mode_bits[3] == "0" else "0"

        # Send mode bits to the serial device
        data = bytearray([ord("M")] + [ord(b) for b in mode_bits])
        return self.write_data(data)

    def set_estop(
        self,
        e_stop_a: bool,
        e_stop_b: bool,
        first_channel: str = "",
        delay_ms: int = 0,
    ) -> bool:
        """
        Set the emergency stop pin states

        Send data to the serial device in the following format:
        Index   Data byte
            0   E
            1   (0|1) - E-stop A
            2   (0|1) - E-stop B

            Optional 5-digit delay in milliseconds
            3   (A|B) - Which e-stop channel to set first before the delay
            4   (0-9)
            5   (0-9)
            6   (0-9)
            7   (0-9)
            8   (0-9)

        e.g. "E10" sets e-stop A ON and B OFF simultaneously,
        "E11B00100" sets e-stop A 100 ms after e-stop B

        e_stop_a: True to set e-stop A, False to clear e-stop A
        e_stop_b: True to set e-stop B, False to clear e-stop B
        first_channel: which e-stop to set first before the delay ("A" or "B")
        delay_ms: delay in milliseconds between setting channels A and B

        Returns:
            True if the data was sent successfully, False otherwise
        """
        # If a delay is specified
        if first_channel == "A" or first_channel == "B":
            e_stop_bits = [
                str(int(e_stop_a)),
                str(int(e_stop_b)),
                first_channel,
                str(delay_ms // 10000 % 10),
                str(delay_ms // 1000 % 10),
                str(delay_ms // 100 % 10),
                str(delay_ms // 10 % 10),
                str(delay_ms % 10),
            ]

        # If no delay is specified
        else:
            e_stop_bits = [str(int(e_stop_a)), str(int(e_stop_b))]

        data = bytearray([ord("E")] + [ord(b) for b in e_stop_bits])
        return self.write_data(data)

    def set_interlock(
        self,
        interlock_a: bool,
        interlock_b: bool,
        first_channel: str = "",
        delay_ms: int = 0,
    ) -> bool:
        """
        Set the interlock pin states

        Send data to the serial device in the following format:
        Index   Data byte
            0   I
            1   (0|1) - Interlock A
            2   (0|1) - Interlock B

            Optional 5-digit delay in milliseconds
            3   (A|B) - Which interlock channel to set first before the delay
            4   (0-9)
            5   (0-9)
            6   (0-9)
            7   (0-9)
            8   (0-9)

        e.g. "E10" sets interlock A ON and B OFF simultaneously,
        "E11B00100" sets interlock A 100 ms after interlock B

        interlock_a: True to set interlock A, False to clear interlock A
        interlock_b: True to set interlock B, False to clear interlock B
        first_channel: which interlock to set first before the delay ("A" or "B")
        delay_ms: delay in milliseconds between setting channels A and B

        Returns:
            True if the data was sent successfully, False otherwise
        """
        # If a delay is specified
        if first_channel == "A" or first_channel == "B":
            interlock_bits = [
                str(int(interlock_a)),
                str(int(interlock_b)),
                first_channel,
                str(delay_ms // 10000 % 10),
                str(delay_ms // 1000 % 10),
                str(delay_ms // 100 % 10),
                str(delay_ms // 10 % 10),
                str(delay_ms % 10),
            ]

        # If no delay is specified
        else:
            interlock_bits = [str(int(interlock_a)), str(int(interlock_b))]

        data = bytearray([ord("I")] + [ord(b) for b in interlock_bits])
        return self.write_data(data)

    def toggle_power(self) -> bool:
        """
        Toggle the controller power state

        Send data to the serial device in the following format:
        Index   Data byte
            0   P
            1   (0|1) - Power

        e.g. "P1" sets power ON, "P0" sets power OFF

        Returns:
            True if the data was sent successfully, False otherwise
        """

        # Get current power state
        pin_states = self.request_output_pin_states()
        power = pin_states["power"]

        # If device is powered on, turn it off
        if power[0] or power[1]:
            data = bytearray([ord("P"), ord("0")])

        # If device is powered off, turn it on
        else:
            data = bytearray([ord("P"), ord("1")])

        return self.write_data(data)

    def request_heartbeat(self) -> tuple[int, int] | None:
        """
        Request heartbeat in Hz from the controller

        Send data to the serial device in the following format:
        Index   Data byte
            0   H

        Receive data to the serial device in the following format:
        Index   Data byte
            0   A
            1   X
            2   X
            3   X
            4   X
            5   X
            6   B
            7   X
            8   X
            9   X
            10  X
            11  X
            12  \n

        e.g. "H" requesets the heartbeat and a response of "A00100B01234" indicates
        the heartbeat on channel A is 100 Hz and the heartbeat on channel B is 1234 Hz

        Returns:
            The heartbeat in Hz as a tuple of (heartbeat A, heartbeat B)
            or None if the request failed
        """
        heartbeat_hz = None
        try:
            self.serial.write(b"H")
            logger.info(f"Sent data: 'H'")
            self.serial.reset_input_buffer()
            data = self.serial.read(13).decode().strip()
            logger.info(f"Response: '{data}'")
        except SerialException:
            return None

        if data[0] == "A" and data[6] == "B":
            try:
                heartbeat_hz = (int(data[1:6]), int(data[7:12]))
            except ValueError:
                return None

        return heartbeat_hz

    def set_echo_string(self, echo_string: str) -> bool:
        """
        Set the echo string

        Send data to the serial device in the following format:
        Index   Data byte
            0   S
            1   Char 1
            2   Char 2
            ...
            N   Char N
            N+1 \n

        e.g. "SHello World!" sets the echo string to "Hello World!"

        echo_string: string to send to the Saftey IO Tester

        Returns:
            True if the data was sent successfully, False otherwise
        """
        data = bytearray([ord("S")] + [ord(c) for c in echo_string])
        return self.write_data(data)


class MockSerialPort:

    """Mock serial port for testing GUI without an Arduino"""

    def __init__(self):
        """
        Initialize the mock serial port
        """
        self.port = None
        self.is_open = False

    def open(self):
        """
        Open the mock serial port
        """
        self.is_open = True

    def close(self):
        """
        Close the mock serial port
        """
        self.is_open = False

    def write(self, data: bytes):
        """
        Write data to stdout instead of to a serial port

        data: bytes to write to stdout

        Raises:
            SerialException if the mock serial port is not open
        """
        if not self.is_open:
            raise SerialException("Mock serial port is not open")

        sys.stdout.write(str(data) + "\n")
        sys.stdout.flush()

    def read(self, size: int = 1) -> bytes:
        """
        Read data from stdin instead of from a serial port

        size: number of bytes to read from stdin

        Returns:
            bytes read from stdin

        Raises:
            SerialException if the mock serial port is not open
        """
        if not self.is_open:
            raise SerialException("Mock serial port is not open")

        return sys.stdin.read(size).encode()

    def reset_input_buffer(self):
        """
        Reset the mock serial port's input buffer

        For this mock serial port, this method does nothing
        """
        pass

    def reset_output_buffer(self):
        """
        Reset the mock serial port's output buffer

        For this mock serial port, this method does nothing
        """
        pass


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
    3   A|B
    4   X
    5   X
    6   X
    7   X
    8   X

Send (set interlock):
    0   I
    1   Interlock A
    2   Interlock B
    3   A|B
    4   X
    5   X
    6   X
    7   X
    8   X

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

Send (set echo string):
    0   S
    1   Char 1
    2   Char 2
    ...
    N   Char N
    N+1 \n

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
    0   A
    1   X
    2   X
    3   X
    4   X
    5   X
    6   B
    7   X
    8   X
    9   X
    10  X
    11  X
    12  \n

"""
