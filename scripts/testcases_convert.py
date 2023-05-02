#!/usr/bin/env python3
"""Convert cs144 test cases from c++ to python."""
import re
from functools import cache
from typing import Optional


class Converter:
    converters: list[type['Converter']] = []
    exec_re = re.compile(r'^test.execute\((.*)\);$')
    cstr_sub_re = re.compile(r'"([^"]*)"')
    cbool2bool = {'true': 'True', 'false': 'False'}
    cbool2gt = {'true': 'Greater', 'false': 'LessEqual'}
    cbool2lt = {'true': 'Less', 'false': 'GreaterEqual'}
    cbool2ge = {'true': 'GreaterEqual', 'false': 'Less'}
    cbool2le = {'true': 'LessEqual', 'false': 'Greater'}
    cbool2eq = {'true': 'Equal', 'false': 'NotEqual'}
    cbool2neq = {'true': 'NotEqual', 'false': 'Equal'}
    cbool2none = {'true': 'IsNone', 'false': 'IsNotNone'}
    cbool2notnone = {'true': 'IsNotNone', 'false': 'IsNone'}

    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        cls.converters.append(cls)

    @classmethod
    def cstr_sub(cls, s: str) -> str:
        return cls.cstr_sub_re.sub(r"b'\1'", s)

    @classmethod
    def convert_line(cls, line: str) -> str:
        line = line.strip()
        if len(line) == 0:
            return ''

        exec_match = cls.exec_re.match(line)
        if exec_match is None:
            return f'# {line}'

        action = exec_match[1].strip()
        for converter_type in cls.converters:
            out = converter_type.convert_action(action)
            if out is not None:
                return 8 * ' ' + out

        return 8 * ' ' + f'raise ValueError({repr(action)})'

    @classmethod
    def convert_action(cls, action: str) -> Optional[str]:
        raise NotImplementedError


class FuncArgsMixin:
    action_re = re.compile(r'^([^\s]+)\s*[\{\(](.*)[\}\)]$')

    @classmethod
    @cache
    def get_func_args(cls, action: str) -> Optional[tuple[str, str]]:
        action_match = cls.action_re.match(action)
        if action_match is None:
            return None
        func = action_match[1].strip()
        args = action_match[2].strip()
        return func, args

    @classmethod
    def get_args(cls, action: str, efunc: str) -> Optional[str]:
        funcargs = cls.get_func_args(action)
        if funcargs is None:
            return None
        func, args = funcargs
        if func != efunc:
            return None
        return args

    @classmethod
    def expect_func(cls, action: str, efunc: str) -> bool:
        return cls.get_args(action, efunc) is not None


class Wrap32StripMixin:
    wrap32_re = re.compile(r'^Wrap32 \{(.*)\}$')

    @classmethod
    def wrap32_strip(cls, arg: str) -> str:
        wrap32_match = cls.wrap32_re.match(arg)
        if wrap32_match is not None:
            return wrap32_match[1].strip()
        return arg


class CopyArgsConverter(FuncArgsMixin, Converter):
    """
    Example:
      test.execute( Close {} )
      => test.close()

      test.execute( Push { "hello" } )
      => test.push(b'hello')
    """
    func_dict = {
        # 'Close': 'test.close',
        # 'Push': 'test.push',
        'SetError': 'test.set_error',
        'Pop': 'test.pop',
    }

    @classmethod
    def convert_action(cls, action: str) -> Optional[str]:
        funcargs = cls.get_func_args(action)
        if funcargs is None:
            return None
        func, args = funcargs
        out = cls.func_dict.get(func)
        if out is None:
            return None
        return f'{out}({args})'


class BoolAssertConverter(FuncArgsMixin, Converter):
    """
    Example:
      test.execute( IsClosed { false } )
      => self.assertFalse(test.is_closed())
    """
    func_dict: dict[str, str] = {
        'IsClosed': 'test.is_closed()',
        'IsFinished': 'test.is_finished()',
        'HasError': 'test.has_error()',
    }

    @classmethod
    def convert_action(cls, action: str) -> Optional[str]:
        funcargs = cls.get_func_args(action)
        if funcargs is None:
            return None
        func, args = funcargs
        out = cls.func_dict.get(func)
        if out is None:
            return None
        return f'self.assert{args.capitalize()}({out})'


