import { Link, useRouterState } from "@tanstack/react-router";
import { Activity, Download, Moon, Radio, Send, Settings, ShieldCheck, Sun } from "lucide-react";
import type { ReactNode } from "react";

import { useTheme } from "@/components/photon/theme-provider";
import { usePhoton } from "@/lib/photon/store";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/", label: "Dashboard", icon: Activity },
  { to: "/send", label: "Send File", icon: Send },
  { to: "/receive", label: "Receive File", icon: Download },
  { to: "/activity", label: "Activity", icon: Activity },
  { to: "/settings", label: "Settings", icon: Settings },
] as const;

const LINK_LABEL: Record<string, string> = {
  idle: "Idle",
  transmitting: "Transmitting",
  receiving: "Receiving",
};

function Logo() {
  return (
    <div className="flex items-center gap-3 px-2 py-1">
      <div className="flex size-11 items-center justify-center rounded-2xl bg-primary shadow-glow">
        <span className="block size-4 rounded-full bg-primary-foreground" />
      </div>
      <div className="leading-tight">
        <p className="font-display text-xl font-bold">PhotonDrop</p>
        <p className="text-xs text-muted-foreground">Optical File Transfer</p>
      </div>
    </div>
  );
}

function LinkStatus() {
  const { linkState } = usePhoton();
  return (
    <div className="rounded-2xl border border-primary/40 bg-accent/60 p-4">
      <div className="flex items-start gap-3">
        <Radio className="mt-0.5 size-4 shrink-0 text-primary" />
        <div className="text-sm text-accent-foreground">
          <p className="font-medium">Optical Link</p>
          <p className="flex items-center gap-1.5">
            <span
              className={cn(
                "inline-block size-1.5 rounded-full bg-primary",
                linkState !== "idle" && "animate-pulse",
              )}
            />
            {LINK_LABEL[linkState]}
          </p>
        </div>
      </div>
    </div>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="sticky top-0 hidden h-screen w-[300px] shrink-0 flex-col justify-between border-r border-sidebar-border bg-sidebar p-6 md:flex">
        <div>
          <Logo />
          <nav className="mt-8 space-y-1">
            {NAV.map(({ to, label, icon: Icon }) => {
              const active = to === "/" ? pathname === "/" : pathname.startsWith(to);
              return (
                <Link
                  key={to}
                  to={to}
                  className={cn(
                    "flex items-center gap-3 rounded-2xl px-4 py-3 text-[15px] font-medium transition-colors",
                    active
                      ? "bg-accent text-accent-foreground"
                      : "text-sidebar-foreground/80 hover:bg-secondary",
                  )}
                >
                  <Icon className="size-[18px]" />
                  {label}
                </Link>
              );
            })}
          </nav>
        </div>
        <LinkStatus />
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <MobileNav pathname={pathname} />
        <main className="flex-1 px-5 py-8 md:px-10 md:py-10">{children}</main>
      </div>
    </div>
  );
}

function MobileNav({ pathname }: { pathname: string }) {
  return (
    <div className="sticky top-0 z-20 flex items-center gap-2 overflow-x-auto border-b border-border bg-sidebar/95 px-4 py-3 backdrop-blur md:hidden">
      {NAV.map(({ to, label, icon: Icon }) => {
        const active = to === "/" ? pathname === "/" : pathname.startsWith(to);
        return (
          <Link
            key={to}
            to={to}
            className={cn(
              "flex shrink-0 items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium",
              active ? "bg-accent text-accent-foreground" : "text-muted-foreground",
            )}
          >
            <Icon className="size-4" />
            {label}
          </Link>
        );
      })}
    </div>
  );
}

export function PageHeader({ title, subtitle }: { title: string; subtitle: string }) {
  const { theme, toggle } = useTheme();
  return (
    <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 className="text-4xl font-bold md:text-5xl">{title}</h1>
        <p className="mt-1 text-base text-muted-foreground">{subtitle}</p>
      </div>
      <div className="flex items-center gap-3">
        <span className="flex items-center gap-2 rounded-full bg-success-soft px-4 py-2 text-sm font-semibold text-success">
          <ShieldCheck className="size-4" />
          Zero Network
        </span>
        <button
          type="button"
          onClick={toggle}
          aria-label="Toggle dark mode"
          className="flex size-10 items-center justify-center rounded-full border border-border bg-surface text-foreground transition-colors hover:bg-secondary"
        >
          {theme === "dark" ? <Sun className="size-[18px]" /> : <Moon className="size-[18px]" />}
        </button>
      </div>
    </header>
  );
}
