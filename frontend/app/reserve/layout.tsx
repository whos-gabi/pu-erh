"use client";
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  // Route protection using next-auth
  // Redirect unauthenticated users to /login
  // Admin users are redirected to /dashboard
  // Member users may access this route
  // Uses client-side guard to avoid SSR mismatch
  const { useEffect } = require("react") as typeof import("react");
  const { useRouter } = require("next/navigation") as typeof import("next/navigation");
  const { useSession } = require("next-auth/react") as typeof import("next-auth/react");
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === "loading") return;
    if (!session) {
      router.replace("/login");
      return;
    }
    if ((session as any).user?.is_superuser) {
      router.replace("/dashboard");
      return;
    }
  }, [status, session, router]);

  if (status === "loading" || !session) {
    return <div className="p-5 text-sm text-muted-foreground">Loading…</div>;
  }

  return <>{children}</>;
}
