"use client";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import UserCard from "@/components/UserCard";
import { getMockUser, getUserReservations, type PuErhUser, type Reservation } from "@/lib/mockData";
import { useEffect, useMemo, useState } from "react";

function splitPastFuture(dates: string[]) {
  const today = new Date().toISOString().slice(0, 10);
  const past: string[] = [];
  const future: string[] = [];
  for (const d of dates) {
    if (d < today) past.push(d);
    else future.push(d);
  }
  return { past, future };
}

export default function DashboardPage() {
  const [user, setUser] = useState<PuErhUser | null>(null);
  const [userReservations, setUserReservations] = useState<Reservation[]>([]);
  useEffect(() => {
    const u = getMockUser();
    setUser(u);
    if (u) setUserReservations(getUserReservations(u.id));
    else setUserReservations([]);
  }, []);
  const { past, future } = useMemo(
    () => splitPastFuture(userReservations.map((r) => r.date).sort()),
    [userReservations]
  );

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mt-2 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <div className="flex gap-2">
          <Link href="/reserve">
            <Button>Make a reservation</Button>
          </Link>
          <Link href="/account">
            <Button variant="outline">Account</Button>
          </Link>
        </div>
      </div>

      <div className="mt-6 grid gap-6 md:grid-cols-3">
        <div className="rounded-xl border p-6 md:col-span-2">
          <h3 className="text-lg font-semibold">Overview</h3>
          <div className="mt-4 grid gap-4 sm:grid-cols-3">
            <div className="rounded-lg border p-4">
              <div className="text-sm text-muted-foreground">Upcoming</div>
              <div className="mt-2 text-2xl font-semibold">{future.length}</div>
            </div>
            <div className="rounded-lg border p-4">
              <div className="text-sm text-muted-foreground">Past</div>
              <div className="mt-2 text-2xl font-semibold">{past.length}</div>
            </div>
            <div className="rounded-lg border p-4">
              <div className="text-sm text-muted-foreground">Total</div>
              <div className="mt-2 text-2xl font-semibold">{userReservations.length}</div>
            </div>
          </div>

          <div className="mt-6">
            <h4 className="font-medium">Next reservations</h4>
            <div className="mt-3 divide-y rounded-xl border">
              {userReservations
                .filter((r) => r.date >= new Date().toISOString().slice(0, 10))
                .sort((a, b) => a.date.localeCompare(b.date))
                .slice(0, 5)
                .map((r) => (
                  <div key={r.id} className="flex items-center justify-between p-4">
                    <div className="text-sm">
                      <div className="font-medium">{r.seatLabel}</div>
                      <div className="text-muted-foreground">
                        Floor {r.floor} • {r.date}
                      </div>
                    </div>
                    <div className="text-xs rounded-full border px-2 py-1">
                      {r.status}
                    </div>
                  </div>
                ))}
              {userReservations.filter((r) => r.date >= new Date().toISOString().slice(0, 10)).length ===
              0 ? (
                <div className="p-6 text-sm text-muted-foreground">
                  No upcoming reservations.{" "}
                  <Link href="/reserve" className="underline">
                    Book one
                  </Link>
                  .
                </div>
              ) : null}
            </div>
          </div>
        </div>
        <div>
          {user ? (
            <UserCard user={user} />
          ) : (
            <div className="rounded-xl border p-6">
              <div className="text-sm text-muted-foreground">
                You are not logged in.
              </div>
              <Link href="/login">
                <Button className="mt-3 w-full">Login</Button>
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

