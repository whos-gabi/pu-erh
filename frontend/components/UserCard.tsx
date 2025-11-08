"use client";
import { PuErhUser } from "@/lib/mockData";

export default function UserCard({ user }: { user: PuErhUser }) {
  return (
    <div className="rounded-xl border p-6">
      <h3 className="text-lg font-semibold">User</h3>
      <div className="mt-3 space-y-1 text-sm">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Name</span>
          <span>{user.name}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Email</span>
          <span>{user.email}</span>
        </div>
        {user.role ? (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Role</span>
            <span>{user.role}</span>
          </div>
        ) : null}
      </div>
    </div>
  );
}

