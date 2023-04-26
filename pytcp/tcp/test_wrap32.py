import random
import unittest

from .wrap32 import Wrap32


class TestWrap32(unittest.TestCase):

    def test_cmp(self):
        self.assertTrue(Wrap32(3) != Wrap32(1))
        self.assertFalse(Wrap32(3) == Wrap32(1))
        for i in range(32768):
            n = random.getrandbits(32)
            diff = random.getrandbits(8)
            m = (n + diff) & 0xffffffff
            self.assertEqual(Wrap32(n) == Wrap32(m), n == m)
            self.assertEqual(Wrap32(n) != Wrap32(m), n != m)

    def test_wrap(self):
        self.assertEqual(Wrap32(0).wrap(3 * (1 << 32)), Wrap32(0))
        self.assertEqual(Wrap32(15).wrap(3 * (1 << 32) + 17), Wrap32(32))
        self.assertEqual(Wrap32(15).wrap(7 * (1 << 32) - 2), Wrap32(13))

    def test_unwrap(self):
        MAXI, MAXi = 0xffffffff, 0x7fffffff
        self.assertEqual(Wrap32(0).unwrap(Wrap32(1), 0), 1)
        self.assertEqual(Wrap32(0).unwrap(Wrap32(1), MAXI), (1 << 32) + 1)
        self.assertEqual(
            Wrap32(0).unwrap(Wrap32(MAXI - 1), 3 * (1 << 32)),
            3 * (1 << 32) - 2)
        self.assertEqual(
            Wrap32(0).unwrap(Wrap32(MAXI - 10), 3 * (1 << 32)),
            3 * (1 << 32) - 11)
        self.assertEqual(Wrap32(0).unwrap(Wrap32(MAXI), 0), MAXI)
        self.assertEqual(Wrap32(16).unwrap(Wrap32(16), 0), 0)
        self.assertEqual(Wrap32(16).unwrap(Wrap32(15), 0), MAXI)
        self.assertEqual(Wrap32(MAXi).unwrap(Wrap32(0), 0), MAXi + 2)
        self.assertEqual(Wrap32(MAXi).unwrap(Wrap32(MAXI), 0), 1 << 31)
        self.assertEqual(Wrap32(1 << 31).unwrap(Wrap32(MAXI), 0), MAXI >> 1)

    def __test_roundtrip(self, isn: Wrap32, n: int, checkpoint: int):
        self.assertEqual(isn.unwrap(isn.wrap(n), checkpoint), n)

    def test_roundtrip(self):
        big_offset = (1 << 31) - 1
        for i in range(10000):
            isn = Wrap32(random.getrandbits(32))
            n = random.getrandbits(63)
            offset = random.getrandbits(31)

            self.__test_roundtrip(isn, n, n)
            self.__test_roundtrip(isn, n + 1, n)
            self.__test_roundtrip(isn, n - 1, n)
            self.__test_roundtrip(isn, n + offset, n)
            self.__test_roundtrip(isn, n - offset, n)
            self.__test_roundtrip(isn, n + big_offset, n)
            self.__test_roundtrip(isn, n - big_offset, n)


if __name__ == '__main__':
    unittest.main()
