import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from typing import Protocol
from abc import ABC, abstractmethod
from PIL import ImageTk, Image
from pathlib import Path


TITLE = "Safety I/O Tester"
IMAGE_PATH = Path(__file__).absolute().parent / "Resource/Images/"
FONT_SIZE = 11


class Presenter(Protocol):
    def connect_to_serial_port(self, port: str) -> None:
        ...

    def disconnect_from_serial_port(self) -> None:
        ...

    def set_mode(self, mode: str) -> None:
        ...

    def toggle_mode_bit(self, bit_id: str) -> None:
        ...

    def toggle_e_stop(self, trigger_state: str, delay_ms: str) -> None:
        ...

    def toggle_interlock(self, trigger_state: str, delay_ms: str) -> None:
        ...

    def toggle_power(self) -> None:
        ...

    def measure_heartbeat(self) -> None:
        ...

    def echo_string(self, message: str) -> None:
        ...

    def start_logging_to_file(self, file_path: str) -> None:
        ...

    def stop_logging_to_file(self) -> None:
        ...


class View(tk.Tk):

    """
    Main GUI window

    Contains all GUI widgets and handles user input

    Attributes:
        frm_interactive: Interactive_Frame object
        frm_logging: Logging_Frame object

    Methods:
        init_gui: Initialize the GUI widgets and add them to the window
        set_output_pin_indicators: Set the output pin indicators to the given state
        set_connection_status: Set the widgets to indicate the serial connection status
        set_heartbeat_values: Set the heartbeat values in the GUI
        log: Log a message to the logging frame
    """

    def __init__(self) -> None:
        """
        Initialize the GUI configuration
        """
        super().__init__()
        self.title(TITLE)
        self.iconphoto(False, tk.PhotoImage(file=IMAGE_PATH / "brooks_logo.png"))
        self.resizable(False, False)

        # Set font size for all widgets
        style = ttk.Style(self)
        style.configure(".", font=("TkDefaultFont", FONT_SIZE))
        self.option_add("*Font", ("TkDefaultFont", FONT_SIZE))

        # Default button size for consistency
        self.button_size = (15, 1)

    def init_gui(self, presenter: Presenter) -> None:
        """
        Initialize the GUI widgets and add them to the window

        presenter: Presenter object
        """
        self.frm_interactive = Interactive_Frame(self, presenter)
        self.frm_logging = Logging_Frame(self, presenter)

        self.frm_interactive.grid(row=0, column=0)
        self.frm_logging.grid(row=1, column=0)

    def set_output_pin_indicators(
        self, pin_states: dict[str, tuple[bool, bool]]
    ) -> None:
        """
        Set the output pin indicators to the given state

        pin_states: dictionary of pin states
        """
        self.frm_interactive.set_output_indicators(pin_states)

    def set_connection_status(self, status: str, port: str = None) -> None:
        """
        Set the widget status to indicate whether the serial connection is active

        status: "Connected" or "Disconnected"
        port: serial port name
        """
        self.frm_interactive.set_connection_status(status, port)

    def set_heartbeat_values(self, heartbeat_hz: tuple[int, int]) -> None:
        """
        Set the heartbeat values in the GUI

        heartbeat_hz: tuple of (heartbeat A, heartbeat B)
        """
        self.frm_interactive.set_heartbeat_values(heartbeat_hz)

    def log(self, message: str) -> None:
        """
        Log a message to the logging frame
        """
        self.frm_logging.log_to_text_box(message)


