import type { Metadata } from "next";
import "./globals.css";
import Navigation from "./componente/Navigation";

export const metadata: Metadata = {
  title: "Pu erh office registration",
  description: "Office reservation system for Pu erh",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={``}>
        <Navigation />
        <div className="pt-20 p-5">{children}</div>
      </body>
    </html>
  );
}
