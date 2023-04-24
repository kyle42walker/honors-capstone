"""
File: model.py
Author: Kyle Walker
Date: 2023-04-24

This module contains the Model class for the Safety IO Tester application.
The model is responsible for all data manipulation and communication with the
serial device.
"""

import serial
from serial import SerialException, SerialTimeoutException
import serial.tools.list_ports
import logging
from mock_serial_port import MockSerialPort
from time import sleep


BAUD_RATE = 115200  # Baud rate for serial communication
logger = logging.getLogger("safety_io_logger")  # Logger for all modules


class Model:

    """
    Model for the Safety IO Tester application

    Attributes:
        serial: Serial object for serial communication
        output_pin_states: Dictionary of dual channel pin names to a tuple of pin states

    Methods:
        detect_arduino_ports: Get port names of all connected Arduinos
        connect_to_serial_port: Connect to the serial device over the specified port
        disconnect_from_serial_port: Disconnect from the serial device
        write_data: Send data to the connected serial device
        read_response_OK: Validate the expected "OK\n" response from the serial device
        request_output_pin_states: Get updated output pin states from the controller
        set_mode: Set the mode of the controller to one of the 4 valid states
        toggle_mode_bit: Toggle the specified mode bit
        toggle_estop: Toggle the E-Stop channels A and B
        toggle_interlock: Toggle the Interlock channels A and B
        toggle_power: Toggle the Power channels A and B
        request_heartbeat: Request a heartbeat measurement from the controller
        set_echo_string: Set the echo string of the Safety IO Tester
        detect_pin_change: Detect a change in a pin other than the heartbeat
    """

    def __init__(self) -> None:
        """
        Initialize the model
        """
        self.serial = MockSerialPort()  # For testing the GUI without Arduino
        # self.serial = serial.Serial() # For running the final application
        self.serial.baudrate = BAUD_RATE
        self.serial.timeout = 1  # Timeout for read operations (in seconds)
        self.serial.write_timeout = 1  # Timeout for write operations (in seconds)

        self.output_pin_states = {
            "mode1": (False, False),
            "mode2": (False, False),
            "estop": (False, False),
            "interlock": (False, False),
            "stop": (False, False),
            "teach": (False, False),
            "heartbeat": (False, False),
            "power": (False, False),
        }

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
            in [0x2341, 0x2A03, 0x1B4F, 0x239A]  # List of typical Arduino vendor IDs
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
            logger.info(f"Sent data: '{data.decode().strip()}'")
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
            True if the response was "OK\n", False otherwise

        Raises:
            SerialException: if there is an error reading from the serial device
        """
        response = self.serial.readline.decode().strip()
        # logger.debug(f"Response: '{response}'")
        return response == "OK"

    def request_output_pin_states(self) -> dict[str, tuple[bool, bool]]:
        """
        Request the output pin states from the controller

        Send data to the serial device in the following format:
        Index   Data byte
            0   R
            1   \n

        Receive data from the serial device in the following format:
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

        e.g. "R\n" requests the output pin states and a response of "A10000010B01000010\n"
        indicates Mode A1, Heartbeat A, Mode B2, and Heartbeat B are set
        and all other pins are cleared

        Returns:
            Dictionary of dual channel pin names to a tuple of pin states (A, B)
            or an empty dictionary if there was an error
        """
        try:
            # Send request and get response
            self.serial.write(b"R\n")
            response = self.serial.readline.decode().strip()

        except (SerialException, SerialTimeoutException):
            self.disconnect_from_serial_port()
            return {}

        # Invalid response syntax
        if response[0] != "A" or response[9] != "B" or len(response) != 18:
            return {}

        # Parse response
        # logger.debug(f"Response: '{response}'")
        pin_states = {
            "mode1": (response[1] == "1", response[10] == "1"),
            "mode2": (response[2] == "1", response[11] == "1"),
            "estop": (response[3] == "1", response[12] == "1"),
            "interlock": (response[4] == "1", response[13] == "1"),
            "stop": (response[5] == "1", response[14] == "1"),
            "teach": (response[6] == "1", response[15] == "1"),
            "heartbeat": (response[7] == "1", response[16] == "1"),
            "power": (response[8] == "1", response[17] == "1"),
        }

        # Only log if the pin states have changed
        if self.detect_pin_change(pin_states):
            logger.info(f"Pin states updated: {response}")
            self.output_pin_states = pin_states
        return pin_states

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
            5   \n

        e.g. "M1001\n" sets bits A1 and B2, setting the controller to "Manual" mode

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
        data = bytearray([ord("M")] + [ord(b) for b in mode_bits] + [ord("\n")])
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
            4   (0|1) - Mode
            5   \n

        e.g. "M1001" sets bits A1 and B2, setting the controller to "Manual" mode

        mode_bit: must be one of ["A1", "A2", "B1", "B2"]

        Returns:
            True if the data was sent successfully, False otherwise
        """
        # Get current mode bits
        mode_ab1, mode_ab2 = [self.output_pin_states[key] for key in ["mode1", "mode2"]]
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
        data = bytearray([ord("M")] + [ord(b) for b in mode_bits] + [ord("\n")])
        return self.write_data(data)

    def toggle_estop(
        self,
        toggle_e_stop_a: bool,
        toggle_e_stop_b: bool,
        first_channel: str = "",
        delay_ms: int = 0,
    ) -> bool:
        """
        Toggle the emergency stop pin states

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

            3 | 9   \n

        e.g. "E10" sets e-stop A ON and B OFF simultaneously,
        "E11B00100" sets e-stop A ON 100 ms after e-stop B ON

        toggle_e_stop_a: True to toggle channel A, False to leave channel A unchanged
        toggle_e_stop_b: True to toggle channel B, False to leave channel B unchanged
        first_channel: which e-stop to toggle first before the delay ("A" or "B")
        delay_ms: delay in milliseconds between setting channels A and B

        Returns:
            True if the data was sent successfully, False otherwise
        """
        # Get current e-stop states
        curr_e_stop_a = self.output_pin_states["estop"][0]
        curr_e_stop_b = self.output_pin_states["estop"][1]

        # Toggle e-stop states if specified
        e_stop_a = not curr_e_stop_a if toggle_e_stop_a else curr_e_stop_a
        e_stop_b = not curr_e_stop_b if toggle_e_stop_b else curr_e_stop_b

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

        data = bytearray([ord("E")] + [ord(b) for b in e_stop_bits] + [ord("\n")])
        return self.write_data(data)

    def toggle_interlock(
        self,
        toggle_interlock_a: bool,
        toggle_interlock_b: bool,
        first_channel: str = "",
        delay_ms: int = 0,
    ) -> bool:
        """
        Toggle the interlock pin states

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

            3 | 9   \n

        e.g. "I10" sets interlock A ON and B OFF simultaneously,
        "I11B00100" sets interlock A 100 ms after interlock B

        toggle_interlock_a: True to toggle channel A, False to leave channel A unchanged
        toggle_interlock_b: True to toggle channel B, False to leave channel B unchanged
        first_channel: which interlock to set first before the delay ("A" or "B")
        delay_ms: delay in milliseconds between setting channels A and B

        Returns:
            True if the data was sent successfully, False otherwise
        """
        # Get current interlock states
        curr_interlock_a = self.output_pin_states["interlock"][0]
        curr_interlock_b = self.output_pin_states["interlock"][1]

        # Toggle interlock states if specified
        interlock_a = not curr_interlock_a if toggle_interlock_a else curr_interlock_a
        interlock_b = not curr_interlock_b if toggle_interlock_b else curr_interlock_b

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

        data = bytearray([ord("I")] + [ord(b) for b in interlock_bits] + [ord("\n")])
        return self.write_data(data)

    def toggle_power(self) -> bool:
        """
        Toggle the controller power state

        Send data to the serial device in the following format:
        Index   Data byte
            0   P
            1   (0|1) - Power
            2   \n

        e.g. "P1" sets power ON, "P0" sets power OFF

        Returns:
            True if the data was sent successfully, False otherwise
        """

        # Get current power state
        power = self.output_pin_states["power"]

        # If device is powered on, turn it off
        if power[0] or power[1]:
            data = bytearray([ord("P"), ord("0"), ord("\n")])

        # If device is powered off, turn it on
        else:
            data = bytearray([ord("P"), ord("1"), ord("\n")])

        return self.write_data(data)

    def request_heartbeat(self) -> tuple[int, int] | None:
        """
        Request heartbeat in Hz from the controller

        Send data to the serial device in the following format:
        Index   Data byte
            0   H
            1   \n

        Receive data to the serial device in the following format:
        Index   Data byte
            0   A
            1   (0-9)
            2   (0-9)
            3   (0-9)
            4   (0-9)
            5   (0-9)
            6   B
            7   (0-9)
            8   (0-9)
            9   (0-9)
            10  (0-9)
            11  (0-9)
            12  \n

        e.g. "H" requesets the heartbeat and a response of "A00100B01234" indicates
        the heartbeat on channel A is 100 Hz and the heartbeat on channel B is 1234 Hz

        Returns:
            The heartbeat in Hz as a tuple of (heartbeat A, heartbeat B)
            or None if the request failed
        """
        heartbeat_hz = None
        try:
            self.serial.write(b"H\n")
            logger.info(f"Sent data: 'H'")
            # Wait for serial device to measure heartbeat
            sleep(1)
            data = self.serial.readline.decode().strip()
            logger.info(f"Response: '{data}'")
        except SerialException:
            return None

        if data[0] == "A" and data[6] == "B" and len(data) == 12:
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
        data = bytearray([ord("S")] + [ord(c) for c in echo_string] + [ord("\n")])
        return self.write_data(data)

    def detect_pin_change(self, new_pin_states: dict[str, tuple[bool, bool]]) -> bool:
        """
        Detect a change in a pin other than the heartbeat pin

        Returns:
            True if a change was detected, False otherwise
        """
        # Compare the current pin states to the previous pin states
        for pin in new_pin_states:
            # Skip the heartbeat pin
            if pin == "heartbeat":
                continue

            if new_pin_states[pin] != self.output_pin_states[pin]:
                return True

        return False
