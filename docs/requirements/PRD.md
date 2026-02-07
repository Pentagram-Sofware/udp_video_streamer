# Product Requirements Document (PRD)

## Product Name
Raspberry Pi Camera Streamer

## Problem Statement
We need a product that captures video from a Raspberry Pi compatible camera and encodes it efficiently for internet streaming using a standard format. The current codebase focuses on receiving and displaying JPEG frames over UDP and lacks a production-grade capture, encoding, and streaming pipeline.

## Key Source Facts From This Project
- **Camera/Platform**: Raspberry Pi 5 + Pi Camera v2.1
- **Capture Stack**: Picamera2 is referenced in project docs

## Data Points
- **Stream Origin**: Video streaming starts on the Raspberry Pi.
- **Primary Clients**: iOS app (real-time video) and web client.
- **Client Preference**: Use standard, native playback stacks over custom protocols.

## Goals
- Capture live video from the Pi Camera v2.1 on Raspberry Pi 5.
- Encode video with an efficient, standard codec suitable for internet streaming.
- Stream over common protocols with reasonable latency and robustness.
- Provide standard player compatibility for iOS and web clients.

## Non-Goals
- Implement advanced video analytics or AI inference.
- Provide full web UI for configuration (CLI or config file is sufficient for MVP).
- Multi-camera aggregation (single camera stream first).

## Users
- Developers building a Pi-based camera stream.
- End users who view live camera streams on desktop or mobile.

## Assumptions
- The device is a Raspberry Pi 5 with a connected Pi Camera v2.1.
- The network environment can be variable (WAN, NAT, jitter).
- Hardware-accelerated encoding (where available) is preferred.

## Functional Requirements
1. **Camera Capture**
   - Use Pi Camera v2.1 via `Picamera2`.
   - Support configurable resolution and frame rate (e.g., 1280x720 @ 30 FPS).
2. **Encoding**
   - Encode using **H.264/AVC** (baseline or main profile).
   - Configurable bitrate, keyframe interval, and profile.
3. **Transport / Streaming**
   - Streaming originates on the Raspberry Pi.
   - Provide standard protocols that align with native playback stacks:
     - **HLS (prefer Low-Latency HLS)** for native iOS playback.
     - **WebRTC** for real-time browser playback.
   - Allow selecting transport at runtime and enable simultaneous outputs.
   - Serve HLS from a local HTTP server (start with Nginx).
4. **Client Playback**
   - iOS: Playable in native AVFoundation/AVPlayer.
   - Web: Playable in standard browser media APIs (WebRTC, HTML5 video).
   - Provide a simple receiver/preview client (CLI is acceptable).
5. **Configuration**
   - Single config file (YAML/JSON) or CLI flags for camera + encoding + transport.
6. **Logging & Metrics**
   - Log frame rate, bitrate, and encoder stats.
   - Basic health status (camera ready, streaming active).

## Non-Functional Requirements
1. **Latency**
   - WebRTC: target < 500 ms end-to-end in LAN conditions.
   - HLS: target 2-4 s end-to-end with Low-Latency HLS.
2. **Reliability**
   - Recover from temporary network dropouts without crashing.
3. **Security**
   - If internet-exposed, provide at least one of:
     - DTLS/SRTP in WebRTC
     - HTTPS/TLS for HLS delivery (and signed URLs if exposed)
4. **Resource Usage**
   - Prefer hardware-accelerated encoding to keep CPU < 50% on Pi 5.
5. **Extensibility**
   - Design the capture pipeline to optionally fork frames for future AI processing.
   - Ensure the AI path can be enabled without disrupting streaming.

## Constraints
- Must run on Raspberry Pi 5 OS with Python 3.x.
- Camera is Pi Camera v2.1, accessed via Picamera2.

## Out of Scope (for MVP)
- Multi-user access control or user management.
- Video recording / archival.
- Advanced QoS or adaptive bitrate streaming.
 - AI inference on-device (future extension only).

## Missing Elements in the Current Project
1. **Server-Side Capture Pipeline**
   - No server component for camera capture or streaming.
2. **Standard Video Encoding**
   - Current design uses JPEG-per-frame, which is bandwidth heavy.
3. **Streaming Protocol Support**
   - No HLS/WebRTC pipeline; current code uses custom UDP chunks.
4. **Network Robustness**
   - No FEC/retransmit or jitter buffer for WAN.
5. **Security**
   - No authentication or encryption.
6. **Operational Controls**
   - No configuration, health checks, or telemetry.
7. **Extensible Frame Pipeline**
   - No hook or interface to branch frames for future AI processing.

## Open Questions
- Preferred HLS server stack (Nginx or Caddy)?
- WebRTC timeline: MVP or follow-on?
