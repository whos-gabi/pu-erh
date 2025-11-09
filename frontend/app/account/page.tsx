"use client";
import { useEffect, useMemo, useState } from "react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { API_BASE_URL } from "@/lib/api";
import { getUserReservations, type Reservation } from "@/lib/mockData";

export default function AccountPage() {
  const [profile, setProfile] = useState<any | null>(null);
  const [reservations, setReservations] = useState<Reservation[]>([]);
  useEffect(() => {
    const userId = localStorage.getItem("pu-erh:user_id");
    const tokensRaw = localStorage.getItem("pu-erh:tokens");
    const access = tokensRaw ? (JSON.parse(tokensRaw).access as string | undefined) : undefined;
    // Fetch user profile
    if (access) {
      // Prefer /me first, then fallback to specific id if provided
      const fetchProfile = async () => {
        const me = await fetch(`/api/users/me/`, {
          headers: { Authorization: `Bearer ${access}` },
        });
        if (me.ok) {
          return me.json();
        }
        if (userId) {
          const byId = await fetch(`/api/users/${userId}/`, {
            headers: { Authorization: `Bearer ${access}` },
          });
          if (byId.ok) return byId.json();
        }
        throw new Error("profile_fetch_failed");
      };
      fetchProfile()
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
      <h1 className="mt-2 text-2xl font-semibold">Account</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Your info and reservations
      </p>

      {/* Profile card */}
      <div className="mt-6">
        <div className="rounded-xl p-6 bg-gradient-to-br from-black to-zinc-900 text-white shadow-[0_10px_35px_rgba(255,0,0,0.25)]">
          <div className="flex items-center gap-4">
            <Avatar className="h-12 w-12 bg-white/10">
              <AvatarFallback className="text-white/90">
                {(() => {
                  const fn = (profile?.first_name ?? "").toString();
                  const ln = (profile?.last_name ?? "").toString();
                  const initial =
                    (fn?.[0]?.toUpperCase?.() ?? "") + (ln?.[0]?.toUpperCase?.() ?? "");
                  if (initial.trim()) return initial;
                  const uname = (profile?.username ?? "").toString();
                  return uname ? uname.slice(0, 2).toUpperCase() : "US";
                })()}
              </AvatarFallback>
            </Avatar>
            <div>
              <div className="text-lg font-semibold">
                {profile ? `${profile.first_name ?? ""} ${profile.last_name ?? ""}`.trim() || profile.username : "—"}
              </div>
              <div className="text-xs text-white/70">{profile?.email ?? "—"}</div>
            </div>
          </div>
          <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
            <div className="rounded-lg bg-white/5 p-4 backdrop-blur-md">
              <div className="text-white/60">Username</div>
              <div className="mt-1">{profile?.username ?? "—"}</div>
            </div>
            <div className="rounded-lg bg-white/5 p-4 backdrop-blur-md">
              <div className="text-white/60">First name</div>
              <div className="mt-1">{profile?.first_name ?? "—"}</div>
            </div>
            <div className="rounded-lg bg-white/5 p-4 backdrop-blur-md">
              <div className="text-white/60">Last name</div>
              <div className="mt-1">{profile?.last_name ?? "—"}</div>
            </div>
            <div className="rounded-lg bg-white/5 p-4 backdrop-blur-md">
              <div className="text-white/60">Active</div>
              <div className="mt-1">{profile?.is_active ? "Yes" : "No"}</div>
            </div>
            <div className="rounded-lg bg-white/5 p-4 backdrop-blur-md">
              <div className="text-white/60">Staff</div>
              <div className="mt-1">{profile?.is_staff ? "Yes" : "No"}</div>
            </div>
            <div className="rounded-lg bg-white/5 p-4 backdrop-blur-md">
              <div className="text-white/60">Role</div>
              <div className="mt-1">{profile?.role ?? "—"}</div>
            </div>
            <div className="rounded-lg bg-white/5 p-4 backdrop-blur-md">
              <div className="text-white/60">Team</div>
              <div className="mt-1">{profile?.team ?? "—"}</div>
            </div>
            <div className="rounded-lg bg-white/5 p-4 backdrop-blur-md">
              <div className="text-white/60">Joined</div>
              <div className="mt-1">
                {profile?.date_joined ? new Date(profile.date_joined).toLocaleString() : "—"}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-8 grid gap-6 md:grid-cols-3">
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

