# MASTER PROJECT PROMPT
# VisualDrop — Offline High-Speed Screen-to-Camera File Transfer Using Fountain Coding

## 1. Project Overview

Build a complete offline file-transfer system called **VisualDrop** that allows a sender device to transmit files to a receiver device using only:

- A display/screen on the sender
- A camera on the receiver
- Visible light
- Software-based visual data encoding/decoding

The system must NOT depend on:

- Internet
- Wi-Fi
- Bluetooth
- Cellular network
- USB cable
- Cloud storage
- External server

The sender converts a file into a sequence of encoded data packets. Those packets are rendered visually as rapidly changing QR/data patterns on the sender's display.

The receiver points its camera at the sender's display. The receiver continuously captures frames, detects and decodes the visual packets, validates them, removes duplicates, performs fountain/erasure decoding, reconstructs the original file, verifies its integrity, and saves the file locally.

The ultimate goal is to create a system conceptually similar to a **high-speed optical wireless file-transfer protocol**, where:

```text
FILE
 ↓
CHUNKING
 ↓
FOUNTAIN / ERASURE ENCODING
 ↓
PACKETIZATION
 ↓
VISUAL ENCODING
 ↓
DISPLAY
 ↓
VISIBLE LIGHT
 ↓
CAMERA
 ↓
FRAME PROCESSING
 ↓
VISUAL/PACKET DECODING
 ↓
FOUNTAIN DECODING
 ↓
BLOCK RECONSTRUCTION
 ↓
FILE RECONSTRUCTION
 ↓
HASH VERIFICATION
 ↓
ORIGINAL FILE
```

---

# 2. Main Objective

The primary objective is:

> Transfer an arbitrary file from one device to another through a visual screen-to-camera communication channel without requiring any conventional network connection.

The project must be designed as a real communication protocol rather than merely a QR-code file-sharing demo.

It must support:

- File metadata
- File chunking
- Session identification
- Packet sequencing
- Duplicate detection
- Corruption detection
- Lost-frame tolerance
- Fountain/erasure coding
- File reconstruction
- Integrity verification
- Transfer progress
- Transfer statistics
- Error handling
- Sender and receiver state management

---

# 3. Example Use Case

Suppose a laptop contains:

```text
example.pdf
```

The user opens VisualDrop Sender and selects the file.

The sender calculates:

```text
File name
File size
MIME type
SHA-256 hash
```

The file is divided into blocks.

For example:

```text
example.pdf
     |
     +---- Block 0
     +---- Block 1
     +---- Block 2
     +---- Block 3
     +---- ...
     +---- Block N
```

The blocks are passed into the fountain encoder.

The encoder generates many encoded packets.

Those packets are converted into visual symbols.

The laptop screen rapidly displays:

```text
FRAME 1
FRAME 2
FRAME 3
FRAME 4
FRAME 5
...
FRAME N
```

The receiver phone points its camera toward the laptop screen.

The receiver:

```text
captures frame
     ↓
detects visual data
     ↓
decodes packet
     ↓
validates packet
     ↓
checks session
     ↓
checks duplicate
     ↓
stores encoded information
     ↓
runs fountain decoder
```

Once enough independent packets have been received:

```text
Encoded packets
      ↓
Fountain decoder
      ↓
Original blocks
      ↓
File
```

Finally:

```text
SHA-256(received file)
        =
SHA-256(original file)
```

If they match:

```text
TRANSFER COMPLETE
```

---

# 4. Core Architecture

Create two primary applications.

## Sender

```text
visualdrop-sender/
```

Responsibilities:

- File selection
- File metadata extraction
- File hashing
- File chunking
- Fountain encoding
- Packet creation
- Visual encoding
- Frame generation
- Screen rendering
- Transmission statistics

## Receiver

```text
visualdrop-receiver/
```

Responsibilities:

