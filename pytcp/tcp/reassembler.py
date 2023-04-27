from collections import deque
from dataclasses import dataclass
from typing import Optional

from .stream import Stream


@dataclass
class _Segment:
    first: int
    last: int
    data: bytes
    eof: bool

    def narrow(self, min_idx: int, max_idx: int) -> Optional['_Segment']:
        if self.first > max_idx or self.last < min_idx:
            return None
        seg = _Segment(self.first, self.last, self.data, self.eof)
        if seg.last > max_idx:
            seg.data = seg.data[:max_idx - seg.first]
            seg.last = max_idx
        if seg.first < min_idx:
            seg.data = seg.data[min_idx - seg.first:]
            seg.first = min_idx
        return seg


class Reassembler(Stream):
    __segs: deque[_Segment]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__segs = deque()

    def insert(self, idx: int, data: bytes, eof: bool = False):
        self.insert_segment(_Segment(idx, idx + len(data), data, eof))

    def insert_segment(self, seg: _Segment):
        min_idx = self.bytes_pushed()
        max_idx = min_idx + self.cap()

        _seg: Optional[_Segment] = seg.narrow(min_idx, max_idx)
        if _seg is None:
            return
        seg = _seg

        segs: deque[_Segment] = deque()
        seg_appended = False

        for s in self.__segs:
            if seg_appended or s.last < seg.first:
                segs.append(s)
                continue
            if s.first > seg.last:
                segs.append(seg)
                seg_appended = True
                segs.append(s)
                continue
            if s.first < seg.first:
                seg.data = s.data[:seg.first - s.first] + seg.data
                seg.first = s.first
            if seg.eof:
                break
            if s.last >= seg.last:
                seg.data += s.data[seg.last - s.first:]
                seg.last = s.last
                seg.eof = s.eof

        if not seg_appended:
            segs.append(seg)

        self.__segs = segs

        if seg.first == min_idx:
            self.__segs.popleft()
            if len(seg.data) != 0:
                self.push(seg.data)
            if seg.eof:
                self.close()

    def bytes_pending(self) -> int:
        return sum(len(seg.data) for seg in self.__segs)