class Interactive_Frame(ttk.Frame):

    """
    GUI frame containing all user-interactive widgets

    Attributes:
        pnl_ser_con: Serial_Connect_Panel object
        pnl_mode: Mode_Selection_Panel object
        pnl_estop: Emergency_Stop_Panel object
        pnl_interlock: Interlock_Panel object
        pnl_power: Power_Panel object
        pnl_heartbeat: Heartbeat_Panel object
        pnl_echo_str: Echo_String_Panel object

    Methods:
        create_panels: Create all interactive panels and add them to the frame
        set_output_indicators: Set the output pin indicators to the given state
        set_connection_status: Set the widgets to indicate serial connection status
        set_heartbeat_values: Set the heartbeat values in the GUI
    """

    def __init__(self, parent: View, presenter: Presenter, **kwargs) -> None:
        """
        Initialize the frame
        """
        super().__init__(parent, **kwargs)
        self.presenter = presenter
        self.button_size = parent.button_size
        self.create_panels()

    def create_panels(self) -> None:
        """
        Create all interactive panels and add them to the frame
        """
        grid_row = tk.IntVar(self, 0)
        self.pnl_ser_con = Serial_Connect_Panel(self, self.presenter, grid_row=grid_row)
        self.pnl_mode = Mode_Selection_Panel(self, self.presenter, grid_row=grid_row)
        self.pnl_estop = Emergency_Stop_Panel(self, self.presenter, grid_row=grid_row)
        self.pnl_interlock = Interlock_Panel(self, self.presenter, grid_row=grid_row)
        self.pnl_power = Power_Panel(self, self.presenter, grid_row=grid_row)
        self.pnl_heartbeat = Heartbeat_Panel(self, self.presenter, grid_row=grid_row)
        self.pnl_echo_str = Echo_String_Panel(self, self.presenter, grid_row=grid_row)

        ttk.Separator(self, orient="vertical").grid(
            row=0, column=3, rowspan=grid_row.get(), sticky="NS"
        )

    def set_output_indicators(self, pin_states: dict[str, tuple[bool, bool]]) -> None:
        """
        Set the output indicators to the given state

        pin_states: dictionary of pin states
        """
        self.pnl_mode.set_output_indicators(*pin_states["mode1"], grid_row=0)
        self.pnl_mode.set_output_indicators(*pin_states["mode2"], grid_row=1)
        self.pnl_estop.set_output_indicators(*pin_states["estop"], grid_row=0)
        self.pnl_estop.set_output_indicators(*pin_states["stop"], grid_row=1)
        self.pnl_interlock.set_output_indicators(*pin_states["interlock"])
        self.pnl_power.set_output_indicators(*pin_states["power"])
        self.pnl_heartbeat.set_output_indicators(*pin_states["heartbeat"])
        self.pnl_echo_str.set_output_indicators(*pin_states["teach"])

    def set_connection_status(self, status: str, port: str = None) -> None:
        """
        Set the widget status to indicate whether the serial connection is active

        status: "Connected" or "Disconnected"
        port: serial port name
        """
        self.pnl_ser_con.set_connection_status(status, port)

    def set_heartbeat_values(self, heartbeat_hz: tuple[int, int]) -> None:
        """
        Set the heartbeat values in the GUI

        heartbeat_hz: tuple of (heartbeat A, heartbeat B)
        """
        self.pnl_heartbeat.set_heartbeat_values(heartbeat_hz)


class Interactive_Panel(ABC):

    """
    Abstract base class for left-center-right split interactive panels

    Contains widgets and methods common to all such panels
    """

    def __init__(
        self, parent: ttk.Frame, presenter: Presenter, grid_row: tk.IntVar
    ) -> None:
        """
        Initialize the panel
        """
        self.presenter = presenter
        self.button_size = parent.button_size

        padx = 10
        pady = 10

        frm_left = ttk.Frame(parent)
        frm_left.grid(row=grid_row.get(), column=0, padx=padx, pady=pady, sticky="NESW")
        frm_center = ttk.Frame(parent)
        frm_center.grid(row=grid_row.get(), column=2, padx=padx, pady=pady, sticky="")
        frm_right = ttk.Frame(parent)
        frm_right.grid(row=grid_row.get(), column=4, padx=padx, pady=pady, sticky="")
        grid_row.set(grid_row.get() + 1)

        ttk.Separator(parent, orient="horizontal").grid(
            row=grid_row.get(), column=0, columnspan=5, sticky="EW"
        )
        grid_row.set(grid_row.get() + 1)

        # Create output pin indicator images
        self.output_pin_indicators = {}
        self.ind_off_img = ImageTk.PhotoImage(
            Image.open(IMAGE_PATH / "indicator_off.png")
        )
        self.ind_on_img = ImageTk.PhotoImage(
            Image.open(IMAGE_PATH / "indicator_on.png")
        )

        # Create widgets
        self.create_left_widgets(frm_left)
        self.create_center_widgets(frm_center)
        self.create_right_widgets(frm_right)

    @abstractmethod
    def create_left_widgets(self, frame: ttk.Frame) -> None:
        """
        Create widgets on the left side of the panel
        """
        pass

    @abstractmethod
    def create_center_widgets(self, frame: ttk.Frame) -> None:
        """
        Create widgets in the center of the panel
        """
        pass

    @abstractmethod
    def create_right_widgets(self, frame: ttk.Frame) -> None:
        """
        Create widgets on the right side of the panel
        """
        pass

    def add_output_pin_pair(
        self, frame: ttk.Frame, lbl_left: str, lbl_right: str, grid_row: int = 0
    ) -> None:
        """
        Add a pair of output pin indicators to the frame
        """
        lbl_left = ttk.Label(frame, text=lbl_left)
        lbl_left.grid(row=grid_row, column=0, sticky="NSE")
        ind_left = ttk.Label(frame, image=self.ind_off_img)
        ind_left.grid(row=grid_row, column=1, sticky="")
        ind_right = ttk.Label(frame, image=self.ind_off_img)
        ind_right.grid(row=grid_row, column=2, sticky="")
        lbl_right = ttk.Label(frame, text=lbl_right)
        lbl_right.grid(row=grid_row, column=3, sticky="NSW")

        self.output_pin_indicators[grid_row] = (ind_left, ind_right)

    def set_output_indicators(
        self, left_state: bool, right_state: bool, grid_row: int = 0
    ) -> None:
        """
        Set the output pin indicators for A (left) and B (right) pins
        """
        # Set left ouput pin indicator
        self.output_pin_indicators[grid_row][0].configure(
            image=(self.ind_on_img if left_state else self.ind_off_img)
        )

        # Set right ouput pin indicator
        self.output_pin_indicators[grid_row][1].configure(
            image=(self.ind_on_img if right_state else self.ind_off_img)
        )


