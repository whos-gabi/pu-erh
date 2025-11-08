"use client";
import * as React from "react";
import { cn } from "@/lib/utils";

type TabsContextType = {
  value: string;
  setValue: (v: string) => void;
};

const TabsContext = React.createContext<TabsContextType | null>(null);

type TabsProps = {
  defaultValue: string;
  onValueChange?: (v: string) => void;
} & React.HTMLAttributes<HTMLDivElement>;

function Tabs({ defaultValue, className, children, onValueChange, ...props }: TabsProps) {
  const [value, setValue] = React.useState(defaultValue);
  const setAndNotify = (v: string) => {
    setValue(v);
    onValueChange?.(v);
  };
  return (
    <TabsContext.Provider value={{ value, setValue: setAndNotify }}>
      <div className={cn("flex flex-col", className)} {...props}>
        {children}
      </div>
    </TabsContext.Provider>
  );
}

function TabsList({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("inline-flex items-center gap-1", className)} {...props}>
      {children}
    </div>
  );
}

type TabsTriggerProps = {
  value: string;
} & React.ButtonHTMLAttributes<HTMLButtonElement>;

function TabsTrigger({ value, className, children, ...props }: TabsTriggerProps) {
  const ctx = React.useContext(TabsContext);
  if (!ctx) return null;
  const isActive = ctx.value === value;
  return (
    <button
      type="button"
      role="tab"
      aria-selected={isActive}
      onClick={() => ctx.setValue(value)}
      className={cn(
        "whitespace-nowrap rounded-md border px-3 py-1.5 text-sm transition-colors",
        isActive
          ? "bg-black text-white border-black"
          : "bg-white text-black hover:bg-black/5 border-zinc-300",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}

type TabsContentProps = {
  value: string;
} & React.HTMLAttributes<HTMLDivElement>;

function TabsContent({ value, className, children, ...props }: TabsContentProps) {
  const ctx = React.useContext(TabsContext);
  if (!ctx) return null;
  if (ctx.value !== value) return null;
  return (
    <div role="tabpanel" className={cn("mt-2", className)} {...props}>
      {children}
    </div>
  );
}

export { Tabs, TabsList, TabsTrigger, TabsContent }


