"use client";
import * as React from "react";
import { cn } from "@/lib/utils";

type ScrollAreaProps = React.HTMLAttributes<HTMLDivElement>;

function ScrollArea({ className, children, ...props }: ScrollAreaProps) {
  return (
    <div
      className={cn("w-full overflow-x-auto overflow-y-hidden", className)}
      {...props}
    >
      {children}
    </div>
  );
}

function ScrollBar({
  orientation = "horizontal",
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { orientation?: "horizontal" | "vertical" }) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        "pointer-events-none h-2 w-full opacity-0",
        orientation === "vertical" && "w-2 h-full",
        className
      )}
      {...props}
    />
  );
}

export { ScrollArea, ScrollBar }


