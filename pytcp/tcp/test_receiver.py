import random
import unittest

from .receiver import Receiver, SenderMessage
from .wrap32 import Wrap32


class TestReceiverConnect(unittest.TestCase):
    MAXH = 0xffff

    def test_connect1(self):
        test = Receiver(4000)
        self.assertEqual(test.receiver_message().winsize, 4000)
        self.assertIsNone(test.receiver_message().ackno)
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.bytes_pushed(), 0)
        test.receive_sender_message(SenderMessage(Wrap32(0), True, False, b''))
        self.assertEqual(test.receiver_message().ackno, Wrap32(1))
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.bytes_pushed(), 0)

    def test_connect2(self):
        test = Receiver(5453)
        self.assertIsNone(test.receiver_message().ackno)
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.bytes_pushed(), 0)
        test.receive_sender_message(
            SenderMessage(Wrap32(89347598), True, False, b''))
        self.assertEqual(test.receiver_message().ackno, Wrap32(89347599))
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.bytes_pushed(), 0)

    def test_connect3(self):
        test = Receiver(5435)
        self.assertIsNone(test.receiver_message().ackno)
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.bytes_pushed(), 0)
        test.receive_sender_message(
            SenderMessage(Wrap32(893475), False, False, b''))
        self.assertIsNone(test.receiver_message().ackno)
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.bytes_pushed(), 0)

    def test_connect4(self):
        test = Receiver(5435)
        self.assertIsNone(test.receiver_message().ackno)
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.bytes_pushed(), 0)
        test.receive_sender_message(
            SenderMessage(Wrap32(893475), False, True, b''))
        self.assertIsNone(test.receiver_message().ackno)
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.bytes_pushed(), 0)

    def test_connect5(self):
        test = Receiver(5435)
        self.assertIsNone(test.receiver_message().ackno)
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.bytes_pushed(), 0)
        test.receive_sender_message(
            SenderMessage(Wrap32(893475), False, True, b''))
        self.assertIsNone(test.receiver_message().ackno)
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.bytes_pushed(), 0)
        test.receive_sender_message(
            SenderMessage(Wrap32(89347598), True, False, b''))
        self.assertEqual(test.receiver_message().ackno, Wrap32(89347599))
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.bytes_pushed(), 0)

    def test_connect6(self):
        test = Receiver(4000)
        test.receive_sender_message(SenderMessage(Wrap32(5), True, True, b''))
        self.assertTrue(test.is_closed())
        self.assertEqual(test.receiver_message().ackno, Wrap32(7))
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.bytes_pushed(), 0)

    def test_winsize_0(self):
        test = Receiver(0)
        self.assertEqual(test.receiver_message().winsize, 0)

    def test_winsize_50(self):
        test = Receiver(50)
        self.assertEqual(test.receiver_message().winsize, 50)

    def test_winsize_max(self):
        test = Receiver(self.MAXH)
        self.assertEqual(test.receiver_message().winsize, self.MAXH)

    def test_winsize_max1(self):
        test = Receiver(self.MAXH + 1)
        self.assertEqual(test.receiver_message().winsize, self.MAXH)

    def test_winsize_max5(self):
        test = Receiver(self.MAXH + 5)
        self.assertEqual(test.receiver_message().winsize, self.MAXH)

    def test_winsize_10m(self):
        test = Receiver(10000000)
        self.assertEqual(test.receiver_message().winsize, self.MAXH)


class TestReceiverTransmit(unittest.TestCase):

    def test_transmit1(self):
        test = Receiver(4000)
        test.receive_sender_message(SenderMessage(Wrap32(0), True, False, b''))
        test.receive_sender_message(
            SenderMessage(Wrap32(1), False, False, b'abcd'))
        self.assertEqual(test.receiver_message().ackno, Wrap32(5))
        self.assertEqual(test.pop(), b'abcd')
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.bytes_pushed(), 4)

    def test_transmit2(self):
        test = Receiver(4000)
        isn = 384678
        test.receive_sender_message(
            SenderMessage(Wrap32(isn), True, False, b''))
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 1), False, False, b'abcd'))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 5))
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.bytes_pushed(), 4)
        self.assertEqual(test.pop(), b'abcd')
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 5), False, False, b'efgh'))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 9))
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.bytes_pushed(), 8)
        self.assertEqual(test.pop(), b'efgh')

    def test_transmit3(self):
        test = Receiver(4000)
        isn = 5
        test.receive_sender_message(
            SenderMessage(Wrap32(isn), True, False, b''))
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 1), False, False, b'abcd'))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 5))
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.bytes_pushed(), 4)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 5), False, False, b'efgh'))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 9))
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.bytes_pushed(), 8)
        self.assertEqual(test.pop(), b'abcdefgh')


