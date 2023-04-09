import time


class Model:
    def __init__(self) -> None:
        pass

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
