from typing import Optional

from .messages import ReceiverMessage, SenderMessage
from .reassembler import Reassembler
from .wrap32 import Wrap32


class Receiver(Reassembler):
    __isn: Optional[Wrap32]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__isn = None

    def receive_sender_message(self, msg: SenderMessage):
        if msg.syn:
            self.__isn = msg.seqno
            msg.seqno += 1
        if self.__isn is None:
            return
        idx = self.__isn.unwrap(msg.seqno, self.bytes_pushed()) - 1
        self.insert(idx, msg.payload, msg.fin)

    def receiver_message(self) -> ReceiverMessage:
        winsize = self.cap()
        if winsize > 0xffff:
            winsize = 0xffff
        if self.__isn is None:
            return ReceiverMessage(None, winsize)
        ackno = self.__isn.wrap(self.bytes_pushed() + 1)
        if self.is_closed():
            ackno += 1
        return ReceiverMessage(ackno, winsize)
