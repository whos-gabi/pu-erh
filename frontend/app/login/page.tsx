"use client";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { setMockUser } from "@/lib/mockData";
import { useState } from "react";

export default function LoginPage() {
  const router = useRouter();
  const [name, setName] = useState("Alex Pop");
  const [email, setEmail] = useState("alex.pop@example.com");

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setMockUser({
      id: "u-1",
      name,
      email,
      role: "Member",
    });
    router.push("/dashboard");
  };

  return (
    <div className="mx-auto max-w-md">
      <h1 className="mt-6 text-2xl font-semibold">Login</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Mocked login for now. Backend coming soon.
      </p>
      <form onSubmit={onSubmit} className="mt-6 space-y-4">
        <div className="space-y-1.5">
          <label className="text-sm">Name</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-md border bg-background px-3 py-2"
            placeholder="Your name"
          />
        </div>
        <div className="space-y-1.5">
          <label className="text-sm">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-md border bg-background px-3 py-2"
            placeholder="you@example.com"
          />
        </div>
        <Button type="submit" className="w-full">
          Continue
        </Button>
      </form>
    </div>
  );
}