class EqualAssertConverter(FuncArgsMixin, Converter):
    """
    Example:
      test.execute( BytesBuffered{ 0 } )
      => self.assertEqual(test.bytes_buffered(), 0)
    """
    func_dict: dict[str, str] = {
        'Peek': 'test.peek()',
        'ReadAll': 'test.pop()',
        'AvailableCapacity': 'test.cap()',
        'BytesPushed': 'test.bytes_pushed()',
        'BytesPopped': 'test.bytes_popped()',
        'BytesBuffered': 'test.bytes_buffered()',
        'BytesPending': 'test.bytes_pending()',
        'ExpectWindow': 'test.receiver_message().winsize',
        'ExpectSeqnosInFlight': 'test.sequence_numbers_in_flight()',
    }

    @classmethod
    def convert_action(cls, action: str) -> Optional[str]:
        funcargs = cls.get_func_args(action)
        if funcargs is None:
            return None
        func, args = funcargs
        out = cls.func_dict.get(func)
        if out is None:
            return None
        return f'self.assertEqual({out}, {cls.cstr_sub(args)})'


class InsertConverter(FuncArgsMixin, Converter):

    @classmethod
    def convert_action(cls, action: str) -> Optional[str]:
        args = cls.get_args(action, 'Insert')
        if args is None:
            return None
        arg12 = args.split(',')
        if len(arg12) != 2:
            return None
        arg1 = cls.cstr_sub(arg12[0].strip())
        arg2 = arg12[1].strip()
        return f'test.insert({arg2}, {arg1})'


class BufferEmptyConverter(FuncArgsMixin, Converter):

    @classmethod
    def convert_action(cls, action: str) -> Optional[str]:
        args = cls.get_args(action, 'BufferEmpty')
        if args is None:
            return None
        return (f'self.assert{cls.cbool2eq[args]}(test.bytes_buffered(), 0)')


class CloseConverter(FuncArgsMixin, Converter):

    @classmethod
    def convert_action(cls, action: str) -> Optional[str]:
        if not cls.expect_func(action, 'Close'):
            return None
        return 'test.close(); test.fill()'


class PushConverter(Converter):
    """
    Example:
      test.execute( Push {} )
      => test.fill()

      test.execute( Push { "hello" } )
      => test.push(b'hello'); test.fill()

      test.execute( Push {}.with_close() )
      => test.close(); test.fill()

      test.execute( Push { "hello" }.with_close() )
      => test.push(b'hello'); test.close(); test.fill()
    """
    action_re = re.compile(r'^Push\s*[\{\(]([^\}\)]*)[\}\)]')

    @classmethod
    def convert_action(cls, action: str) -> Optional[str]:
        action_match = cls.action_re.match(action)
        if action_match is None:
            return None
        arg = action_match[1].strip()
        out = []
        if len(arg) != 0:
            out.append(f'test.push({cls.cstr_sub(arg)})')
        if action.find('.with_close') >= 0:
            out.append('test.close()')
        out.append('test.fill()')
        return '; '.join(out)


class TickConverter(Converter):
    """
    Example:
      test.execute( Tick { 1 } )
      => test.tick(1)

      test.execute( Tick { 1 }.with_max_retx_exceeded( true ) )
      => test.tick(1); self.assertGreater(
           test.consecutive_retransmissions(), MAX_RETX_ATTEMPTS)
    """
    action_re = re.compile(r'^Tick \{([^\}]*)\}')
    max_retx_exceeded_re = re.compile(
        r'\.with_max_retx_exceeded\( (true|false) \)')

    @classmethod
    def convert_action(cls, action: str) -> Optional[str]:
        action_match = cls.action_re.match(action)
        if action_match is None:
            return None
        arg = action_match[1].strip()
        out = [f'test.tick({arg})']
        max_retx_exceeded_match = cls.max_retx_exceeded_re.search(action)
        if max_retx_exceeded_match is not None:
            max_retx_exceeded = max_retx_exceeded_match[1]
            out.append(
                f'self.assert{cls.cbool2gt[max_retx_exceeded]}('
                'test.consecutive_retransmissions(), MAX_RETX_ATTEMPTS)')
        return '; '.join(out)


class HasAcknoConverter(FuncArgsMixin, Converter):

    @classmethod
    def convert_action(cls, action: str) -> Optional[str]:
        args = cls.get_args(action, 'HasAckno')
        if args is None:
            return None
        return (f'self.assert{cls.cbool2notnone[args]}('
                'test.receiver_message().ackno)')