class TestReceiverWin(unittest.TestCase):

    def test_winsize_decreases(self):
        test = Receiver(4000)
        cap = 4000
        isn = 23452
        test.receive_sender_message(
            SenderMessage(Wrap32(isn), True, False, b''))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 1))
        self.assertEqual(test.receiver_message().winsize, cap)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 1), False, False, b'abcd'))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 5))
        self.assertEqual(test.receiver_message().winsize, cap - 4)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 9), False, False, b'ijkl'))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 5))
        self.assertEqual(test.receiver_message().winsize, cap - 4)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 5), False, False, b'efgh'))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 13))
        self.assertEqual(test.receiver_message().winsize, cap - 12)

    def test_winsize_expands_after_pop(self):
        test = Receiver(4000)
        cap = 4000
        isn = 23452
        test.receive_sender_message(
            SenderMessage(Wrap32(isn), True, False, b''))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 1))
        self.assertEqual(test.receiver_message().winsize, cap)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 1), False, False, b'abcd'))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 5))
        self.assertEqual(test.receiver_message().winsize, cap - 4)
        self.assertEqual(test.pop(), b'abcd')
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 5))
        self.assertEqual(test.receiver_message().winsize, cap)

    def test_arriving_segment_with_high_seqno(self):
        test = Receiver(2)
        isn = 23452
        test.receive_sender_message(
            SenderMessage(Wrap32(isn), True, False, b''))
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 2), False, False, b'bc'))
        self.assertEqual(test.bytes_pushed(), 0)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 1), False, False, b'a'))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 3))
        self.assertEqual(test.receiver_message().winsize, 0)
        self.assertEqual(test.bytes_pushed(), 2)
        self.assertEqual(test.pop(), b'ab')
        self.assertEqual(test.receiver_message().winsize, 2)

    def test_arriving_segment_with_low_seqno(self):
        test = Receiver(4)
        cap = 4
        isn = 294058
        test.receive_sender_message(
            SenderMessage(Wrap32(isn), True, False, b''))
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 1), False, False, b'ab'))
        self.assertEqual(test.bytes_pushed(), 2)
        self.assertEqual(test.receiver_message().winsize, cap - 2)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 1), False, False, b'abc'))
        self.assertEqual(test.bytes_pushed(), 3)
        self.assertEqual(test.receiver_message().winsize, cap - 3)
        self.assertEqual(test.pop(), b'abc')

    def test_segment_overflowing_window_on_left_side(self):
        test = Receiver(4)
        isn = 23452
        test.receive_sender_message(
            SenderMessage(Wrap32(isn), True, False, b''))
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 1), False, False, b'ab'))
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 3), False, False, b'cdef'))
        self.assertEqual(test.pop(), b'abcd')

    def test_segment_matching_window(self):
        test = Receiver(4)
        isn = 23452
        test.receive_sender_message(
            SenderMessage(Wrap32(isn), True, False, b''))
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 1), False, False, b'ab'))
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 3), False, False, b'cd'))
        self.assertEqual(test.pop(), b'abcd')

    def test_byte_with_invalid_stream_index(self):
        test = Receiver(4)
        isn = 23452
        test.receive_sender_message(
            SenderMessage(Wrap32(isn), True, False, b''))
        test.receive_sender_message(
            SenderMessage(Wrap32(isn), False, False, b'a'))
        self.assertEqual(test.bytes_pushed(), 0)


