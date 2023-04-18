import sys
import random
from serial import SerialException


class MockSerialPort:

    """
    Mock serial port for testing GUI without an Arduino

    The mock serial port simulates the Arduino's behavior by responding to commands
    with the expected responses. If it receives an unknown command, it reads and
    writes to stdin and stdout instead of a serial port.

    Attributes:
        port: name of the serial port
        is_open: True if the serial port is open, False otherwise
        expect_ok: True if the next read should return "OK\n", False otherwise
        read_requested: True if the next read should return the pin states
        heartbeat_requested: True if the next read should return the heartbeat
        pin_states: dictionary of pin states reflecting the controllers current state

    Methods:
        open: open the mock serial port
        close: close the mock serial port
        write: write data to the mock serial port and simulate the Arduino's behavior
        read: read data from the mock serial port and simulate the Arduino's behavior
        _encode_pin_states: encode the pin states into a byte string
        _encode_heartbeat: encode the heartbeat into a byte string
    """

    def __init__(self):
        """
        Initialize the mock serial port
        """
        self.port = None
        self.is_open = False

        # Variables to simulate controller state
        self.expect_ok = False
        self.read_requested = False
        self.heartbeat_requested = False

        # Set the default pin states
        self.pin_states = {
            "mode1": (False, True),
            "mode2": (True, False),
            "estop": (True, True),
            "interlock": (True, True),
            "stop": (True, True),
            "teach": (False, False),
            "heartbeat": (False, False),
            "power": (True, True),
        }

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

        str_data = data.decode().strip()

        match str_data[0]:
            case "R":
                self.read_requested = True
            case "H":
                self.heartbeat_requested = True
            case "M":
                self.pin_states["mode1"] = (
                    chr(data[1]) == "1",
                    chr(data[3]) == "1",
                )
                self.pin_states["mode2"] = (
                    chr(data[2]) == "1",
                    chr(data[4]) == "1",
                )
                self.expect_ok = True
            case "E":
                self.pin_states["estop"] = (
                    chr(data[1]) == "1",
                    chr(data[2]) == "1",
                )
                self.expect_ok = True
            case "I":
                self.pin_states["interlock"] = (
                    chr(data[1]) == "1",
                    chr(data[2]) == "1",
                )
                self.expect_ok = True
            case "P":
                self.pin_states["power"] = (
                    chr(data[1]) == "1",
                    chr(data[1]) == "1",
                )
                self.expect_ok = True
            case "S":
                self.expect_ok = True

            # Unexpected output: print the data to stdout
            case _:
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

        if self.expect_ok:
            self.expect_ok = False
            return b"OK\n"

        elif self.read_requested:
            self.read_requested = False
            return self._encode_pin_states()

        elif self.heartbeat_requested:
            self.heartbeat_requested = False
            return self._encode_heartbeat()

        else:
            return sys.stdin.read(size).encode()

    def _encode_pin_states(self) -> bytes:
        """
        Encode the pin states into a byte string

        Pin states are encoded into a byte string in the following format:
        Index   Data byte
            0   A
            1   (0|1) - Mode A1
            2   (0|1) - Mode A2
            3   (0|1) - E-Stop A
            4   (0|1) - Interlock A
            5   (0|1) - Stop A
            6   (0|1) - Teach Mode A
            7   (0|1) - Heartbeat A
            8   (0|1) - Power A
            9   B
            10  (0|1) - Mode B1
            11  (0|1) - Mode B2
            12  (0|1) - E-Stop B
            13  (0|1) - Interlock B
            14  (0|1) - Stop B
            15  (0|1) - Teach Mode B
            16  (0|1) - Heartbeat B
            17  (0|1) - Power B
            18  \n

        Returns:
            Byte string of the pin states
        """
        response = [
            "A",
            str(int(self.pin_states["mode1"][0])),
            str(int(self.pin_states["mode2"][0])),
            str(int(self.pin_states["estop"][0])),
            str(int(self.pin_states["interlock"][0])),
            str(int(self.pin_states["stop"][0])),
            str(int(self.pin_states["teach"][0])),
            str(int(self.pin_states["heartbeat"][0])),
            str(int(self.pin_states["power"][0])),
            "B",
            str(int(self.pin_states["mode1"][1])),
            str(int(self.pin_states["mode2"][1])),
            str(int(self.pin_states["estop"][1])),
            str(int(self.pin_states["interlock"][1])),
            str(int(self.pin_states["stop"][1])),
            str(int(self.pin_states["teach"][1])),
            str(int(self.pin_states["heartbeat"][1])),
            str(int(self.pin_states["power"][1])),
            "\n",
        ]
        return bytearray([ord(b) for b in response])

    def _encode_heartbeat(self) -> bytes:
        """
        Encode the heartbeat into a byte string

        For this mock serial port, the heartbeat is a random number between 0 and 99999

        Heartbeat is encoded into a byte string in the following format:
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

        Returns:
            Byte string of the heartbeat
        """
        heartbeat_a = random.randint(0, 99999)
        heartbeat_b = random.randint(0, 99999)

        return bytes(f"A{heartbeat_a:05d}B{heartbeat_b:05d}", "utf-8")