- Camera capture
- Frame preprocessing
- Visual symbol detection
- Packet decoding
- Packet validation
- Duplicate detection
- Session handling
- Fountain decoding
- File reconstruction
- Hash verification
- Transfer statistics
- Saving the reconstructed file

---

# 5. Recommended Technology Stack

For the first implementation, prioritize correctness and portability over maximum speed.

## Sender

Use:

- Python
- PySide6 or another desktop UI framework
- OpenCV
- NumPy
- QR/Data Matrix encoder
- Custom protocol layer

## Receiver

For the first prototype, use:

- Python
- OpenCV
- PySide6

A later version can use:

- Android
- Kotlin
- CameraX
- OpenCV
- native decoder libraries

The architecture must keep the protocol independent from the UI and platform.

---

# 6. Important Design Principle

Separate the system into layers.

Do NOT put everything into one Python file.

Use:

```text
Application Layer
        ↓
Transfer Layer
        ↓
Fountain Coding Layer
        ↓
Packet Protocol Layer
        ↓
Visual Encoding Layer
        ↓
Display / Camera Layer
```

This allows the visual transport to be replaced later without rewriting the entire system.

---

# 7. Complete Project Structure

Create the following architecture:

```text
VisualDrop/
│
├── README.md
├── LICENSE
├── .gitignore
├── requirements.txt
├── pyproject.toml
│
├── docs/
│   ├── architecture.md
│   ├── protocol.md
│   ├── fountain-coding.md
│   ├── visual-channel.md
│   ├── performance.md
│   └── troubleshooting.md
│
├── shared/
│   ├── __init__.py
│   ├── protocol.py
│   ├── constants.py
│   ├── models.py
│   ├── checksum.py
│   ├── hashing.py
│   └── serialization.py
│
├── fountain/
│   ├── __init__.py
│   ├── encoder.py
│   ├── decoder.py
│   ├── symbols.py
│   ├── degree_distribution.py
│   └── tests/
│
├── visual/
│   ├── __init__.py
│   ├── encoder.py
│   ├── decoder.py
│   ├── detector.py
│   ├── renderer.py
│   └── preprocessing.py
│
├── sender/
│   ├── __init__.py
│   ├── main.py
│   ├── sender.py
│   ├── file_reader.py
│   ├── packet_generator.py
│   ├── transmission_engine.py
│   └── ui/
│
├── receiver/
│   ├── __init__.py
│   ├── main.py
│   ├── receiver.py
│   ├── camera.py
│   ├── packet_processor.py
│   ├── reconstruction.py
│   └── ui/
│
├── tests/
│   ├── test_protocol.py
│   ├── test_fountain.py
│   ├── test_packet_loss.py
│   ├── test_reconstruction.py
│   ├── test_integrity.py
│   └── test_end_to_end.py
│
└── examples/
    └── sample_files/
```

---

# 8. File Processing Pipeline

When the sender selects a file:

```text
File
 ↓
Read metadata
 ↓
Calculate SHA-256
 ↓
Split into fixed-size blocks
 ↓
Assign block IDs
 ↓
Pass blocks to fountain encoder
```

Metadata should include at minimum:

```text
file_id
session_id
file_name
file_size
mime_type
block_size
total_source_blocks
sha256
```

---

# 9. Session ID

Every transfer must have a unique session ID.

Example:

```text
SESSION_ID = 128-bit random identifier
```

The session ID prevents packets from previous transfers from being mixed into the current transfer.

Example:

```text
Session A:
A7F81C...

Session B:
F12E91...
```

The receiver must reject packets belonging to another session.

---

# 10. Packet Protocol

Design a compact binary packet.

Conceptually:

