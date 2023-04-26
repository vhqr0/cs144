import unittest

from .stream import Stream


class TestStreamBasics(unittest.TestCase):

    def __test_all_zeros(self, test: Stream):
        self.assertEqual(test.bytes_buffered(), 0)
        self.assertEqual(test.cap(), 15)
        self.assertEqual(test.bytes_pushed(), 0)
        self.assertEqual(test.bytes_popped(), 0)

    def test_construction(self):
        test = Stream(15)
        self.assertFalse(test.is_closed())
        self.assertFalse(test.is_finished())
        self.assertFalse(test.has_error())
        self.__test_all_zeros(test)

    def test_close(self):
        test = Stream(15)
        test.close()
        self.assertTrue(test.is_closed())
        self.assertTrue(test.is_finished())
        self.assertFalse(test.has_error())
        self.__test_all_zeros(test)

    def test_set_error(self):
        test = Stream(15)
        test.set_error()
        self.assertFalse(test.is_closed())
        self.assertFalse(test.is_finished())
        self.assertTrue(test.has_error())
        self.__test_all_zeros(test)


class TestStreamCap(unittest.TestCase):

    def test_overwrite(self):
        test = Stream(2)
        test.push(b'cat')
        self.assertFalse(test.is_closed())
        self.assertFalse(test.bytes_buffered() == 0)
        self.assertFalse(test.is_finished())
        self.assertEqual(test.bytes_popped(), 0)
        self.assertEqual(test.bytes_pushed(), 2)
        self.assertEqual(test.cap(), 0)
        self.assertEqual(test.bytes_buffered(), 2)
        self.assertEqual(test.peek(), b'ca')
        test.push(b't')
        self.assertFalse(test.is_closed())
        self.assertFalse(test.bytes_buffered() == 0)
        self.assertFalse(test.is_finished())
        self.assertEqual(test.bytes_popped(), 0)
        self.assertEqual(test.bytes_pushed(), 2)
        self.assertEqual(test.cap(), 0)
        self.assertEqual(test.bytes_buffered(), 2)
        self.assertEqual(test.peek(), b'ca')

    def test_overwrite_clear_overwrite(self):
        test = Stream(2)
        test.push(b'cat')
        self.assertEqual(test.bytes_pushed(), 2)
        test.pop(2)
        test.push(b'tac')
        self.assertFalse(test.is_closed())
        self.assertFalse(test.bytes_buffered() == 0)
        self.assertFalse(test.is_finished())
        self.assertEqual(test.bytes_popped(), 2)
        self.assertEqual(test.bytes_pushed(), 4)
        self.assertEqual(test.cap(), 0)
        self.assertEqual(test.bytes_buffered(), 2)
        self.assertEqual(test.peek(), b'ta')

    def test_overwrite_pop_overwrite(self):
        test = Stream(2)
        test.push(b'cat')
        self.assertEqual(test.bytes_pushed(), 2)
        test.pop(1)
        test.push(b'tac')
        self.assertFalse(test.is_closed())
        self.assertFalse(test.bytes_buffered() == 0)
        self.assertFalse(test.is_finished())
        self.assertEqual(test.bytes_popped(), 1)
        self.assertEqual(test.bytes_pushed(), 3)
        self.assertEqual(test.cap(), 0)
        self.assertEqual(test.bytes_buffered(), 2)
        self.assertEqual(test.peek(), b'at')

    def test_peeks(self):
        test = Stream(2)
        test.push(b'')
        test.push(b'')
        test.push(b'')
        test.push(b'')
        test.push(b'')
        test.push(b'cat')
        test.push(b'')
        test.push(b'')
        test.push(b'')
        test.push(b'')
        test.push(b'')
        self.assertEqual(test.peek(), b'ca')
        self.assertEqual(test.peek(), b'ca')
        self.assertEqual(test.bytes_buffered(), 2)
        self.assertEqual(test.peek(), b'ca')
        self.assertEqual(test.peek(), b'ca')
        test.pop(1)
        test.push(b'')
        test.push(b'')
        test.push(b'')
        self.assertEqual(test.peek(), b'a')
        self.assertEqual(test.peek(), b'a')
        self.assertEqual(test.bytes_buffered(), 1)


