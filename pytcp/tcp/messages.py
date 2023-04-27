from dataclasses import dataclass
from typing import Optional

from .wrap32 import Wrap32


@dataclass
class SenderMessage:
    seqno: Wrap32
    syn: bool
    fin: bool
    payload: bytes


@dataclass
class ReceiverMessage:
    ackno: Optional[Wrap32]
    winsize: int