```text
┌───────────────────────────────┐
│ MAGIC                         │
├───────────────────────────────┤
│ VERSION                       │
├───────────────────────────────┤
│ PACKET TYPE                   │
├───────────────────────────────┤
│ SESSION ID                    │
├───────────────────────────────┤
│ FILE ID                       │
├───────────────────────────────┤
│ ENCODED SYMBOL ID             │
├───────────────────────────────┤
│ SOURCE BLOCK COUNT             │
├───────────────────────────────┤
│ PAYLOAD LENGTH                 │
├───────────────────────────────┤
│ FOUNTAIN METADATA              │
├───────────────────────────────┤
│ PAYLOAD                        │
├───────────────────────────────┤
│ CHECKSUM                       │
└───────────────────────────────┘
```

Use a binary serialization format rather than verbose JSON for high-speed transmission.

During debugging, however, provide a human-readable representation.

---

# 11. Packet Types

Define packet types such as:

```text
SESSION_START
FILE_METADATA
DATA
SESSION_END
TRANSFER_COMPLETE
```

The system should primarily operate as a one-way stream.

Avoid requiring acknowledgements for the basic protocol.

---

# 12. Why Fountain Coding Is Required

Do not design the protocol assuming that every visual frame will be received.

Camera-based transmission is inherently lossy.

For example:

```text
Sender:

1 2 3 4 5 6 7 8 9 10

Receiver:

1 ✓
2 ✗
3 ✓
4 ✓
5 ✗
6 ✓
7 ✗
8 ✓
9 ✓
10 ✗
```

If ordinary sequential chunks are used, missing chunks cause holes.

Fountain coding solves this problem.

The sender creates additional encoded symbols.

The receiver only needs enough independent symbols to recover the original source blocks.

---

# 13. Fountain Coding Concept

Suppose the source blocks are:

```text
A
B
C
D
E
```

The encoder can produce symbols such as:

```text
S1 = A
S2 = C
S3 = A XOR D
S4 = B XOR E
S5 = A XOR B XOR C
...
```

The receiver collects encoded symbols.

The decoder constructs relationships between symbols and source blocks.

Once enough information is available:

```text
Encoded symbols
       ↓
Solve relationships
       ↓
A B C D E
```

For the production implementation, use a mathematically sound fountain/erasure coding approach such as:

- LT codes
- Raptor-style coding
- RaptorQ-compatible approach

Do not implement a fake "random XOR" scheme and call it fountain coding.

The implementation must be able to tolerate missing symbols.

---

# 14. First Prototype Recommendation

For Version 1, implement a simplified LT-code-style decoder.

Source blocks:

```text
K blocks
```

For every encoded symbol:

1. Randomly select a degree.
2. Select source block IDs using a deterministic PRNG seeded by symbol ID.
3. XOR the selected blocks.
4. Store the symbol ID and seed/degree information.

The receiver can regenerate the same block selection from the symbol ID.

This reduces metadata size.

---

# 15. Deterministic Symbol Generation

A critical design requirement:

The sender and receiver must derive the same block selection.

For example:

```text
seed = hash(session_id + symbol_id)
```

Then:

```text
PRNG(seed)
    ↓
degree
    ↓
selected source blocks
```

Therefore the receiver knows:

```text
Symbol 124
→ generated from blocks [2, 17, 31, 42]
```

without transmitting a huge list of block IDs.

---

# 16. Visual Encoding

The encoded packet must be converted into a visual representation.

Version 1 can use:

```text
QR Code
```

or:

```text
Data Matrix
```

for simplicity.

However, design the visual abstraction so that it can later support a custom high-density visual protocol.

Interface:

```python
encode_packet(packet) -> image
```

and:

```python
decode_frame(image) -> packet
```

---

# 17. Visual Frame Design

Each displayed frame should contain:

```text
┌────────────────────────────────┐
│                                │
│        visual data region      │
│                                │
│                                │
│        encoded packet          │
│                                │
│                                │
└────────────────────────────────┘
```

For custom visual encoding, reserve areas for:

```text
Synchronization
Orientation
Version
Session
Packet
Payload
Checksum
```

Use finder/orientation patterns so the receiver can locate the data region.

---

# 18. Synchronization

The receiver must determine:

> "Where is the data pattern?"

and:

> "Is this a valid VisualDrop frame?"