class Serial_Connect_Panel(Interactive_Panel):

    """Controls to connect to the serial port"""

    def __init__(
        self, parent: ttk.Frame, presenter: Presenter, grid_row: tk.IntVar
    ) -> None:
        """
        Initialize the serial connect panel
        """
        super().__init__(parent, presenter, grid_row)

    def create_left_widgets(self, frame: ttk.Frame) -> None:
        """
        Create button to connect to the serial port
        """
        lbl_serial_connect = ttk.Label(frame, text="Serial Connect:")
        lbl_serial_connect.grid(row=0, column=0, sticky="NW")

        self.btn_connect = tk.Button(
            frame,
            text="Connect",
            background="light grey",
            relief="groove",
            width=self.button_size[0],
            height=self.button_size[1],
            font=("TKDefaultFont", FONT_SIZE, "bold"),
            command=lambda: self.presenter.connect_to_serial_port(
                self.com_port.get().upper()
            ),
        )
        self.btn_connect.grid(row=1, column=0, sticky="W")

    def create_center_widgets(self, frame: ttk.Frame) -> None:
        """
        Create entry to specify the serial port
        """
        lbl__port = ttk.Label(frame, text="Specify Port:")
        lbl__port.grid(row=0, column=0, sticky="E")

        self.com_port = tk.StringVar(frame)
        self.ent_com_port = ttk.Entry(
            frame,
            width=14,
            font=("TkDefaultFont", FONT_SIZE),
            justify="left",
            textvariable=self.com_port,
        )
        self.ent_com_port.grid(row=0, column=2, sticky="W")

    def create_right_widgets(self, frame: ttk.Frame) -> None:
        """
        Create labels to display the connection status
        """
        ttk.Label(frame, text="Status:").grid(row=0, column=0, sticky="E")

        self.lbl_status = ttk.Label(
            frame,
            text="Disconnected",
            foreground="red",
        )
        self.lbl_status.grid(row=0, column=1, sticky="W")

    def set_connection_status(self, status: str, port: str = None) -> None:
        """
        Configure the widgets of this panel to reflect the connection status

        status: "Connected" or "Disconnected"
        port: COM port name (optional)
        """
        match status:
            case "Connected":
                if port:
                    self.com_port.set(port)
                self.ent_com_port.configure(state="disabled")
                self.lbl_status.configure(text=status, foreground="green")
                self.btn_connect.configure(
                    text="Disconnect",
                    command=self.presenter.disconnect_from_serial_port,
                )

            case "Disconnected":
                self.ent_com_port.configure(state="normal")
                self.lbl_status.configure(text=status, foreground="red")
                self.btn_connect.configure(
                    text="Connect",
                    command=lambda: self.presenter.connect_to_serial_port(
                        self.com_port.get().upper()
                    ),
                )


