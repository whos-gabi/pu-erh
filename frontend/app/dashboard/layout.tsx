"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === "loading") return; // wait for session to load

    if (!session) {
      // User not logged in, redirect to login page
      router.push("/login");
      return;
    }

    console.log(session.user.is_superuser);
    if (session.user.is_superuser) {
      // router.push("/dashboard");
    } else {
      router.push("/account");
    }
  }, [status, session, router]);

  if (status === "loading") {
    return <div>Loading...</div>;
  }

  return <>{children}</>;
}