Add a synchronization pattern.

Conceptually:

```text
┌──────┐
│SYNC  │
└──────┘
      DATA DATA DATA
      DATA DATA DATA
```

The receiver first detects synchronization and then processes the payload.

---

# 19. Camera Pipeline

The receiver camera pipeline should be:

```text
Camera
 ↓
Frame capture
 ↓
Resize
 ↓
Grayscale
 ↓
Contrast enhancement
 ↓
Noise reduction
 ↓
Pattern detection
 ↓
Perspective correction
 ↓
Visual decoder
 ↓
Packet extraction
```

Do not unnecessarily process every pixel at maximum resolution.

Use an adaptive processing strategy.

---

# 20. Perspective Correction

The sender screen and phone camera will rarely be perfectly aligned.

The receiver should detect the visual data region.

If the four corners are:

```text
P1 P2
P4 P3
```

apply a perspective transformation:

```text
camera image
     ↓
homography
     ↓
rectified data image
     ↓
decoder
```

This greatly improves decoding reliability.

---

# 21. Frame Validation

Every decoded packet must be validated.

Check:

```text
MAGIC
VERSION
SESSION_ID
FILE_ID
PAYLOAD_LENGTH
CHECKSUM
```

If invalid:

```text
INVALID FRAME
```

Do not pass invalid data to the fountain decoder.

---

# 22. Duplicate Detection

The receiver must track already received symbols.

Maintain something like:

```text
received_symbol_ids = set()
```

When a packet arrives:

```python
if symbol_id in received_symbol_ids:
    duplicate_count += 1
else:
    received_symbol_ids.add(symbol_id)
    process_symbol()
```

This is important because the camera may capture the same visual frame more than once.

---

# 23. Transfer State Machine

The receiver should have explicit states:

```text
IDLE
 ↓
SEARCHING
 ↓
SESSION_DETECTED
 ↓
RECEIVING_METADATA
 ↓
RECEIVING_DATA
 ↓
DECODING
 ↓
RECONSTRUCTING
 ↓
VERIFYING
 ↓
COMPLETE
```

Error state:

```text
ERROR
```

Never allow arbitrary transitions.

---

# 24. Receiver Progress

The receiver UI should display:

```text
Transfer detected

File:
example.pdf

Size:
365 KB

Received:
284 KB

Progress:
77.8%

Unique symbols:
132

Duplicates:
17

Invalid:
3

Capture FPS:
60

Decode FPS:
48

Goodput:
140 KB/s

Elapsed:
2.1 sec
```

---

# 25. Sender UI

Create a clean desktop interface.

Main screen:

```text
VISUALDROP

Offline Visual File Transfer

[ Select File ]

Selected:
example.pdf

Size:
365 KB

[ START TRANSMISSION ]

Transmission:
████████████████████ 100%

FPS:
60

Payload:
365 KB

Goodput:
140 KB/s

Status:
TRANSMITTING
```

When finished:

```text
Transmission complete
```

---

# 26. Receiver UI

Receiver:

```text
VISUALDROP

Point camera at sender screen

┌──────────────────────────┐
│                          │
│      CAMERA PREVIEW      │
│                          │
│       [ DATA FOUND ]     │
│                          │
└──────────────────────────┘

Session:
A8F32...

File:
example.pdf

Progress:
78%

Unique:
132

Duplicate:
17

Dropped:
8

Decode FPS:
49

Goodput:
137 KB/s
```

---

# 27. Transfer Completion

The receiver must not report success merely because it received enough bytes.

It must reconstruct the entire file and verify:

```text
SHA256(received_file)
```

against:

```text
SHA256(original_file)
```

Only if:

```text
hash_received == hash_original
```

should the UI display:

```text
TRANSFER COMPLETE
FILE VERIFIED
```

Otherwise:

```text
TRANSFER FAILED
INTEGRITY CHECK FAILED
```

---

# 28. Performance Metrics

