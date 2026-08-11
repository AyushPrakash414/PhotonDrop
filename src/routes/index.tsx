import { Link, createFileRoute } from "@tanstack/react-router";
import { Download, Radio, ShieldCheck, Send, Zap } from "lucide-react";

import { PageHeader } from "@/components/photon/app-shell";
import { StatCard } from "@/components/photon/stat-card";
import { usePhoton } from "@/lib/photon/store";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "PhotonDrop — Offline Optical File Transfer" },
      {
        name: "description",
        content:
          "Send files screen-to-camera with visible light. Fountain-coded optical frames, no Wi-Fi, Bluetooth, cables or cloud.",
      },
      { property: "og:title", content: "PhotonDrop — Offline Optical File Transfer" },
      {
        property: "og:description",
        content:
          "Transfer arbitrary files through visible light using loss-tolerant optical frames.",
      },
    ],
  }),
  component: Dashboard,
});

const PIPELINE = [
  "File",
  "Split into chunks",
  "Add loss recovery",
  "Visual frames",
  "Sender screen",
  "Visible light",
  "Receiver camera",
  "Decode frames",
  "Recover missing data",
  "Reconstruct file",
  "Verify integrity",
];

function Dashboard() {
  const { linkState, senderFps, receiverFps, goodput } = usePhoton();

  return (
    <div className="mx-auto max-w-6xl">
      <PageHeader title="Dashboard" subtitle="Overview of screen-to-camera optical transport" />

      <section className="hero-surface relative overflow-hidden rounded-3xl border border-border p-8 md:p-10">
        <div className="relative z-10 max-w-2xl">
          <span className="eyebrow inline-block rounded-full border border-primary/40 px-4 py-2 text-primary">
            Zero-network optical transport
          </span>
          <h2 className="mt-6 text-3xl font-bold md:text-4xl">Screen-to-Camera Optical Channel</h2>
          <p className="mt-3 text-base text-muted-foreground">
            Transmit arbitrary binary files through visible light using LT fountain coding. No
            Wi-Fi. No Bluetooth. No Internet.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Link
              to="/send"
              className="inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90"
            >
              <Send className="size-4" /> Send File
            </Link>
            <Link
              to="/receive"
              className="inline-flex items-center gap-2 rounded-full bg-secondary px-6 py-3 text-sm font-semibold text-secondary-foreground transition-colors hover:bg-muted"
            >
              <Download className="size-4" /> Receive File
            </Link>
          </div>
        </div>
        <div className="pointer-events-none absolute top-1/2 right-10 hidden -translate-y-1/2 lg:block">
          <div className="photon-pulse flex size-32 items-center justify-center rounded-full border-2 border-primary bg-card">
            <Radio className="size-10 text-primary" />
          </div>
        </div>
      </section>

      <section className="mt-6 grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Active Goodput"
          value={goodput.toFixed(1)}
          unit="KB/s"
          icon={Zap}
          tone="primary"
        />
        <StatCard label="Sender FPS" value={senderFps.toFixed(1)} unit="FPS" icon={Send} />
        <StatCard
          label="Receiver Decode"
          value={receiverFps.toFixed(1)}
          unit="FPS"
          icon={Download}
        />
        <StatCard
          label="Optical Link"
          value={
            linkState === "idle" ? "Idle" : linkState === "receiving" ? "Receiving" : "Sending"
          }
          icon={ShieldCheck}
          tone="success"
        />
      </section>

      <section className="mt-6 rounded-3xl border border-border bg-card p-8 shadow-soft">
        <h3 className="text-xl font-semibold">Transport pipeline</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Every transfer walks the same eleven stages, end to end, entirely on-device.
        </p>
        <ol className="mt-6 flex flex-wrap gap-2">
          {PIPELINE.map((step, index) => (
            <li
              key={step}
              className="flex items-center gap-2 rounded-full border border-border bg-surface-2 px-4 py-2 text-sm"
            >
              <span className="font-mono text-xs text-primary">
                {String(index + 1).padStart(2, "0")}
              </span>
              {step}
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