class Mode_Selection_Panel(Interactive_Panel):

    """
    Mode selection controls
    """

    def __init__(
        self, parent: ttk.Frame, presenter: Presenter, grid_row: tk.IntVar
    ) -> None:
        """
        Initialize the mode selection panel
        """
        super().__init__(parent, presenter, grid_row)

    def create_left_widgets(self, frame: ttk.Frame) -> None:
        """
        Create the mode selection dropdown and checkbox to enable/disable bit toggling
        """
        # Mode selection via dropdown menu
        lbl_mode = ttk.Label(frame, text="Mode:")
        lbl_mode.grid(row=0, column=0, sticky="NW")

        self.valid_modes = [
            "Automatic",
            "Stop",
            "Manual",
            "Mute",
        ]
        self.mode_selection = tk.StringVar(frame)

        self.opt_mode_dropdown = ttk.Combobox(
            frame,
            textvariable=self.mode_selection,
            values=self.valid_modes,
            state="readonly",
            width=self.button_size[0],
            font=("TKDefaultFont", FONT_SIZE, "bold"),
        )
        self.opt_mode_dropdown.grid(row=1, column=0, sticky="W")
        self.opt_mode_dropdown.bind(
            "<<ComboboxSelected>>",
            lambda _: self.presenter.set_mode(self.mode_selection.get()),
        )

        # Advanced bit toggling to set mode
        self.bit_toggling_enabled = tk.BooleanVar(frame)

        chk_mode_bit_toggle = ttk.Checkbutton(
            frame,
            text="Enable Bit Toggling",
            variable=self.bit_toggling_enabled,
            command=self.chk_mode_bit_toggled,
        )
        chk_mode_bit_toggle.grid(row=2, column=0)

    def create_center_widgets(self, frame: ttk.Frame) -> None:
        """
        Create buttons to toggle mode bits (A1, A2, B1, B2)
        """
        bit_button_size = (10, 1)
        padx = pady = 4

        self.btn_a1_mode_bit = tk.Button(
            frame,
            text="A1",
            background="light grey",
            relief="groove",
            width=bit_button_size[0],
            height=bit_button_size[1],
            font=("TKDefaultFont", FONT_SIZE),
            command=lambda: self.presenter.toggle_mode_bit("A1"),
        )
        self.btn_a1_mode_bit.grid(row=0, column=0, padx=padx, pady=pady)

        self.btn_a2_mode_bit = tk.Button(
            frame,
            text="A2",
            background="light grey",
            relief="groove",
            width=bit_button_size[0],
            height=bit_button_size[1],
            font=("TKDefaultFont", FONT_SIZE),
            command=lambda: self.presenter.toggle_mode_bit("A2"),
        )
        self.btn_a2_mode_bit.grid(row=1, column=0, padx=padx, pady=pady)

        self.btn_b1_mode_bit = tk.Button(
            frame,
            text="B1",
            background="light grey",
            relief="groove",
            width=bit_button_size[0],
            height=bit_button_size[1],
            font=("TKDefaultFont", FONT_SIZE),
            command=lambda: self.presenter.toggle_mode_bit("B1"),
        )
        self.btn_b1_mode_bit.grid(row=0, column=1, padx=padx, pady=pady)

        self.btn_b2_mode_bit = tk.Button(
            frame,
            text="B2",
            background="light grey",
            relief="groove",
            width=bit_button_size[0],
            height=bit_button_size[1],
            font=("TKDefaultFont", FONT_SIZE),
            command=lambda: self.presenter.toggle_mode_bit("B2"),
        )
        self.btn_b2_mode_bit.grid(row=1, column=1, padx=padx, pady=pady)

        # Set initial button states
        self.chk_mode_bit_toggled()

    def create_right_widgets(self, frame: ttk.Frame) -> None:
        """
        Add the output pin pairs for the mode bits
        """
        self.add_output_pin_pair(frame, "Mode A1", "Mode B1", 0)
        self.add_output_pin_pair(frame, "Mode A2", "Mode B2", 1)

    def chk_mode_bit_toggled(self) -> None:
        """
        Enable or disable the mode bit toggling buttons and the mode dropdown
        """
        if self.bit_toggling_enabled.get():
            self.opt_mode_dropdown["state"] = tk.DISABLED
            self.btn_a1_mode_bit["state"] = tk.NORMAL
            self.btn_a2_mode_bit["state"] = tk.NORMAL
            self.btn_b1_mode_bit["state"] = tk.NORMAL
            self.btn_b2_mode_bit["state"] = tk.NORMAL
        else:
            self.opt_mode_dropdown["state"] = "readonly"
            self.btn_a1_mode_bit["state"] = tk.DISABLED
            self.btn_a2_mode_bit["state"] = tk.DISABLED
            self.btn_b1_mode_bit["state"] = tk.DISABLED
            self.btn_b2_mode_bit["state"] = tk.DISABLED


