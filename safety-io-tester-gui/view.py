import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from typing import Protocol
from abc import ABC, abstractmethod
from PIL import ImageTk, Image


TITLE = "Safety I/O Tester"
IMAGE_PATH = "Resource/Images/"
FONT_SIZE = 11


class Presenter(Protocol):
    def set_mode(self, mode: str) -> None:
        ...

    def toggle_mode_bit(self, bit_id: str) -> None:
        ...

    def toggle_e_stop(self, trigger_selection_index: int, delay_ms: str) -> None:
        ...

    def toggle_interlock(self, trigger_selection_index: int, delay_ms: str) -> None:
        ...

    def toggle_power(self) -> None:
        ...

    def measure_heartbeat(self) -> None:
        ...

    def echo_string(self, message: str) -> None:
        ...

    def connect_to_serial_port(self, port: str) -> None:
        ...

    def start_logging_to_file(self, file_path: str) -> None:
        ...

    def stop_logging_to_file(self) -> None:
        ...


class View(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(TITLE)
        self.iconphoto(False, tk.PhotoImage(file=IMAGE_PATH + "brooks_logo.png"))
        self.resizable(False, False)

        # Set font size for all widgets
        style = ttk.Style(self)
        style.configure(".", font=("TkDefaultFont", FONT_SIZE))
        self.option_add("*Font", ("TkDefaultFont", FONT_SIZE))

        # Default button size for consistency
        self.button_size = (15, 1)

    def init_gui(self, presenter: Presenter) -> None:
        self.frm_interactive = Interactive_Frame(self, presenter)
        self.frm_logging = Logging_Frame(self, presenter)

        self.frm_interactive.grid(row=0, column=0)
        self.frm_logging.grid(row=1, column=0)

    def enable_widgets(self) -> None:
        print("enable widgets stub")

    def disable_widgets(self) -> None:
        print("disable widgets stub")

    def set_output_pin_indicators(self, pin_states: dict[str, tuple[bool]]) -> None:
        self.frm_interactive.set_output_indicators(pin_states)

    def log(self, message: str) -> None:
        self.frm_logging.log_to_text_box(message)


class Interactive_Frame(ttk.Frame):

    """GUI frame containing all user-interactive widgets"""

    def __init__(self, parent: View, presenter: Presenter, **kwargs) -> None:
        super().__init__(parent, **kwargs)
        self.presenter = presenter
        self.button_size = parent.button_size
        self.create_panels()

    def create_panels(self) -> None:
        grid_row = tk.IntVar(self, 0)
        self.pnl_ser_con = Serial_Connect_Panel(self, self.presenter, grid_row=grid_row)
        self.pnl_mode = Mode_Selection_Panel(self, self.presenter, grid_row=grid_row)
        self.pnl_estop = Emergency_Stop_Panel(self, self.presenter, grid_row=grid_row)
        self.pnl_interlock = Interlock_Panel(self, self.presenter, grid_row=grid_row)
        self.pnl_power = Power_Panel(self, self.presenter, grid_row=grid_row)

        # ttk.Separator(self, orient="vertical").grid(
        #     row=0, column=1, rowspan=grid_row.get(), sticky="NS"
        # )

        self.pnl_heartbeat = Heartbeat_Panel(self, self.presenter, grid_row=grid_row)
        self.pnl_echo_str = Echo_String_Panel(self, self.presenter, grid_row=grid_row)

        ttk.Separator(self, orient="vertical").grid(
            row=0, column=3, rowspan=grid_row.get(), sticky="NS"
        )

    def set_output_indicators(self, pin_states: dict[str, tuple[bool]]) -> None:
        self.pnl_mode.set_output_indicators(*pin_states["mode1"], grid_row=0)
        self.pnl_mode.set_output_indicators(*pin_states["mode2"], grid_row=1)
        self.pnl_estop.set_output_indicators(*pin_states["estop"], grid_row=0)
        self.pnl_estop.set_output_indicators(*pin_states["stop"], grid_row=1)
        self.pnl_interlock.set_output_indicators(*pin_states["interlock"])
        self.pnl_power.set_output_indicators(*pin_states["power"])
        self.pnl_heartbeat.set_output_indicators(*pin_states["heartbeat"])
        self.pnl_echo_str.set_output_indicators(*pin_states["teach"])


class Interactive_Panel(ABC):

    """ABC for left-center-right split interactive panels"""

    def __init__(
        self, parent: ttk.Frame, presenter: Presenter, grid_row: tk.IntVar
    ) -> None:
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
            Image.open(IMAGE_PATH + "indicator_off.png")
        )
        self.ind_on_img = ImageTk.PhotoImage(
            Image.open(IMAGE_PATH + "indicator_on.png")
        )

        # Create widgets
        self.create_left_widgets(frm_left)
        self.create_center_widgets(frm_center)
        self.create_right_widgets(frm_right)

    @abstractmethod
    def create_left_widgets(self, frame: ttk.Frame) -> None:
        pass

    @abstractmethod
    def create_center_widgets(self, frame: ttk.Frame) -> None:
        pass

    @abstractmethod
    def create_right_widgets(self, frame: ttk.Frame) -> None:
        pass

    def add_output_pin_pair(
        self, frame: ttk.Frame, lbl_left: str, lbl_right: str, grid_row: int = 0
    ) -> None:
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
        super().__init__(parent, presenter, grid_row)

    def create_left_widgets(self, frame: ttk.Frame) -> None:
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
        ttk.Label(frame, text="Status:").grid(row=0, column=0, sticky="E")

        lbl_status = ttk.Label(
            frame,
            text="Disconnected",
            foreground="red",
        )
        lbl_status.grid(row=0, column=1, sticky="W")