Measure at least:

```text
capture_fps
decode_fps
display_fps
total_frames
new_frames
duplicate_frames
invalid_frames
dropped_frames
unique_symbols
total_symbols
payload_bytes
goodput
elapsed_time
decode_latency
reconstruction_time
```

Calculate:

```text
Goodput = successfully reconstructed payload / elapsed time
```

Also calculate:

```text
Raw throughput
Application throughput
Effective goodput
```

Do not confuse these metrics.

---

# 29. Target Performance

Do NOT hard-code the target performance.

The first version should prioritize reliability.

Set benchmark targets:

### Version 1

```text
Reliable transfer
Small files
~5–20 KB/s
```

### Version 2

```text
Improved visual encoding
~20–100 KB/s
```

### Version 3

```text
Optimized decoding
high-refresh-rate display
~100+ KB/s
```

### Stretch goal

Approach the demonstration's approximate:

```text
140 KB/s
```

depending on hardware.

Do not claim this speed until measured experimentally.

---

# 30. Handling Frame Loss

The system must work when:

```text
5%
10%
20%
30%
```

of frames are lost.

Create an automated simulation test.

Example:

```text
Original:
1000 symbols

Drop:
100 symbols

Receiver:
900 symbols

Result:
File successfully reconstructed
```

Repeat for multiple loss percentages.

---

# 31. Handling Duplicates

Simulate:

```text
Packet 1
Packet 2
Packet 2
Packet 3
Packet 3
Packet 3
Packet 4
```

The decoder should process each unique symbol only once.

---

# 32. Handling Corruption

Randomly modify packet bytes.

The checksum should detect corruption.

Example:

```text
Original packet
     ↓
Modify byte 123
     ↓
Checksum mismatch
     ↓
Reject packet
```

The corrupted packet must never enter the fountain decoder.

---

# 33. File Types

The system should support arbitrary binary files.

Do NOT restrict the implementation to:

```text
.txt
.jpg
.png
.pdf
```

It should support:

```text
PDF
PNG
JPG
MP4
ZIP
EXE
DOCX
TXT
CSV
JSON
etc.
```

Everything must be treated as raw bytes.

---

# 34. Security

The receiver must not automatically execute received files.

Received files should be stored safely.

Sanitize filenames.

For example:

```text
../../malicious.exe
```

must NOT be able to escape the download directory.

Convert it into a safe filename.

Also limit:

```text
maximum file size
maximum session duration
maximum packet size
```

to prevent memory exhaustion.

---

# 35. Privacy

The system should be completely local.

No:

```text
analytics
cloud upload
external API
remote server
```

unless explicitly added later.

The file should remain on the two participating devices.

---

# 36. No Acknowledgement Requirement

The basic protocol should be one-way:

```text
Sender
   ↓
Screen
   ↓
Camera
   ↓
Receiver
```

Do not require the receiver to communicate back to the sender.

This makes the system usable even when the sender has no camera or return channel.

A future version can optionally implement a bidirectional protocol.

---

# 37. Optional Bidirectional Version

Later support:

```text
Sender Screen
      ↓
Receiver Camera

Receiver Screen
      ↓
Sender Camera
```

This would allow:

```text
ACK
NACK
adaptive bitrate
transmission control
pause
resume
```

But this must NOT be required for Version 1.

---

# 38. Adaptive Transmission

A future optimization should dynamically adjust:

```text
display frame rate
payload size
visual redundancy
encoding density
```

based on receiver performance.

For example:

```text
Decode FPS = 60
Frame loss = 1%
```

Increase speed.

If:

```text
Decode FPS = 20
Frame loss = 35%
```

reduce transmission rate.

---

# 39. Compression

Optional compression can be added before chunking.

Pipeline:

```text
Original File
 ↓
Compression
 ↓
Chunking
 ↓
Fountain Encoding
 ↓
Visual Encoding
```

Do not blindly compress already-compressed files.

Provide an option:

