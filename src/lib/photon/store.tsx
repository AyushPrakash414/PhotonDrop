import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type LinkState = "idle" | "transmitting" | "receiving";

export type ActivityEntry = {
  id: string;
  direction: "send" | "receive";
  name: string;
  size: number;
  at: number;
  frames: number;
  status: "verified" | "mismatch" | "aborted" | "streaming";
  digest?: string;
};

export type Settings = {
  chunkSize: number;
  fps: number;
  redundancy: number;
  errorCorrection: "L" | "M" | "Q" | "H";
};

export const DEFAULT_SETTINGS: Settings = {
  chunkSize: 320,
  fps: 8,
  redundancy: 1.7,
  errorCorrection: "M",
};

type Live = {
  linkState: LinkState;
  senderFps: number;
  receiverFps: number;
  goodput: number;
};

type Store = Live & {
  settings: Settings;
  activity: ActivityEntry[];
  setSettings: (next: Partial<Settings>) => void;
  setLive: (next: Partial<Live>) => void;
  logActivity: (entry: Omit<ActivityEntry, "id" | "at">) => void;
  clearActivity: () => void;
};

const ACTIVITY_KEY = "photondrop.activity";
const SETTINGS_KEY = "photondrop.settings";

const PhotonContext = createContext<Store | null>(null);

export function PhotonProvider({ children }: { children: ReactNode }) {
  const [settings, setSettingsState] = useState<Settings>(DEFAULT_SETTINGS);
  const [activity, setActivity] = useState<ActivityEntry[]>([]);
  const [live, setLiveState] = useState<Live>({
    linkState: "idle",
    senderFps: 0,
    receiverFps: 0,
    goodput: 0,
  });

  useEffect(() => {
    try {
      const storedSettings = window.localStorage.getItem(SETTINGS_KEY);
      if (storedSettings)
        setSettingsState({ ...DEFAULT_SETTINGS, ...(JSON.parse(storedSettings) as Settings) });
      const storedActivity = window.localStorage.getItem(ACTIVITY_KEY);
      if (storedActivity) setActivity(JSON.parse(storedActivity) as ActivityEntry[]);
    } catch {
      /* ignore corrupt local state */
    }
  }, []);

  const setSettings = useCallback((next: Partial<Settings>) => {
    setSettingsState((prev) => {
      const merged = { ...prev, ...next };
      window.localStorage.setItem(SETTINGS_KEY, JSON.stringify(merged));
      return merged;
    });
  }, []);

  const setLive = useCallback((next: Partial<Live>) => {
    setLiveState((prev) => ({ ...prev, ...next }));
  }, []);

  const logActivity = useCallback((entry: Omit<ActivityEntry, "id" | "at">) => {
    setActivity((prev) => {
      const next = [
        { ...entry, id: crypto.randomUUID(), at: Date.now() },
        ...prev.filter((e) => e.status !== "streaming"),
      ].slice(0, 40);
      window.localStorage.setItem(ACTIVITY_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  const clearActivity = useCallback(() => {
    setActivity([]);
    window.localStorage.removeItem(ACTIVITY_KEY);
  }, []);

  const value = useMemo<Store>(
    () => ({ ...live, settings, activity, setSettings, setLive, logActivity, clearActivity }),
    [live, settings, activity, setSettings, setLive, logActivity, clearActivity],
  );

  return <PhotonContext.Provider value={value}>{children}</PhotonContext.Provider>;
}

export function usePhoton() {
  const context = useContext(PhotonContext);
  if (!context) throw new Error("usePhoton must be used inside PhotonProvider");
  return context;
}
