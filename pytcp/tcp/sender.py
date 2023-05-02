import random
from collections import deque
from dataclasses import dataclass
from typing import Optional

from .defaults import SENDER_IRTO, SENDER_MSS
from .messages import ReceiverMessage, SenderMessage
from .stream import Stream
from .wrap32 import Wrap32


@dataclass
class _Segment:
    first: int
    last: int
    data: bytes
    bof: bool
    eof: bool

    def sender_message(self, isn: Wrap32) -> SenderMessage:
        return SenderMessage(isn.wrap(self.first), self.bof, self.eof,
                             self.data)


class Sender(Stream):
    __isn: Wrap32
    __seqno: int
    __ackno: int
    __mss: int
    __winsize: int
    __eof_sent: bool

    __irto: int
    __rto: int
    __to: int
    __consecutive_retransmissions: int

    __segs: deque[_Segment]
    __outstanding_segs: deque[_Segment]

    def __init__(self,
                 *args,
                 isn: Optional[int] = None,
                 mss: int = SENDER_MSS,
                 irto: int = SENDER_IRTO,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.__isn = Wrap32(isn if isn is not None else random.getrandbits(32))
        self.__seqno = 0
        self.__ackno = 0
        self.__mss = mss
        self.__winsize = 0
        self.__eof_sent = False

        self.__irto = irto
        self.__rto = irto
        self.__to = 0
        self.__consecutive_retransmissions = 0

        self.__segs = deque()
        self.__outstanding_segs = deque()
        self.__segs.append(_Segment(0, 1, b'', True, False))

    @property
    def __last_seqno(self):
        return self.__seqno if len(self.__segs) == 0 else self.__segs[-1].last

    def __ensure_last_seg(self) -> _Segment:
        if len(self.__segs) == 0:
            seqno = self.__last_seqno
            seg = _Segment(seqno, seqno, b'', False, False)
            self.__segs.append(seg)
            return seg
        return self.__segs[-1]

    def __ensure_last_extensible_seg(self) -> _Segment:
        seg = self.__ensure_last_seg()
        if len(seg.data) >= self.__mss:
            seqno = self.__last_seqno
            seg = _Segment(seqno, seqno, b'', False, False)
            self.__segs.append(seg)
        return seg

    def fill(self):
        if self.__eof_sent:
            return

        cap = self.__ackno + max(1, self.__winsize) - self.__last_seqno
        to_pop = min(cap, self.bytes_buffered())
        data = self.pop(to_pop)

        while len(data) > 0:
            seg = self.__ensure_last_extensible_seg()
            to_fill = min(self.__mss - len(seg.data), len(data))
            seg.data += data[:to_fill]
            seg.last += to_fill
            data = data[to_fill:]

        if to_pop < cap and self.is_finished():
            seg = self.__ensure_last_seg()
            seg.eof = True
            seg.last += 1
            self.__eof_sent = True

    def optional_sender_message(self) -> Optional[SenderMessage]:
        if len(self.__segs) == 0:
            return None
        seg = self.__segs.popleft()
        if seg.last > self.__seqno:
            self.__seqno = seg.last
            if len(self.__outstanding_segs) == 0:
                self.__to = self.__rto
            self.__outstanding_segs.append(seg)
        return seg.sender_message(self.__isn)

    def empty_sender_message(self) -> SenderMessage:
        return SenderMessage(self.__isn.wrap(self.__seqno), False, False, b'')

    def receive_receiver_message(self, msg: ReceiverMessage):
        if msg.ackno is None:
            self.__winsize = msg.winsize
            return

        ackno = self.__isn.unwrap(msg.ackno, self.__ackno)
        if ackno > self.__seqno:
            return

        refresh = False
        while len(self.__outstanding_segs) > 0:
            seg = self.__outstanding_segs[0]
            if ackno < seg.last:
                break
            refresh = True
            self.__outstanding_segs.popleft()

        edge = max(ackno + msg.winsize, self.__ackno + self.__winsize)
        self.__ackno = max(ackno, self.__ackno)
        self.__winsize = edge - self.__ackno

        if not refresh:
            return

        self.__rto = self.__irto
        if len(self.__outstanding_segs) > 0:
            self.__to = self.__rto
        self.__consecutive_retransmissions = 0

    def tick(self, ms_since_last_tick: int):
        if len(self.__outstanding_segs) == 0:
            return
        if ms_since_last_tick < self.__to:
            self.__to -= ms_since_last_tick
            return
        self.__segs.appendleft(self.__outstanding_segs[0])
        if self.__winsize != 0 or self.__outstanding_segs[0].bof:
            self.__consecutive_retransmissions += 1
            self.__rto *= 2
        self.__to = self.__rto

    def sequence_numbers_in_flight(self) -> int:
        return self.__last_seqno - self.__ackno

    def consecutive_retransmissions(self) -> int:
        return self.__consecutive_retransmissions
