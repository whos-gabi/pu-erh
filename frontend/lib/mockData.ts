export type PuErhUser = {
  id: string;
  name: string;
  email: string;
  role?: string;
};

export type Reservation = {
  id: string;
  userId: string;
  seatId: string;
  seatLabel: string;
  floor: string;
  date: string; // ISO date
  status: "confirmed" | "cancelled";
};

const USER_KEY = "pu-erh:user";
const RES_KEY = "pu-erh:reservations";

export function getMockUser(): PuErhUser | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as PuErhUser;
  } catch {
    return null;
  }
}

export function setMockUser(user: PuErhUser) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function ensureSeedReservations() {
  const existing = localStorage.getItem(RES_KEY);
  if (existing) return;
  const user = getMockUser() ?? {
    id: "u-1",
    name: "Alex Pop",
    email: "alex.pop@example.com",
    role: "Member",
  };
  const today = new Date();
  const iso = (d: Date) => d.toISOString().slice(0, 10);
  const seed: Reservation[] = [
    {
      id: "r-1",
      userId: user.id,
      seatId: "G-12",
      seatLabel: "Desk G-12",
      floor: "4",
      date: iso(new Date(today.getFullYear(), today.getMonth(), today.getDate() - 7)),
      status: "confirmed",
    },
    {
      id: "r-2",
      userId: user.id,
      seatId: "G-08",
      seatLabel: "Desk G-08",
      floor: "4",
      date: iso(new Date(today.getFullYear(), today.getMonth(), today.getDate() + 2)),
      status: "confirmed",
    },
  ];
  localStorage.setItem(RES_KEY, JSON.stringify(seed));
}

export function getReservations(): Reservation[] {
  try {
    const raw = localStorage.getItem(RES_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as Reservation[];
  } catch {
    return [];
  }
}

export function addReservation(r: Reservation) {
  const list = getReservations();
  list.push(r);
  localStorage.setItem(RES_KEY, JSON.stringify(list));
}

export function getUserReservations(userId: string) {
  return getReservations().filter((r) => r.userId === userId);
}


