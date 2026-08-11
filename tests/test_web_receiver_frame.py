import asyncio
import base64
import os
import sys

import cv2

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.api.receiver_routes import (  # noqa: E402
    ProcessFrameRequest,
    StartReceiverRequest,
    global_receiver,
    process_browser_frame,
    start_receiving,
)
from sender.file_reader import split_into_blocks  # noqa: E402
from sender.packet_generator import PacketGenerator  # noqa: E402
from shared.hashing import compute_sha256  # noqa: E402
from shared.models import FileMetadata, ReceiverState  # noqa: E402
from visual.encoder import QRTransport  # noqa: E402
from visual.renderer import render_frame  # noqa: E402


def _frame_data_url(packet_bytes: bytes) -> str:
    qr = QRTransport(error_correction="M", box_size=4, border=2).encode(packet_bytes)
    rendered = render_frame(qr, canvas_size=(400, 400))
    ok, buffer = cv2.imencode(".png", rendered)
    assert ok
    b64 = base64.b64encode(buffer).decode("ascii")
    return f"data:image/png;base64,{b64}"


def test_browser_start_does_not_open_server_camera():
    global_receiver.reset()

    result = asyncio.run(start_receiving(StartReceiverRequest(mode="browser")))

    assert result["status"] == "browser_ready"
    assert global_receiver.is_active
    assert not global_receiver.camera.is_running
    assert global_receiver.state == ReceiverState.SEARCHING

    global_receiver.reset()


def test_browser_frame_endpoint_processes_qr_packet(tmp_path):
    global_receiver.reset()
    old_output_dir = global_receiver.reconstruction.output_dir
    global_receiver.reconstruction.output_dir = tmp_path
    data = b"hello from the browser receiver"
    blocks = split_into_blocks(data, block_size=64)
    metadata = FileMetadata(
        file_id="webtest123456789",
        session_id=FileMetadata.generate_session_id(),
        file_name="web-test.bin",
        file_size=len(data),
        mime_type="application/octet-stream",
        block_size=64,
        total_source_blocks=len(blocks),
        sha256=compute_sha256(data),
    )
    packets = PacketGenerator(metadata, blocks)

    try:
        asyncio.run(start_receiving(StartReceiverRequest(mode="browser")))
        asyncio.run(process_browser_frame(ProcessFrameRequest(frame_b64=_frame_data_url(packets.session_start_bytes()))))
        asyncio.run(process_browser_frame(ProcessFrameRequest(frame_b64=_frame_data_url(packets.metadata_bytes()))))

        assert global_receiver.state == ReceiverState.RECEIVING_DATA
        assert global_receiver.reconstruction.session.file_metadata is not None
        assert global_receiver.reconstruction.session.file_metadata.file_name == "web-test.bin"

        for _ in range(5):
            asyncio.run(process_browser_frame(ProcessFrameRequest(frame_b64=_frame_data_url(packets.next_data_bytes()))))
            if global_receiver.state == ReceiverState.COMPLETE:
                break

        assert global_receiver.state == ReceiverState.COMPLETE
        assert (tmp_path / "web-test.bin").read_bytes() == data
    finally:
        global_receiver.reset()
        global_receiver.reconstruction.output_dir = old_output_dir
