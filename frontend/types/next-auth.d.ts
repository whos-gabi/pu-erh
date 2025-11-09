import NextAuth from "next-auth";

declare module "next-auth" {
  interface Session {
    user: {
      id: string;
      username: string;
      is_superuser: boolean;
      token?: string;
      refresh?: string;
    };
  }

  interface User {
    id: string;
    username: string;
    is_superuser: boolean;
    token?: string;
    refresh?: string;
  }
}
