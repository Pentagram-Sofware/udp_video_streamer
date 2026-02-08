import struct


def build_frame_packets(data: bytes, frame_id: int, payload_size: int) -> list[bytes]:
    if payload_size <= 0:
        payload_size = 1200

    size = len(data)
    chunk_count = (size + payload_size - 1) // payload_size
    packets: list[bytes] = []

    frame_header = struct.pack("<III", frame_id, size, chunk_count)
    packets.append(b"FRAME_START" + frame_header)

    chunk_index = 0
    for offset in range(0, size, payload_size):
        chunk = data[offset:offset + payload_size]
        chunk_header = struct.pack("<II", frame_id, chunk_index)
        packets.append(b"CHUNK" + chunk_header + chunk)
        chunk_index += 1

    return packets