```text
Automatic compression
```

---

# 40. Resume Support

Future version:

If a transfer stops at:

```text
73%
```

the receiver should be able to resume if the sender still has the same session/file.

This requires persistent transfer metadata.

---

# 41. Multiple Files

Future version should support:

```text
Select multiple files
```

and package them into a transfer archive:

```text
transfer.zip
```

or a custom container.

---

# 42. Testing Strategy

Implement unit tests first.

## Protocol tests

Test:

```text
serialization
deserialization
checksum
metadata
packet validation
```

## Fountain tests

Test:

```text
encoding
decoding
missing symbols
duplicate symbols
random ordering
high packet loss
```

## Visual tests

Test:

```text
encoding
decoding
rotation
perspective
brightness
blur
noise
```

## End-to-end tests

Test:

```text
File
 ↓
Sender
 ↓
Visual frames
 ↓
Receiver
 ↓
File
```

Then compare hashes.

---

# 43. Automated End-to-End Test

Create:

```text
tests/test_end_to_end.py
```

The test should:

1. Generate a random binary file.
2. Calculate SHA-256.
3. Encode it.
4. Generate visual frames.
5. Simulate frame loss.
6. Shuffle frames.
7. Decode packets.
8. Fountain-decode blocks.
9. Reconstruct file.
10. Calculate SHA-256.
11. Compare hashes.

Expected:

```text
Original SHA256:
abc123...

Received SHA256:
abc123...

PASS
```

---

# 44. Visual Channel Simulation

Before using a physical camera, build a simulated channel.

Simulate:

```text
frame loss
duplicate frames
blur
rotation
brightness changes
perspective distortion
noise
compression artifacts
```

Example:

```text
Sender frame
    ↓
Gaussian blur
    ↓
Perspective distortion
    ↓
JPEG compression
    ↓
Noise
    ↓
Random frame drop
    ↓
Receiver decoder
```

This allows protocol development before hardware optimization.

---

# 45. Debug Mode

Add a debug mode.

It should show:

```text
Frame number
Detected region
Decoded packet ID
Session ID
Checksum status
Decoder state
FPS
Latency
```

Optionally save failed frames:

```text
debug/
    failed_001.png
    failed_002.png
```

This will be extremely useful during development.

---

# 46. Logging

Use structured logging.

Example:

```text
INFO  Session detected
INFO  File metadata received
INFO  Symbol received: 124
DEBUG Duplicate symbol: 124
WARN  Invalid checksum
INFO  Fountain decoder progress: 82%
INFO  File reconstruction started
INFO  SHA256 verification passed
INFO  Transfer complete
```

Do not spam the console with every frame in normal mode.

Provide:

```text
INFO
DEBUG
TRACE
```

logging levels.

---

# 47. Error Handling

Handle:

```text
camera unavailable
camera permission denied
invalid frame
corrupted packet
unknown session
timeout
insufficient symbols
file reconstruction failure
hash mismatch
unsupported format
file too large
decoder exception
```

Every error should provide a useful message.

---

# 48. Timeout

If the receiver doesn't detect a valid frame for a configurable period:

```text
SEARCHING...
```

If a session has started but no packets arrive for too long:

```text
SESSION TIMEOUT
```

Do not hang indefinitely.

---

# 49. Protocol Documentation

Create:

```text
docs/protocol.md
```

Document:

- packet structure
- field sizes
- byte ordering
- session handling
- checksum
- symbol IDs
- fountain coding
- state machine
- visual encoding
- error handling

Someone unfamiliar with the project should be able to implement another compatible receiver from this document.

---

# 50. Important Separation

Do NOT tightly couple:

```text
QR
```

to:

```text
Fountain coding
```

The system should look like:

```text
Fountain packet
      ↓
Transport abstraction
      ↓
Visual encoder
```

Then later the visual transport can become:

```text
QR
Data Matrix
Custom binary matrix
Color matrix
Temporal modulation
```

without changing the fountain layer.