class Emergency_Stop_Panel(Interactive_Panel):

    """
    Controls to toggle the emergency stop state
    """

    def __init__(
        self, parent: ttk.Frame, presenter: Presenter, grid_row: tk.IntVar
    ) -> None:
        """
        Initialize the emergency stop panel
        """
        super().__init__(parent, presenter, grid_row)

    def create_left_widgets(self, frame: ttk.Frame) -> None:
        """
        Create the label and toggle e-stop button
        """
        lbl_e_stop = ttk.Label(frame, text="Emergency Stop:")
        lbl_e_stop.grid(row=0, column=0, sticky="NW")

        btn_e_stop = tk.Button(
            frame,
            text="Toggle E-Stop",
            background="red",
            relief="groove",
            width=self.button_size[0],
            height=self.button_size[1],
            font=("TKDefaultFont", FONT_SIZE, "bold"),
            command=lambda: self.presenter.toggle_e_stop(
                [  # Get the trigger state key from the value in the dict
                    trig_state_key
                    for trig_state_key, trig_state_val in self.trigger_states.items()
                    if trig_state_val == self.e_stop_trigger_selection.get()
                ][0],
                self.e_stop_delay_ms.get(),
            ),
        )
        btn_e_stop.grid(row=1, column=0, sticky="W")

    def create_center_widgets(self, frame: ttk.Frame) -> None:
        """
        Create the dropdown selection and delay entry widgets for the e-stop panel
        """
        # E-Stop dual channel trigger selection
        self.trigger_states = {
            "A and B": "Toggle A and B together",
            "A then B": "Toggle A then B, [Delay] ms",
            "B then A": "Toggle B then A, [Delay] ms",
            "A only": "Toggle A only",
            "B only": "Toggle B only",
        }
        self.e_stop_trigger_selection = tk.StringVar(frame)
        self.e_stop_trigger_selection.set(self.trigger_states["A and B"])
        opt_e_stop_dropdown = ttk.Combobox(
            frame,
            textvariable=self.e_stop_trigger_selection,
            values=[*self.trigger_states.values()],
            state="readonly",
            width=23,
        )
        opt_e_stop_dropdown.bind("<<ComboboxSelected>>", self.toggle_delay_entry_state)
        opt_e_stop_dropdown.grid(row=0, column=0, columnspan=3)

        # E-Stop triggering delay entry
        self.e_stop_delay_ms = tk.StringVar(frame, "")

        ttk.Label(frame, text="Delay: ").grid(row=1, column=0, sticky="E")

        vcmd = (frame.register(self.validate_delay_entry), "%P")
        self.ent_e_stop_delay = ttk.Entry(
            frame,
            width=2,
            font=("TkDefaultFont", FONT_SIZE),
            justify="right",
            textvariable=self.e_stop_delay_ms,
            state=tk.DISABLED,
            validate="key",
            validatecommand=vcmd,
        )
        self.ent_e_stop_delay.grid(row=1, column=1, sticky="EW")

        ttk.Label(frame, text="ms").grid(row=1, column=2, sticky="W")

    def create_right_widgets(self, frame: ttk.Frame) -> None:
        """
        Add the output pin pairs for the E-Stop and Stop buttons
        """
        self.add_output_pin_pair(frame, "E-Stop A", "E-Stop B", 0)
        self.add_output_pin_pair(frame, "Stop A", "Stop B", 1)

    def toggle_delay_entry_state(self, event: tk.Event) -> None:
        """
        Enable or disable the delay entry based on the trigger selection
        """
        if (
            self.e_stop_trigger_selection.get() == self.trigger_states["A then B"]
            or self.e_stop_trigger_selection.get() == self.trigger_states["B then A"]
        ):
            # Enable delay entry
            self.ent_e_stop_delay["state"] = tk.NORMAL

            # Set initial value to 0, select text with cursor at the end, and focus
            self.e_stop_delay_ms.set("0")
            self.ent_e_stop_delay.selection_range(0, tk.END)
            self.ent_e_stop_delay.icursor("end")
            self.ent_e_stop_delay.focus_set()

        else:
            # Disable delay entry and clear value
            self.ent_e_stop_delay["state"] = tk.DISABLED
            self.e_stop_delay_ms.set("")

    def validate_delay_entry(self, value: str) -> None:
        """
        Validate the delay entry value is an integer between 0 and 99999
        """
        if value:
            try:
                val = int(value)
                if val < 0 or val > 99999:
                    return False
                return True
            except ValueError:
                return False
        return True