class TestStreamOneWrite(unittest.TestCase):

    def test_write_end_pop(self):
        test = Stream(15)
        test.push(b'cat')
        self.assertFalse(test.is_closed())
        self.assertFalse(test.bytes_buffered() == 0)
        self.assertFalse(test.is_finished())
        self.assertEqual(test.bytes_popped(), 0)
        self.assertEqual(test.bytes_pushed(), 3)
        self.assertEqual(test.cap(), 12)
        self.assertEqual(test.bytes_buffered(), 3)
        self.assertEqual(test.peek(), b'cat')
        test.close()
        self.assertTrue(test.is_closed())
        self.assertFalse(test.bytes_buffered() == 0)
        self.assertFalse(test.is_finished())
        self.assertEqual(test.bytes_popped(), 0)
        self.assertEqual(test.bytes_pushed(), 3)
        self.assertEqual(test.cap(), 12)
        self.assertEqual(test.bytes_buffered(), 3)
        self.assertEqual(test.peek(), b'cat')
        test.pop(3)
        self.assertTrue(test.is_closed())
        self.assertTrue(test.bytes_buffered() == 0)
        self.assertTrue(test.is_finished())
        self.assertEqual(test.bytes_popped(), 3)
        self.assertEqual(test.bytes_pushed(), 3)
        self.assertEqual(test.cap(), 15)
        self.assertEqual(test.bytes_buffered(), 0)

    def test_write_pop_end(self):
        test = Stream(15)
        test.push(b'cat')
        self.assertFalse(test.is_closed())
        self.assertFalse(test.bytes_buffered() == 0)
        self.assertFalse(test.is_finished())
        self.assertEqual(test.bytes_popped(), 0)
        self.assertEqual(test.bytes_pushed(), 3)
        self.assertEqual(test.cap(), 12)
        self.assertEqual(test.bytes_buffered(), 3)
        self.assertEqual(test.peek(), b'cat')
        test.pop(3)
        self.assertFalse(test.is_closed())
        self.assertTrue(test.bytes_buffered() == 0)
        self.assertFalse(test.is_finished())
        self.assertEqual(test.bytes_popped(), 3)
        self.assertEqual(test.bytes_pushed(), 3)
        self.assertEqual(test.cap(), 15)
        self.assertEqual(test.bytes_buffered(), 0)
        test.close()
        self.assertTrue(test.is_closed())
        self.assertTrue(test.bytes_buffered() == 0)
        self.assertTrue(test.is_finished())
        self.assertEqual(test.bytes_popped(), 3)
        self.assertEqual(test.bytes_pushed(), 3)
        self.assertEqual(test.cap(), 15)
        self.assertEqual(test.bytes_buffered(), 0)

    def test_write_pop2_end(self):
        test = Stream(15)
        test.push(b'cat')
        self.assertFalse(test.is_closed())
        self.assertFalse(test.bytes_buffered() == 0)
        self.assertFalse(test.is_finished())
        self.assertEqual(test.bytes_popped(), 0)
        self.assertEqual(test.bytes_pushed(), 3)
        self.assertEqual(test.cap(), 12)
        self.assertEqual(test.bytes_buffered(), 3)
        self.assertEqual(test.peek(), b'cat')
        test.pop(1)
        self.assertFalse(test.is_closed())
        self.assertFalse(test.bytes_buffered() == 0)
        self.assertFalse(test.is_finished())
        self.assertEqual(test.bytes_popped(), 1)
        self.assertEqual(test.bytes_pushed(), 3)
        self.assertEqual(test.cap(), 13)
        self.assertEqual(test.bytes_buffered(), 2)
        self.assertEqual(test.peek(), b'at')
        test.pop(2)
        self.assertFalse(test.is_closed())
        self.assertTrue(test.bytes_buffered() == 0)
        self.assertFalse(test.is_finished())
        self.assertEqual(test.bytes_popped(), 3)
        self.assertEqual(test.bytes_pushed(), 3)
        self.assertEqual(test.cap(), 15)
        self.assertEqual(test.bytes_buffered(), 0)
        test.close()
        self.assertTrue(test.is_closed())
        self.assertTrue(test.bytes_buffered() == 0)
        self.assertTrue(test.is_finished())
        self.assertEqual(test.bytes_popped(), 3)
        self.assertEqual(test.bytes_pushed(), 3)
        self.assertEqual(test.cap(), 15)
        self.assertEqual(test.bytes_buffered(), 0)