---

# 51. Transport Interface

Design something similar to:

```python
class VisualTransport:

    def encode(self, packet):
        ...

    def decode(self, frame):
        ...
```

Implement:

```text
QRTransport
```

first.

Later:

```text
CustomMatrixTransport
```

---

# 52. Protocol Interface

Similarly:

```python
class FountainEncoder:

    def generate_symbol(self):
        ...


class FountainDecoder:

    def add_symbol(self, symbol):
        ...

    def is_complete(self):
        ...

    def reconstruct(self):
        ...
```

This keeps the architecture modular.

---

# 53. Important Optimization Strategy

Do NOT attempt maximum speed immediately.

Follow this order:

```text
1. Correctness
2. Reliability
3. Protocol stability
4. Camera decoding
5. Frame synchronization
6. Performance profiling
7. Optimization
```

Never sacrifice correctness merely to increase FPS.

---

# 54. Performance Optimization

After the system works:

Profile:

```text
camera capture
image preprocessing
pattern detection
visual decoding
packet validation
fountain decoding
file writing
```

Determine the bottleneck.

Possible optimization techniques:

- lower resolution during detection
- crop ROI
- parallel decoding
- frame skipping
- native libraries
- NumPy vectorization
- OpenCV optimization
- multithreading
- multiprocessing where appropriate
- GPU acceleration where beneficial

Do not optimize components without measuring them first.

---

# 55. Hardware Benchmark

Create a benchmark report containing:

```text
Sender device
CPU
GPU
Display resolution
Display refresh rate

Receiver device
CPU
Camera resolution
Camera FPS

Distance
Lighting
Angle

File size
Transfer duration
Goodput
Frame loss
Duplicate rate
Decode FPS
```

Example:

```text
File: 365 KB
Time: 2.6 sec
Goodput: 140.42 KB/s
Capture FPS: 60
Decode FPS: 52
Frame loss: 4.2%
Duplicate rate: 1.3%
```

Only report measured values.

---

# 56. Final User Experience

The final system should be extremely simple.

## Sender

```text
1. Open VisualDrop
2. Select file
3. Click Start
4. Show sender screen to receiver camera
5. Wait
6. Transfer complete
```

## Receiver

```text
1. Open VisualDrop
2. Start camera
3. Point at sender display
4. Wait
5. File automatically reconstructed
6. File verified
```

No accounts.

No login.

No Internet.

No pairing.

No cables.

---

# 57. Project Name

Use:

# VisualDrop

Subtitle:

> Offline Optical File Transfer Through Screen-to-Camera Communication

Alternative names can be considered later, but keep the implementation name consistent.

---

# 58. README Requirements

The README must explain:

## What is VisualDrop?

An offline optical file-transfer system that uses a sender display and receiver camera.

## How it works

Include the complete pipeline:

```text
File
→ Chunking
→ Fountain Encoding
→ Packetization
→ Visual Encoding
→ Display
→ Camera
→ Decoding
→ Fountain Decoding
→ Reconstruction
→ SHA-256 Verification
```

## Features

- Offline
- No Wi-Fi
- No Bluetooth
- Camera-based
- Screen-based
- Fountain coding
- Loss tolerant
- Duplicate tolerant
- Binary file support
- Integrity verification
- Real-time statistics

## Architecture

Include architecture diagrams.

## Installation

Provide exact commands.

## Running sender

Provide command.

## Running receiver

Provide command.

## Testing

Provide test commands.

## Performance

Document benchmark methodology.

## Limitations

Be honest about:

- line of sight
- camera quality
- screen refresh rate
- lighting
- distance
- decoding performance

---

# 59. Development Roadmap

Implement the project in the following exact order.

## Milestone 1 — Protocol

Implement:

```text
packet format
metadata
checksum
session ID
serialization
```

Do not touch camera yet.

---

## Milestone 2 — File Chunking

Implement:

```text
file → blocks → file reconstruction
```

