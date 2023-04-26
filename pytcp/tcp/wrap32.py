class Wrap32:
    raw: int

    MASK32 = 0xffffffff
    MASK64_HIGH32 = 0xffffffff00000000
    ATOMIC_HIGH32 = 0x100000000

    def __init__(self, raw: int):
        self.raw = raw & self.MASK32

    def __eq__(self, other) -> bool:
        if isinstance(other, Wrap32):
            return self.raw == other.raw
        return self.raw == Wrap32(other).raw

    def __add__(self, other):
        if isinstance(other, Wrap32):
            return Wrap32(self.raw + other.raw)
        return Wrap32(self.raw + other)

    def wrap(self, n: int) -> 'Wrap32':
        return Wrap32(self.raw + n)

    def unwrap(self, w: 'Wrap32', checkpoint: int) -> int:
        n = (w.raw - self.raw) & self.MASK32
        cl = checkpoint & self.MASK32
        ch = checkpoint & self.MASK64_HIGH32
        if n == cl:
            return ch + n
        if (n - cl) & self.MASK32 < (cl - n) & self.MASK32:
            return ch + n if n > cl else ch + n + self.ATOMIC_HIGH32
        else:
            return ch + n if n < cl else \
                (n if ch == 0 else ch + n - self.ATOMIC_HIGH32)
