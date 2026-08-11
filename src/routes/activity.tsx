import { createFileRoute } from "@tanstack/react-router";
import { ArrowDownLeft, ArrowUpRight, ShieldAlert, ShieldCheck, Trash2 } from "lucide-react";

import { PageHeader } from "@/components/photon/app-shell";
import { formatBytes } from "@/lib/photon/codec";
import { usePhoton } from "@/lib/photon/store";

export const Route = createFileRoute("/activity")({
  head: () => ({
    meta: [
      { title: "Activity — PhotonDrop Transfer History" },
      {
        name: "description",
        content:
          "Review every optical transfer: direction, size, frames emitted or decoded, and integrity result.",
      },
      { property: "og:title", content: "Activity — PhotonDrop Transfer History" },
      {
        property: "og:description",
        content: "A local log of optical transfers with frame counts and verification status.",
      },
    ],
  }),
  component: ActivityPage,
});

function ActivityPage() {
  const { activity, clearActivity } = usePhoton();

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader title="Activity" subtitle="Local history of optical transfers on this device" />

      <div className="rounded-3xl border border-border bg-card shadow-soft">
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <p className="text-sm text-muted-foreground">{activity.length} recorded transfers</p>
          <button
            type="button"
            onClick={clearActivity}
            className="inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-secondary"
          >
            <Trash2 className="size-4" /> Clear
          </button>
        </div>

        {activity.length === 0 ? (
          <p className="px-6 py-16 text-center text-sm text-muted-foreground">
            No transfers yet. Send or receive a file to populate the log.
          </p>
        ) : (
          <ul className="divide-y divide-border">
            {activity.map((entry) => (
              <li key={entry.id} className="flex flex-wrap items-center gap-4 px-6 py-4">
                <span className="flex size-10 items-center justify-center rounded-2xl bg-accent text-accent-foreground">
                  {entry.direction === "send" ? (
                    <ArrowUpRight className="size-4" />
                  ) : (
                    <ArrowDownLeft className="size-4" />
                  )}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium">{entry.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {formatBytes(entry.size)} · {entry.frames} frames ·{" "}
                    {new Date(entry.at).toLocaleString()}
                  </p>
                </div>
                <span
                  className={
                    entry.status === "verified"
                      ? "flex items-center gap-1.5 rounded-full bg-success-soft px-3 py-1.5 text-xs font-semibold text-success"
                      : "flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-xs font-semibold text-muted-foreground"
                  }
                >
                  {entry.status === "verified" ? (
                    <ShieldCheck className="size-3.5" />
                  ) : (
                    <ShieldAlert className="size-3.5" />
                  )}
                  {entry.status}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