class Interlock_Panel(Interactive_Panel):

    """
    Controls to toggle the interlock state
    """

    def __init__(
        self, parent: ttk.Frame, presenter: Presenter, grid_row: tk.IntVar
    ) -> None:
        """
        Initialize the interlock panel
        """
        super().__init__(parent, presenter, grid_row)

    def create_left_widgets(self, frame: ttk.Frame) -> None:
        """
        Create the label and toggle interlock button
        """
        lbl_interlock = ttk.Label(frame, text="Interlock:")
        lbl_interlock.grid(row=0, column=0, sticky="NW")

        btn_interlock = tk.Button(
            frame,
            text="Toggle Interlock",
            background="yellow",
            relief="groove",
            width=self.button_size[0],
            height=self.button_size[1],
            font=("TKDefaultFont", FONT_SIZE, "bold"),
            command=lambda: self.presenter.toggle_interlock(
                [  # Get the trigger state key from the value in the dict
                    trig_state_key
                    for trig_state_key, trig_state_val in self.trigger_states.items()
                    if trig_state_val == self.interlock_trigger_selection.get()
                ][0],
                self.interlock_delay_ms.get(),
            ),
        )
        btn_interlock.grid(row=1, column=0, sticky="W")

    def create_center_widgets(self, frame: ttk.Frame) -> None:
        """
        Create the dropdown selection and delay entry widgets for the interlock panel
        """
        # Interlock dual channel trigger selection
        self.trigger_states = {
            "A and B": "Toggle A and B together",
            "A then B": "Toggle A then B, [Delay] ms",
            "B then A": "Toggle B then A, [Delay] ms",
            "A only": "Toggle A only",
            "B only": "Toggle B only",
        }
        self.interlock_trigger_selection = tk.StringVar(frame)
        self.interlock_trigger_selection.set(self.trigger_states["A and B"])
        opt_interlock_dropdown = ttk.Combobox(
            frame,
            textvariable=self.interlock_trigger_selection,
            values=[*self.trigger_states.values()],
            state="readonly",
            width=23,
        )
        opt_interlock_dropdown.bind(
            "<<ComboboxSelected>>", self.toggle_delay_entry_state
        )
        opt_interlock_dropdown.grid(row=0, column=0, columnspan=3)

        # Interlock triggering delay entry
        self.interlock_delay_ms = tk.StringVar(frame, "")

        ttk.Label(frame, text="Delay: ").grid(row=1, column=0, sticky="E")

        vcmd = (frame.register(self.validate_delay_entry), "%P")
        self.ent_interlock_delay = ttk.Entry(
            frame,
            width=2,
            justify="right",
            font=("TkDefaultFont", FONT_SIZE),
            textvariable=self.interlock_delay_ms,
            state=tk.DISABLED,
            validate="key",
            validatecommand=vcmd,
        )
        self.ent_interlock_delay.grid(row=1, column=1, sticky="EW")

        ttk.Label(frame, text="ms").grid(row=1, column=2, sticky="W")

    def create_right_widgets(self, frame: ttk.Frame) -> None:
        """
        Add output pin pair for controller interlock
        """
        self.add_output_pin_pair(frame, "Interlock A", "Interlock B")

    def toggle_delay_entry_state(self, event: tk.Event) -> None:
        """
        Enable or disable the delay entry based on the interlock trigger selection
        """
        if (
            self.interlock_trigger_selection.get() == self.trigger_states["A then B"]
            or self.interlock_trigger_selection.get() == self.trigger_states["B then A"]
        ):
            # Enable delay entry
            self.ent_interlock_delay["state"] = tk.NORMAL

            # Set initial value to 0, select text with cursor at the end, and focus
            self.interlock_delay_ms.set("0")
            self.ent_interlock_delay.selection_range(0, tk.END)
            self.ent_interlock_delay.icursor("end")
            self.ent_interlock_delay.focus_set()

        else:
            # Disable delay entry and clear value
            self.ent_interlock_delay["state"] = tk.DISABLED
            self.interlock_delay_ms.set("")

    def validate_delay_entry(self, value: str) -> None:
        """
        Validate delay entry value is an integer between 0 and 99999
        """
        if value:
            try:
                val = int(value)
                if val < 0 or val > 99999:
                    return False
                return True
            except ValueError:
                return False
        return True


