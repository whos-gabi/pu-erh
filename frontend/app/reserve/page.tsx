"use client";
import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import {
  addReservation,
  getMockUser,
  Reservation,
  type PuErhUser,
} from "@/lib/mockData";
import { requiresApproval } from "@/lib/roomTypes";
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

  const confirmReservation = () => {
    if (!user || !selected || !date) return;
    // simulate backend call
    // eslint-disable-next-line no-console
    console.log("POST", `${API_BASE_URL}reservations`, {
      user: user.email,
      objectId: selected.id,
      date,
    });
    const reservation: Reservation = {
      id: `r-${Date.now()}`,
      userId: user.id,
      seatId: selected.id,
      seatLabel: selected.label,
      floor: "4",
      date,
      status: "confirmed",
    };
    addReservation(reservation);
    setSelected(null);
  };

  const requestApproval = () => {
    if (!user || !selected || !date) return;
    // simulate backend call
    // eslint-disable-next-line no-console
    console.log("POST", `${API_BASE_URL}approvals`, {
      user: user.email,
      objectId: selected.id,
      date,
    });
    // simulate approval request
    setSelected(null);
  };

  const handleSheetOpenChange = (open: boolean) => {
    if (!open) setSelected(null);
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
            // simulate API call on date change
            // eslint-disable-next-line no-console
            console.log("Simulating API call for date:", v);
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

      <div className="mt-4 w-full">
        <MapComponent
          activeDate={activeDate}
          onSelect={(id) => setSelected(id ? { id, label: id } : null)}
        />
      </div>

      {!isDesktop && (
        <Sheet open={!!selected} onOpenChange={handleSheetOpenChange}>
          <SheetContent
            side="bottom"
            className="transition-all duration-300 rounded-t-2xl h-80 max-h-[80vh] overflow-y-auto z-[60]"
          >
            <SheetHeader>
              <SheetTitle>Reserve seat</SheetTitle>
              <SheetDescription className="sr-only">Reservation details</SheetDescription>
            </SheetHeader>
            <div className="p-2">
              {selected ? (
                <div className="space-y-3">
                  <div className="text-sm">
                    <div className="text-muted-foreground">Selected</div>
                    <div className="mt-1 text-base font-semibold">
                      {selected.label} • Floor 4 • Data {date}
                    </div>
                  </div>
                </div>
              ) : null}
            </div>
            <SheetFooter>
              {needsApproval ? (
                <Button onClick={requestApproval} disabled={!user}>
                  Request approval
                </Button>
              ) : (
                <Button onClick={confirmReservation} disabled={!user}>
                  Make appointment
                </Button>
              )}
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
                      {selected.label} • Floor 4 • Data {date}
                    </div>
                  </div>
                  {needsApproval ? (
                    <Button onClick={requestApproval} disabled={!user} className="w-full">
                      Request approval
                    </Button>
                  ) : (
                    <Button onClick={confirmReservation} disabled={!user} className="w-full">
                      Make appointment
                    </Button>
                  )}
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

