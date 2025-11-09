// Minimal chart helpers adapted for shadcn with Recharts v2
import * as React from "react"
import { cn } from "@/lib/utils"

export function ChartContainer({
  className,
  children,
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "relative flex w-full items-center justify-center rounded-lg border p-3",
        className
      )}
    >
      {children}
    </div>
  )
}

export function ChartTooltip({
  content,
  ...props
}: {
  content: React.ReactElement
}) {
  // Proxy to Recharts <Tooltip />, but we import lazily on usage side
  // This component exists to mirror shadcn API.
  return React.cloneElement(content, props as any)
}

export function ChartTooltipContent({
  label,
  payload,
}: {
  label?: string
  payload?: Array<{ value: number; payload?: any; name?: string; color?: string }>
}) {
  if (!payload || payload.length === 0) return null
  return (
    <div className="rounded-md border bg-background p-2 text-xs shadow">
      {label ? <div className="mb-1 font-medium">{label}</div> : null}
      <div className="space-y-0.5">
        {payload.map((p, i) => (
          <div key={i} className="flex items-center justify-between gap-3">
            <span className="text-muted-foreground">{p.name ?? "value"}</span>
            <span className="font-medium">{p.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export function ChartLegend({ content }: { content?: React.ReactElement }) {
  return content ?? null
}

export function ChartLegendContent({
  items,
}: {
  items?: Array<{ name: string; color?: string }>
}) {
  if (!items || items.length === 0) return null
  return (
    <div className="flex flex-wrap items-center gap-3 text-xs">
      {items.map((it, i) => (
        <div key={i} className="flex items-center gap-1.5">
          <span
            className="inline-block size-2 rounded-full"
            style={{ backgroundColor: it.color || "var(--chart-1)" }}
          />
          <span className="text-muted-foreground">{it.name}</span>
        </div>
      ))}
    </div>
  )
}