class Mode_Selection_Panel(Interactive_Panel):

    """Mode selection controls"""

    def __init__(
        self, parent: ttk.Frame, presenter: Presenter, grid_row: tk.IntVar
    ) -> None:
        super().__init__(parent, presenter, grid_row)

    def create_left_widgets(self, frame: ttk.Frame) -> None:
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
        # Buttons to toggle mode bits (A1, A2, B1, B2)
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
        self.btn_a1_mode_bit.grid(row=1, column=0, padx=padx, pady=pady)

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
        self.btn_a2_mode_bit.grid(row=2, column=0, padx=padx, pady=pady)

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
        self.btn_b1_mode_bit.grid(row=1, column=1, padx=padx, pady=pady)

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
        self.btn_b2_mode_bit.grid(row=2, column=1, padx=padx, pady=pady)

        # Set initial button states
        self.chk_mode_bit_toggled()

    def create_right_widgets(self, frame: ttk.Frame) -> None:
        self.add_output_pin_pair(frame, "Mode A1", "Mode B1", 0)
        self.add_output_pin_pair(frame, "Mode A2", "Mode B2", 1)

    def chk_mode_bit_toggled(self) -> None:
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

    """Emergency stop trigger controls"""

    def __init__(
        self, parent: ttk.Frame, presenter: Presenter, grid_row: tk.IntVar
    ) -> None:
        super().__init__(parent, presenter, grid_row)

    def create_left_widgets(self, frame: ttk.Frame) -> None:
        lbl_e_stop = ttk.Label(frame, text="Emergency Stop:")
        lbl_e_stop.grid(row=0, column=0, sticky="NW")

        btn_e_stop = tk.Button(
            frame,
            text="E-Stop",
            background="red",
            relief="groove",
            width=self.button_size[0],
            height=self.button_size[1],
            font=("TKDefaultFont", FONT_SIZE, "bold"),
            command=lambda: self.presenter.toggle_e_stop(
                self.dual_channel_trigger_states.index(
                    self.e_stop_trigger_selection.get()
                ),
                self.e_stop_delay_ms.get(),
            ),
        )
        btn_e_stop.grid(row=1, column=0, sticky="W")

    def create_center_widgets(self, frame: ttk.Frame) -> None:
        # NOTE: The order of this list is important.
        # The presenter and other functions in this class depend on this order
        self.dual_channel_trigger_states = [
            "A and B on simultaneously",
            "A on after B by [Delay] ms",
            "B on after A by [Delay] ms",
            "A on and B off",
            "B on and A off",
        ]
        self.e_stop_trigger_selection = tk.StringVar(frame)

        opt_e_stop_dropdown = ttk.OptionMenu(
            frame,
            self.e_stop_trigger_selection,
            self.dual_channel_trigger_states[0],
            *self.dual_channel_trigger_states,
            command=self.toggle_delay_entry_state,
        )
        opt_e_stop_dropdown["menu"].configure(font=("TKDefaultFont", FONT_SIZE))
        opt_e_stop_dropdown.config(width=25)
        opt_e_stop_dropdown.grid(row=0, column=0, columnspan=3)

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
        self.add_output_pin_pair(frame, "E-Stop A", "E-Stop B", 0)
        self.add_output_pin_pair(frame, "Stop A", "Stop B", 1)

    def toggle_delay_entry_state(self, trigger_selection: str) -> None:
        if (
            trigger_selection == self.dual_channel_trigger_states[1]
            or trigger_selection == self.dual_channel_trigger_states[2]
        ):
            self.e_stop_delay_ms.set("0")
            self.ent_e_stop_delay["state"] = tk.NORMAL
            self.ent_e_stop_delay.selection_range(0, tk.END)
            self.ent_e_stop_delay.icursor("end")
            self.ent_e_stop_delay.focus_set()
        else:
            self.e_stop_delay_ms.set("")
            self.ent_e_stop_delay["state"] = tk.DISABLED

    def validate_delay_entry(self, value: str) -> None:
        if value:
            try:
                int(value)
                return True
            except ValueError:
                return False
        return True