class Power_Panel(Interactive_Panel):

    """
    Power controls -- toggle the controller on or off
    """

    def __init__(
        self, parent: ttk.Frame, presenter: Presenter, grid_row: tk.IntVar
    ) -> None:
        """
        Initialize the power panel
        """
        super().__init__(parent, presenter, grid_row)

    def create_left_widgets(self, frame: ttk.Frame) -> None:
        """
        Add power toggle button
        """
        lbl_power = ttk.Label(frame, text="Controller Power:")
        lbl_power.grid(row=0, column=0, sticky="NW")

        btn_power = tk.Button(
            frame,
            text="Toggle Power",
            background="green3",
            relief="groove",
            width=self.button_size[0],
            height=self.button_size[1],
            font=("TKDefaultFont", FONT_SIZE, "bold"),
            command=self.presenter.toggle_power,
        )
        btn_power.grid(row=1, column=0, sticky="W")

    def create_center_widgets(self, frame: ttk.Frame) -> None:
        """
        No center widgets for the power panel
        """
        # Leave intentionally blank
        pass

    def create_right_widgets(self, frame: ttk.Frame) -> None:
        """
        Add output pin pair for controller power
        """
        self.add_output_pin_pair(frame, "Power A", "Power B")


class Heartbeat_Panel(Interactive_Panel):

    """
    Heartbeat monitoring controls
    """

    def __init__(
        self, parent: ttk.Frame, presenter: Presenter, grid_row: tk.IntVar
    ) -> None:
        """
        Initialize the heartbeat panel
        """
        super().__init__(parent, presenter, grid_row)

    def create_left_widgets(self, frame: ttk.Frame) -> None:
        """
        Create label and button for measuring the heartbeat frequency
        """
        lbl_heartbeat = ttk.Label(frame, text="Hearbeat:")
        lbl_heartbeat.grid(row=0, column=0, sticky="NW")

        self.btn_measure_hearbeat = tk.Button(
            frame,
            text="Measure Hearbeat",
            background="light grey",
            relief="groove",
            width=self.button_size[0],
            height=self.button_size[1],
            font=("TKDefaultFont", FONT_SIZE, "bold"),
            command=self.presenter.measure_heartbeat,
        )
        self.btn_measure_hearbeat.grid(row=1, column=0, sticky="W")

    def create_center_widgets(self, frame: ttk.Frame) -> None:
        """
        Create widgets for displaying the measured heartbeat frequency
        """
        ttk.Label(frame, text="Channel A: ").grid(row=0, column=0)
        self.heart_beat_a = ttk.Label(
            frame, text="N/A", relief="solid", borderwidth=1, width=5, anchor="e"
        )
        self.heart_beat_a.grid(row=0, column=1)
        ttk.Label(frame, text="Hz").grid(row=0, column=2)
        ttk.Label(frame, text="Channel B: ").grid(row=1, column=0)
        self.heart_beat_b = ttk.Label(
            frame, text="N/A", relief="solid", borderwidth=1, width=5, anchor="e"
        )
        self.heart_beat_b.grid(row=1, column=1)
        ttk.Label(frame, text="Hz").grid(row=1, column=2)

    def create_right_widgets(self, frame: ttk.Frame) -> None:
        """
        Add the output pin pair for the controller heartbeat
        """
        self.add_output_pin_pair(frame, "Heartbeat A", "Heartbeat B")

    def set_heartbeat_values(self, heartbeat_hz: tuple[int, int]):
        """
        Set the heartbeat values in the GUI
        """
        self.heart_beat_a["text"] = heartbeat_hz[0]
        self.heart_beat_b["text"] = heartbeat_hz[1]


