"use client";
import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import {
  addReservation,
  getMockUser,
  Reservation,
  type PuErhUser,
} from "@/lib/mockData";
import { requiresApproval, isSeatId } from "@/lib/roomTypes";
import { Button } from "@/components/ui/button";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetFooter,
  SheetDescription,
} from "@/components/ui/sheet";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ChartContainer } from "@/components/ui/chart";
import { API_BASE_URL } from "@/lib/api";

type SelectedSeat = {
  id: string;
  label: string;
};

const MapComponent = dynamic(() => import("@/components/InteractiveMap"), {
  ssr: false,
  loading: () => <p>Loading map...</p>,
});

export default function ReservePage() {
  const [selected, setSelected] = useState<SelectedSeat | null>(null);
  const [statusMap, setStatusMap] = useState<Record<string, "free" | "occupied" | "teammate">>({});
  const [itemsMap, setItemsMap] = useState<Record<string, number>>({});
  const [itemStats, setItemStats] = useState<any | null>(null);
  const [legendColors, setLegendColors] = useState<{ free: string; occupied: string; teammate: string; opacity: number }>({
    free: "#22c55e",
    occupied: "#ef4444",
    teammate: "#a855f7",
    opacity: 0.35,
  });
  const [mobileSheetHeight, setMobileSheetHeight] = useState<number | null>(null);
  const mobileMinHeight = 120; // px
  const hourIntervals1h = [
    { label: "08:00–09:00", start: "08:00", end: "09:00", value: "08:00-09:00" },
    { label: "09:00–10:00", start: "09:00", end: "10:00", value: "09:00-10:00" },
    { label: "10:00–11:00", start: "10:00", end: "11:00", value: "10:00-11:00" },
    { label: "11:00–12:00", start: "11:00", end: "12:00", value: "11:00-12:00" },
    { label: "12:00–13:00", start: "12:00", end: "13:00", value: "12:00-13:00" },
    { label: "13:00–14:00", start: "13:00", end: "14:00", value: "13:00-14:00" },
    { label: "14:00–15:00", start: "14:00", end: "15:00", value: "14:00-15:00" },
    { label: "15:00–16:00", start: "15:00", end: "16:00", value: "15:00-16:00" },
    { label: "16:00–17:00", start: "16:00", end: "17:00", value: "16:00-17:00" },
    { label: "17:00–18:00", start: "17:00", end: "18:00", value: "17:00-18:00" },
    { label: "18:00–19:00", start: "18:00", end: "19:00", value: "18:00-19:00" },
    { label: "19:00–20:00", start: "19:00", end: "20:00", value: "19:00-20:00" },
  ] as const;
  const [selectedIntervalAppointment, setSelectedIntervalAppointment] = useState<string>(hourIntervals1h[0].value);
  const intervals = [
    { label: "08:00–10:00", start: "08:00", end: "10:00", value: "08:00-10:00" },
    { label: "10:00–12:00", start: "10:00", end: "12:00", value: "10:00-12:00" },
    { label: "12:00–14:00", start: "12:00", end: "14:00", value: "12:00-14:00" },
    { label: "14:00–16:00", start: "14:00", end: "16:00", value: "14:00-16:00" },
    { label: "16:00–18:00", start: "16:00", end: "18:00", value: "16:00-18:00" },
    { label: "18:00–20:00", start: "18:00", end: "20:00", value: "18:00-20:00" },
  ] as const;
  const [selectedInterval, setSelectedInterval] = useState<string>(intervals[0].value);
  const formatLocalYMD = (d: Date) => {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${dd}`;
  };
  const todayLocal = formatLocalYMD(new Date());
  const [date, setDate] = useState<string>(todayLocal);
  const [activeDate, setActiveDate] = useState<string>(todayLocal);
  const [user, setUser] = useState<PuErhUser | null>(null);
  const [isDesktop, setIsDesktop] = useState(false);
  const needsApproval = selected ? requiresApproval(selected.id) : false;

  useEffect(() => {
    setUser(getMockUser());
  }, []);

  useEffect(() => {
    const mq = window.matchMedia("(min-width: 768px)");
    const update = () => setIsDesktop(mq.matches);
    update();
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, []);

  // Read status colors dynamically from CSS variables
  useEffect(() => {
    try {
      const cs = getComputedStyle(document.documentElement);
      const free = (cs.getPropertyValue("--map-status-free") || "").trim();
      const occ = (cs.getPropertyValue("--map-status-occupied") || "").trim();
      const team = (cs.getPropertyValue("--map-status-teammate") || "").trim();
      const opStr = (cs.getPropertyValue("--map-status-opacity") || "").trim();
      const opacity = Number.parseFloat(opStr) || 0.35;
      setLegendColors((prev) => ({
        free: free || prev.free,
        occupied: occ || prev.occupied,
        teammate: team || prev.teammate,
        opacity,
      }));
    } catch {}
  }, []);

  const fetchAvailability = (v: string) => {
    try {
      const uid = localStorage.getItem("pu-erh:user_id") || "";
      const tokensRaw = localStorage.getItem("pu-erh:tokens");
      const access = tokensRaw ? (JSON.parse(tokensRaw).access as string | undefined) : undefined;
      const q = new URLSearchParams({ date: v });
      if (uid) q.set("user_id", uid);
      fetch(`/api/availability/check/?${q.toString()}`, {
        headers: access ? { Authorization: `Bearer ${access}` } : undefined,
      })
        .then(async (r) => {
          const text = await r.text();
          let data: any = null;
          try {
            data = JSON.parse(text);
          } catch {
            // eslint-disable-next-line no-console
            console.log("Availability (raw):", text);
            return null;
          }
          // eslint-disable-next-line no-console
          console.log("Availability:", data);
          const map: Record<string, "free" | "occupied" | "teammate"> = {};
          // items by name
          if (Array.isArray(data?.free_items)) {
            for (const it of data.free_items) {
              if (it?.name) map[it.name] = "free";
            }
          }
          if (Array.isArray(data?.occupied_items)) {
            for (const it of data.occupied_items) {
              if (it?.name) map[it.name] = it.occupied_by_teammate ? "teammate" : "occupied";
            }
          }
          // rooms by code - authoritative lists only
          if (Array.isArray(data?.free_rooms)) {
            for (const rm of data.free_rooms) {
              if (rm?.code) map[rm.code] = "free";
            }
          }
          if (Array.isArray(data?.occupied_rooms)) {
            for (const rm of data.occupied_rooms) {
              if (rm?.code)
                map[rm.code] =
                  rm.occupied_by_teammate ? "teammate" : "occupied";
            }
          }
          // NOTE: do not derive status from is_available; only the authoritative arrays above are used.
          setStatusMap(map);
          return null;
        })
        .catch(() => {
          // eslint-disable-next-line no-console
          console.log("Availability check failed");
        });
    } catch {
      // ignore
    }
  };

  // initial load
  useEffect(() => {
    if (activeDate) fetchAvailability(activeDate);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Ensure items map is loaded (name -> id)
  const ensureItemsMap = async () => {
    if (Object.keys(itemsMap).length > 0) return itemsMap;
    try {
      const tokensRaw = localStorage.getItem("pu-erh:tokens");
      const access = tokensRaw ? (JSON.parse(tokensRaw).access as string | undefined) : undefined;
      const res = await fetch("/api/items/", {
        headers: access ? { Authorization: `Bearer ${access}` } : undefined,
        cache: "no-store",
      });
      const text = await res.text();
      let data: any = null;
      try {
        data = JSON.parse(text);
      } catch {
        // eslint-disable-next-line no-console
        console.log("Items (raw):", text);
        return {};
      }
      const map: Record<string, number> = {};
      if (Array.isArray(data)) {
        for (const it of data) {
          if (it?.name && typeof it?.id === "number") {
            map[String(it.name)] = it.id;
          }
        }
      } else if (Array.isArray(data?.results)) {
        for (const it of data.results) {
          if (it?.name && typeof it?.id === "number") {
            map[String(it.name)] = it.id;
          }
        }
      }
      setItemsMap(map);
      return map;
    } catch {
      // eslint-disable-next-line no-console
      console.log("Items fetch failed");
      return {};
    }
  };

  // On selecting any item, fetch and log occupancy stats (if it maps to an item id)
  useEffect(() => {
    (async () => {
      if (!selected) return;
      const map = await ensureItemsMap();
      const itemId = map[selected.label];
      if (!itemId) return;
      try {
        const tokensRaw = localStorage.getItem("pu-erh:tokens");
        const access = tokensRaw ? (JSON.parse(tokensRaw).access as string | undefined) : undefined;
        const q = new URLSearchParams({ item_id: String(itemId) }).toString();
        const res = await fetch(`/api/item-occupancy-stats/stats/?${q}`, {
          headers: access ? { Authorization: `Bearer ${access}` } : undefined,
          cache: "no-store",
        });
        const text = await res.text();
        try {
          const json = JSON.parse(text);
          // eslint-disable-next-line no-console
          console.log("Item occupancy stats:", json);
          setItemStats(json);
        } catch {
          // eslint-disable-next-line no-console
          console.log("Item occupancy stats (raw):", text);
          setItemStats(null);
        }
      } catch {
        // eslint-disable-next-line no-console
        console.log("Item occupancy stats fetch failed");
        setItemStats(null);
      }
    })();
    // only when selection id changes
  }, [selected?.id]); 

  const statsChartData = (() => {
    if (!itemStats || !Array.isArray(itemStats.weekdays)) return [];
    // Aggregate 08:00-20:00 average popularity per day; label with two-letter abbreviation
    const hourInRange = (h: number) => h >= 8 && h <= 20;
    const dayAbbrev = (w: string) => {
      const map: Record<string, string> = {
        Monday: "Mo",
        Tuesday: "Tu",
        Wednesday: "We",
        Thursday: "Th",
        Friday: "Fr",
        Saturday: "Sa",
        Sunday: "Su",
      };
      return map[w] || (w || "").slice(0, 2);
    };
    return itemStats.weekdays.map((d: any) => {
      const hrs = Array.isArray(d.hours) ? d.hours.filter((h: any) => hourInRange(Number(h.hour))) : [];
      const avg =
        hrs.length > 0
          ? Math.round(
              (hrs.reduce((sum: number, h: any) => sum + Number(h.popularity || 0), 0) / hrs.length) * 10
            ) / 10
          : 0;
      return { day: dayAbbrev(String(d.weekday || "")), value: avg };
    });
  })();

  const StatsBars = ({ data }: { data: Array<{ day: string; value: number }> }) => {
    if (!data || data.length === 0) return null;
    return (
      <ChartContainer className="min-h-[160px] w-full">
        <div className="flex w-full items-end justify-between gap-3 px-2 pb-2">
          {data.map((d) => (
            <div key={d.day} className="flex flex-col items-center justify-end gap-2">
              <div className="h-[120px] w-6 rounded-sm bg-muted relative overflow-hidden">
                <div
                  className="absolute bottom-0 left-0 right-0 rounded-t-sm"
                  style={{
                    height: `${Math.max(0, Math.min(100, d.value))}%`,
                    backgroundColor: "#a855f7",
                  }}
                />
              </div>
              <span className="text-[11px] text-muted-foreground">{d.day}</span>
            </div>
          ))}
        </div>
      </ChartContainer>
    );
  };

  const getSelectedStatus = (): { kind: "free" | "occupied" | "teammate" | "unknown"; label: string; color: string } => {
    if (!selected) return { kind: "unknown", label: "Unknown", color: legendColors.occupied };
    const id = selected.id;
    const tryKeys: string[] = [id];
    // Generate alternates between base and Area ids for rooms/stations/booths
    const addAlternates = (base: string, area: string) => {
      if (!tryKeys.includes(base)) tryKeys.push(base);
      if (!tryKeys.includes(area)) tryKeys.push(area);
    };
    const num = id.match(/(\d+)/)?.[1] ?? "";
    if (id.startsWith("meetingRoomArea")) addAlternates(`meetingRoom${num}`, `meetingRoomArea${num}`);
    if (id.startsWith("meetingRoom") && !id.includes("Area")) addAlternates(`meetingRoom${num}`, `meetingRoomArea${num}`);
    if (id.startsWith("meetingLargeArea")) addAlternates(`meetingLarge${num}`, `meetingLargeArea${num}`);
    if (id.startsWith("meetingLarge") && !id.includes("Area")) addAlternates(`meetingLarge${num}`, `meetingLargeArea${num}`);
    if (id.startsWith("meetingStationArea")) addAlternates(`meetingStation${num}`, `meetingStationArea${num}`);
    if (id.startsWith("meetingStation") && !id.includes("Area")) addAlternates(`meetingStation${num}`, `meetingStationArea${num}`);
    if (id.startsWith("meetingBoothArea")) addAlternates(`meetingBooth${num}`, `meetingBoothArea${num}`);
    if (id.startsWith("meetingBooth") && !id.includes("Area")) addAlternates(`meetingBooth${num}`, `meetingBoothArea${num}`);
    // Look up first matching status in statusMap
    const foundKey = tryKeys.find((k) => statusMap[k as keyof typeof statusMap] !== undefined);
    const st = (foundKey ? statusMap[foundKey as keyof typeof statusMap] : undefined) as
      | "free"
      | "occupied"
      | "teammate"
      | undefined;
    if (st === "free") return { kind: "free", label: "Available", color: legendColors.free };
    if (st === "teammate") return { kind: "teammate", label: "Occupied by teammate", color: legendColors.teammate };
    if (st === "occupied") return { kind: "occupied", label: "Occupied", color: legendColors.occupied };
    return { kind: "unknown", label: "Status unknown", color: legendColors.occupied };
  };

  const hexToRgba = (hex: string, alpha: number) => {
    const m = hex.trim().replace('#','');
    const full = m.length === 3 ? m.split('').map(c => c + c).join('') : m;
    const num = parseInt(full, 16);
    const r = (num >> 16) & 255;
    const g = (num >> 8) & 255;
    const b = num & 255;
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  };

  const confirmReservation = async () => {
    if (!user || !selected || !date) return;
    const isSeat = isSeatId(selected.id);
    const startEnd = (() => {
      if (isSeat) {
        return { start: "08:00", end: "17:00" };
      }
      const int = hourIntervals1h.find((x) => x.value === selectedIntervalAppointment) ?? hourIntervals1h[0];
      return { start: int.start, end: int.end };
    })();
    const payload = {
      user: (() => {
        const stored = localStorage.getItem("pu-erh:user_id");
        const parsed = stored ? parseInt(stored, 10) : NaN;
        return Number.isFinite(parsed) ? parsed : user.id;
      })(),
      item_name: selected.label,
      start_date: toIsoWithTime(date, startEnd.start),
      end_date: toIsoWithTime(date, startEnd.end),
    };
    try {
      const tokensRaw = localStorage.getItem("pu-erh:tokens");
      const access = tokensRaw ? (JSON.parse(tokensRaw).access as string | undefined) : undefined;
      // eslint-disable-next-line no-console
      console.log("POST /api/appointments/ payload:", payload);
      const res = await fetch("/api/appointments/", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          ...(access ? { Authorization: `Bearer ${access}` } : {}),
        },
        body: JSON.stringify(payload),
      });
      const text = await res.text();
      // eslint-disable-next-line no-console
      console.log("Appointment response:", res.status, text);
      setSelected(null);
    } catch {
      // eslint-disable-next-line no-console
      console.log("Appointment create failed");
    }
  };

  const toIsoWithTime = (dYmd: string, hm: string) => {
    const [h, m] = hm.split(":").map((x) => parseInt(x, 10));
    const [yy, mm, dd] = dYmd.split("-").map((x) => parseInt(x, 10));
    // Months are 0-based in JS Date
    const dt = new Date(yy, mm - 1, dd, h, m, 0, 0);
    return dt.toISOString();
  };

  const requestApproval = async () => {
    if (!user || !selected || !date) return;
    const int = intervals.find((x) => x.value === selectedInterval) ?? intervals[0];
    const payload = {
      room_code: selected.label,
      start_date: toIsoWithTime(date, int.start),
      end_date: toIsoWithTime(date, int.end),
      note: "",
    };
    try {
      const tokensRaw = localStorage.getItem("pu-erh:tokens");
      const access = tokensRaw ? (JSON.parse(tokensRaw).access as string | undefined) : undefined;
      // eslint-disable-next-line no-console
      console.log("POST /api/requests/ payload:", payload);
      const res = await fetch("/api/requests/", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          ...(access ? { Authorization: `Bearer ${access}` } : {}),
        },
        body: JSON.stringify(payload),
      });
      const text = await res.text();
      // eslint-disable-next-line no-console
      console.log("Request response:", res.status, text);
      setSelected(null);
    } catch (e) {
      // eslint-disable-next-line no-console
      console.log("Request approval failed");
    }
  };

  const handleSheetOpenChange = (open: boolean) => {
    if (!open) setSelected(null);
    // reset height when closing
    if (!open) setMobileSheetHeight(null);
  };

  // Build date tabs items (today -> +30 days)
  const tabItems = (() => {
    const days = 30;
    const items: { label: string; value: string }[] = [];
    const now = new Date();
    for (let i = 0; i <= days; i++) {
      const d = new Date(now.getFullYear(), now.getMonth(), now.getDate() + i);
      const value = formatLocalYMD(d);
      const label = d.toLocaleDateString(undefined, { day: "numeric", month: "short" });
      items.push({ label, value });
    }
    return items;
  })();

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mt-2 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Make a reservation</h1>
      </div>
      <div className="mt-3">
        <Tabs
          defaultValue={activeDate}
          onValueChange={(v) => {
            setActiveDate(v);
            setDate(v);
            fetchAvailability(v);
          }}
          className="gap-1"
        >
          <ScrollArea>
            <TabsList className="mb-3 w-max">
              {tabItems.map((tab) => (
                <TabsTrigger key={tab.value} value={tab.value}>
                  {tab.label}
                </TabsTrigger>
              ))}
            </TabsList>
            <ScrollBar orientation="horizontal" />
          </ScrollArea>
        </Tabs>
      </div>

      {/* Legend */}
      <div className="mt-2 flex items-center gap-6">
        <div className="flex items-center gap-2">
          <span
            className="inline-block rounded-full"
            style={{
              width: 16,
              height: 16,
              backgroundColor: legendColors.free,
              opacity: legendColors.opacity,
            }}
          />
          <span className="text-sm text-muted-foreground">Free</span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className="inline-block rounded-full"
            style={{
              width: 16,
              height: 16,
              backgroundColor: legendColors.occupied,
              opacity: legendColors.opacity,
            }}
          />
          <span className="text-sm text-muted-foreground">Occupied</span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className="inline-block rounded-full"
            style={{
              width: 16,
              height: 16,
              backgroundColor: legendColors.teammate,
              opacity: legendColors.opacity,
            }}
          />
          <span className="text-sm text-muted-foreground">Occupied by teammate</span>
        </div>
      </div>

      <div className="mt-4 w-full">
        <MapComponent
          activeDate={activeDate}
          statusMap={statusMap}
          isDesktop={isDesktop}
          onSelect={(id) => setSelected(id ? { id, label: id } : null)}
        />
      </div>

      {!isDesktop && (
        <Sheet open={!!selected} onOpenChange={handleSheetOpenChange}>
          <SheetContent
            side="bottom"
            className="transition-all duration-300 rounded-t-2xl max-h-[80vh] overflow-y-auto z-[60]"
            style={
              mobileSheetHeight
                ? {
                    height: mobileSheetHeight,
                  }
                : undefined
            }
          >
            {/* Drag handle */}
            <div className="flex justify-center pt-1">
              <button
                type="button"
                aria-label="Drag handle"
                className="h-1.5 w-12 rounded-full bg-muted-foreground/30 cursor-grab active:cursor-grabbing touch-none"
                onPointerDown={(e) => {
                  try {
                    const startY = e.clientY;
                    const measured =
                      (e.currentTarget.closest("[data-slot='sheet-content']") as HTMLElement | null)?.getBoundingClientRect()
                        ?.height || 0;
                    const startH = mobileSheetHeight ?? measured;
                    const onMove = (ev: PointerEvent) => {
                      const delta = startY - ev.clientY; // drag up -> positive
                      const vhMax = Math.floor(window.innerHeight * 0.8);
                      const next = Math.max(mobileMinHeight, Math.min(vhMax, Math.floor(startH + delta)));
                      setMobileSheetHeight(next);
                    };
                    const onUp = () => {
                      window.removeEventListener("pointermove", onMove);
                      window.removeEventListener("pointerup", onUp);
                    };
                    window.addEventListener("pointermove", onMove, { passive: true });
                    window.addEventListener("pointerup", onUp, { passive: true });
                  } catch {}
                }}
              />
            </div>
            <SheetHeader className="py-0">
              <SheetTitle className="text-2xl md:text-3xl">Reserve Seat</SheetTitle>
              <SheetDescription className="sr-only">Reservation details</SheetDescription>
            </SheetHeader>
            <div className="p-2">
              {selected ? (
                <div className="space-y-3">
                  <div className="text-sm">
                    <div className="text-muted-foreground">Selected</div>
                    <div className="mt-1 text-base font-semibold">
                      {selected.label} • Floor 4 • Date {date}
                    </div>
                  </div>
                  {(() => {
                    const s = getSelectedStatus();
                    return (
                      <Alert
                        className="border-none"
                        style={{
                          backgroundColor: hexToRgba(s.color, 0.12),
                          color: s.color,
                        }}
                      >
                        <AlertTitle>Status</AlertTitle>
                        <AlertDescription style={{ color: hexToRgba(s.color, 0.8) }}>
                          {s.label}
                        </AlertDescription>
                      </Alert>
                    );
                  })()}
                  {statsChartData.length > 0 ? (
                    <div className="space-y-1">
                      <div className="text-base font-semibold">Popularity Stats</div>
                      <StatsBars data={statsChartData} />
                    </div>
                  ) : null}
                  {(() => {
                    const s = getSelectedStatus();
                    if (!needsApproval || s.kind !== "free") return null;
                    return (
                      <div className="space-y-2">
                        <div className="text-xs text-muted-foreground">Select interval</div>
                        <ScrollArea>
                          <Tabs defaultValue={selectedInterval} onValueChange={(v) => setSelectedInterval(v)} className="gap-1">
                            <TabsList className="w-max mb-1">
                              {intervals.map((it) => (
                                <TabsTrigger key={it.value} value={it.value}>
                                  {it.label}
                                </TabsTrigger>
                              ))}
                            </TabsList>
                          </Tabs>
                          <ScrollBar orientation="horizontal" />
                        </ScrollArea>
                      </div>
                    );
                  })()}
                  {(() => {
                    const s = getSelectedStatus();
                    const isSeat = selected && isSeatId(selected.id);
                    if (needsApproval || s.kind !== "free" || !selected || isSeat) return null;
                    return (
                      <div className="space-y-2">
                        <div className="text-xs text-muted-foreground">Select hour interval</div>
                        <ScrollArea>
                          <Tabs defaultValue={selectedIntervalAppointment} onValueChange={(v) => setSelectedIntervalAppointment(v)} className="gap-1">
                            <TabsList className="w-max mb-1">
                              {hourIntervals1h.map((it) => (
                                <TabsTrigger key={it.value} value={it.value}>
                                  {it.label}
                                </TabsTrigger>
                              ))}
                            </TabsList>
                          </Tabs>
                          <ScrollBar orientation="horizontal" />
                        </ScrollArea>
                      </div>
                    );
                  })()}
                </div>
              ) : null}
            </div>
            <SheetFooter>
              {(() => {
                const s = getSelectedStatus();
                return needsApproval ? (
                  <Button onClick={requestApproval} disabled={!user || s.kind !== "free"}>
                  Request approval
                </Button>
                ) : (
                <Button onClick={confirmReservation} disabled={!user || s.kind !== "free"}>
                  Make appointment
                </Button>
                );
              })()}
              {!user ? (
                <div className="text-xs text-muted-foreground">
                  Please login to reserve.
                </div>
              ) : null}
            </SheetFooter>
          </SheetContent>
        </Sheet>
      )}

      {isDesktop && (
        <Sheet open={!!selected} onOpenChange={handleSheetOpenChange}>
          <SheetContent
            side="left"
            className="transition-all duration-300 h-full w-80 p-5 z-[60]"
          >
            <SheetHeader>
              <SheetTitle>Reserve seat</SheetTitle>
              <SheetDescription className="sr-only">Reservation details</SheetDescription>
            </SheetHeader>
            <div className="mt-2">
              {selected ? (
                <div className="space-y-4">
                  <div className="text-sm">
                    <div className="text-muted-foreground">Selected</div>
                    <div className="mt-1 text-lg font-semibold">
                      {selected.label} • Floor 4 • Date {date}
                    </div>
                  </div>
                  {(() => {
                    const s = getSelectedStatus();
                    return (
                      <Alert
                        className="border-none"
                        style={{
                          backgroundColor: hexToRgba(s.color, 0.12),
                          color: s.color,
                        }}
                      >
                        <AlertTitle>Status</AlertTitle>
                        <AlertDescription style={{ color: hexToRgba(s.color, 0.8) }}>
                          {s.label}
                        </AlertDescription>
                      </Alert>
                    );
                  })()}
                  {statsChartData.length > 0 ? (
                    <div className="space-y-1">
                      <div className="text-sm font-semibold">Popularity Stats</div>
                      <StatsBars data={statsChartData} />
                    </div>
                  ) : null}
                  {(() => {
                    const s = getSelectedStatus();
                    if (needsApproval && s.kind === "free") {
                      return (
                        <div className="space-y-2">
                          <div className="text-xs text-muted-foreground">Select interval</div>
                          <ScrollArea>
                            <Tabs defaultValue={selectedInterval} onValueChange={(v) => setSelectedInterval(v)} className="gap-1">
                              <TabsList className="w-max mb-1">
                                {intervals.map((it) => (
                                  <TabsTrigger key={it.value} value={it.value}>
                                    {it.label}
                                  </TabsTrigger>
                                ))}
                              </TabsList>
                            </Tabs>
                            <ScrollBar orientation="horizontal" />
                          </ScrollArea>
                        </div>
                      );
                    }
                    const isSeat = selected && isSeatId(selected.id);
                    if (!needsApproval && s.kind === "free" && selected && !isSeat) {
                      return (
                        <div className="space-y-2">
                          <div className="text-xs text-muted-foreground">Select hour interval</div>
                          <ScrollArea>
                            <Tabs defaultValue={selectedIntervalAppointment} onValueChange={(v) => setSelectedIntervalAppointment(v)} className="gap-1">
                              <TabsList className="w-max mb-1">
                                {hourIntervals1h.map((it) => (
                                  <TabsTrigger key={it.value} value={it.value}>
                                    {it.label}
                                  </TabsTrigger>
                                ))}
                              </TabsList>
                            </Tabs>
                            <ScrollBar orientation="horizontal" />
                          </ScrollArea>
                        </div>
                      );
                    }
                    return null;
                  })()}
                  {(() => {
                    const s = getSelectedStatus();
                    return needsApproval ? (
                      <Button onClick={requestApproval} disabled={!user || s.kind !== "free"} className="w-full">
                        Request approval
                      </Button>
                    ) : (
                      <Button onClick={confirmReservation} disabled={!user || s.kind !== "free"} className="w-full">
                        Make appointment
                      </Button>
                    );
                  })()}
                  {!user ? (
                    <div className="text-xs text-muted-foreground">
                      Please login to reserve.
                    </div>
                  ) : null}
                </div>
              ) : (
                <div className="text-sm text-muted-foreground">Select an element on the map.</div>
              )}
            </div>
          </SheetContent>
        </Sheet>
      )}
    </div>
  );
}

