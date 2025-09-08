# UDP Video Streaming Frame Format Documentation

## Overview

This document describes the frame format and data structure used in the Raspberry Pi UDP video streaming system. The system captures video from a Pi Camera, compresses frames using JPEG, serializes them with Python pickle, and transmits them over UDP with a custom protocol.

## Frame Processing Pipeline

```
Raw Camera Frame (640x480 RGB888)
    ↓ Color Conversion
BGR Frame 
    ↓ JPEG Compression (80% quality)
JPEG Buffer (bytes)
    ↓ Python Pickle Serialization
Pickled JPEG Data
    ↓ UDP Packetization with Headers
Network Packets → Client
```

## Compression Details

### Image Compression
- **Format**: JPEG compression using OpenCV
- **Quality**: 80% JPEG quality (`cv2.IMWRITE_JPEG_QUALITY, 80`)
- **Method**: `cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])`
- **Type**: Lossy compression with good size/quality balance
- **Independence**: Each frame is compressed independently (no inter-frame compression)

### Serialization
- **Method**: Python pickle serialization
- **Function**: `pickle.dumps(jpeg_buffer)`
- **Purpose**: Converts JPEG byte buffer into transmittable binary format
- **Requirement**: Clients must be Python-based to deserialize

## UDP Packet Structure (Always-Chunked, NAT-Friendly)

To avoid IP fragmentation across the internet, frames are ALWAYS sent as small UDP chunks (default payload ~1200 bytes). Each frame has a unique frame_id.

### Frame Start Packet
```
┌──────────────┬────────────────────┬──────────────────┬──────────────────┐
│ "FRAME_START"│ frame_id (uint32)  │ frame_size (u32) │ chunk_count (u32)│
│ 11 bytes     │ 4 bytes            │ 4 bytes          │ 4 bytes          │
└──────────────┴────────────────────┴──────────────────┴──────────────────┘
```

### Chunk Packets
```
┌─────────┬────────────────────┬────────────────────┬────────────────────┐
│ "CHUNK" │ frame_id (uint32)  │ chunk_index (u32)  │ chunk_payload (<=1200B)
│ 5 bytes │ 4 bytes            │ 4 bytes            │ variable           │
└─────────┴────────────────────┴────────────────────┴────────────────────┘
```

### Implementation (Sender)
```python
payload_size = 1200
chunk_count = (size + payload_size - 1) // payload_size
sock.sendto(b"FRAME_START" + struct.pack("LLL", frame_id, size, chunk_count), addr)

for idx, off in enumerate(range(0, size, payload_size)):
    chunk = data[off:off+payload_size]
    sock.sendto(b"CHUNK" + struct.pack("LL", frame_id, idx) + chunk, addr)
```

## Network Protocol

### Client Registration (Single Port, NAT-Friendly)
Clients must register before receiving frames:

```
Client → Server (UDP 9999): "REGISTER_CLIENT" (from a single UDP socket)
Server → Client: "REGISTERED"
```

- **Single socket model**: Client uses the SAME UDP socket to send `REGISTER_CLIENT` and to `recvfrom()` frames. This preserves NAT mappings.
- **Port**: Server listens on UDP 9999. Frames are sent back to the exact source address (IP:port) used by the registration packet.
- **Keepalive**: Client sends `KEEPALIVE` every ~15–20 seconds to keep NAT mapping alive.
- **Disconnect**: Client may send `DISCONNECT` when done.

### Server Configuration
- **Listening Port**: 9999 (UDP)
- **Binding**: `0.0.0.0:9999` (all interfaces)
- **Max Packet Size**: 65,507 bytes (UDP maximum)
- **Client Timeout**: 30 seconds

## Frame Specifications

### Camera Settings
- **Resolution**: 640x480 pixels
- **Format**: RGB888 → BGR (OpenCV standard)
- **Frame Rate**: 30 FPS (configurable)
- **Color Space**: sRGB

### Size Characteristics
- **Typical Frame Size**: 15-50 KB (depends on scene complexity)
- **Maximum Frame Size**: ~921 KB (640×480×3 uncompressed)
- **Compressed Size**: ~20-80 KB with JPEG 80% quality
- **Variable Size**: Frame size varies based on image complexity

## Performance Metrics

### Observed Performance
- **Target FPS**: 30
- **Actual FPS**: 13.6-40.7 (varies with network conditions)
- **Throughput**: ~273 frames per 10 seconds average
- **Latency**: Low (UDP + minimal processing)

### Bandwidth Usage
- **Per Frame**: ~20-80 KB
- **Per Second**: ~600 KB - 2.4 MB (at 30 FPS)
- **Per Minute**: ~36-144 MB

## Client Implementation Guide

### Basic Client Structure (Single Socket)
```python
import socket
import pickle
import cv2
import struct

# One UDP socket for both register and receive
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Register (let OS choose source port; NAT will map it)
sock.sendto(b"REGISTER_CLIENT", (server_ip, 9999))

# State for assembling frames
pending = {}
expected = {}

while True:
    data, addr = sock.recvfrom(65507)

    if data == b"REGISTERED":
        continue

    if data.startswith(b"FRAME_START"):
        frame_id, frame_size, chunk_count = struct.unpack("LLL", data[11:23])
        pending[frame_id] = bytearray(frame_size)
        expected[frame_id] = chunk_count

    elif data.startswith(b"CHUNK"):
        frame_id, chunk_index = struct.unpack("LL", data[5:13])
        payload = data[13:]
        if frame_id in pending:
            offset = chunk_index * 1200
            pending[frame_id][offset:offset+len(payload)] = payload
            expected[frame_id] -= 1
            if expected[frame_id] == 0:
                frame_data = bytes(pending.pop(frame_id))
                expected.pop(frame_id, None)
                # Deserialize and display
                jpeg_buffer = pickle.loads(frame_data)
                frame = cv2.imdecode(jpeg_buffer, cv2.IMREAD_COLOR)
                cv2.imshow('Stream', frame)
                if cv2.waitKey(1) == 27:
                    break
```

### Chunk Reassembly
Clients must:
1. Receive `FRAME_START` (frame_id, frame_size, chunk_count)
2. Collect all `CHUNK` packets for that frame_id
3. Place each chunk by `offset = chunk_index * payload_size` (default 1200)
4. When all chunks arrive, concatenate buffer and deserialize

## Advantages & Limitations

### Advantages
- ✅ **Internet-safe UDP**: No reliance on IP fragmentation
- ✅ **NAT-friendly**: Single-socket client model works through typical home routers
- ✅ **Low Latency**: Small UDP packets; immediate decode upon full frame
- ✅ **Frame Independence**: No inter-frame dependencies

### Limitations
- ❌ **Python Dependency**: Clients must support pickle deserialization
- ❌ **No FEC/Resend**: Lost chunks drop a frame
- ❌ **Bandwidth Intensive**: JPEG-per-frame less efficient than video codecs
- ❌ **Security**: Pickle deserialization has security implications
- ❌ **No Synchronization**: No frame timing or sync mechanisms

## Alternative Considerations

For production systems, consider:
- **H.264 Encoding**: Better compression ratios
- **WebRTC**: Standard video streaming protocol
- **Raw Binary**: Remove pickle dependency
- **TCP Fallback**: For reliability-critical applications
- **Frame Buffering**: For smoother playback

---

**Document Version**: 1.1  
**Last Updated**: January 2025  
**System**: Raspberry Pi 5 + Pi Camera v2.1  
**Software**: Python 3.x, OpenCV, Picamera2
