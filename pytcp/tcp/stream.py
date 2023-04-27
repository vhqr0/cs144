from .defaults import STREAM_CAP


class Stream:
    __cap: int
    __buf: bytes
    __is_closed: bool
    __has_error: bool
    __bytes_pushed: int
    __bytes_popped: int

    def __init__(self, cap: int = STREAM_CAP):
        self.__cap = cap
        self.__buf = b''
        self.__is_closed = False
        self.__has_error = False
        self.__bytes_pushed = 0
        self.__bytes_popped = 0

    def push(self, buf: bytes):
        to_push = min(len(buf), self.cap())
        self.__buf += buf[:to_push]
        self.__bytes_pushed += to_push

    def close(self):
        self.__is_closed = True

    def set_error(self):
        self.__has_error = True

    def is_closed(self) -> bool:
        return self.__is_closed

    def cap(self) -> int:
        return self.__cap - len(self.__buf)

    def bytes_pushed(self) -> int:
        return self.__bytes_pushed

    def peek(self) -> bytes:
        return self.__buf

    def pop(self, n: int = -1) -> bytes:
        if n < 0:
            n = self.bytes_buffered()
        to_pop = min(self.bytes_buffered(), n)
        buf, self.__buf = self.__buf[:to_pop], self.__buf[to_pop:]
        self.__bytes_popped += to_pop
        return buf

    def is_finished(self) -> bool:
        return self.bytes_buffered() == 0 and self.is_closed()

    def has_error(self) -> bool:
        return self.__has_error

    def bytes_buffered(self) -> int:
        return len(self.__buf)

    def bytes_popped(self) -> int:
        return self.__bytes_popped