class TestReceiverReorder(unittest.TestCase):

    def test_inwindow_later_segment(self):
        test = Receiver(2358)
        isn = random.getrandbits(32)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn), True, False, b''))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 1))
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 10), False, False, b'abcd'))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 1))
        self.assertEqual(test.pop(), b'')
        self.assertEqual(test.bytes_pending(), 4)
        self.assertEqual(test.bytes_pushed(), 0)

    def test_inwindow_later_segment_then_hole_filled(self):
        test = Receiver(2358)
        isn = random.getrandbits(32)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn), True, False, b''))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 1))
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 5), False, False, b'efgh'))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 1))
        self.assertEqual(test.pop(), b'')
        self.assertEqual(test.bytes_pending(), 4)
        self.assertEqual(test.bytes_pushed(), 0)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 1), False, False, b'abcd'))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 9))
        self.assertEqual(test.pop(), b'abcdefgh')
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.bytes_pushed(), 8)

    def test_holy_filled_bitbybit(self):
        test = Receiver(2358)
        isn = random.getrandbits(32)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn), True, False, b''))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 1))
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 5), False, False, b'efgh'))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 1))
        self.assertEqual(test.pop(), b'')
        self.assertEqual(test.bytes_pending(), 4)
        self.assertEqual(test.bytes_pushed(), 0)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 1), False, False, b'ab'))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 3))
        self.assertEqual(test.pop(), b'ab')
        self.assertEqual(test.bytes_pending(), 4)
        self.assertEqual(test.bytes_pushed(), 2)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 3), False, False, b'cd'))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 9))
        self.assertEqual(test.pop(), b'cdefgh')
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.bytes_pushed(), 8)

    def test_many_gaps_filled_bitbybit(self):
        test = Receiver(2358)
        isn = random.getrandbits(32)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn), True, False, b''))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 1))
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 5), False, False, b'e'))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 1))
        self.assertEqual(test.pop(), b'')
        self.assertEqual(test.bytes_pending(), 1)
        self.assertEqual(test.bytes_pushed(), 0)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 7), False, False, b'g'))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 1))
        self.assertEqual(test.pop(), b'')
        self.assertEqual(test.bytes_pending(), 2)
        self.assertEqual(test.bytes_pushed(), 0)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 3), False, False, b'c'))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 1))
        self.assertEqual(test.pop(), b'')
        self.assertEqual(test.bytes_pending(), 3)
        self.assertEqual(test.bytes_pushed(), 0)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 1), False, False, b'ab'))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 4))
        self.assertEqual(test.pop(), b'abc')
        self.assertEqual(test.bytes_pending(), 2)
        self.assertEqual(test.bytes_pushed(), 3)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 6), False, False, b'f'))
        self.assertEqual(test.bytes_pending(), 3)
        self.assertEqual(test.bytes_pushed(), 3)
        self.assertEqual(test.pop(), b'')
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 4), False, False, b'd'))
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.bytes_pushed(), 7)
        self.assertEqual(test.pop(), b'defg')

    def test_many_gaps_then_subsumed(self):
        test = Receiver(2358)
        isn = random.getrandbits(32)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn), True, False, b''))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 1))
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 5), False, False, b'e'))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 1))
        self.assertEqual(test.pop(), b'')
        self.assertEqual(test.bytes_pending(), 1)
        self.assertEqual(test.bytes_pushed(), 0)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 7), False, False, b'g'))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 1))
        self.assertEqual(test.pop(), b'')
        self.assertEqual(test.bytes_pending(), 2)
        self.assertEqual(test.bytes_pushed(), 0)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 3), False, False, b'c'))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 1))
        self.assertEqual(test.pop(), b'')
        self.assertEqual(test.bytes_pending(), 3)
        self.assertEqual(test.bytes_pushed(), 0)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 1), False, False, b'abcdefgh'))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 9))
        self.assertEqual(test.pop(), b'abcdefgh')
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.bytes_pushed(), 8)