class ExpectAcknoConverter(Wrap32StripMixin, FuncArgsMixin, Converter):

    @classmethod
    def convert_action(cls, action: str) -> Optional[str]:
        args = cls.get_args(action, 'ExpectAckno')
        if args is None:
            return None
        if args == 'std::optional<Wrap32> {}':
            return 'self.assertIsNone(test.receiver_message().ackno)'
        return ('self.assertEqual(test.receiver_message().ackno, '
                f'Wrap32({cls.wrap32_strip(args)})')


class ExpectSeqnoConverter(Wrap32StripMixin, FuncArgsMixin, Converter):

    @classmethod
    def convert_action(cls, action: str) -> Optional[str]:
        args = cls.get_args(action, 'ExpectSeqno')
        if args is None:
            return None
        return ('self.assertEqual(test.empty_sender_message().seqno, '
                f'Wrap32({cls.wrap32_strip(args)}))')


class ExpectNoSegmentConverter(FuncArgsMixin, Converter):

    @classmethod
    def convert_action(cls, action: str) -> Optional[str]:
        if not cls.expect_func(action, 'ExpectNoSegment'):
            return None
        return 'self.assertIsNone(test.optional_sender_message())'


class ExpectMessageConverter(Converter):
    action_re = re.compile(r'^ExpectMessage \{\}')
    seqno_re = re.compile(r'\.with_seqno\(([^\)]*)\)')
    payload_size_re = re.compile(r'\.with_payload_size\(([^\)]*)\)')
    data_re = re.compile(r'\.with_data\(([^\)]*)\)')

    @classmethod
    def convert_action(cls, action: str) -> Optional[str]:
        action_match = cls.action_re.match(action)
        if action_match is None:
            return None
        out = [
            'msg = test.optional_sender_message()',
            'self.assertLessEqual(len(msg.payload), SENDER_MSS)',
        ]
        if action.find('.with_syn') >= 0:
            out.append('self.assertTrue(msg.syn)')
        if action.find('.with_fin') >= 0:
            out.append('self.assertTrue(msg.fin)')
        seqno_match = cls.seqno_re.search(action)
        if seqno_match is not None:
            seqno = seqno_match[1].strip()
            out.append(f'self.assertEqual(msg.seqno, Wrap32({seqno}))')
        payload_size_match = cls.payload_size_re.search(action)
        if payload_size_match is not None:
            payload_size = payload_size_match[1].strip()
            out.append(f'self.assertEqual(len(msg.payload), {payload_size})')
        data_match = cls.data_re.search(action)
        if data_match is not None:
            data = cls.cstr_sub(data_match[1].strip())
            out.append(f'self.assertEqual(msg.payload, {data})')
        return '; '.join(out)


class SegmentArrivesConverter(Converter):
    action_re = re.compile(r'^SegmentArrives \{\}')
    seqno_re = re.compile(r'\.with_seqno\(([^\)]*)\)')
    data_re = re.compile(r'\.with_data\(([^\)]*)\)')

    @classmethod
    def convert_action(cls, action: str) -> Optional[str]:
        action_match = cls.action_re.match(action)
        if action_match is None:
            return None
        seqno, syn, fin, data = '0', False, False, "b''"
        seqno_match = cls.seqno_re.search(action)
        if seqno_match is not None:
            seqno = seqno_match[1].strip()
        if action.find('.with_syn') >= 0:
            syn = True
        if action.find('.with_fin') >= 0:
            fin = True
        data_match = cls.data_re.search(action)
        if data_match is not None:
            data = cls.cstr_sub(data_match[1].strip())
        return ('test.receiver_message('
                f'SenderMessage(Wrap32({seqno}), {syn}, {fin}, {data}))')


class AckReceivedConverter(Wrap32StripMixin, Converter):
    action_re = re.compile(r'^AckReceived \{([^\}]*)\}')
    win_re = re.compile(r'\.with_win\(([^\)]*)\)')

    @classmethod
    def convert_action(cls, action: str) -> Optional[str]:
        action_match = cls.action_re.match(action)
        if action_match is None:
            return None
        arg = cls.wrap32_strip(action_match[1])
        win = 'win'
        win_match = cls.win_re.search(action)
        if win_match is not None:
            win = win_match[1].strip()
        return ('test.receive_receiver_message('
                f'ReceiverMessage(Wrap32({arg}), {win}))'
                '; test.fill()')


if __name__ == '__main__':
    import fileinput
    for line in fileinput.input():
        print(Converter.convert_line(line))