class TestStreamTwoWrites(unittest.TestCase):

    def test_write_write_end_pop_pop(self):
        test = Stream(15)
        test.push(b'cat')
        self.assertFalse(test.is_closed())
        self.assertFalse(test.bytes_buffered() == 0)
        self.assertFalse(test.is_finished())
        self.assertEqual(test.bytes_popped(), 0)
        self.assertEqual(test.bytes_pushed(), 3)
        self.assertEqual(test.cap(), 12)
        self.assertEqual(test.bytes_buffered(), 3)
        self.assertEqual(test.peek(), b'cat')
        test.push(b'tac')
        self.assertFalse(test.is_closed())
        self.assertFalse(test.bytes_buffered() == 0)
        self.assertFalse(test.is_finished())
        self.assertEqual(test.bytes_popped(), 0)
        self.assertEqual(test.bytes_pushed(), 6)
        self.assertEqual(test.cap(), 9)
        self.assertEqual(test.bytes_buffered(), 6)
        self.assertEqual(test.peek(), b'cattac')
        test.close()
        self.assertTrue(test.is_closed())
        self.assertFalse(test.bytes_buffered() == 0)
        self.assertFalse(test.is_finished())
        self.assertEqual(test.bytes_popped(), 0)
        self.assertEqual(test.bytes_pushed(), 6)
        self.assertEqual(test.cap(), 9)
        self.assertEqual(test.bytes_buffered(), 6)
        self.assertEqual(test.peek(), b'cattac')
        test.pop(2)
        self.assertTrue(test.is_closed())
        self.assertFalse(test.bytes_buffered() == 0)
        self.assertFalse(test.is_finished())
        self.assertEqual(test.bytes_popped(), 2)
        self.assertEqual(test.bytes_pushed(), 6)
        self.assertEqual(test.cap(), 11)
        self.assertEqual(test.bytes_buffered(), 4)
        self.assertEqual(test.peek(), b'ttac')
        test.pop(4)
        self.assertTrue(test.is_closed())
        self.assertTrue(test.bytes_buffered() == 0)
        self.assertTrue(test.is_finished())
        self.assertEqual(test.bytes_popped(), 6)
        self.assertEqual(test.bytes_pushed(), 6)
        self.assertEqual(test.cap(), 15)
        self.assertEqual(test.bytes_buffered(), 0)

    def test_write_pop_write_end_pop(self):
        test = Stream(15)
        test.push(b'cat')
        self.assertFalse(test.is_closed())
        self.assertFalse(test.bytes_buffered() == 0)
        self.assertFalse(test.is_finished())
        self.assertEqual(test.bytes_popped(), 0)
        self.assertEqual(test.bytes_pushed(), 3)
        self.assertEqual(test.cap(), 12)
        self.assertEqual(test.bytes_buffered(), 3)
        self.assertEqual(test.peek(), b'cat')
        test.pop(2)
        self.assertFalse(test.is_closed())
        self.assertFalse(test.bytes_buffered() == 0)
        self.assertFalse(test.is_finished())
        self.assertEqual(test.bytes_popped(), 2)
        self.assertEqual(test.bytes_pushed(), 3)
        self.assertEqual(test.cap(), 14)
        self.assertEqual(test.bytes_buffered(), 1)
        self.assertEqual(test.peek(), b't')
        test.push(b'tac')
        self.assertFalse(test.is_closed())
        self.assertFalse(test.bytes_buffered() == 0)
        self.assertFalse(test.is_finished())
        self.assertEqual(test.bytes_popped(), 2)
        self.assertEqual(test.bytes_pushed(), 6)
        self.assertEqual(test.cap(), 11)
        self.assertEqual(test.bytes_buffered(), 4)
        self.assertEqual(test.peek(), b'ttac')
        test.close()
        self.assertTrue(test.is_closed())
        self.assertFalse(test.bytes_buffered() == 0)
        self.assertFalse(test.is_finished())
        self.assertEqual(test.bytes_popped(), 2)
        self.assertEqual(test.bytes_pushed(), 6)
        self.assertEqual(test.cap(), 11)
        self.assertEqual(test.bytes_buffered(), 4)
        self.assertEqual(test.peek(), b'ttac')
        test.pop(4)
        self.assertTrue(test.is_closed())
        self.assertTrue(test.bytes_buffered() == 0)
        self.assertTrue(test.is_finished())
        self.assertEqual(test.bytes_popped(), 6)
        self.assertEqual(test.bytes_pushed(), 6)
        self.assertEqual(test.cap(), 15)
        self.assertEqual(test.bytes_buffered(), 0)


if __name__ == '__main__':
    unittest.main()