class Interlock_Panel(Interactive_Panel):

    """Interlock trigger controls"""

    def __init__(
        self, parent: ttk.Frame, presenter: Presenter, grid_row: tk.IntVar
    ) -> None:
        super().__init__(parent, presenter, grid_row)

    def create_left_widgets(self, frame: ttk.Frame) -> None:
        lbl_interlock = ttk.Label(frame, text="Interlock:")
        lbl_interlock.grid(row=0, column=0, sticky="NW")

        btn_interlock = tk.Button(
            frame,
            text="Interlock",
            background="yellow",
            relief="groove",
            width=self.button_size[0],
            height=self.button_size[1],
            font=("TKDefaultFont", FONT_SIZE, "bold"),
            command=lambda: self.presenter.toggle_interlock(
                self.dual_channel_trigger_states.index(
                    self.interlock_trigger_selection.get()
                ),
                self.interlock_delay_ms.get(),
            ),
        )
        btn_interlock.grid(row=1, column=0, sticky="W")

    def create_center_widgets(self, frame: ttk.Frame) -> None:
        # NOTE: The order of this list is important.
        # The presenter and other functions in this class depend on this order
        self.dual_channel_trigger_states = [
            "A and B on simultaneously",
            "A on after B by [Delay] ms",
            "B on after A by [Delay] ms",
            "A on and B off",
            "B on and A off",
        ]
        self.interlock_trigger_selection = tk.StringVar(frame)

        opt_interlock_dropdown = ttk.OptionMenu(
            frame,
            self.interlock_trigger_selection,
            self.dual_channel_trigger_states[0],
            *self.dual_channel_trigger_states,
            command=self.toggle_delay_entry_state,
        )
        opt_interlock_dropdown["menu"].configure(font=("TKDefaultFont", FONT_SIZE))
        opt_interlock_dropdown.config(width=25)
        opt_interlock_dropdown.grid(row=0, column=0, columnspan=3)

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
        self.add_output_pin_pair(frame, "Interlock A", "Interlock B")

    def toggle_delay_entry_state(self, trigger_selection: str) -> None:
        if (
            trigger_selection == self.dual_channel_trigger_states[1]
            or trigger_selection == self.dual_channel_trigger_states[2]
        ):
            self.interlock_delay_ms.set("0")
            self.ent_interlock_delay["state"] = tk.NORMAL
            self.ent_interlock_delay.selection_range(0, tk.END)
            self.ent_interlock_delay.icursor("end")
            self.ent_interlock_delay.focus_set()
        else:
            self.interlock_delay_ms.set("")
            self.ent_interlock_delay["state"] = tk.DISABLED

    def validate_delay_entry(self, value: str) -> None:
        if value:
            try:
                int(value)
                return True
            except ValueError:
                return False
        return True


