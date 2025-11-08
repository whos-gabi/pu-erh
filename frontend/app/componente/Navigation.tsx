"use client";
import Link from "next/link";
import React, { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { signOut } from "next-auth/react";

export default function Navigation() {
  const [isAuthed, setIsAuthed] = useState(false);
  const [role, setRole] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  useEffect(() => {
    try {
      const u = localStorage.getItem("pu-erh:user");
      setIsAuthed(!!u);
      if (u) {
        const parsed = JSON.parse(u) as { role?: string };
        setRole(parsed.role ?? null);
      } else {
        setRole(null);
      }
    } catch {}
    setOpen(false);
  }, [pathname]);

  const handleLogout = () => {
    try {
      signOut({ callbackUrl: "/" });
      localStorage.removeItem("pu-erh:user");
      setIsAuthed(false);
      setRole(null);
    } catch {}
  };

  return (
    <nav>
      <div className="fixed z-10 w-full bg-black text-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Link className="w-full" href="/">
              <div className="py-4 px-5 font-bold text-l">Pu erh</div>
            </Link>
          </div>
          <div className="hidden items-center gap-2 md:flex">
            {isAuthed && role === "Admin" ? (
              <Link className="w-full" href="/dashboard">
                <div className="py-5 px-0">Dashboard</div>
              </Link>
            ) : null}
            {isAuthed && role === "Member" ? (
              <>
                <Link className="w-full" href="/account">
                  <div className="py-5 px-0">Account</div>
                </Link>
                <Link className="w-full" href="/reserve">
                  <div className="py-5 px-0">Reservation</div>
                </Link>
              </>
            ) : null}
            {!isAuthed ? (
              <Link className="w-full" href="/login">
                <div className="py-5 px-0">Login</div>
              </Link>
            ) : (
              <button
                onClick={handleLogout}
                className="py-5 px-0 hover:bg-white/10"
              >
                Logout
              </button>
            )}
          </div>
          <button
            className="py-5 px-5 md:hidden"
            aria-label="Open menu"
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
          >
            <div className="flex flex-col gap-1.5">
              <span className="block h-0.5 w-6 bg-white"></span>
              <span className="block h-0.5 w-6 bg-white"></span>
              <span className="block h-0.5 w-6 bg-white"></span>
            </div>
          </button>
        </div>
        {open ? (
          <div className="md:hidden">
            <div className="flex flex-col border-t border-white/10">
              {isAuthed && role === "Admin" ? (
                <Link className="w-full" href="/dashboard">
                  <div className="py-3 px-5">Dashboard</div>
                </Link>
              ) : null}
              {isAuthed && role === "Member" ? (
                <>
                  <Link className="w-full" href="/account">
                    <div className="py-3 px-5">Account</div>
                  </Link>
                  <Link className="w-full" href="/reserve">
                    <div className="py-3 px-5">Reservation</div>
                  </Link>
                </>
              ) : null}
              {!isAuthed ? (
                <Link className="w-full" href="/login">
                  <div className="py-3 px-5">Login</div>
                </Link>
              ) : (
                <button
                  onClick={handleLogout}
                  className="w-full text-left py-3 px-5 hover:bg-white/10"
                >
                  Logout
                </button>
              )}
            </div>
          </div>
        ) : null}
      </div>
    </nav>
  );
}
