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
      <section className=" rounded-xl bg-gradient-to-br from-black to-zinc-800 p-6 md:p-10 text-white">
        <h1 className="text-3xl font-semibold md:text-5xl">
          Pu erh office registration
        </h1>
        <p className="mt-4 max-w-2xl text-white/80">
          Reserve desks with ease. Modern, fast, and simple. Manage your future and
          past reservations in one place.
        </p>
        <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
          <Link href={user ? "/dashboard" : "/login"}>
            <Button size="lg" className="w-full sm:w-auto">
              {user ? "Go to dashboard" : "Login to start"}
            </Button>
          </Link>
          <Link href="/reserve">
            <Button variant="outline" size="lg" className="text-black w-full sm:w-auto">
              Make a reservation
            </Button>
          </Link>
        </div>
      </section>

      <section className="mt-10 grid gap-6 md:grid-cols-3">
        <div className="rounded-xl border p-6">
          <h3 className="text-lg font-semibold">About the project</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Pu erh is a lightweight office seat reservation system. Browse the floor
            plan, click a desk, and confirm. Your reservations are tracked for past
            and future dates.
          </p>
        </div>
        <div className="rounded-xl border p-6">
          <h3 className="text-lg font-semibold">Login</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Authentication is mocked for now. A backend will power real users soon.
          </p>
        </div>
        <div className="rounded-xl border p-6">
          <h3 className="text-lg font-semibold">Dashboard</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Quickly view your upcoming reservations, history, and user info.
          </p>
        </div>
      </section>
    </div>
  );
}
