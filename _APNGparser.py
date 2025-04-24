import struct
import zlib
import io
from typing import List
from PIL import Image
import numpy as np

PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'

class NotPNGError(Exception): pass
class NotAPNGError(Exception): pass
def is_not_png(err): return isinstance(err, NotPNGError)
def is_not_apng(err): return isinstance(err, NotAPNGError)

def calculate_crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xffffffff

class Frame:
    def __init__(self):
        self.left = 0
        self.top = 0
        self.width = 0
        self.height = 0
        self.delay_num = 0
        self.delay_den = 100  # default to 100 if unspecified
        self.delay_ms = 0
        self.disposeOp = 0
        self.blendOp = 0
        self.image_data = None  # Raw reconstructed PNG
        self.data = None  # Final RGBA image

class APNG:
    def __init__(self):
        self.width = 0
        self.height = 0
        self.num_plays = 0
        self.play_time = 0
        self.frames: List[Frame] = []

def parse_apng(buffer: bytes) -> APNG:
    if buffer[:8] != PNG_SIGNATURE:
        raise NotPNGError('Not a PNG')
    
    offset = 8
    is_animated = False
    while offset < len(buffer):
        length = struct.unpack('>I', buffer[offset:offset + 4])[0]
        chunk_type = buffer[offset + 4:offset + 8].decode('ascii')
        if chunk_type == 'acTL':
            is_animated = True
            break
        offset += 12 + length
        if chunk_type == 'IEND':
            break
    
    if not is_animated:
        raise NotAPNGError('Not an animated PNG')
    
    apng = APNG()
    
    pre_data_parts, post_data_parts = [], []
    header_data_bytes = None
    
    frame = None
    frame_number = 0
    offset = 8
    
    while offset < len(buffer):
        length = struct.unpack('>I', buffer[offset:offset + 4])[0]
        chunk_type = buffer[offset + 4:offset + 8].decode('ascii')
        chunk_data = buffer[offset + 8: offset + 8 + length]
        
        if chunk_type == 'IHDR':
            header_data_bytes = chunk_data
            apng.width, apng.height = struct.unpack('>II', chunk_data[:8])
        
        elif chunk_type == 'acTL':
            apng.num_plays = struct.unpack('>I', chunk_data[4:8])[0]
        
        elif chunk_type == 'fcTL':
            if frame:
                apng.frames.append(frame)
                frame_number += 1

            frame = Frame()
            frame.width, frame.height = struct.unpack('>II', chunk_data[4:12])
            frame.left, frame.top = struct.unpack('>II', chunk_data[12:20])
            frame.delay_num, frame.delay_den = struct.unpack('>HH', chunk_data[20:24])
            if frame.delay_den == 0:
                print(f':: FRAME #{frame_number+1} DENOMINATOR DELAY WAS FIXED!')
                frame.delay_den = 100
            
            frame.delay_ms = (frame.delay_num / frame.delay_den) * 1000
            apng.play_time += frame.delay_ms
            
            frame.disposeOp, frame.blendOp = chunk_data[24], chunk_data[25]
            if frame_number == 0 and frame.disposeOp == 2:
                frame.disposeOp = 1

        elif chunk_type in ('IDAT', 'fdAT'):
            if frame:
                data_start = 12 if chunk_type == 'fdAT' else 8
                if not hasattr(frame, 'data_parts'):
                    frame.data_parts = []
                frame.data_parts.append(buffer[offset + data_start: offset + 8 + length])
        
        elif chunk_type == 'IEND':
            post_data_parts.append(buffer[offset: offset + 12 + length])
        
        else:
            pre_data_parts.append(buffer[offset: offset + 12 + length])
        
        offset += 12 + length
        if chunk_type == 'IEND':
            break
    
    if frame:
        apng.frames.append(frame)
    
    if not apng.frames:
        raise NotAPNGError('No animation frames found')
    
    apng.play_time = round(apng.play_time, 3)
    pre_blob = b''.join(pre_data_parts)
    post_blob = b''.join(post_data_parts)
    
    for frame in apng.frames:
        bb = bytearray(PNG_SIGNATURE)
        header_copy = bytearray(header_data_bytes)
        header_copy[0:4] = frame.width.to_bytes(4, 'big')
        header_copy[4:8] = frame.height.to_bytes(4, 'big')
        bb.extend(make_chunk_bytes('IHDR', header_copy))
        bb.extend(pre_blob)
        for part in getattr(frame, 'data_parts', []):
            bb.extend(make_chunk_bytes('IDAT', part))
        bb.extend(post_blob)
        frame.image_data = io.BytesIO(bb)
        del frame.data_parts  # cleanup

    return apng

def make_chunk_bytes(chunk_type: str, data_bytes: bytes) -> bytes:
    chunk_type_bytes = chunk_type.encode("ascii")
    crc = calculate_crc32(chunk_type_bytes + data_bytes)
    return (
        struct.pack('>I', len(data_bytes)) +
        chunk_type_bytes +
        data_bytes +
        struct.pack('>I', crc)
    )

def create_png(width, height):
    return Image.new('RGBA', (width, height), (0, 0, 0, 0))

def to_png_bytes(image):
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()

def apng_disassemble(buffer):
    apng = parse_apng(buffer)
    
    width, height = apng.width, apng.height
    current_frame = create_png(width, height)

    for index, frame in enumerate(apng.frames):
        image_data = Image.open(frame.image_data).convert('RGBA')
        blend_op = frame.blendOp
        dispose_op = frame.disposeOp

        previous_frame = current_frame.copy()

        if blend_op == 1:
            current_frame.paste(image_data, (frame.left, frame.top), image_data)
        else:
            cur_data = np.array(current_frame)
            overlay = np.array(image_data)

            y1, y2 = frame.top, frame.top + frame.height
            x1, x2 = frame.left, frame.left + frame.width

            cur_data[y1:y2, x1:x2] = overlay
            current_frame = Image.fromarray(cur_data, 'RGBA')
        
        apng.frames[index].data = current_frame

        if dispose_op == 1:
            current_frame = create_png(width, height)
        elif dispose_op == 2:
            current_frame = previous_frame
    
    return apng
