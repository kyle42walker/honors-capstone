"""
File: mock_serial_port.py
Author: Kyle Walker
Date: 2023-04-24

This module contains the MockSerialPort class, which is used to simulate the
Arduino's behavior when testing the GUI without an Arduino.
"""

import sys
import random
from serial import SerialException
import threading


class MockSerialPort:

    """
    Mock serial port for testing GUI without an Arduino

    The mock serial port simulates the Arduino's behavior by responding to commands
    with the expected responses. If it receives an unknown command, it reads and
    writes to stdin and stdout instead of a serial port.

    Attributes:
        port: name of the serial port
        is_open: True if the serial port is open, False otherwise

    Methods:
        open: open the mock serial port
        close: close the mock serial port
        write: write data to the mock serial port and simulate the Arduino's behavior
        read: read data from the mock serial port and simulate the Arduino's behavior
    """

    def __init__(self):
        """
        Initialize the mock serial port
        """
        self.port = None
        self.is_open = False

        # Variables to simulate controller state
        self._expect_ok = False
        self._read_requested = False
        self._heartbeat_requested = False

        # Set the default pin states
        self._pin_states = {
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
            SerialException if the mock serial port is not open or if the data is
            invalid (unknown command or incorrect format)
        """
        if not self.is_open:
            raise SerialException("Mock serial port is not open")

        str_data = data.decode().strip()

        match str_data[0]:
            case "R":
                # Requset pin states
                self._read_requested = True
            case "H":
                # Request heartbeat
                self._heartbeat_requested = True
            case "M":
                self._set_mode_from_serial_data(data)
                self._expect_ok = True
            case "E":
                self._set_estop_from_serial_data(data)
                self._expect_ok = True
            case "I":
                self._set_interlock_from_serial_data(data)
                self._expect_ok = True
            case "P":
                self._set_power_from_serial_data(data)
                self._expect_ok = True
            case "S":
                self._expect_ok = True

            # Unexpected output: print the data to stdout
            case _:
                sys.stdout.write(str(data) + "\n")
                sys.stdout.flush()
                raise SerialException("Unexpected output: " + str_data)

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

        if self._expect_ok:
            self._expect_ok = False
            return b"OK\n"

        elif self._read_requested:
            self._read_requested = False
            return self._encode_pin_states()

        elif self._heartbeat_requested:
            self._heartbeat_requested = False
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
            str(int(self._pin_states["mode1"][0])),
            str(int(self._pin_states["mode2"][0])),
            str(int(self._pin_states["estop"][0])),
            str(int(self._pin_states["interlock"][0])),
            str(int(self._pin_states["stop"][0])),
            str(int(self._pin_states["teach"][0])),
            str(int(self._pin_states["heartbeat"][0])),
            str(int(self._pin_states["power"][0])),
            "B",
            str(int(self._pin_states["mode1"][1])),
            str(int(self._pin_states["mode2"][1])),
            str(int(self._pin_states["estop"][1])),
            str(int(self._pin_states["interlock"][1])),
            str(int(self._pin_states["stop"][1])),
            str(int(self._pin_states["teach"][1])),
            str(int(self._pin_states["heartbeat"][1])),
            str(int(self._pin_states["power"][1])),
            "\n",
        ]
        self._update_heartbeat()
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
        heartbeat_a = random.randint(5, 15)
        heartbeat_b = random.randint(5, 15)

        return bytes(f"A{heartbeat_a:05d}B{heartbeat_b:05d}", "utf-8")

    def _update_heartbeat(self):
        """
        Update the heartbeat pin states

        For this mock serial port, the heartbeat pins are randomly set to 0 or 1
        """
        self._pin_states["heartbeat"] = (
            random.getrandbits(1),
            random.getrandbits(1),
        )

    def _set_mode_from_serial_data(self, ser_data: bytes) -> None:
        """
        Set the mode pin states from the serial data

        ser_data: serial data to set the mode pin states from
        """
        # Set mode pin states
        self._pin_states["mode1"] = (
            chr(ser_data[1]) == "1",
            chr(ser_data[3]) == "1",
        )
        self._pin_states["mode2"] = (
            chr(ser_data[2]) == "1",
            chr(ser_data[4]) == "1",
        )

    def _set_estop_from_serial_data(self, ser_data: bytes) -> None:
        """
        Set the e-stop pin states from the serial data

        ser_data: serial data to set the e-stop pin states from

        Raises:
            SerialException: if the serial data is invalid (formatted incorrectly)
        """
        str_data = ser_data.decode().strip()

        # No delay was specified, set the pin states immediately
        if len(str_data) == 3:
            self._pin_states["estop"] = (
                chr(ser_data[1]) == "1",
                chr(ser_data[2]) == "1",
            )

        # If a delay was specified, start a timer to set the estop pin states
        elif len(str_data) == 9:
            first_channel = str_data[3]
            delay_ms = int(str_data[4:9])

            # Set the first channel immediately
            if first_channel == "A":
                self._pin_states["estop"] = (
                    chr(ser_data[1]) == "1",
                    self._pin_states["estop"][1],
                )
                second_channel = "B"
                second_state = chr(ser_data[2]) == "1"
            elif first_channel == "B":
                self._pin_states["estop"] = (
                    self._pin_states["estop"][0],
                    chr(ser_data[2]) == "1",
                )
                second_channel = "A"
                second_state = chr(ser_data[1]) == "1"
            else:
                raise SerialException("Invalid channel: " + first_channel)

            # Set the second channel after the specified delay
            timer = threading.Timer(
                delay_ms / 1000,
                self._process_estop_delay,
                [second_channel, second_state],
            )
            timer.start()

        # Invalid serial data
        else:
            raise SerialException("Invalid serial data: " + str_data)

        # Set stop pin states, which depend on e-stop
        self._update_stop_pin_state()

    def _process_estop_delay(self, channel: str, state: bool):
        """
        Set the specified channel of the E-Stop pin state

        channel: channel of the E-Stop pin state to set (A or B)
        state: state to set the channel to
        """
        if channel == "A":
            self._pin_states["estop"] = (state, self._pin_states["estop"][1])
        elif channel == "B":
            self._pin_states["estop"] = (self._pin_states["estop"][0], state)

        self._update_stop_pin_state()

    def _update_stop_pin_state(self):
        """
        Update the stop pin states according to the e-stop pin states
        """
        # Set stop pin states, which depend on e-stop
        self._pin_states["stop"] = (
            self._pin_states["estop"][0],
            self._pin_states["estop"][1],
        )

    def _set_interlock_from_serial_data(self, ser_data: bytes) -> None:
        """
        Set the interlock pin states from the serial data

        ser_data: serial data to set the interlock pin states from

        Raises:
            SerialException: if the serial data is invalid (formatted incorrectly)
        """
        str_data = ser_data.decode().strip()

        # No delay was specified, set the pin states immediately
        if len(str_data) == 3:
            self._pin_states["interlock"] = (
                chr(ser_data[1]) == "1",
                chr(ser_data[2]) == "1",
            )

        # If a delay was specified, start a timer to set the interlock pin states
        elif len(str_data) == 9:
            first_channel = str_data[3]
            delay_ms = int(str_data[4:9])

            # Set the first channel immediately
            if first_channel == "A":
                self._pin_states["interlock"] = (
                    chr(ser_data[1]) == "1",
                    self._pin_states["interlock"][1],
                )
                second_channel = "B"
                second_state = chr(ser_data[2]) == "1"
            elif first_channel == "B":
                self._pin_states["interlock"] = (
                    self._pin_states["interlock"][0],
                    chr(ser_data[2]) == "1",
                )
                second_channel = "A"
                second_state = chr(ser_data[1]) == "1"
            else:
                raise SerialException("Invalid channel: " + first_channel)

            # Set the second channel after the specified delay
            timer = threading.Timer(
                delay_ms / 1000,
                self._process_interlock_delay,
                [second_channel, second_state],
            )
            timer.start()

        # Invalid serial data
        else:
            raise SerialException("Invalid serial data: " + str_data)

    def _process_interlock_delay(self, channel: str, state: bool):
        """
        Set the specified channel of the interlock pin state

        channel: channel of the interlock pin state to set (A or B)
        state: state to set the channel to
        """
        if channel == "A":
            self._pin_states["interlock"] = (state, self._pin_states["interlock"][1])
        elif channel == "B":
            self._pin_states["interlock"] = (self._pin_states["interlock"][0], state)

    def _set_power_from_serial_data(self, ser_data: bytes) -> None:
        """
        Set the power pin states from the serial data

        ser_data: serial data to set the power pin states from
        """
        self._pin_states["power"] = (
            chr(ser_data[1]) == "1",
            chr(ser_data[1]) == "1",
        )
