import random
import unittest

from .reassembler import Reassembler


class TestReassemblerSingle(unittest.TestCase):

    def test_construction(self):
        test = Reassembler(65000)
        self.assertEqual(test.bytes_pushed(), 0)
        self.assertFalse(test.is_finished())

    def test_insert_a0(self):
        test = Reassembler(65000)
        test.insert(0, b'a')
        self.assertEqual(test.bytes_pushed(), 1)
        self.assertEqual(test.pop(), b'a')
        self.assertFalse(test.is_finished())

    def test_insert_a0_eof(self):
        test = Reassembler(65000)
        test.insert(0, b'a', True)
        self.assertEqual(test.bytes_pushed(), 1)
        self.assertEqual(test.pop(), b'a')
        self.assertTrue(test.is_finished())

    def test_empty_stream(self):
        test = Reassembler(65000)
        test.insert(0, b'', True)
        self.assertEqual(test.bytes_pushed(), 0)
        self.assertTrue(test.is_finished())

    def test_insert_b0_eof(self):
        test = Reassembler(65000)
        test.insert(0, b'b', True)
        self.assertEqual(test.bytes_pushed(), 1)
        self.assertEqual(test.pop(), b'b')
        self.assertTrue(test.is_finished())

    def test_insert_0(self):
        test = Reassembler(65000)
        test.insert(0, b'')
        self.assertEqual(test.bytes_pushed(), 0)
        self.assertFalse(test.is_finished())


class TestReassemblerCap(unittest.TestCase):

    def test_all_within_cap(self):
        test = Reassembler(2)
        test.insert(0, b'ab')
        self.assertEqual(test.bytes_pushed(), 2)
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.pop(), b'ab')
        test.insert(2, b'cd')
        self.assertEqual(test.bytes_pushed(), 4)
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.pop(), b'cd')
        test.insert(4, b'ef')
        self.assertEqual(test.bytes_pushed(), 6)
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.pop(), b'ef')

    def test_insert_beyond_cap(self):
        test = Reassembler(2)
        test.insert(0, b'ab')
        self.assertEqual(test.bytes_pushed(), 2)
        self.assertEqual(test.bytes_pending(), 0)
        test.insert(2, b'cd')
        self.assertEqual(test.bytes_pushed(), 2)
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.pop(), b'ab')
        self.assertEqual(test.bytes_pushed(), 2)
        self.assertEqual(test.bytes_pending(), 0)
        test.insert(2, b'cd')
        self.assertEqual(test.bytes_pushed(), 4)
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.pop(), b'cd')

    def test_overlapping_insert(self):
        test = Reassembler(1)
        test.insert(0, b'ab')
        self.assertEqual(test.bytes_pushed(), 1)
        self.assertEqual(test.bytes_pending(), 0)
        test.insert(0, b'ab')
        self.assertEqual(test.bytes_pushed(), 1)
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.pop(), b'a')
        self.assertEqual(test.bytes_pushed(), 1)
        self.assertEqual(test.bytes_pending(), 0)
        test.insert(0, b'abc')
        self.assertEqual(test.bytes_pushed(), 2)
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.pop(), b'b')
        self.assertEqual(test.bytes_pushed(), 2)
        self.assertEqual(test.bytes_pending(), 0)

    def test_insert_beyond_cap_repeated(self):
        test = Reassembler(2)
        test.insert(1, b'b')
        self.assertEqual(test.bytes_pushed(), 0)
        self.assertEqual(test.bytes_pending(), 1)
        test.insert(2, b'bX')
        self.assertEqual(test.bytes_pushed(), 0)
        self.assertEqual(test.bytes_pending(), 1)
        test.insert(0, b'a')
        self.assertEqual(test.bytes_pushed(), 2)
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.pop(), b'ab')
        test.insert(1, b'bc')
        self.assertEqual(test.bytes_pushed(), 3)
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.pop(), b'c')


class TestReassemblerSeq(unittest.TestCase):

    def test_seq1(self):
        test = Reassembler(65000)
        test.insert(0, b'abcd')
        self.assertEqual(test.bytes_pushed(), 4)
        self.assertEqual(test.pop(), b'abcd')
        self.assertFalse(test.is_finished())
        test.insert(4, b'efgh')
        self.assertEqual(test.bytes_pushed(), 8)
        self.assertEqual(test.pop(), b'efgh')
        self.assertFalse(test.is_finished())

    def test_seq2(self):
        test = Reassembler(65000)
        test.insert(0, b'abcd')
        self.assertEqual(test.bytes_pushed(), 4)
        self.assertFalse(test.is_finished())
        test.insert(4, b'efgh')
        self.assertEqual(test.bytes_pushed(), 8)
        self.assertEqual(test.pop(), b'abcdefgh')
        self.assertFalse(test.is_finished())

    def test_seq3(self):
        test = Reassembler(65000)
        buf = b''
        for i in range(100):
            self.assertEqual(test.bytes_pushed(), 4 * i)
            test.insert(4 * i, b'abcd')
            self.assertFalse(test.is_finished())
            buf += b'abcd'
        self.assertEqual(test.pop(), buf)
        self.assertFalse(test.is_finished())

    def test_seq4(self):
        test = Reassembler(65000)
        for i in range(100):
            self.assertEqual(test.bytes_pushed(), 4 * i)
            test.insert(4 * i, b'abcd')
            self.assertFalse(test.is_finished())
            self.assertEqual(test.pop(), b'abcd')


