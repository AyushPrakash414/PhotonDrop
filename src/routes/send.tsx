import { createFileRoute } from "@tanstack/react-router";
import { FileUp, Pause, Play, RotateCcw, Upload } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { PageHeader } from "@/components/photon/app-shell";
import {
  buildDataFrame,
  buildManifestFrame,
  encodeSymbol,
  formatBytes,
  sha256Hex,
  splitIntoChunks,
  type Manifest,
} from "@/lib/photon/codec";
import { usePhoton } from "@/lib/photon/store";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/send")({
  head: () => ({
    meta: [
      { title: "Send File — PhotonDrop Optical Transmitter" },
      {
        name: "description",
        content:
          "Pick any file and stream it as fountain-coded optical frames on your screen for a receiving camera.",
      },
      { property: "og:title", content: "Send File — PhotonDrop Optical Transmitter" },
      {
        property: "og:description",
        content: "Stream any file as loss-tolerant visual frames through visible light.",
      },
    ],
  }),
  component: SendPage,
});

type Prepared = { manifest: Manifest; chunks: Uint8Array[]; fileId: number };

function SendPage() {
  const { settings, setLive, logActivity } = usePhoton();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const preparedRef = useRef<Prepared | null>(null);
  const seedRef = useRef(0);
  const framesRef = useRef(0);

  const [prepared, setPrepared] = useState<Prepared | null>(null);
  const [transmitting, setTransmitting] = useState(false);
  const [framesSent, setFramesSent] = useState(0);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);

  const targetFrames = prepared ? Math.ceil(prepared.manifest.chunks * settings.redundancy) : 0;

  const loadFile = useCallback(
    async (file: File) => {
      setBusy(true);
      setTransmitting(false);
      const buffer = new Uint8Array(await file.arrayBuffer());
      const digest = await sha256Hex(buffer);
      const chunks = splitIntoChunks(buffer, settings.chunkSize);
      const manifest: Manifest = {
        name: file.name,
        size: buffer.length,
        mime: file.type || "application/octet-stream",
        digest,
        chunks: chunks.length,
        chunkSize: settings.chunkSize,
      };
      const next = { manifest, chunks, fileId: Math.floor(Math.random() * 0xffffffff) };
      preparedRef.current = next;
      seedRef.current = 0;
      framesRef.current = 0;
      setFramesSent(0);
      setPrepared(next);
      setBusy(false);
    },
    [settings.chunkSize],
  );

  // Frame pump: paints one optical frame per tick at the configured FPS.
  useEffect(() => {
    if (!transmitting || !prepared) return;
    let cancelled = false;
    let timer: number | undefined;

    const run = async () => {
      const QR = (await import("qrcode")).default;
      const tick = async () => {
        const active = preparedRef.current;
        const canvas = canvasRef.current;
        if (cancelled || !active || !canvas) return;

        const index = framesRef.current;
        const text =
          index % 14 === 0
            ? buildManifestFrame(active.fileId, active.manifest)
            : buildDataFrame({
                fileId: active.fileId,
                chunks: active.manifest.chunks,
                chunkSize: active.manifest.chunkSize,
                size: active.manifest.size,
                seed: seedRef.current++,
                payload: encodeSymbol(active.chunks, seedRef.current - 1),
              });

        try {
          await QR.toCanvas(canvas, text, {
            errorCorrectionLevel: settings.errorCorrection,
            margin: 2,
            width: 520,
            color: { dark: "#000000ff", light: "#ffffffff" },
          });
        } catch {
          /* frame too large for this QR config; skip it */
        }
        // qrcode writes inline width/height styles; clear them so the layout owns sizing.
        canvas.style.removeProperty("width");
        canvas.style.removeProperty("height");

        framesRef.current = index + 1;
        setFramesSent(framesRef.current);
        if (!cancelled) timer = window.setTimeout(tick, Math.round(1000 / settings.fps));
      };
      void tick();
    };

    void run();
    setLive({
      linkState: "transmitting",
      senderFps: settings.fps,
      goodput: (settings.fps * settings.chunkSize) / 1024,
    });

    return () => {
      cancelled = true;
      if (timer) window.clearTimeout(timer);
      setLive({ linkState: "idle", senderFps: 0, goodput: 0 });
    };
  }, [transmitting, prepared, settings, setLive]);

  const stop = () => {
    setTransmitting(false);
    if (prepared && framesRef.current > 0) {
      logActivity({
        direction: "send",
        name: prepared.manifest.name,
        size: prepared.manifest.size,
        frames: framesRef.current,
        status: framesRef.current >= targetFrames ? "verified" : "aborted",
        digest: prepared.manifest.digest,
      });
    }
  };

  const reset = () => {
    setTransmitting(false);
    preparedRef.current = null;
    setPrepared(null);
    framesRef.current = 0;
    seedRef.current = 0;
    setFramesSent(0);
  };

  const progress = targetFrames ? Math.min(100, (framesSent / targetFrames) * 100) : 0;

  return (
    <div className="mx-auto max-w-6xl">
      <PageHeader
        title="Send File"
        subtitle="Transmit arbitrary binary files through visible light"
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <section
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            const file = e.dataTransfer.files?.[0];
            if (file) void loadFile(file);
          }}
          className={cn(
            "flex flex-col items-center justify-center rounded-3xl border border-border bg-card p-10 text-center shadow-soft transition-colors",
            dragging && "border-primary bg-accent/40",
          )}
        >
          <div className="flex size-16 items-center justify-center rounded-2xl bg-accent">
            <Upload className="size-7 text-primary" />
          </div>
          <h2 className="mt-6 text-2xl font-bold">
            {prepared ? prepared.manifest.name : "Select a file to transmit"}
          </h2>
          <p className="mt-2 text-[15px] text-muted-foreground">
            {prepared
              ? `${formatBytes(prepared.manifest.size)} · ${prepared.manifest.chunks} chunks · SHA-256 ${prepared.manifest.digest.slice(0, 12)}…`
              : "Drop your file here or choose from your computer"}
          </p>

          <input
            ref={inputRef}
            type="file"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) void loadFile(file);
            }}
          />
          <div className="mt-7 flex flex-wrap justify-center gap-3">
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              className="inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90"
            >
              <FileUp className="size-4" /> {prepared ? "Choose another" : "Select File"}
            </button>
            {prepared ? (
              <>
                <button
                  type="button"
                  onClick={() => (transmitting ? stop() : setTransmitting(true))}
                  className="inline-flex items-center gap-2 rounded-full bg-secondary px-6 py-3 text-sm font-semibold text-secondary-foreground transition-colors hover:bg-muted"
                >
                  {transmitting ? <Pause className="size-4" /> : <Play className="size-4" />}
                  {transmitting ? "Pause" : "Start transmitting"}
                </button>
                <button
                  type="button"
                  onClick={reset}
                  aria-label="Reset transmission"
                  className="inline-flex items-center gap-2 rounded-full border border-border px-4 py-3 text-sm font-semibold transition-colors hover:bg-secondary"
                >
                  <RotateCcw className="size-4" />
                </button>
              </>
            ) : null}
          </div>

          {prepared ? (
            <div className="mt-8 w-full text-left">
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>
                  Frames emitted <span className="font-mono text-foreground">{framesSent}</span> /{" "}
                  {targetFrames}
                </span>
                <span className="font-mono">{progress.toFixed(0)}%</span>
              </div>
              <div className="mt-2 h-2 overflow-hidden rounded-full bg-secondary">
                <div
                  className="h-full rounded-full bg-primary transition-[width]"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                Redundancy {settings.redundancy.toFixed(1)}× — the receiver only needs enough
                frames, not specific ones.
              </p>
            </div>
          ) : null}
        </section>

        <section className="flex flex-col items-center justify-center rounded-3xl border border-border bg-card p-8 shadow-soft">
          <div className="relative flex size-[340px] items-center justify-center rounded-3xl border border-border bg-surface-2 md:size-[380px]">
            <canvas
              ref={canvasRef}
              data-photon-frame=""
              className={cn(
                "w-full max-w-[300px] rounded-xl md:max-w-[340px]",
                (!transmitting || busy) && "opacity-90",
              )}
            />
            {!prepared ? (
              <div className="absolute inset-0 flex items-center justify-center rounded-3xl bg-surface-2">
                <div className="flex size-40 items-center justify-center rounded-2xl border border-dashed border-border text-sm text-muted-foreground">
                  Optical Data Output
                </div>
              </div>
            ) : null}
          </div>
          <p className="eyebrow mt-6 flex items-center gap-2">
            <span
              className={cn(
                "inline-block size-2 rounded-full",
                transmitting ? "bg-primary" : "bg-muted-foreground",
              )}
            />
            {transmitting ? "Transmitting — hold steady" : "Idle — ready to send"}
          </p>
          <p className="mt-2 text-sm text-muted-foreground">
            Point the receiver camera directly at this visual display screen
          </p>
        </section>
      </div>
    </div>
  );
}
