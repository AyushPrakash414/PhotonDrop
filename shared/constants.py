"""
PhotonDrop — Protocol Constants

Defines magic bytes, protocol version, packet types, default sizes,
and safety limits for the PhotonDrop wire protocol.
"""

# ─── Magic & Version ───────────────────────────────────────────────
MAGIC = b"PDROP"           # 5-byte magic header identifying PhotonDrop packets
PROTOCOL_VERSION = 1        # Wire protocol version

# ─── Packet Types ──────────────────────────────────────────────────
PACKET_TYPE_SESSION_START     = 0x01
PACKET_TYPE_FILE_METADATA     = 0x02
PACKET_TYPE_DATA              = 0x03
PACKET_TYPE_SESSION_END       = 0x04
PACKET_TYPE_TRANSFER_COMPLETE = 0x05

PACKET_TYPE_NAMES = {
    PACKET_TYPE_SESSION_START:     "SESSION_START",
    PACKET_TYPE_FILE_METADATA:     "FILE_METADATA",
    PACKET_TYPE_DATA:              "DATA",
    PACKET_TYPE_SESSION_END:       "SESSION_END",
    PACKET_TYPE_TRANSFER_COMPLETE: "TRANSFER_COMPLETE",
}

# ─── Block / Payload Sizing ───────────────────────────────────────
DEFAULT_BLOCK_SIZE = 256      # bytes per source block (tunable)
MAX_PAYLOAD_SIZE   = 2048     # hard ceiling for a single packet payload
MAX_PACKET_SIZE    = 4096     # hard ceiling for the entire serialized packet

# ─── Session ───────────────────────────────────────────────────────
SESSION_ID_BYTES = 16         # 128-bit session identifier

# ─── File Limits ───────────────────────────────────────────────────
MAX_FILE_SIZE     = 100 * 1024 * 1024   # 100 MB safety cap
MAX_FILENAME_LEN  = 255                  # max sanitized filename length

# ─── Timeouts (seconds) ───────────────────────────────────────────
SESSION_TIMEOUT    = 30.0     # no packets → timeout the session
SEARCH_TIMEOUT     = 60.0     # no valid frame found → stop searching

# ─── Checksum ─────────────────────────────────────────────────────
CHECKSUM_ALGO = "crc32"       # fast per-packet integrity check

# ─── Hash ─────────────────────────────────────────────────────────
FILE_HASH_ALGO = "sha256"     # full-file integrity verification

# ─── Display / Camera defaults ────────────────────────────────────
DEFAULT_DISPLAY_FPS = 30      # sender frame rate target
DEFAULT_QR_VERSION  = None    # auto-select QR version based on payload
QR_ERROR_CORRECTION = "M"     # QR error-correction level (L/M/Q/H)

# ─── Logging ──────────────────────────────────────────────────────
LOG_FORMAT = "%(asctime)s %(levelname)-5s [%(name)s] %(message)s"
LOG_DATE_FORMAT = "%H:%M:%S"
