import type { Metadata } from "next";
import "./globals.css";
import Navigation from "./componente/Navigation";
import Providers from "./Provider"; // ✅ client wrapper

export const metadata: Metadata = {
  title: "Pu erh office registration",
  description: "Office reservation system for Pu erh",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <Navigation />
          <div className="pt-20 p-5">{children}</div>
        </Providers>
      </body>
    </html>
  );
}
