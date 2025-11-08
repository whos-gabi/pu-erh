"use client";

import { useState, useRef, useEffect } from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  SheetClose,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";

export default function BottomSheetExample() {
  const [expanded, setExpanded] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const img = new Image();
    img.src = "/floorFARA.svg";
    img.onload = () => {
      const zoom = 5; // how much you want to zoom in
      const sx = 0; // top-left x
      const sy = 0; // top-left y
      const sw = img.width / zoom; // crop width
      const sh = img.height; // full height

      // Set canvas to **match the cropped portion** size
      canvas.width = sw;
      canvas.height = sh;

      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw top-left zoomed portion
      ctx.drawImage(img, sx, sy, sw, sh, 0, 0, canvas.width, canvas.height);
    };
  }, []);

  return (
    <>
      {/* Sheets */}
      <Sheet>
        <SheetTrigger asChild>
          <Button className="md:hidden">Open Sheet</Button>
        </SheetTrigger>
        <SheetContent
          side="bottom"
          className="transition-all duration-300 rounded-t-2xl h-64 md:hidden"
        >
          <SheetHeader>
            <SheetTitle>Bottom-to-Top Sheet</SheetTitle>
          </SheetHeader>
          <p>This content slides up from the bottom!</p>
          <Button onClick={() => setExpanded(!expanded)}>
            {expanded ? "Shrink" : "Expand"}
          </Button>
          <SheetClose asChild>
            <Button>Close</Button>
          </SheetClose>
        </SheetContent>
      </Sheet>

      <Sheet>
        <SheetTrigger asChild>
          <Button className="md:block hidden">Open Sheet</Button>
        </SheetTrigger>
        <SheetContent
          side="left"
          className={`transition-all duration-300 h-full w-80 p-5 hidden md:block ${
            expanded ? "w-96" : "w-80"
          }`}
        >
          <SheetHeader>
            <SheetTitle>Left-side Sheet</SheetTitle>
          </SheetHeader>
          <p>This content slides from the left!</p>
          <SheetClose asChild>
            <Button>Close</Button>
          </SheetClose>
        </SheetContent>
      </Sheet>

      {/* Canvas for top-left zoom */}
      <div className="flex justify-center items-start px-4 md:px-0 mt-5">
        <canvas
          ref={canvasRef}
          className="border"
          style={{ width: "100%", height: "auto" }} // responsive
        />
      </div>
    </>
  );
}