class TestReassemblerDup(unittest.TestCase):

    def test_dup1(self):
        test = Reassembler(65000)
        test.insert(0, b'abcd')
        self.assertEqual(test.bytes_pushed(), 4)
        self.assertEqual(test.pop(), b'abcd')
        self.assertFalse(test.is_finished())
        test.insert(0, b'abcd')
        self.assertEqual(test.bytes_pushed(), 4)
        self.assertEqual(test.pop(), b'')
        self.assertFalse(test.is_finished())

    def test_dup2(self):
        test = Reassembler(65000)
        test.insert(0, b'abcd')
        self.assertEqual(test.bytes_pushed(), 4)
        self.assertEqual(test.pop(), b'abcd')
        self.assertFalse(test.is_finished())
        test.insert(4, b'abcd')
        self.assertEqual(test.bytes_pushed(), 8)
        self.assertEqual(test.pop(), b'abcd')
        self.assertFalse(test.is_finished())
        test.insert(0, b'abcd')
        self.assertEqual(test.bytes_pushed(), 8)
        self.assertEqual(test.pop(), b'')
        self.assertFalse(test.is_finished())
        test.insert(4, b'abcd')
        self.assertEqual(test.bytes_pushed(), 8)
        self.assertEqual(test.pop(), b'')
        self.assertFalse(test.is_finished())

    def test_dup3(self):
        test = Reassembler(65000)
        test.insert(0, b'abcdefgh')
        self.assertEqual(test.bytes_pushed(), 8)
        self.assertEqual(test.pop(), b'abcdefgh')
        self.assertFalse(test.is_finished())
        buf = b'abcdefgh'
        for i in range(1000):
            j = random.randint(0, 7)
            k = random.randint(j, 8)
            test.insert(j, buf[j:k])
            self.assertEqual(test.bytes_pushed(), 8)
            self.assertEqual(test.pop(), b'')
            self.assertFalse(test.is_finished())

    def test_dup4(self):
        test = Reassembler(65000)
        test.insert(0, b'abcd')
        self.assertEqual(test.bytes_pushed(), 4)
        self.assertEqual(test.pop(), b'abcd')
        self.assertFalse(test.is_finished())
        test.insert(0, b'abcdef')
        self.assertEqual(test.bytes_pushed(), 6)
        self.assertEqual(test.pop(), b'ef')
        self.assertFalse(test.is_finished())


class TestReassemblerHoles(unittest.TestCase):

    def test_holes1(self):
        test = Reassembler(65000)
        test.insert(1, b'b')
        self.assertEqual(test.bytes_pushed(), 0)
        self.assertEqual(test.pop(), b'')
        self.assertFalse(test.is_finished())

    def test_holes2(self):
        test = Reassembler(65000)
        test.insert(1, b'b')
        test.insert(0, b'a')
        self.assertEqual(test.bytes_pushed(), 2)
        self.assertEqual(test.pop(), b'ab')
        self.assertFalse(test.is_finished())

    def test_holes3(self):
        test = Reassembler(65000)
        test.insert(1, b'b', True)
        self.assertEqual(test.bytes_pushed(), 0)
        self.assertEqual(test.pop(), b'')
        self.assertFalse(test.is_finished())
        test.insert(0, b'a')
        self.assertEqual(test.bytes_pushed(), 2)
        self.assertEqual(test.pop(), b'ab')
        self.assertTrue(test.is_finished())

    def test_holes4(self):
        test = Reassembler(65000)
        test.insert(1, b'b')
        test.insert(0, b'ab')
        self.assertEqual(test.bytes_pushed(), 2)
        self.assertEqual(test.pop(), b'ab')
        self.assertFalse(test.is_finished())

    def test_holes5(self):
        test = Reassembler(65000)
        test.insert(1, b'b')
        self.assertEqual(test.bytes_pushed(), 0)
        self.assertEqual(test.pop(), b'')
        self.assertFalse(test.is_finished())
        test.insert(3, b'd')
        self.assertEqual(test.bytes_pushed(), 0)
        self.assertEqual(test.pop(), b'')
        self.assertFalse(test.is_finished())
        test.insert(2, b'c')
        self.assertEqual(test.bytes_pushed(), 0)
        self.assertEqual(test.pop(), b'')
        self.assertFalse(test.is_finished())
        test.insert(0, b'a')
        self.assertEqual(test.bytes_pushed(), 4)
        self.assertEqual(test.pop(), b'abcd')
        self.assertFalse(test.is_finished())

    def test_holes6(self):
        test = Reassembler(65000)
        test.insert(1, b'b')
        self.assertEqual(test.bytes_pushed(), 0)
        self.assertEqual(test.pop(), b'')
        self.assertFalse(test.is_finished())
        test.insert(3, b'd')
        self.assertEqual(test.bytes_pushed(), 0)
        self.assertEqual(test.pop(), b'')
        self.assertFalse(test.is_finished())
        test.insert(0, b'abc')
        self.assertEqual(test.bytes_pushed(), 4)
        self.assertEqual(test.pop(), b'abcd')
        self.assertFalse(test.is_finished())

    def test_holes7(self):
        test = Reassembler(65000)
        test.insert(1, b'b')
        self.assertEqual(test.bytes_pushed(), 0)
        self.assertEqual(test.pop(), b'')
        self.assertFalse(test.is_finished())
        test.insert(3, b'd')
        self.assertEqual(test.bytes_pushed(), 0)
        self.assertEqual(test.pop(), b'')
        self.assertFalse(test.is_finished())
        test.insert(0, b'a')
        self.assertEqual(test.bytes_pushed(), 2)
        self.assertEqual(test.pop(), b'ab')
        self.assertFalse(test.is_finished())
        test.insert(2, b'c')
        self.assertEqual(test.bytes_pushed(), 4)
        self.assertEqual(test.pop(), b'cd')
        self.assertFalse(test.is_finished())
        test.insert(4, b'', True)
        self.assertEqual(test.bytes_pushed(), 4)
        self.assertEqual(test.pop(), b'')
        self.assertTrue(test.is_finished())


