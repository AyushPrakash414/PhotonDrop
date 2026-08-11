import { createFileRoute } from "@tanstack/react-router";
import { CameraOff, Check, Download, ShieldAlert, ShieldCheck, Video } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { PageHeader } from "@/components/photon/app-shell";
import {
  FountainDecoder,
  formatBytes,
  parseFrame,
  sha256Hex,
  type Manifest,
} from "@/lib/photon/codec";
import { usePhoton } from "@/lib/photon/store";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/receive")({
  head: () => ({
    meta: [
      { title: "Receive File — PhotonDrop Optical Receiver" },
      {
        name: "description",
        content:
          "Point your camera at a sending screen to decode optical frames, recover missing data and verify the file.",
      },
      { property: "og:title", content: "Receive File — PhotonDrop Optical Receiver" },
      {
        property: "og:description",
        content:
          "Decode visible-light frames back into the original file with integrity verification.",
      },
    ],
  }),
  component: ReceivePage,
});

type Verification = "pending" | "verified" | "mismatch";

function ReceivePage() {
  const { setLive, logActivity } = usePhoton();
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const decoderRef = useRef<FountainDecoder | null>(null);
  const manifestRef = useRef<Manifest | null>(null);
  const statsRef = useRef({ frames: 0, useful: 0, duplicates: 0, lastTick: 0, decoded: 0 });

  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [solved, setSolved] = useState(0);
  const [stats, setStats] = useState({ frames: 0, useful: 0, duplicates: 0, fps: 0 });
  const [verification, setVerification] = useState<Verification>("pending");
  const [result, setResult] = useState<{ url: string; name: string; size: number } | null>(null);

  const finish = useCallback(
    async (decoder: FountainDecoder, activeManifest: Manifest) => {
      const bytes = decoder.assemble();
      if (!bytes) return;
      const digest = await sha256Hex(bytes);
      const ok = digest === activeManifest.digest;
      setVerification(ok ? "verified" : "mismatch");
      const blob = new Blob([bytes.slice().buffer as ArrayBuffer], { type: activeManifest.mime });
      setResult({
        url: URL.createObjectURL(blob),
        name: activeManifest.name,
        size: activeManifest.size,
      });
      setScanning(false);
      logActivity({
        direction: "receive",
        name: activeManifest.name,
        size: activeManifest.size,
        frames: statsRef.current.frames,
        status: ok ? "verified" : "mismatch",
        digest,
      });
    },
    [logActivity],
  );

  useEffect(() => {
    if (!scanning) return;
    let cancelled = false;
    let stream: MediaStream | null = null;
    let raf = 0;

    const start = async () => {
      const jsQR = (await import("jsqr")).default;
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 720 } },
        });
      } catch {
        setError("Camera access was denied. Allow camera permission to receive optical frames.");
        setScanning(false);
        return;
      }
      const video = videoRef.current;
      if (!video || cancelled) return;
      video.srcObject = stream;
      await video.play().catch(() => undefined);

      const loop = () => {
        if (cancelled) return;
        const canvas = canvasRef.current;
        const context = canvas?.getContext("2d", { willReadFrequently: true });
        if (canvas && context && video.readyState >= 2 && video.videoWidth) {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          context.drawImage(video, 0, 0, canvas.width, canvas.height);
          const image = context.getImageData(0, 0, canvas.width, canvas.height);
          const code = jsQR(image.data, image.width, image.height, {
            inversionAttempts: "dontInvert",
          });
          if (code?.data) handleFrame(code.data);
        }
        raf = requestAnimationFrame(loop);
      };
      raf = requestAnimationFrame(loop);
    };

    const handleFrame = (text: string) => {
      const frame = parseFrame(text);
      if (!frame) return;
      const s = statsRef.current;
      s.frames += 1;

      const now = performance.now();
      if (now - s.lastTick >= 1000) {
        const fps = (s.decoded * 1000) / (now - s.lastTick);
        s.lastTick = now;
        s.decoded = 0;
        setLive({ linkState: "receiving", receiverFps: fps });
        setStats({ frames: s.frames, useful: s.useful, duplicates: s.duplicates, fps });
      }
      s.decoded += 1;

      if (frame.type === "manifest") {
        if (!manifestRef.current) {
          manifestRef.current = frame.manifest;
          setManifest(frame.manifest);
          decoderRef.current = new FountainDecoder(
            frame.manifest.chunks,
            frame.manifest.chunkSize,
            frame.manifest.size,
          );
        }
        return;
      }

      if (!decoderRef.current) {
        decoderRef.current = new FountainDecoder(frame.chunks, frame.chunkSize, frame.size);
      }
      const decoder = decoderRef.current;
      if (decoder.chunks !== frame.chunks) return;
      if (decoder.hasSeed(frame.seed)) {
        s.duplicates += 1;
        return;
      }
      if (decoder.addSymbol(frame.seed, frame.payload)) s.useful += 1;
      setSolved(decoder.solvedCount);
      setStats({ frames: s.frames, useful: s.useful, duplicates: s.duplicates, fps: stats.fps });

      if (decoder.complete && manifestRef.current) {
        void finish(decoder, manifestRef.current);
      }
    };

    void start();

    return () => {
      cancelled = true;
      cancelAnimationFrame(raf);
      stream?.getTracks().forEach((track) => track.stop());
      setLive({ linkState: "idle", receiverFps: 0 });
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scanning, finish, setLive]);

  const reset = () => {
    decoderRef.current = null;
    manifestRef.current = null;
    statsRef.current = { frames: 0, useful: 0, duplicates: 0, lastTick: 0, decoded: 0 };
    setManifest(null);
    setSolved(0);
    setStats({ frames: 0, useful: 0, duplicates: 0, fps: 0 });
    setVerification("pending");
    setResult(null);
    setError(null);
  };

  const total = manifest?.chunks ?? 0;
  const progress = total ? Math.min(100, (solved / total) * 100) : 0;

  return (
    <div className="mx-auto max-w-6xl">
      <PageHeader title="Receive File" subtitle="Decode optical frames captured by your camera" />

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-3xl border border-border bg-card p-6 shadow-soft">
          <div className="relative aspect-square overflow-hidden rounded-2xl border border-border bg-surface-2">
            <video
              ref={videoRef}
              playsInline
              muted
              className={cn("size-full object-cover", !scanning && "hidden")}
            />
            <canvas ref={canvasRef} className="hidden" />
            {!scanning ? (
              <div className="flex size-full flex-col items-center justify-center gap-3 px-10 text-center text-muted-foreground">
                <CameraOff className="size-8" />
                <p className="text-sm">
                  Camera idle — start capture to lock onto the sender screen
                </p>
              </div>
            ) : (
              <div className="pointer-events-none absolute inset-8 rounded-2xl border-2 border-primary/70" />
            )}
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => {
                if (scanning) {
                  setScanning(false);
                  return;
                }
                reset();
                setScanning(true);
              }}
              className="inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90"
            >
              <Video className="size-4" /> {scanning ? "Stop capture" : "Start capture"}
            </button>
            <button
              type="button"
              onClick={reset}
              className="inline-flex items-center gap-2 rounded-full bg-secondary px-6 py-3 text-sm font-semibold text-secondary-foreground transition-colors hover:bg-muted"
            >
              Reset decoder
            </button>
          </div>
          {error ? <p className="mt-4 text-sm text-destructive">{error}</p> : null}
        </section>

        <section className="rounded-3xl border border-border bg-card p-8 shadow-soft">
          <h2 className="text-xl font-semibold">Reconstruction</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {manifest
              ? `${manifest.name} · ${formatBytes(manifest.size)}`
              : "Waiting for a manifest frame from the sender…"}
          </p>

          <div className="mt-6 flex justify-between text-xs text-muted-foreground">
            <span>
              Chunks recovered <span className="font-mono text-foreground">{solved}</span> / {total}
            </span>
            <span className="font-mono">{progress.toFixed(0)}%</span>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-secondary">
            <div
              className="h-full rounded-full bg-primary transition-[width]"
              style={{ width: `${progress}%` }}
            />
          </div>

          <dl className="mt-7 grid grid-cols-2 gap-4 text-sm">
            <Metric label="Frames seen" value={String(stats.frames)} />
            <Metric label="Useful symbols" value={String(stats.useful)} />
            <Metric label="Duplicates dropped" value={String(stats.duplicates)} />
            <Metric label="Decode rate" value={`${stats.fps.toFixed(1)} FPS`} />
          </dl>

          <div
            className={cn(
              "mt-7 flex items-center gap-3 rounded-2xl border p-4 text-sm",
              verification === "verified" && "border-success/40 bg-success-soft text-success",
              verification === "mismatch" && "border-destructive/40 text-destructive",
              verification === "pending" && "border-border text-muted-foreground",
            )}
          >
            {verification === "verified" ? (
              <ShieldCheck className="size-5" />
            ) : verification === "mismatch" ? (
              <ShieldAlert className="size-5" />
            ) : (
              <ShieldCheck className="size-5" />
            )}
            <span>
              {verification === "verified"
                ? "SHA-256 integrity verified — the file is byte-identical."
                : verification === "mismatch"
                  ? "Digest mismatch — data corrupted, rescan required."
                  : "Integrity check runs automatically once every chunk is recovered."}
            </span>
          </div>

          {result ? (
            <a
              href={result.url}
              download={result.name}
              className="mt-6 inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90"
            >
              <Download className="size-4" /> Save {result.name}
            </a>
          ) : null}
        </section>
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-surface-2 p-4">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="mt-1 flex items-center gap-1 font-mono text-lg">
        {value}
        {parseFloat(value) > 0 ? <Check className="size-3 text-success" /> : null}
      </dd>
    </div>
  );
}
