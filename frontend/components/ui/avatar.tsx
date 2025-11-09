"use client"
import * as React from "react"
import { cn } from "@/lib/utils"

export function Avatar({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "relative inline-flex h-10 w-10 items-center justify-center overflow-hidden rounded-full bg-zinc-200 text-zinc-700",
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export function AvatarFallback({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn("select-none text-sm font-medium", className)}
      {...props}
    >
      {children}
    </span>
  )
}


