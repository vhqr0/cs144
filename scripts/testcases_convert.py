#!/usr/bin/env python3
"""Convert cs144 test cases from c++ to python."""
import re
from functools import cache
from typing import Optional


class Converter:
    converters: list[type['Converter']] = []
    exec_re = re.compile(r'^test.execute\((.*)\);$')
    cstr_sub_re = re.compile(r'"([^"]*)"')

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


class NoArgConverter(Converter):
    """
    Example:
      test.execute( Close {} )
      => test.close()
    """
    action_re = re.compile(r'^([^\s]+) \{\}$')
    func_dict: dict[str, str] = {
        'Close': 'test.close()',
        'SetError': 'test.set_error()',
    }

    @classmethod
    def convert_action(cls, action: str) -> Optional[str]:
        action_match = cls.action_re.match(action)
        if action_match is None:
            return None
        func = action_match[1].strip()
        return cls.func_dict.get(func)


class CopyArgsConverter(FuncArgsMixin, Converter):
    """
    Example:
      test.execute( Push { "hello" } )
      => test.push(b'hello')
    """
    func_dict = {
        'Push': 'test.push(%s)',
        'Pop': 'test.pop(%s)',
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
        return out % cls.cstr_sub(args)


class BoolAssertConverter(Converter):
    """
    Example:
      test.execute( IsClosed { false } )
      => self.assertFalse(test.is_closed())
    """
    action_re = re.compile(r'^([^\s]+) \{ (true|false) \}$')
    func_dict: dict[str, str] = {
        'IsClosed': 'test.is_closed()',
        'IsFinished': 'test.is_finished()',
        'HasError': 'test.has_error()',
        'BufferEmpty': 'test.bytes_buffered() == 0',
        'HasAckno': 'test.receiver_message().ackno is not None',
    }

    @classmethod
    def convert_action(cls, action: str) -> Optional[str]:
        action_match = cls.action_re.match(action)
        if action_match is None:
            return None
        func = action_match[1].strip()
        arg = action_match[2].strip()
        out = cls.func_dict.get(func)
        if out is None:
            return None
        return f'self.assert{arg.capitalize()}({out})'


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
        funcargs = cls.get_func_args(action)
        if funcargs is None:
            return funcargs
        func, args = funcargs
        if func != 'Insert':
            return None
        arg12 = args.split(',')
        if len(arg12) != 2:
            return None
        arg1, arg2 = arg12
        arg1 = cls.cstr_sub(arg12[0].strip())
        arg2 = arg12[1].strip()
        return f'test.insert({arg2}, {arg1})'


class ExpectAcknoConverter(Converter):
    action_re1 = re.compile(r'^ExpectAckno \{ std::optional<Wrap32> \{\} \}$')
    action_re2 = re.compile(r'^ExpectAckno \{ Wrap32 \{ (.*) \} \}$')

    @classmethod
    def convert_action(cls, action: str) -> Optional[str]:
        action_match1 = cls.action_re1.match(action)
        if action_match1 is not None:
            return 'self.assertEqual(test.receiver_message().ackno, None)'
        action_match2 = cls.action_re2.match(action)
        if action_match2 is not None:
            return ('self.assertEqual(test.receiver_message().ackno, '
                    f'Wrap32({action_match2[1]}))')
        return None


class SegmentArrivesConverter(Converter):
    action_re = re.compile(r'^SegmentArrives \{\}')
    seqno_re = re.compile(r'\.with_seqno\(([^\)]*)\)')
    syn_re = re.compile(r'\.with_syn')
    fin_re = re.compile(r'\.with_fin')
    data_re = re.compile(r'\.with_data\(([^\)]*)\)')

    @classmethod
    def convert_action(cls, action: str) -> Optional[str]:
        action_match = cls.action_re.match(action)
        if action_match is None:
            return None
        seqno, syn, fin, data = '0', False, False, '""'
        seqno_match = cls.seqno_re.search(action)
        if seqno_match is not None:
            seqno = seqno_match[1].strip()
        if cls.syn_re.search(action) is not None:
            syn = True
        if cls.fin_re.search(action) is not None:
            fin = True
        data_match = cls.data_re.search(action)
        if data_match is not None:
            data = data_match[1].strip()
        data = cls.cstr_sub(data)
        return ('test.receiver_message('
                f'SenderMessage(Wrap32({seqno}), {syn}, {fin}, {data}))')


if __name__ == '__main__':
    import fileinput
    for line in fileinput.input():
        print(Converter.convert_line(line))