class Power_Panel(Interactive_Panel):

    """Power controls -- turn controller on or off"""

    def __init__(
        self, parent: ttk.Frame, presenter: Presenter, grid_row: tk.IntVar
    ) -> None:
        super().__init__(parent, presenter, grid_row)

    def create_left_widgets(self, frame: ttk.Frame) -> None:
        lbl_power = ttk.Label(frame, text="Controller Power:")
        lbl_power.grid(row=0, column=0, sticky="NW")

        btn_power = tk.Button(
            frame,
            text="Power",
            background="green3",
            relief="groove",
            width=self.button_size[0],
            height=self.button_size[1],
            font=("TKDefaultFont", FONT_SIZE, "bold"),
            command=self.presenter.toggle_power,
        )
        btn_power.grid(row=1, column=0, sticky="W")

    def create_center_widgets(self, frame: ttk.Frame) -> None:
        # leave intentionally blank
        pass

    def create_right_widgets(self, frame: ttk.Frame) -> None:
        self.add_output_pin_pair(frame, "Power A", "Power B")


class Heartbeat_Panel(Interactive_Panel):

    """Heartbeat monitoring controls"""

    def __init__(
        self, parent: ttk.Frame, presenter: Presenter, grid_row: tk.IntVar
    ) -> None:
        super().__init__(parent, presenter, grid_row)

    def create_left_widgets(self, frame: ttk.Frame) -> None:
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
        ttk.Label(frame, text="Channel A: ").grid(row=0, column=0)
        self.heart_beat_a = ttk.Label(frame, text="NA", relief="solid", borderwidth=1)
        self.heart_beat_a.grid(row=0, column=1)
        ttk.Label(frame, text="Hz").grid(row=0, column=2)
        ttk.Label(frame, text="Channel B: ").grid(row=1, column=0)
        self.heart_beat_b = ttk.Label(frame, text="NA", relief="solid", borderwidth=1)
        self.heart_beat_b.grid(row=1, column=1)
        ttk.Label(frame, text="Hz").grid(row=1, column=2)

    def create_right_widgets(self, frame: ttk.Frame) -> None:
        self.add_output_pin_pair(frame, "Heartbeat A", "Heartbeat B")


class Echo_String_Panel(Interactive_Panel):

    """Controls to send string to the LCD"""

    def __init__(
        self, parent: ttk.Frame, presenter: Presenter, grid_row: tk.IntVar
    ) -> None:
        super().__init__(parent, presenter, grid_row)

    def create_left_widgets(self, frame: ttk.Frame) -> None:
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
        self.add_output_pin_pair(frame, "Teach Mode A", "Teach Mode B")


class Logging_Frame(ttk.Frame):

    """GUI frame containing logged messages to and from the controller"""

    def __init__(self, parent: View, presenter: Presenter, **kwargs) -> None:
        super().__init__(parent, **kwargs)
        self.presenter = presenter
        self.button_size = parent.button_size
        self.text_box_size = (82, 10)

        self.create_widgets()

    def create_widgets(self) -> None:
        lbl_logging = ttk.Label(self, text="Logging:")
        lbl_logging.grid(row=0, column=0, pady=5, sticky="SW")

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
        """Toggle logging to file"""
        logging_is_off = self.btn_toggle_logging.cget("text") == "Start Logging to File"
        if logging_is_off:
            file_path = self.prompt_log_file_path()
            # do nothing if user cancels file selection
            if file_path:
                self.presenter.start_logging_to_file(file_path)
                self.btn_toggle_logging.configure(text="Stop Logging to File")
        else:
            self.presenter.stop_logging_to_file()
            self.btn_toggle_logging.configure(text="Start Logging to File")

    def prompt_log_file_path(self) -> str:
        """Prompt user to select a file to log to"""
        file_path = fd.asksaveasfilename(
            title="Select file",
            filetypes=((".txt files", "*.txt"), ("All files", "*.*")),
        )

        return file_path

    def log_to_text_box(self, message: str) -> None:
        """Log a message to the text box"""
        self.txt_logging.configure(state=tk.NORMAL)

        # insert the message at the end of the text box
        self.txt_logging.insert(tk.END, message + "\n")

        # delete the first line if the text box is full
        if self.txt_logging.yview()[1] != 1.0:
            self.txt_logging.delete(1.0, 2.0)

        # return text box to readonly state
        self.txt_logging.configure(state=tk.DISABLED)
