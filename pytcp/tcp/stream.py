class Stream:
    _cap: int
    _buf: bytes
    _is_closed: bool
    _has_error: bool
    _bytes_pushed: int
    _bytes_popped: int

    def __init__(self, cap: int = 65536):
        self._cap = cap
        self._buf = b''
        self._is_closed = False
        self._has_error = False
        self._bytes_pushed = 0
        self._bytes_popped = 0

    def push(self, buf: bytes):
        to_push = min(len(buf), self.cap())
        self._buf += buf[:to_push]
        self._bytes_pushed += to_push

    def close(self):
        self._is_closed = True

    def set_error(self):
        self._has_error = True

    def is_closed(self) -> bool:
        return self._is_closed

    def cap(self) -> int:
        return self._cap - len(self._buf)

    def bytes_pushed(self) -> int:
        return self._bytes_pushed

    def peek(self) -> bytes:
        return self._buf

    def pop(self, n: int = -1) -> bytes:
        if n < 0:
            n = self.bytes_buffered()
        to_pop = min(self.bytes_buffered(), n)
        buf, self._buf = self._buf[:to_pop], self._buf[to_pop:]
        self._bytes_popped += to_pop
        return buf

    def is_finished(self) -> bool:
        return self.bytes_buffered() == 0 and self.is_closed()

    def has_error(self) -> bool:
        return self._has_error

    def bytes_buffered(self) -> int:
        return len(self._buf)

    def bytes_popped(self) -> int:
        return self._bytes_popped
