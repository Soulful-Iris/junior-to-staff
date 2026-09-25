import struct

HEADER = struct.Struct(">I")
DEFAULT_MAX_FRAME = 16 * 1024 * 1024


def encode(items):
    out = bytearray()
    for item in items:
        if not isinstance(item, (bytes, bytearray)):
            raise ValueError("items must be bytes")
        out += HEADER.pack(len(item))
        out += item
    return bytes(out)


class FrameDecoder:
    def __init__(self, max_frame=DEFAULT_MAX_FRAME):
        self.max_frame = max_frame
        self._buffer = bytearray()

    def feed(self, chunk):
        if not isinstance(chunk, (bytes, bytearray)):
            raise ValueError("chunk must be bytes")
        self._buffer += chunk
        frames = []
        offset = 0
        while len(self._buffer) - offset >= HEADER.size:
            (n,) = HEADER.unpack_from(self._buffer, offset)
            if n > self.max_frame:
                raise ValueError(f"frame length {n} exceeds max {self.max_frame}")
            if len(self._buffer) - offset - HEADER.size < n:
                break
            start = offset + HEADER.size
            frames.append(bytes(self._buffer[start:start + n]))
            offset = start + n
        del self._buffer[:offset]
        return frames

    def pending(self):
        return len(self._buffer)


def decode(data, max_frame=DEFAULT_MAX_FRAME):
    decoder = FrameDecoder(max_frame)
    frames = decoder.feed(data)
    if decoder.pending():
        raise ValueError("truncated frame at end of data")
    return frames
