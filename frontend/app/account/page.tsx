"use client";
import UserCard from "@/components/UserCard";
import { getMockUser, getUserReservations, type PuErhUser, type Reservation } from "@/lib/mockData";
import { useEffect, useMemo, useState } from "react";

export default function AccountPage() {
  const [user, setUser] = useState<PuErhUser | null>(null);
  const [reservations, setReservations] = useState<Reservation[]>([]);
  useEffect(() => {
    const u = getMockUser();
    setUser(u);
    if (u) {
      setReservations(getUserReservations(u.id));
    } else {
      setReservations([]);
    }
  }, []);

  const today = useMemo(() => new Date().toISOString().slice(0, 10), []);
  const { future, past } = useMemo(() => {
    const futureList = reservations
      .filter((r) => r.date >= today)
      .sort((a, b) => a.date.localeCompare(b.date));
    const pastList = reservations
      .filter((r) => r.date < today)
      .sort((a, b) => b.date.localeCompare(a.date));
    return { future: futureList, past: pastList };
  }, [reservations, today]);

  return (
    <div className="mx-auto max-w-6xl">
      <h1 className="mt-2 text-2xl font-semibold">Account</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Your info and reservations
      </p>

      <div className="mt-6 grid gap-6 md:grid-cols-3">
        <div className="md:col-span-1">
          {user ? (
            <UserCard user={user} />
          ) : (
            <div className="rounded-xl border p-6">
              <div className="text-sm text-muted-foreground">
                You are not logged in.
              </div>
            </div>
          )}
        </div>
        <div className="md:col-span-2">
          <section>
            <h2 className="text-lg font-semibold">Upcoming reservations</h2>
            <div className="mt-3 divide-y rounded-xl border">
              {future.map((r) => (
                <div key={r.id} className="flex items-center justify-between p-4">
                  <div className="text-sm">
                    <div className="font-medium">{r.seatLabel}</div>
                    <div className="text-muted-foreground">
                      {r.date} • Floor {r.floor}
                    </div>
                  </div>
                  <div className="text-xs rounded-full border px-2 py-1">
                    {r.status}
                  </div>
                </div>
              ))}
              {future.length === 0 ? (
                <div className="p-6 text-sm text-muted-foreground">
                  No upcoming reservations.
                </div>
              ) : null}
            </div>
          </section>

          <section className="mt-8">
            <h2 className="text-lg font-semibold">Past reservations</h2>
            <div className="mt-3 divide-y rounded-xl border">
              {past.map((r) => (
                <div key={r.id} className="flex items-center justify-between p-4">
                  <div className="text-sm">
                    <div className="font-medium">{r.seatLabel}</div>
                    <div className="text-muted-foreground">
                      {r.date} • Floor {r.floor}
                    </div>
                  </div>
                  <div className="text-xs rounded-full border px-2 py-1">
                    {r.status}
                  </div>
                </div>
              ))}
              {past.length === 0 ? (
                <div className="p-6 text-sm text-muted-foreground">
                  No past reservations.
                </div>
              ) : null}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

