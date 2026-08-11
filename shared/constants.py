"""
PhotonDrop — Protocol Constants

Defines magic bytes, protocol version, packet types, default sizes,
and safety limits for the PhotonDrop wire protocol.
Matches lightspeed-share-main protocol specification exactly.
"""

# ─── Magic & Version ───────────────────────────────────────────────
MAGIC_0 = 0x50            # 'P'
MAGIC_1 = 0x44            # 'D'
PROTOCOL_VERSION = 1       # Wire protocol version
HEADER_BYTES = 24          # Fixed header size in bytes

# Legacy compatibility constants
MAGIC = b"PD"

# ─── Packet Types ──────────────────────────────────────────────────
FRAME_MANIFEST = 0
FRAME_DATA = 1

# Legacy constant aliases
PACKET_TYPE_SESSION_START     = 0x00
PACKET_TYPE_FILE_METADATA     = 0x00
PACKET_TYPE_DATA              = 0x01
PACKET_TYPE_SESSION_END       = 0x02
PACKET_TYPE_TRANSFER_COMPLETE = 0x03

PACKET_TYPE_NAMES = {
    FRAME_MANIFEST: "MANIFEST",
    FRAME_DATA:     "DATA",
}

# ─── Block / Payload Sizing ───────────────────────────────────────
DEFAULT_BLOCK_SIZE = 512      # default bytes per source block (matches lightspeed default)
MAX_PAYLOAD_SIZE   = 4096     # hard ceiling for a single packet payload
MAX_PACKET_SIZE    = 8192     # hard ceiling for the entire serialized packet

# ─── Session ───────────────────────────────────────────────────────
SESSION_ID_BYTES = 4          # 32-bit integer uint32 session/file ID

# ─── File Limits ───────────────────────────────────────────────────
MAX_FILE_SIZE     = 100 * 1024 * 1024   # 100 MB safety cap
MAX_FILENAME_LEN  = 255                  # max sanitized filename length

# ─── Timeouts (seconds) ───────────────────────────────────────────
SESSION_TIMEOUT    = 30.0     # no packets → timeout the session
SEARCH_TIMEOUT     = 60.0     # no valid frame found → stop searching

# ─── Checksum & Hash ───────────────────────────────────────────────
CHECKSUM_ALGO = "crc32"
FILE_HASH_ALGO = "sha256"     # full-file integrity verification

# ─── Display / Camera defaults ────────────────────────────────────
DEFAULT_DISPLAY_FPS = 30      # sender frame rate target
DEFAULT_QR_VERSION  = None    # auto-select QR version based on payload
QR_ERROR_CORRECTION = "M"     # QR error-correction level (L/M/Q/H)

# ─── Logging ──────────────────────────────────────────────────────
LOG_FORMAT = "%(asctime)s %(levelname)-5s [%(name)s] %(message)s"
LOG_DATE_FORMAT = "%H:%M:%S"
