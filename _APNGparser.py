import struct
import zlib
import io
from typing import List, Optional
from PIL import Image

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

class NotPNGError(Exception): pass
class NotAPNGError(Exception): pass

def calculate_crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xffffffff

class Frame:
    def __init__(self):
        self.left = 0
        self.top = 0
        self.width = 0
        self.height = 0
        self.delay = 0
        self.disposeOp = 0
        self.blendOp = 0
        self.image_data: Optional[io.BytesIO] = None
        self.image: Optional[Image.Image] = None
        self.data_parts: List[bytes] = []

    def create_image(self):
        if self.image or self.image_data is None:
            return
        try:
            with self.image_data as buf:
                self.image = Image.open(buf)
                self.image.load()
        except Exception as e:
            self.image = None
            raise RuntimeError("Image creation error") from e

class APNG:
    def __init__(self):
        self.width = 0
        self.height = 0
        self.num_plays = 0
        self.play_time = 0
        self.frames: List[Frame] = []
        self.curr_frame_number = 0
        self.curr_frame: Optional[Frame] = None
        self.paused = self.ended = False

    def create_images(self):
        for frame in self.frames:
            frame.create_image()

def is_not_png(err): return isinstance(err, NotPNGError)
def is_not_apng(err): return isinstance(err, NotAPNGError)

def parse_apng(buffer: bytes) -> APNG:
    if buffer[:8] != PNG_SIGNATURE:
        raise NotPNGError("Not a PNG")

    is_animated = False
    each_chunk(buffer, lambda t, *_: t == 'acTL' and setattr(globals(), 'is_animated', True))
    if not is_animated:
        raise NotAPNGError("Not an animated PNG")

    apng = APNG()
    pre_data_parts, post_data_parts = [], []
    header_data_bytes = None
    frame = None
    frame_number = 0

    def handle_chunk(chunk_type, data, offset, length):
        nonlocal frame, frame_number, header_data_bytes

        chunk_data = data[offset + 8: offset + 8 + length]

        if chunk_type == 'IHDR':
            header_data_bytes = chunk_data
            apng.width, apng.height = struct.unpack(">II", chunk_data[:8])
        elif chunk_type == 'acTL':
            apng.num_plays = struct.unpack(">I", chunk_data[4:8])[0]
        elif chunk_type == 'fcTL':
            if frame:
                apng.frames.append(frame)
                frame_number += 1
            frame = Frame()
            frame.width, frame.height = struct.unpack(">II", chunk_data[4:12])
            frame.left, frame.top = struct.unpack(">II", chunk_data[12:20])
            delay_num, delay_den = struct.unpack(">HH", chunk_data[20:24])
            delay_den = delay_den or 100
            frame.delay = max(1000 * delay_num / delay_den, 100)
            apng.play_time += frame.delay
            frame.disposeOp, frame.blendOp = chunk_data[24], chunk_data[25]
            if frame_number == 0 and frame.disposeOp == 2:
                frame.disposeOp = 1
        elif chunk_type in ('IDAT', 'fdAT'):
            if frame:
                data_start = 12 if chunk_type == 'fdAT' else 8
                frame.data_parts.append(data[offset + data_start: offset + 8 + length])
        elif chunk_type == 'IEND':
            post_data_parts.append(data[offset: offset + 12 + length])
        else:
            pre_data_parts.append(data[offset: offset + 12 + length])

    each_chunk(buffer, handle_chunk)

    if frame:
        apng.frames.append(frame)

    if not apng.frames:
        raise NotAPNGError("No animation frames found")

    pre_blob = b''.join(pre_data_parts)
    post_blob = b''.join(post_data_parts)

    for frame in apng.frames:
        bb = bytearray(PNG_SIGNATURE)
        header_copy = bytearray(header_data_bytes)
        header_copy[0:4] = frame.width.to_bytes(4, 'big')
        header_copy[4:8] = frame.height.to_bytes(4, 'big')
        bb.extend(make_chunk_bytes('IHDR', header_copy))
        bb.extend(pre_blob)
        for part in frame.data_parts:
            bb.extend(make_chunk_bytes('IDAT', part))
        bb.extend(post_blob)
        frame.image_data = io.BytesIO(bb)
        del frame.data_parts

    return apng

def each_chunk(data: bytes, callback):
    offset = 8
    while offset < len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        chunk_type = data[offset + 4:offset + 8].decode("ascii")
        callback(chunk_type, data, offset, length)
        offset += 12 + length
        if chunk_type == 'IEND':
            break

def make_chunk_bytes(chunk_type: str, data_bytes: bytes) -> bytes:
    chunk_type_bytes = chunk_type.encode("ascii")
    crc = calculate_crc32(chunk_type_bytes + data_bytes)
    return (
        struct.pack(">I", len(data_bytes)) +
        chunk_type_bytes +
        data_bytes +
        struct.pack(">I", crc)
    )
