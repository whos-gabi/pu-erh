"use client";
import { useEffect, useRef, useState } from "react";
import {
  addReservation,
  getMockUser,
  Reservation,
  type PuErhUser,
} from "@/lib/mockData";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetFooter,
} from "@/components/ui/sheet";

type SelectedSeat = {
  id: string;
  label: string;
};

export default function ReservePage() {
  const svgContainerRef = useRef<HTMLDivElement | null>(null);
  const [svgMarkup, setSvgMarkup] = useState<string>("");
  const [selected, setSelected] = useState<SelectedSeat | null>(null);
  const [date, setDate] = useState<string>(new Date().toISOString().slice(0, 10));
  const [user, setUser] = useState<PuErhUser | null>(null);

  useEffect(() => {
    setUser(getMockUser());
  }, []);

  useEffect(() => {
    // Load svg
    fetch("/floor4.svg")
      .then((r) => r.text())
      .then((text) => {
        setSvgMarkup(text);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!svgContainerRef.current) return;
    const root = svgContainerRef.current;
    // Clean previous listeners by cloning node
    const clone = root.cloneNode(true) as HTMLDivElement;
    root.replaceWith(clone);
    svgContainerRef.current = clone;

    const svg = clone.querySelector("svg");
    if (!svg) return;
    const groups = Array.from(svg.querySelectorAll("g"));

    groups.forEach((g, idx) => {
      (g as HTMLElement).style.cursor = "pointer";
      g.setAttribute("data-seat-label", g.getAttribute("id") || `G-${idx + 1}`);

      const handleEnter = () => {
        g.setAttribute("data-hover", "1");
        g.querySelectorAll("*").forEach((el) => {
          const elAny = el as HTMLElement;
          const prev = elAny.getAttribute("data-prev-fill");
          if (!prev && (elAny as any).style && (elAny as any).style.fill) {
            elAny.setAttribute("data-prev-fill", (elAny as any).style.fill);
          }
          (elAny as any).style.fill = "rgba(0,0,0,0.2)";
        });
      };
      const handleLeave = () => {
        g.removeAttribute("data-hover");
        g.querySelectorAll("*").forEach((el) => {
          const elAny = el as HTMLElement;
          const prev = elAny.getAttribute("data-prev-fill");
          if (prev !== null) {
            (elAny as any).style.fill = prev;
          } else {
            (elAny as any).style.fill = "";
          }
        });
      };
      const handleClick = () => {
        const label = g.getAttribute("data-seat-label") || g.getAttribute("id") || "Seat";
        setSelected({ id: label, label });
      };
      g.addEventListener("mouseenter", handleEnter);
      g.addEventListener("mouseleave", handleLeave);
      g.addEventListener("click", handleClick);
    });

    return () => {
      groups.forEach((g) => {
        g.replaceWith(g.cloneNode(true));
      });
    };
  }, [svgMarkup]);

  const confirmReservation = () => {
    if (!user || !selected || !date) return;
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
    alert("Reservation confirmed!");
  };

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mt-2 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Make a reservation</h1>
      </div>
      <p className="mt-1 text-sm text-muted-foreground">
        Click a highlighted desk on the floor plan to select it. Hover to preview.
      </p>

      <div className="mt-6 overflow-auto rounded-xl border bg-white p-4">
        <div
          ref={svgContainerRef}
          className="relative"
          dangerouslySetInnerHTML={{ __html: svgMarkup }}
        />
      </div>

      <Sheet open={!!selected} onOpenChange={(o) => !o && setSelected(null)}>
        <SheetContent side="right">
          <SheetHeader>
            <SheetTitle>Reserve seat</SheetTitle>
          </SheetHeader>
          <div className="p-4">
            {selected ? (
              <div className="space-y-4">
                <div className="text-sm">
                  <div className="text-muted-foreground">Selected seat</div>
                  <div className="mt-1 text-lg font-semibold">
                    {selected.label} • Floor 4
                  </div>
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm">Date</label>
                  <input
                    type="date"
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                    className="w-full rounded-md border bg-background px-3 py-2"
                  />
                </div>
              </div>
            ) : null}
          </div>
          <SheetFooter>
            <Button onClick={confirmReservation} disabled={!user}>
              Confirm reservation
            </Button>
            {!user ? (
              <div className="text-xs text-muted-foreground">
                Please login to reserve.
              </div>
            ) : null}
          </SheetFooter>
        </SheetContent>
      </Sheet>
    </div>
  );
}

