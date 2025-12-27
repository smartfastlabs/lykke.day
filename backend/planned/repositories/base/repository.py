from blinker import Signal


class BaseRepository:
    signal_source: Signal

    def __init__(self) -> None:
        self.signal_source = Signal()

