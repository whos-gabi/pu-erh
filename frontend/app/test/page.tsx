"use client";

import { useState } from "react";
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

  return (
    <>
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
        {/* Left side for medium+ screens */}
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
    </>
  );
}
