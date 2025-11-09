"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { API_BASE_URL } from "@/lib/api";
import { getUserReservations, type Reservation } from "@/lib/mockData";

export default function AccountPage() {
  const [profile, setProfile] = useState<any | null>(null);
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const didFetchRef = useRef(false);
  useEffect(() => {
    if (didFetchRef.current) return;
    didFetchRef.current = true; // prevent double-run in React StrictMode (dev)
    const userId = localStorage.getItem("pu-erh:user_id");
    const tokensRaw = localStorage.getItem("pu-erh:tokens");
    const access = tokensRaw
      ? (JSON.parse(tokensRaw).access as string | undefined)
      : undefined;
    // Fetch user profile
    if (access && userId) {
      fetch(`/api/users/${userId}/`, {
        headers: { Authorization: `Bearer ${access}` },
      })
        .then((r) => {
          if (!r.ok) throw new Error(String(r.status));
          return r.json();
        })
        .then((data) => setProfile(data))
        .catch(() => setProfile(null));
      setReservations(getUserReservations(userId));
    } else {
      setProfile(null);
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
      {/* <h1 className="mt-2 text-2xl font-semibold">Account</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Your info and reservations
      </p> */}

      {/* Profile card - compact, hero-like */}
      <div className="mt-3">
        <div className="rounded-xl p-6 bg-gradient-to-br from-black to-zinc-900 text-white shadow-[0_10px_35px_rgba(255,0,0,0.25)]">
          <div className="flex items-center gap-5">
            <Avatar className="h-16 w-16 bg-white/10">
              <AvatarFallback className="text-white/90 text-lg">
                {(() => {
                  const fn = (profile?.first_name ?? "").toString();
                  const ln = (profile?.last_name ?? "").toString();
                  const initial =
                    (fn?.[0]?.toUpperCase?.() ?? "") +
                    (ln?.[0]?.toUpperCase?.() ?? "");
                  if (initial.trim()) return initial;
                  const uname = (profile?.username ?? "").toString();
                  return uname ? uname.slice(0, 2).toUpperCase() : "US";
                })()}
              </AvatarFallback>
            </Avatar>
            <div>
              <div className="text-2xl font-semibold">
                {profile
                  ? `${profile.first_name ?? ""} ${
                      profile.last_name ?? ""
                    }`.trim() || profile.username
                  : "—"}
              </div>
              <div className="text-xs text-white/60">
                @{profile?.username ?? "—"} • {profile?.email ?? "—"}
              </div>
            </div>
          </div>
          {/* Compact meta */}
          <div className="mt-4 flex flex-wrap items-center gap-3 text-xs text-white/70">
            <span className="rounded-full bg-white/10 px-3 py-1">
              Role: {profile?.role ?? "—"}
            </span>
            <span className="rounded-full bg-white/10 px-3 py-1">
              Team: {profile?.team ?? "—"}
            </span>
            <span className="rounded-full bg-white/10 px-3 py-1">
              Active: {profile?.is_active ? "Yes" : "No"}
            </span>
            <span className="rounded-full bg-white/10 px-3 py-1">
              Staff: {profile?.is_staff ? "Yes" : "No"}
            </span>
            <span className="rounded-full bg-white/10 px-3 py-1">
              Joined:{" "}
              {profile?.date_joined
                ? new Date(profile.date_joined).toLocaleDateString()
                : "—"}
            </span>
          </div>
        </div>
      </div>

      <div className="mt-8 grid gap-6 md:grid-cols-2">
        <div className="md:col-span-2 w-full">
          {(() => {
            const fmt = (iso?: string) =>
              iso ? new Date(iso).toLocaleString() : "—";
            const toRows = (when: "today" | "future" | "past") => {
              const appts: Array<{
                id: string;
                start_date?: string;
                resource_name?: string;
                status?: string;
              }> = Array.isArray(profile?.appointments?.[when])
                ? profile.appointments[when].map((a: any) => ({
                    id: `appt-${String(a.id)}`,
                    start_date: a.start_date,
                    resource_name: a.resource_name,
                    status: "BOOKED",
                  }))
                : [];
              const reqs: Array<{
                id: string;
                start_date?: string;
                resource_name?: string;
                status?: string;
              }> = Array.isArray(profile?.requests?.[when])
                ? profile.requests[when].map((r: any) => ({
                    id: `req-${String(r.id)}`,
                    start_date: r.start_date,
                    resource_name: r.resource_name,
                    status: r.status,
                  }))
                : [];
              const rows = [...appts, ...reqs].sort((a, b) =>
                (a.start_date ?? "").localeCompare(b.start_date ?? "")
              );
              return rows;
            };

            const todayRows = toRows("today");
            const futureRows = toRows("future");
            const pastRows = toRows("past");

            const Section = ({
              title,
              rows,
              emptyText,
            }: {
              title: string;
              rows: Array<{
                id: string;
                start_date?: string;
                resource_name?: string;
                status?: string;
              }>;
              emptyText: string;
            }) => (
              <section className="mt-0 first:mt-0">
                <h2 className="text-lg font-semibold">{title}</h2>
                <div className="mt-3 divide-y rounded-xl border">
                  {rows.map((row) => (
                    <div
                      key={`${title}-${row.id}-${row.start_date ?? ""}`}
                      className="flex items-center justify-between p-4"
                    >
                      <div className="text-sm">
                        <div className="font-medium">
                          {row.resource_name ?? "—"}
                        </div>
                        <div className="text-muted-foreground">
                          {fmt(row.start_date)}
                        </div>
                      </div>
                      <div className="text-xs rounded-full border px-2 py-1">
                        {row.status ?? "—"}
                      </div>
                    </div>
                  ))}
                  {rows.length === 0 ? (
                    <div className="p-6 text-sm text-muted-foreground">
                      {emptyText}
                    </div>
                  ) : null}
                </div>
              </section>
            );

            return (
              <>
                <Section
                  title="Today"
                  rows={todayRows}
                  emptyText="No items for today."
                />
                <div className="h-6" />
                <Section
                  title="Future"
                  rows={futureRows}
                  emptyText="No upcoming items."
                />
                <div className="h-6" />
                <Section
                  title="Past"
                  rows={pastRows}
                  emptyText="No past items."
                />
              </>
            );
          })()}
        </div>
      </div>
    </div>
  );
}