class TestReceiverClose(unittest.TestCase):

    def test_close1(self):
        test = Receiver(4000)
        isn = random.getrandbits(32)
        self.assertIsNone(test.receiver_message().ackno)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 0), True, False, b''))
        self.assertFalse(test.is_closed())
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 1), False, True, b''))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 2))
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.peek(), b'')
        self.assertEqual(test.bytes_pushed(), 0)
        self.assertTrue(test.is_closed())

    def test_close2(self):
        test = Receiver(4000)
        isn = random.getrandbits(32)
        self.assertIsNone(test.receiver_message().ackno)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 0), True, False, b''))
        self.assertFalse(test.is_closed())
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 1), False, True, b'a'))
        self.assertTrue(test.is_closed())
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 3))
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.pop(), b'a')
        self.assertEqual(test.bytes_pushed(), 1)
        self.assertTrue(test.is_closed())
        self.assertTrue(test.is_finished())


class TestReceiverSpecial(unittest.TestCase):

    def test_segment_before_syn(self):
        test = Receiver(4000)
        isn = random.getrandbits(32)
        self.assertIsNone(test.receiver_message().ackno)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 1), False, False, b'hello'))
        self.assertIsNone(test.receiver_message().ackno)
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.pop(), b'')
        self.assertEqual(test.bytes_pushed(), 0)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn), True, False, b''))
        self.assertIsNotNone(test.receiver_message().ackno)
        self.assertFalse(test.is_closed())
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 1))

    def test_segment_with_syn_data(self):
        test = Receiver(4000)
        isn = random.getrandbits(32)
        self.assertIsNone(test.receiver_message().ackno)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn), True, False, b'Hello, CS144!'))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 14))
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.pop(), b'Hello, CS144!')
        self.assertFalse(test.is_closed())

    def test_empty_segment(self):
        test = Receiver(4000)
        isn = random.getrandbits(32)
        self.assertIsNone(test.receiver_message().ackno)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn), True, False, b''))
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 1))
        self.assertEqual(test.bytes_pending(), 0)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 1), True, False, b''))
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.bytes_pushed(), 0)
        self.assertFalse(test.is_closed())
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 5), True, False, b''))
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.bytes_pushed(), 0)
        self.assertFalse(test.is_closed())

    def test_segment_with_null_byte(self):
        test = Receiver(4000)
        isn = random.getrandbits(32)
        buf = b'Here\'s a null byte:\x00and it\'s gone.'
        self.assertIsNone(test.receiver_message().ackno)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn), True, False, b''))
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.bytes_pushed(), 0)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 1), False, False, buf))
        self.assertEqual(test.pop(), buf)
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 35))
        self.assertFalse(test.is_closed())

    def test_segment_with_data_fin(self):
        test = Receiver(4000)
        isn = random.getrandbits(32)
        self.assertIsNone(test.receiver_message().ackno)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn), True, False, b''))
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 1), False, True, b'Goodbye, CS144!'))
        self.assertTrue(test.is_closed())
        self.assertEqual(test.pop(), b'Goodbye, CS144!')
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 17))
        self.assertTrue(test.is_finished())

    def test_segment_with_fin(self):
        test = Receiver(4000)
        isn = random.getrandbits(32)
        self.assertIsNone(test.receiver_message().ackno)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn), True, False, b''))
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 2), False, True, b'oodbye, CS144!'))
        self.assertEqual(test.pop(), b'')
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 1))
        self.assertFalse(test.is_closed())
        test.receive_sender_message(
            SenderMessage(Wrap32(isn + 1), False, False, b'G'))
        self.assertTrue(test.is_closed())
        self.assertEqual(test.pop(), b'Goodbye, CS144!')
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 17))
        self.assertTrue(test.is_finished())

    def test_segment_with_syn_payload_fin(self):
        test = Receiver(4000)
        isn = random.getrandbits(32)
        self.assertIsNone(test.receiver_message().ackno)
        test.receive_sender_message(
            SenderMessage(Wrap32(isn), True, True,
                          b'Hello and goodbye, CS144!'))
        self.assertTrue(test.is_closed())
        self.assertEqual(test.receiver_message().ackno, Wrap32(isn + 27))
        self.assertEqual(test.bytes_pending(), 0)
        self.assertEqual(test.pop(), b'Hello and goodbye, CS144!')
        self.assertTrue(test.is_finished())


if __name__ == '__main__':
    unittest.main()