class Echo_String_Panel(Interactive_Panel):

    """
    Controls to send a string to the Safety IO Tester's LCD
    """

    def __init__(
        self, parent: ttk.Frame, presenter: Presenter, grid_row: tk.IntVar
    ) -> None:
        """
        Initialize the echo string panel
        """
        super().__init__(parent, presenter, grid_row)

    def create_left_widgets(self, frame: ttk.Frame) -> None:
        """
        Add the label and send string button to the frame
        """
        lbl_echo_string = ttk.Label(frame, text="Echo String:")
        lbl_echo_string.grid(row=0, column=0, sticky="NW")

        self.btn_echo_string = tk.Button(
            frame,
            text="Send to LCD",
            background="light grey",
            relief="groove",
            width=self.button_size[0],
            height=self.button_size[1],
            font=("TKDefaultFont", FONT_SIZE, "bold"),
            command=lambda: self.presenter.echo_string(self.message.get()),
        )
        self.btn_echo_string.grid(row=1, column=0, sticky="W")

    def create_center_widgets(self, frame: ttk.Frame) -> None:
        """
        Add the entry box for the echo string
        """
        self.message = tk.StringVar(frame)
        self.ent_echo_string = ttk.Entry(
            frame,
            width=25,
            font=("TkDefaultFont", FONT_SIZE),
            justify="left",
            textvariable=self.message,
        )
        self.ent_echo_string.grid(row=0, column=0, sticky="EW")

    def create_right_widgets(self, frame: ttk.Frame) -> None:
        """
        Add the output pin pair for teach mode
        """
        self.add_output_pin_pair(frame, "Teach Mode A", "Teach Mode B")


class Logging_Frame(ttk.Frame):

    """
    GUI frame containing logged messages to and from the controller

    Attributes:
        parent: The parent view
        presenter: The presenter for the view
        button_size: The size of the buttons in the frame
        text_box_size: The size of the text box in the frame
        btn_toggle_logging: The button to toggle logging to file
        txt_logging: The text box to display logged messages

    Methods:
        create_widgets: Create the widgets for the logging frame
        toggle_logging_to_file: Toggle logging to file
        prompt_log_file_path: Prompt the user for a log file path
        log_to_text_box: Log a message to the text box
    """

    def __init__(self, parent: View, presenter: Presenter, **kwargs) -> None:
        """
        Initialize the logging frame
        """
        super().__init__(parent, **kwargs)
        self.presenter = presenter
        self.button_size = parent.button_size
        self.text_box_size = (80, 10)

        self.create_widgets()

    def create_widgets(self) -> None:
        """
        Create the widgets for the logging frame
        """
        # Logging label
        lbl_logging = ttk.Label(self, text="Logging:")
        lbl_logging.grid(row=0, column=0, pady=5, sticky="SW")

        # Toggle logging to file button
        self.btn_toggle_logging = tk.Button(
            self,
            text="Start Logging to File",
            background="light grey",
            relief="groove",
            width=self.button_size[0],
            height=self.button_size[1],
            font=("TkDefaultFont", FONT_SIZE),
            command=self.toggle_logging_to_file,
        )
        self.btn_toggle_logging.grid(row=0, column=1, pady=5, sticky="SE")

        # Logging text box
        self.txt_logging = tk.Text(
            self,
            width=self.text_box_size[0],
            height=self.text_box_size[1],
            relief="groove",
            borderwidth=2,
            font=("TkDefaultFont", FONT_SIZE),
        )
        self.txt_logging.grid(row=1, column=0, columnspan=2, sticky="EW", pady=10)
        self.txt_logging.configure(state=tk.DISABLED)

    def toggle_logging_to_file(self) -> None:
        """
        Toggle logging to file
        """
        logging_is_off = self.btn_toggle_logging.cget("text") == "Start Logging to File"

        if logging_is_off:
            file_path = self.prompt_log_file_path()

            # Do nothing if user cancels file selection
            if file_path:
                self.presenter.start_logging_to_file(file_path)
                self.btn_toggle_logging.configure(text="Stop Logging to File")

        else:
            self.presenter.stop_logging_to_file()
            self.btn_toggle_logging.configure(text="Start Logging to File")

    def prompt_log_file_path(self) -> str:
        """
        Prompt user to select a file to log to
        """
        file_path = fd.asksaveasfilename(
            title="Select file",
            filetypes=((".txt files", "*.txt"), ("All files", "*.*")),
        )

        return file_path

    def log_to_text_box(self, message: str) -> None:
        """
        Log a message to the text box

        If the text box is full, delete the first line before inserting the new message

        message: the message to log
        """
        self.txt_logging.configure(state=tk.NORMAL)

        # Insert the message at the end of the text box
        self.txt_logging.insert(tk.END, message + "\n")

        # Delete the first line if the text box is full
        if self.txt_logging.yview()[1] != 1.0:
            self.txt_logging.delete(1.0, 2.0)

        # Return text box to readonly state
        self.txt_logging.configure(state=tk.DISABLED)
