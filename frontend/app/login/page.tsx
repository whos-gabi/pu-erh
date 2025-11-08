"use client";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useState, useEffect } from "react";
import { signIn, useSession } from "next-auth/react";

export default function LoginPage() {
  const [username, setUsername] = useState("Alex Pop");
  const [password, setPassword] = useState("alex.pop@example.com");
  const router = useRouter();
  const { data: session } = useSession();

  // Automatically redirect if logged in
  useEffect(() => {
    if (session?.user) {
      console.log(session.user);
      if (session.user.is_superuser) {
        router.push("/dashboard");
      } else {
        router.push("/account");
      }
    }
  }, [session, router]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // Sign in using credentials
    await signIn("credentials", {
      redirect: false, // prevent automatic redirect
      username,
      password,
    });
  };

  return (
    <div className="mx-auto max-w-md">
      <h1 className="mt-6 text-2xl font-semibold">Login</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Mocked login for now. Backend coming soon.
      </p>
      <form onSubmit={onSubmit} className="mt-6 space-y-4">
        <div className="space-y-1.5">
          <label className="text-sm">Username</label>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full rounded-md border bg-background px-3 py-2"
            placeholder="Your username"
          />
        </div>
        <div className="space-y-1.5">
          <label className="text-sm">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-md border bg-background px-3 py-2"
            placeholder="Your password"
          />
        </div>
        <Button type="submit" className="w-full">
          Continue
        </Button>
      </form>
    </div>
  );
}
