"use client";
import React, { useEffect, useRef, useState } from "react";
import styles from "@/styles/InteractiveMap.module.css";
import { Button } from "@/components/ui/button";

type InteractiveMapProps = {
  onSelect?: (id: string | null) => void;
  activeDate?: string | null;
};

export default function InteractiveMap({ onSelect, activeDate }: InteractiveMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const viewportRef = useRef<HTMLDivElement | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const prevModifiedRef = useRef<
    Array<{ el: Element; prevStyleFill: string | null }>
  >(
    []
  );
  const [scale, setScale] = useState(1);
  const [translate, setTranslate] = useState<{ x: number; y: number }>({
    x: 0,
    y: 0,
  });
  const isPanningRef = useRef(false);
  const panStartRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const translateStartRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  useEffect(() => {
    let cancelled = false;
    fetch("/floorFARA.svg")
      .then((r) => r.text())
      .then((text) => {
        if (cancelled) return;
        // Ensure the root svg has a stable id for querying
        const withId = text.includes('id="floor-plan-svg-root"')
          ? text
          : text.replace("<svg", '<svg id="floor-plan-svg-root"');
        if (containerRef.current) {
          containerRef.current.innerHTML = withId;
          // Force responsive sizing on the inserted SVG to prevent overflow
          const svg = containerRef.current.querySelector(
            "#floor-plan-svg-root"
          ) as SVGElement | null;
          if (svg) {
            svg.style.width = "100%";
            svg.style.height = "auto";
            svg.style.display = "block";
            svg.style.maxWidth = "100%";
            // Remove hard-coded width/height attributes if present
            svg.removeAttribute("width");
            svg.removeAttribute("height");
            // Note: preserve viewBox for proper scaling
          }
          setLoaded(true);
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  // React to active date changes (simulate API/state update)
  useEffect(() => {
    if (!loaded) return;
    if (activeDate) {
      // Simulate API-driven map updates for a given date
      // You can hook any per-date availability visuals here
      // eslint-disable-next-line no-console
      console.log("Map updating for date:", activeDate);
    }
  }, [activeDate, loaded]);

  useEffect(() => {
    if (!loaded || !containerRef.current) return;
    const svgRoot = containerRef.current.querySelector(
      "#floor-plan-svg-root"
    ) as SVGElement | null;
    if (!svgRoot) return;

    // Mark only seats, meeting stations, and meeting booths as clickable (not their containers)
    const seats = svgRoot.querySelectorAll(
      "g[id^='scaun'], g[id^='meetingStation'], g[id^='meetingBooth']"
    );
    seats.forEach((g) => {
      g.classList.add(styles.clickable);
    });

    // Setup Areas logic
    const areasRoot = svgRoot.querySelector("#Areas") as SVGGElement | null;
    if (areasRoot) {
      const roomAreas = areasRoot.querySelectorAll(
        "[id^='meetingRoomArea']"
      ) as NodeListOf<SVGGraphicsElement>;
      const stationAreas = areasRoot.querySelectorAll(
        "[id^='meetingStationArea']"
      ) as NodeListOf<SVGGraphicsElement>;
      const boothAreas = areasRoot.querySelectorAll(
        "[id^='meetingBoothArea']"
      ) as NodeListOf<SVGGraphicsElement>;
      const massageAreas = areasRoot.querySelectorAll(
        "[id^='massageArea']"
      ) as NodeListOf<SVGGraphicsElement>;
      const beerPointAreas = areasRoot.querySelectorAll(
        "[id^='beerPointArea']"
      ) as NodeListOf<SVGGraphicsElement>;
      const meetingLargeAreas = areasRoot.querySelectorAll(
        "#meetingLargeArea1, #meetingLargeArea2, [id^='meetingLargeArea']"
      ) as NodeListOf<SVGGraphicsElement>;

      const getNum = (id: string) => {
        const m = id.match(/(\d+)/);
        return m ? m[1] : "";
      };
      const findRoomGroups = (num: string) => {
        // Try exact id and any variant starting with meetingRoom<num>
        const exact = svgRoot.querySelectorAll(
          `g#meetingRoom${num}, g[id^='meetingRoom${num}']`
        ) as NodeListOf<SVGGElement>;
        return Array.from(exact);
      };

      roomAreas.forEach((el) => {
        el.classList.add(styles.clickable);
        const num = getNum(el.id);
        const onEnter = () => {
          const groups = findRoomGroups(num);
          groups.forEach((g) => {
            g.classList.add(styles.selected);
          });
        };
        const onLeave = () => {
          const groups = findRoomGroups(num);
          groups.forEach((g) => {
            if (!g.hasAttribute("data-click-selected")) {
              g.classList.remove(styles.selected);
            }
          });
        };
        el.addEventListener("mouseenter", onEnter);
        el.addEventListener("mouseleave", onLeave);
      });

      [...stationAreas, ...boothAreas].forEach((el) => {
        el.classList.add(styles.clickable);
      });

      // Simple hover tint helper for single area elements (tint the element itself)
      const hoverPrev = new WeakMap<
        Element,
        { fill: string | null; fillOpacity: string | null }
      >();
      const addSimpleAreaHover = (el: SVGGraphicsElement) => {
        el.classList.add(styles.clickable);
        const onEnter = () => {
          const any = el as unknown as HTMLElement;
          hoverPrev.set(el, {
            fill: any.style.fill || null,
            fillOpacity: (any.style as any).fillOpacity || null,
          });
          any.style.setProperty("fill", "#0056b3", "important");
          any.style.setProperty("fill-opacity", "0.3", "important");
        };
        const onLeave = () => {
          const any = el as unknown as HTMLElement;
          const prev = hoverPrev.get(el);
          if (prev) {
            if (prev.fill !== null) any.style.setProperty("fill", prev.fill);
            else any.style.removeProperty("fill");
            if (prev.fillOpacity !== null)
              any.style.setProperty("fill-opacity", prev.fillOpacity);
            else any.style.removeProperty("fill-opacity");
          } else {
            any.style.removeProperty("fill");
            any.style.removeProperty("fill-opacity");
          }
        };
        el.addEventListener("mouseenter", onEnter);
        el.addEventListener("mouseleave", onLeave);
      };
      // Disable hover for massage/beerPoint areas (was glitchy); click handles selection tint instead
      meetingLargeAreas.forEach((el) => {
        // Hover over meetingLargeAreaN highlights corresponding meetingLargeN group(s)
        el.classList.add(styles.clickable);
        const id = el.id;
        const base = id.replace("Area", ""); // meetingLargeN
        const onEnter = () => {
          const groups = svgRoot.querySelectorAll(
            `g#${CSS.escape(base)}, g[id^='${CSS.escape(base)}']`
          );
          groups.forEach((g) => (g as SVGGElement).classList.add(styles.selected));
        };
        const onLeave = () => {
          const groups = svgRoot.querySelectorAll(
            `g#${CSS.escape(base)}, g[id^='${CSS.escape(base)}']`
          );
          groups.forEach((g) => {
            if (!(g as SVGGElement).hasAttribute("data-click-selected")) {
              (g as SVGGElement).classList.remove(styles.selected);
            }
          });
        };
        el.addEventListener("mouseenter", onEnter);
        el.addEventListener("mouseleave", onLeave);
      });
    }

    const handleClick = (e: Event) => {
      const target = e.target as Element | null;
      if (!target) return;
      // Prefer selecting target types
      const areaEl =
        (target.closest(
          "[id^='meetingRoomArea'], [id^='meetingStationArea'], [id^='meetingBoothArea'], [id^='massageArea'], [id^='beerPointArea'], [id^='meetingLargeArea']"
        ) as SVGElement | null) || null;

      // If clicked an area element, handle accordingly
      if (areaEl) {
        // Clear previous selection and inline fills
        svgRoot
          .querySelectorAll(`.${styles.selected}, .${styles.areaSelected}`)
          .forEach((elSel) => elSel.classList.remove(styles.selected, styles.areaSelected));
        prevModifiedRef.current.forEach(({ el, prevStyleFill }) => {
          const elAny = el as HTMLElement;
          if (prevStyleFill !== null) {
            elAny.style.setProperty("fill", prevStyleFill);
          } else {
            elAny.style.removeProperty("fill");
          }
        });
        prevModifiedRef.current = [];

        const id = areaEl.id;
        if (id.startsWith("meetingRoomArea")) {
          const num = id.match(/(\d+)/)?.[1] ?? "";
          const groups = svgRoot.querySelectorAll(
            `g#meetingRoom${num}, g[id^='meetingRoom${num}']`
          );
          groups.forEach((g) => {
            g.classList.add(styles.selected);
            g.setAttribute("data-click-selected", "1");
          });
          setSelectedId(`meetingRoom${num}`);
          onSelect?.(`meetingRoom${num}`);
          return;
         } else if (id.startsWith("meetingStationArea")) {
          // Tint the area element itself
          const elAny = areaEl as unknown as HTMLElement;
          const prevStyleFill = elAny.style.fill || null;
          prevModifiedRef.current.push({
            el: areaEl,
            prevStyleFill,
          });
           // Use CSS class for consistent tinting
           elAny.classList.add(styles.areaSelected);
          setSelectedId(id);
          onSelect?.(id);
          return;
        } else if (id.startsWith("meetingBoothArea")) {
          // Tint the area element (rect) itself
          const elAny = areaEl as unknown as HTMLElement;
          const prevStyleFill = elAny.style.fill || null;
          prevModifiedRef.current.push({
            el: areaEl,
            prevStyleFill,
          });
           elAny.classList.add(styles.areaSelected);
          setSelectedId(id);
          onSelect?.(id);
          return;
        } else if (id.startsWith("massageArea")) {
          const elAny = areaEl as unknown as HTMLElement;
          elAny.classList.add(styles.areaSelected);
          setSelectedId(id);
          onSelect?.(id);
          return;
        } else if (id.startsWith("beerPointArea")) {
          const elAny = areaEl as unknown as HTMLElement;
          elAny.classList.add(styles.areaSelected);
          setSelectedId(id);
          onSelect?.(id);
          return;
        } else if (id === "meetingLargeArea1" || id === "meetingLargeArea2" || id.startsWith("meetingLargeArea")) {
          const base = id.replace("Area", ""); // meetingLargeN
          const groups = svgRoot.querySelectorAll(
            `g#${CSS.escape(base)}, g[id^='${CSS.escape(base)}']`
          );
          groups.forEach((g) => {
            (g as SVGGElement).classList.add(styles.selected);
            (g as SVGGElement).setAttribute("data-click-selected", "1");
          });
          setSelectedId(base);
          onSelect?.(base);
          return;
        }
      }

      // Prefer selecting only allowed groups; no generic fallback to avoid picking containers like 'Areas' or 'pereti'
      let clickedGroup = target.closest(
        "g[id^='scaun'], g[id^='meetingStation'], g[id^='meetingBooth']"
      ) as SVGGElement | null;
      // Deselect if clicking outside any group
      if (!clickedGroup) {
        svgRoot
          .querySelectorAll(`.${styles.selected}, .${styles.areaSelected}`)
          .forEach((elSel) => elSel.classList.remove(styles.selected, styles.areaSelected));
        // revert modified fills
        prevModifiedRef.current.forEach(({ el, prevStyleFill }) => {
          const elAny = el as HTMLElement;
          if (prevStyleFill !== null) {
            elAny.style.setProperty("fill", prevStyleFill);
          } else {
            elAny.style.removeProperty("fill");
          }
        });
        prevModifiedRef.current = [];
        setSelectedId(null);
        onSelect?.(null);
        return;
      }
      const id = clickedGroup.id;
      if (!id) return;
      // Explicitly ignore selecting 'Areas' or 'pereti' containers
      if (id === "Areas" || id === "pereti" || id.startsWith("pereti")) {
        return;
      }

      // Clear previous selection
      svgRoot
        .querySelectorAll(`.${styles.selected}, .${styles.areaSelected}`)
        .forEach((elSel) => elSel.classList.remove(styles.selected, styles.areaSelected));
      // revert modified fills
      prevModifiedRef.current.forEach(({ el, prevStyleFill }) => {
        const elAny = el as HTMLElement;
        if (prevStyleFill !== null) {
          elAny.style.setProperty("fill", prevStyleFill);
        } else {
          elAny.style.removeProperty("fill");
        }
      });
      prevModifiedRef.current = [];

      if (id.startsWith("scaun")) {
        // Seats: rely only on the selected class to color the full subtree
        clickedGroup.classList.add(styles.selected);
      } else if (id.startsWith("meetingStation") || id.startsWith("meetingBooth")) {
        // Meeting stations: specifically tint the second direct path child
        const secondPath = clickedGroup.querySelector(":scope > path:nth-of-type(2)") as SVGPathElement | null;
        if (secondPath) {
        const pathEl = secondPath as unknown as HTMLElement;
        const prevStyleFill = pathEl.style.fill || null;
        prevModifiedRef.current.push({
          el: secondPath,
          prevStyleFill,
        });
        pathEl.style.setProperty("fill", "#007bff", "important");
        }
      }

      setSelectedId(id);
      onSelect?.(id);
    };

    svgRoot.addEventListener("click", handleClick);
    return () => {
      svgRoot.removeEventListener("click", handleClick);
    };
  }, [loaded, onSelect]);

  // Zoom/pan controls
  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;
    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      const zoomIntensity = 0.0015;
      const delta = -e.deltaY;
      const newScale = Math.min(4, Math.max(0.3, scale * (1 + delta * zoomIntensity)));

      // Zoom towards cursor position
      const rect = viewport.getBoundingClientRect();
      const cx = e.clientX - rect.left;
      const cy = e.clientY - rect.top;
      const scaleRatio = newScale / scale;
      const newTranslateX = cx - (cx - translate.x) * scaleRatio;
      const newTranslateY = cy - (cy - translate.y) * scaleRatio;

      setScale(newScale);
      setTranslate({ x: newTranslateX, y: newTranslateY });
    };
    const onPointerDown = (e: PointerEvent) => {
      isPanningRef.current = true;
      panStartRef.current = { x: e.clientX, y: e.clientY };
      translateStartRef.current = { ...translate };
      (e.target as Element).setPointerCapture?.(e.pointerId);
    };
    const onPointerMove = (e: PointerEvent) => {
      if (!isPanningRef.current) return;
      const dx = e.clientX - panStartRef.current.x;
      const dy = e.clientY - panStartRef.current.y;
      setTranslate({
        x: translateStartRef.current.x + dx,
        y: translateStartRef.current.y + dy,
      });
    };
    const onPointerUp = (e: PointerEvent) => {
      isPanningRef.current = false;
      (e.target as Element).releasePointerCapture?.(e.pointerId);
    };
    viewport.addEventListener("wheel", handleWheel, { passive: false });
    viewport.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
    return () => {
      viewport.removeEventListener("wheel", handleWheel);
      viewport.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
    };
  }, [scale, translate]);

  const zoomIn = () => setScale((s) => Math.min(4, s * 1.2));
  const zoomOut = () => setScale((s) => Math.max(0.3, s / 1.2));
  const resetView = () => {
    setScale(1);
    setTranslate({ x: 0, y: 0 });
  };

  return (
    <div>
      <p className="text-sm text-muted-foreground">
        Selected Seat: <strong>{selectedId || "None"}</strong>
      </p>
      <div
        ref={viewportRef}
        className="relative w-full overflow-hidden rounded-xl border"
        style={{
          height: "70vh",
          marginLeft: 0,
          marginRight: 0,
          touchAction: "none",
          background: "white",
        }}
      >
        <div
          ref={containerRef}
          className="will-change-transform select-none"
          style={{
            transform: `translate(${translate.x}px, ${translate.y}px) scale(${scale})`,
            transformOrigin: "0 0",
          }}
        />
        <div className="absolute right-3 top-3 flex flex-col gap-2">
          <Button size="icon" variant="secondary" onClick={zoomIn}>
            +
          </Button>
          <Button size="icon" variant="secondary" onClick={zoomOut}>
            −
          </Button>
          <Button size="icon" variant="secondary" onClick={resetView}>
            ⤾
          </Button>
        </div>
      </div>
    </div>
  );
}


