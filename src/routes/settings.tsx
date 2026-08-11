import { createFileRoute } from "@tanstack/react-router";
import { RotateCcw } from "lucide-react";

import { PageHeader } from "@/components/photon/app-shell";
import { DEFAULT_SETTINGS, usePhoton } from "@/lib/photon/store";
import { useTheme } from "@/components/photon/theme-provider";

export const Route = createFileRoute("/settings")({
  head: () => ({
    meta: [
      { title: "Settings — PhotonDrop Channel Tuning" },
      {
        name: "description",
        content:
          "Tune chunk size, frame rate, redundancy and QR error correction for your optical channel.",
      },
      { property: "og:title", content: "Settings — PhotonDrop Channel Tuning" },
      {
        property: "og:description",
        content:
          "Adjust chunk size, frame rate, redundancy and error correction of the light channel.",
      },
    ],
  }),
  component: SettingsPage,
});

function SettingsPage() {
  const { settings, setSettings } = usePhoton();
  const { theme, toggle } = useTheme();

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title="Settings" subtitle="Tune the optical channel for your screen and camera" />

      <div className="space-y-5">
        <Panel
          title="Chunk size"
          hint={`${settings.chunkSize} bytes per optical symbol. Smaller chunks decode more reliably on low-quality cameras.`}
        >
          <input
            type="range"
            min={64}
            max={800}
            step={32}
            value={settings.chunkSize}
            onChange={(e) => setSettings({ chunkSize: Number(e.target.value) })}
            className="w-full accent-primary"
          />
        </Panel>

        <Panel title="Frame rate" hint={`${settings.fps} frames per second on the sender screen.`}>
          <input
            type="range"
            min={2}
            max={20}
            step={1}
            value={settings.fps}
            onChange={(e) => setSettings({ fps: Number(e.target.value) })}
            className="w-full accent-primary"
          />
        </Panel>

        <Panel
          title="Redundancy"
          hint={`${settings.redundancy.toFixed(1)}× fountain overhead — higher values survive more dropped frames.`}
        >
          <input
            type="range"
            min={1.2}
            max={3}
            step={0.1}
            value={settings.redundancy}
            onChange={(e) => setSettings({ redundancy: Number(e.target.value) })}
            className="w-full accent-primary"
          />
        </Panel>

        <Panel
          title="QR error correction"
          hint="Higher levels tolerate glare and blur but hold less data."
        >
          <div className="flex gap-2">
            {(["L", "M", "Q", "H"] as const).map((level) => (
              <button
                key={level}
                type="button"
                onClick={() => setSettings({ errorCorrection: level })}
                className={
                  settings.errorCorrection === level
                    ? "rounded-full bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground"
                    : "rounded-full bg-secondary px-5 py-2 text-sm font-semibold text-secondary-foreground transition-colors hover:bg-muted"
                }
              >
                {level}
              </button>
            ))}
          </div>
        </Panel>

        <Panel title="Appearance" hint="PhotonDrop ships identical light and dark interfaces.">
          <button
            type="button"
            onClick={toggle}
            className="rounded-full bg-secondary px-5 py-2 text-sm font-semibold text-secondary-foreground transition-colors hover:bg-muted"
          >
            Switch to {theme === "dark" ? "light" : "dark"} mode
          </button>
        </Panel>

        <button
          type="button"
          onClick={() => setSettings(DEFAULT_SETTINGS)}
          className="inline-flex items-center gap-2 rounded-full border border-border px-5 py-2.5 text-sm font-semibold transition-colors hover:bg-secondary"
        >
          <RotateCcw className="size-4" /> Restore defaults
        </button>
      </div>
    </div>
  );
}

function Panel({
  title,
  hint,
  children,
}: {
  title: string;
  hint: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-3xl border border-border bg-card p-6 shadow-soft">
      <h2 className="text-lg font-semibold">{title}</h2>
      <p className="mt-1 mb-4 text-sm text-muted-foreground">{hint}</p>
      {children}
    </section>
  );
}
