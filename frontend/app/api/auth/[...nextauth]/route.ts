// app/api/auth/[...nextauth]/route.ts
import NextAuth, { NextAuthOptions, Session, User } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { JWT } from "next-auth/jwt";
import axios from "axios";
import { jwtDecode } from "jwt-decode";

// Define our user type
export interface MyUser extends User {
  id: string;
  username: string;
  email: string;
  is_superuser: boolean;
  token?: string;
}

// Extend JWT type to include user
interface MyJWT extends JWT {
  user?: MyUser;
}

// NextAuth options
export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        username: { label: "Username", type: "text" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.username || !credentials?.password) return null;

        try {
          const res = await axios.post("/api/auth/login/", {
            username: credentials.username,
            password: credentials.password,
          });
          const tokenData = jwtDecode(res.data.access);
          if (res.data?.access) {
            const user: MyUser = {
              id: res.data.id || res.data.username,
              username: res.data.username,
              email: res.data.email || "",
              // @ts-ignore
              is_superuser: tokenData.is_superuser,
              token: res.data.access,
            };
            return user;
          }

          return null;
        } catch (err) {
          console.error(err);
          return null;
        }
      },
    }),
  ],
  session: { strategy: "jwt" },
  callbacks: {
    async jwt({ token, user }) {
      if (user) (token as MyJWT).user = user as MyUser;
      return token;
    },
    async session({ session, token }) {
      const myToken = token as MyJWT;
      if (myToken.user) {
        session.user = {
          ...myToken.user,
          is_superuser: !!myToken.user.is_superuser, // force boolean
        } as MyUser;
      }
      return session;
    },
  },
};

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