Verify SHA-256.

---

## Milestone 3 — Fountain Coding

Implement:

```text
blocks → encoded symbols
encoded symbols → blocks
```

Test with random packet loss.

---

## Milestone 4 — QR Transport

Implement:

```text
packet → QR image
QR image → packet
```

---

## Milestone 5 — Screen Sender

Display generated QR frames continuously.

---

## Milestone 6 — Camera Receiver

Capture camera frames and decode QR frames.

---

## Milestone 7 — End-to-End Transfer

Build:

```text
Laptop screen
       ↓
Phone/laptop camera
       ↓
Original file
```

---

## Milestone 8 — Statistics

Add:

```text
FPS
goodput
duplicates
dropped frames
invalid packets
progress
elapsed time
```

---

## Milestone 9 — Reliability

Test:

```text
10% loss
20% loss
30% loss
```

and different camera angles.

---

## Milestone 10 — Performance

Optimize toward:

```text
60 FPS
100+ KB/s
```

and eventually attempt to approach:

```text
~140 KB/s
```

if the hardware permits.

---

# 60. Critical Development Rule

Do NOT pretend that the project is finished merely because a QR code can be scanned.

The actual objective is:

```text
ARBITRARY FILE
       ↓
FOUNTAIN ENCODING
       ↓
CONTINUOUS VISUAL TRANSMISSION
       ↓
CAMERA RECEIVER
       ↓
LOSS-TOLERANT DECODING
       ↓
ORIGINAL FILE
       ↓
HASH VERIFIED
```

The final system must demonstrate a genuine end-to-end transfer.

---

# 61. Deliverables

At the end of development, provide:

```text
1. Working sender application
2. Working receiver application
3. Shared protocol implementation
4. Fountain encoder
5. Fountain decoder
6. Visual encoder
7. Visual decoder
8. Camera pipeline
9. File reconstruction
10. SHA-256 verification
11. Real-time statistics
12. Unit tests
13. Integration tests
14. End-to-end tests
15. Documentation
16. Architecture diagram
17. Protocol specification
18. Performance benchmark
19. Troubleshooting guide
20. README
```

---

# 62. Definition of Done

The project is considered complete only when the following works:

```text
Select a file
      ↓
Start sender
      ↓
Sender continuously displays visual data
      ↓
Receiver camera captures it
      ↓
Receiver decodes packets
      ↓
Packets can arrive out of order
      ↓
Packets can be duplicated
      ↓
Some packets can be lost
      ↓
Fountain decoder reconstructs source blocks
      ↓
File is reconstructed
      ↓
SHA-256 matches
      ↓
Receiver reports:

TRANSFER COMPLETE
FILE VERIFIED
```

The implementation must be reproducible and documented.

---

# 63. Final Engineering Goal

The project should ultimately demonstrate that a normal computer display and camera can be turned into a practical **short-range optical data channel**.

The conceptual communication stack is:

```text
┌─────────────────────────────────────┐
│          APPLICATION                │
│          File Transfer              │
├─────────────────────────────────────┤
│          FILE LAYER                 │
│      Chunking / Reconstruction      │
├─────────────────────────────────────┤
│          CODING LAYER               │
│       Fountain / Erasure Code       │
├─────────────────────────────────────┤
│          PACKET LAYER               │
│   Session / ID / Checksum / Data    │
├─────────────────────────────────────┤
│          VISUAL LAYER               │
│      QR / Custom Matrix             │
├─────────────────────────────────────┤
│          OPTICAL CHANNEL            │
│          Display → Light            │
├─────────────────────────────────────┤
│          CAMERA LAYER               │
│       Capture / Processing          │
└─────────────────────────────────────┘
```

Build the system from the bottom up, verify each layer independently, and only then integrate the complete pipeline.

The first goal is **correct and reliable transfer**.

The second goal is **loss tolerance**.

The third goal is **high throughput**.

Do not claim performance numbers that have not been measured on real hardware.