class TestReassemblerOverlapping(unittest.TestCase):

    def test_overlapping_assembled_unread_section(self):
        test = Reassembler(1000)
        test.insert(0, b'a')
        test.insert(0, b'ab')
        self.assertEqual(test.bytes_pushed(), 2)
        self.assertEqual(test.pop(), b'ab')

    def test_overlapping_assembled_read_section(self):
        test = Reassembler(1000)
        test.insert(0, b'a')
        self.assertEqual(test.pop(), b'a')
        test.insert(0, b'ab')
        self.assertEqual(test.pop(), b'b')
        self.assertEqual(test.bytes_pushed(), 2)

    def test_overlapping_unassembled_section_to_fill_hole(self):
        test = Reassembler(1000)
        test.insert(1, b'b')
        self.assertEqual(test.pop(), b'')
        test.insert(0, b'ab')
        self.assertEqual(test.pop(), b'ab')
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.bytes_pushed(), 2)

    def test_overlapping_unassembled_section(self):
        test = Reassembler(1000)
        test.insert(1, b'b')
        self.assertEqual(test.pop(), b'')
        test.insert(1, b'bc')
        self.assertEqual(test.pop(), b'')
        self.assertEqual(test.bytes_pending(), 2)
        self.assertEqual(test.bytes_pushed(), 0)

    def test_overlapping_unassembled_section2(self):
        test = Reassembler(1000)
        test.insert(2, b'c')
        self.assertEqual(test.pop(), b'')
        test.insert(1, b'bcd')
        self.assertEqual(test.pop(), b'')
        self.assertEqual(test.bytes_pending(), 3)
        self.assertEqual(test.bytes_pushed(), 0)

    def test_overlapping_multiple_unassembled_section(self):
        test = Reassembler(1000)
        test.insert(1, b'b')
        test.insert(3, b'd')
        self.assertEqual(test.pop(), b'')
        test.insert(1, b'bcde')
        self.assertEqual(test.pop(), b'')
        self.assertEqual(test.bytes_pushed(), 0)
        self.assertEqual(test.bytes_pending(), 4)

    def test_insert_over_existing_section(self):
        test = Reassembler(1000)
        test.insert(2, b'c')
        test.insert(1, b'bcd')
        self.assertEqual(test.pop(), b'')
        self.assertEqual(test.bytes_pushed(), 0)
        self.assertEqual(test.bytes_pending(), 3)
        test.insert(0, b'a')
        self.assertEqual(test.pop(), b'abcd')
        self.assertEqual(test.bytes_pushed(), 4)
        self.assertEqual(test.bytes_pending(), 0)

    def test_insert_within_existing_section(self):
        test = Reassembler(1000)
        test.insert(1, b'bcd')
        test.insert(2, b'c')
        self.assertEqual(test.pop(), b'')
        self.assertEqual(test.bytes_pushed(), 0)
        self.assertEqual(test.bytes_pending(), 3)
        test.insert(0, b'a')
        self.assertEqual(test.pop(), b'abcd')
        self.assertEqual(test.bytes_pushed(), 4)
        self.assertEqual(test.bytes_pending(), 0)


if __name__ == '__main__':
    unittest.main()
