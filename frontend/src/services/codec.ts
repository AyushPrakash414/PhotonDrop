/**
 * PhotonDrop optical codec (TypeScript client-side implementation).
 * Matches Python backend wire format 100%.
 *
 * File -> chunks -> LT fountain coded symbols -> binary frames -> base64 -> QR
 * frames. The receiver peels the equations back into the original chunks and
 * verifies a SHA-256 digest.
 */

export const MAGIC_0 = 0x50; // 'P'
export const MAGIC_1 = 0x44; // 'D'
export const VERSION = 1;
export const HEADER_BYTES = 24;

export const FRAME_MANIFEST = 0;
export const FRAME_DATA = 1;

export type Manifest = {
  name: string;
  size: number;
  mime: string;
  digest: string;
  chunks: number;
  chunkSize: number;
  fileId?: number;
};

export type ParsedFrame =
  | { type: "manifest"; fileId: number; manifest: Manifest }
  | {
      type: "data";
      fileId: number;
      chunks: number;
      chunkSize: number;
      size: number;
      seed: number;
      payload: Uint8Array;
    };

/** Deterministic PRNG so the receiver can rebuild an encoder's chunk picks. */
export function mulberry32(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Robust-soliton-ish degree distribution for LT coding. */
function pickDegree(rand: () => number, chunks: number) {
  if (chunks <= 1) return 1;
  const r = rand();
  if (r < 0.06) return 1;
  let cumulative = 0.06;
  for (let d = 2; d <= Math.min(chunks, 40); d++) {
    cumulative += 0.94 / (d * (d - 1));
    if (r < cumulative) return d;
  }
  return 2;
}

/** The chunk indices XOR-ed into the symbol identified by `seed`. */
export function chunkIndicesForSeed(seed: number, chunks: number): number[] {
  if (seed < chunks) return [seed]; // systematic prefix: fast first pass
  const rand = mulberry32((seed + 0x9e3779b9) >>> 0);
  const degree = pickDegree(rand, chunks);
  const picked = new Set<number>();
  let guard = 0;
  while (picked.size < degree && guard++ < degree * 32) {
    picked.add(Math.floor(rand() * chunks) % chunks);
  }
  return [...picked];
}

export function xorInto(target: Uint8Array, source: Uint8Array) {
  for (let i = 0; i < target.length; i++) target[i] ^= source[i];
}

export async function sha256Hex(data: Uint8Array | ArrayBuffer): Promise<string> {
  const buffer = data instanceof Uint8Array ? (data.slice().buffer as ArrayBuffer) : data;
  const digest = await crypto.subtle.digest("SHA-256", buffer);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

export function bytesToBase64(bytes: Uint8Array): string {
  let out = "";
  const step = 0x8000;
  for (let i = 0; i < bytes.length; i += step) {
    out += String.fromCharCode(...bytes.subarray(i, i + step));
  }
  return btoa(out);
}

export function base64ToBytes(value: string): Uint8Array {
  const raw = atob(value);
  const bytes = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
  return bytes;
}

function writeHeader(
  view: DataView,
  type: number,
  fileId: number,
  chunks: number,
  chunkSize: number,
  size: number,
  seed: number,
) {
  view.setUint8(0, MAGIC_0);
  view.setUint8(1, MAGIC_1);
  view.setUint8(2, VERSION);
  view.setUint8(3, type);
  view.setUint32(4, fileId >>> 0, false);
  view.setUint32(8, chunks >>> 0, false);
  view.setUint32(12, chunkSize >>> 0, false);
  view.setUint32(16, size >>> 0, false);
  view.setUint32(20, seed >>> 0, false);
}

export function buildDataFrame(opts: {
  fileId: number;
  chunks: number;
  chunkSize: number;
  size: number;
  seed: number;
  payload: Uint8Array;
}): string {
  const frame = new Uint8Array(HEADER_BYTES + opts.payload.length);
  writeHeader(
    new DataView(frame.buffer),
    FRAME_DATA,
    opts.fileId,
    opts.chunks,
    opts.chunkSize,
    opts.size,
    opts.seed,
  );
  frame.set(opts.payload, HEADER_BYTES);
  return bytesToBase64(frame);
}

export function buildManifestFrame(fileId: number, manifest: Manifest): string {
  const json = new TextEncoder().encode(JSON.stringify(manifest));
  const frame = new Uint8Array(HEADER_BYTES + json.length);
  writeHeader(
    new DataView(frame.buffer),
    FRAME_MANIFEST,
    fileId,
    manifest.chunks,
    manifest.chunkSize,
    manifest.size,
    0,
  );
  frame.set(json, HEADER_BYTES);
  return bytesToBase64(frame);
}

export function parseFrame(text: string): ParsedFrame | null {
  let bytes: Uint8Array;
  try {
    bytes = base64ToBytes(text.trim());
  } catch {
    return null;
  }
  if (bytes.length <= HEADER_BYTES) return null;
  if (bytes[0] !== MAGIC_0 || bytes[1] !== MAGIC_1 || bytes[2] !== VERSION) return null;

  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const type = view.getUint8(3);
  const fileId = view.getUint32(4, false);
  const chunks = view.getUint32(8, false);
  const chunkSize = view.getUint32(12, false);
  const size = view.getUint32(16, false);
  const seed = view.getUint32(20, false);
  const payload = bytes.subarray(HEADER_BYTES);

  if (type === FRAME_MANIFEST) {
    try {
      const manifest = JSON.parse(new TextDecoder().decode(payload)) as Manifest;
      return { type: "manifest", fileId, manifest };
    } catch {
      return null;
    }
  }
  if (type !== FRAME_DATA || chunks === 0 || payload.length !== chunkSize) return null;
  return { type: "data", fileId, chunks, chunkSize, size, seed, payload: payload.slice() };
}

/** Splits a file body into fixed-size, zero-padded chunks. */
export function splitIntoChunks(data: Uint8Array, chunkSize = 512): Uint8Array[] {
  const count = Math.max(1, Math.ceil(data.length / chunkSize));
  const chunks: Uint8Array[] = [];
  for (let i = 0; i < count; i++) {
    const chunk = new Uint8Array(chunkSize);
    chunk.set(data.subarray(i * chunkSize, Math.min((i + 1) * chunkSize, data.length)));
    chunks.push(chunk);
  }
  return chunks;
}

export function encodeSymbol(chunks: Uint8Array[], seed: number): Uint8Array {
  const indices = chunkIndicesForSeed(seed, chunks.length);
  const symbol = new Uint8Array(chunks[0].length);
  for (const index of indices) xorInto(symbol, chunks[index]);
  return symbol;
}

/** Incremental peeling decoder: tolerates dropped and duplicated frames. */
export class FountainDecoder {
  readonly chunks: number;
  readonly chunkSize: number;
  readonly size: number;
  private solved = new Map<number, Uint8Array>();
  private equations: { indices: Set<number>; data: Uint8Array }[] = [];
  private seenSeeds = new Set<number>();

  constructor(chunks: number, chunkSize: number, size: number) {
    this.chunks = chunks;
    this.chunkSize = chunkSize;
    this.size = size;
  }

  get solvedCount() {
    return this.solved.size;
  }

  get complete() {
    return this.solved.size >= this.chunks;
  }

  hasSeed(seed: number) {
    return this.seenSeeds.has(seed);
  }

  /** Returns true when the symbol carried new information. */
  addSymbol(seed: number, payload: Uint8Array): boolean {
    if (this.seenSeeds.has(seed) || this.complete) return false;
    this.seenSeeds.add(seed);

    const indices = new Set(chunkIndicesForSeed(seed, this.chunks));
    const data = payload.slice();
    this.reduce(indices, data);
    if (indices.size === 0) return false;

    this.equations.push({ indices, data });
    this.peel();
    return true;
  }

  private reduce(indices: Set<number>, data: Uint8Array) {
    for (const index of [...indices]) {
      const known = this.solved.get(index);
      if (known) {
        xorInto(data, known);
        indices.delete(index);
      }
    }
  }

  private peel() {
    let progressed = true;
    while (progressed) {
      progressed = false;
      for (let i = this.equations.length - 1; i >= 0; i--) {
        const equation = this.equations[i];
        this.reduce(equation.indices, equation.data);
        if (equation.indices.size === 0) {
          this.equations.splice(i, 1);
          continue;
        }
        if (equation.indices.size === 1) {
          const index = [...equation.indices][0];
          this.solved.set(index, equation.data);
          this.equations.splice(i, 1);
          progressed = true;
        }
      }
    }
  }

  assemble(): Uint8Array | null {
    if (!this.complete) return null;
    const out = new Uint8Array(this.chunks * this.chunkSize);
    for (let i = 0; i < this.chunks; i++) {
      const chunk = this.solved.get(i);
      if (!chunk) return null;
      out.set(chunk, i * this.chunkSize);
    }
    return out.subarray(0, this.size);
  }
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}
