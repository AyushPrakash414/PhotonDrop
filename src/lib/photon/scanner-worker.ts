/**
 * PhotonDrop scanner Web Worker.
 *
 * Receives camera frame pixel data, runs jsQR off the main thread, and posts
 * back the decoded binary payload.  This keeps the UI responsive even at high
 * camera frame rates.
 */

import jsQR from "jsqr";

export type ScanRequest = {
  data: Uint8ClampedArray;
  width: number;
  height: number;
};

export type ScanResult = {
  /** Raw binary bytes from the QR Byte-mode payload. */
  binaryData: number[];
};

self.onmessage = (e: MessageEvent<ScanRequest>) => {
  const { data, width, height } = e.data;
  const code = jsQR(data, width, height, { inversionAttempts: "dontInvert" });
  if (code?.binaryData) {
    const msg: ScanResult = { binaryData: code.binaryData };
    self.postMessage(msg);
  } else {
    // Signal that this frame had no QR code so main thread can send the next
    self.postMessage(null);
  }
};
