"use client";

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
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button>Open Sheet</Button>
      </SheetTrigger>
      <SheetContent side="bottom">
        <SheetHeader>
          <SheetTitle>Bottom-to-Top Sheet</SheetTitle>
        </SheetHeader>
        <p>This content slides up from the bottom!</p>
        <SheetClose asChild>
          <Button>Close</Button>
        </SheetClose>
      </SheetContent>
    </Sheet>
  );
}
