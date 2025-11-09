"use client";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useEffect, useState } from "react";
import { ensureSeedReservations, getMockUser, setMockUser, type PuErhUser } from "@/lib/mockData";

export default function Home() {
  const [user, setUser] = useState<PuErhUser | null>(null);
  useEffect(() => {
    // Seed data on first visit for demo
    let u = getMockUser();
    if (!u) {
      u = {
        id: "u-1",
        name: "Alex Pop",
        email: "alex.pop@example.com",
        role: "Member",
      };
      setMockUser(u);
    }
    ensureSeedReservations();
    setUser(u);
  }, []);

  return (
    <div className="mx-auto max-w-6xl">
      <section className="rounded-xl bg-gradient-to-br from-black to-zinc-800 p-6 md:p-10 text-white relative overflow-hidden">
        <div className="pointer-events-none absolute -bottom-10 -left-10 h-64 w-64 rounded-full blur-3xl" style={{background: "radial-gradient(circle, rgba(255,0,0,0.45) 0%, rgba(255,0,0,0) 60%)"}} />
        <h1 className="text-4xl font-semibold md:text-6xl">BookMe.</h1>
        <p className="mt-4 max-w-2xl text-white/80">
          Reserve desks with ease. Modern, fast, and simple. Manage your future and past reservations in one place.
        </p>
        <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
          <Link href="/reserve">
            <Button size="lg" className="w-full sm:w-auto">
              Make a reservation
            </Button>
          </Link>
          <a href="#more" className="w-full sm:w-auto">
            <Button variant="outline" size="lg" className="w-full sm:w-auto bg-white/10 text-white/80 hover:bg-white/20 border-white/20">
              View more
            </Button>
          </a>
        </div>
      </section>

      <section id="more" className="mt-10 grid gap-6 md:grid-cols-3">
        <div className="rounded-xl border bg-white/5 backdrop-blur-md p-6 shadow-[0_10px_35px_rgba(255,0,0,0.25)]">
          <h3 className="text-lg font-semibold">Fast booking</h3>
          <p className="mt-2 text-sm text-zinc-700">
            Browse the floor plan, click a desk, and confirm. Your reservations are tracked for past and future dates.
          </p>
        </div>
        <div className="rounded-xl border bg-white/5 backdrop-blur-md p-6 shadow-[0_10px_35px_rgba(255,0,0,0.25)]">
          <h3 className="text-lg font-semibold">Smart approvals</h3>
          <p className="mt-2 text-sm text-zinc-700">
            Meeting rooms and special areas can request approval with a single click.
          </p>
        </div>
        <div className="rounded-xl border bg-white/5 backdrop-blur-md p-6 shadow-[0_10px_35px_rgba(255,0,0,0.25)]">
          <h3 className="text-lg font-semibold">Modern UX</h3>
          <p className="mt-2 text-sm text-zinc-700">
            Smooth animations and a glassy interface give you a delightful experience.
          </p>
        </div>
      </section>
    </div>
  );
}
