import struct

from packetization import build_frame_packets


def _parse_frame_start(packet: bytes):
    assert packet.startswith(b"FRAME_START")
    return struct.unpack("<III", packet[11:23])


def _parse_chunk(packet: bytes):
    assert packet.startswith(b"CHUNK")
    frame_id, chunk_index = struct.unpack("<II", packet[5:13])
    return frame_id, chunk_index, packet[13:]


def test_packet_count_and_headers():
    data = b"A" * 2500
    packets = build_frame_packets(data, frame_id=123, payload_size=1000)
    # 1 FRAME_START + 3 CHUNK packets
    assert len(packets) == 4
    frame_id, size, chunk_count = _parse_frame_start(packets[0])
    assert frame_id == 123
    assert size == 2500
    assert chunk_count == 3


def test_chunk_payload_slicing():
    data = b"0123456789" * 100  # 1000 bytes
    packets = build_frame_packets(data, frame_id=1, payload_size=400)
    # 1 frame start + 3 chunks (400, 400, 200)
    _, _, chunk_count = _parse_frame_start(packets[0])
    assert chunk_count == 3

    _, idx0, payload0 = _parse_chunk(packets[1])
    _, idx1, payload1 = _parse_chunk(packets[2])
    _, idx2, payload2 = _parse_chunk(packets[3])

    assert idx0 == 0
    assert idx1 == 1
    assert idx2 == 2
    assert payload0 == data[0:400]
    assert payload1 == data[400:800]
    assert payload2 == data[800:1000]


def test_payload_size_default_when_invalid():
    data = b"A" * 1201
    packets = build_frame_packets(data, frame_id=7, payload_size=0)
    _, _, chunk_count = _parse_frame_start(packets[0])
    # Default 1200 => 2 chunks
    assert chunk_count == 2
