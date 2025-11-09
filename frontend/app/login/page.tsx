"use client";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useState, useEffect } from "react";
import { signIn, useSession } from "next-auth/react";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const router = useRouter();
  const { data: session } = useSession();

  // Automatically redirect if logged in
  useEffect(() => {
    if (session?.user) {
      // Persist tokens and user identity for API calls and navbar
      try {
        const access = (session.user as any).token as string | undefined;
        const refresh = (session.user as any).refresh as string | undefined;
        const user_id = (session.user as any).id as string | undefined;
        const uname = (session.user as any).username as string | undefined;
        const is_superuser = !!(session.user as any).is_superuser;
        if (access && refresh) {
          localStorage.setItem(
            "pu-erh:tokens",
            JSON.stringify({ access, refresh })
          );
        }
        if (user_id || uname) {
          localStorage.setItem(
            "pu-erh:user",
            JSON.stringify({ id: user_id, username: uname, is_superuser })
          );
          if (user_id) localStorage.setItem("pu-erh:user_id", user_id);
        }
      } catch {}

      if (session.user.is_superuser) {
        const today = new Date();
        const formattedDate = `${today.getFullYear()}-${(today.getMonth() + 1)
          .toString()
          .padStart(2, "0")}-${today.getDate().toString().padStart(2, "0")}`;

        router.push(`/dashboard/meetingRoom1/${formattedDate}`);
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
        Enter your credentials to continue.
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
