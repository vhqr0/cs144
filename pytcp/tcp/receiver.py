from dataclasses import dataclass
from typing import Optional

from .reassembler import Reassembler
from .wrap32 import Wrap32


@dataclass
class SenderMessage:
    seqno: Wrap32
    syn: bool
    fin: bool
    payload: bytes

    def __len__(self) -> int:
        return len(self.payload) + int(self.syn) + int(self.fin)


@dataclass
class ReceiverMessage:
    ackno: Optional[Wrap32]
    winsize: int


class Receiver(Reassembler):
    isn: Optional[Wrap32]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.isn = None

    def receive(self, msg: SenderMessage):
        if msg.syn:
            self.isn = msg.seqno
            msg.seqno += 1
        if self.isn is None:
            return
        idx = self.isn.unwrap(msg.seqno, self.bytes_pushed()) - 1
        self.insert(idx, msg.payload, msg.fin)

    def receiver_message(self) -> ReceiverMessage:
        winsize = self.cap()
        if winsize > 0xffff:
            winsize = 0xffff
        if self.isn is None:
            return ReceiverMessage(None, winsize)
        ackno = self.isn.wrap(self.bytes_pushed() + 1)
        if self.is_closed():
            ackno += 1
        return ReceiverMessage(ackno, winsize)
