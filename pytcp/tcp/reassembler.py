from collections import deque
from dataclasses import dataclass

from .stream import Stream


@dataclass
class Segment:
    first: int
    last: int
    data: bytes
    eof: bool

    def __len__(self) -> int:
        return len(self.data)

    def narrow(self, min_idx: int, max_idx: int) -> bool:
        if self.first > max_idx or self.last < min_idx:
            return False

        if self.last > max_idx:
            self.data = self.data[:max_idx - self.first]
            self.last = max_idx
        if self.first < min_idx:
            self.data = self.data[min_idx - self.first:]
            self.first = min_idx
        return True


class Reassembler(Stream):
    segs: deque[Segment]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.segs = deque()

    def insert(self, idx: int, data: bytes, eof: bool = False):
        self.insert_segment(Segment(idx, idx + len(data), data, eof))

    def insert_segment(self, seg: Segment):
        min_idx = self.bytes_pushed()
        max_idx = min_idx + self.cap()

        if not seg.narrow(min_idx, max_idx):
            return

        new_segs: deque[Segment] = deque()
        seg_appended = False

        for s in self.segs:
            if seg_appended or s.last < seg.first:
                new_segs.append(s)
                continue
            if s.first > seg.last:
                new_segs.append(seg)
                seg_appended = True
                new_segs.append(s)
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
            new_segs.append(seg)

        self.segs = new_segs

        if seg.first == min_idx:
            self.segs.popleft()
            if len(seg.data) != 0:
                self.push(seg.data)
            if seg.eof:
                self.close()

    def bytes_pending(self) -> int:
        return sum(len(seg) for seg in self.segs)
