import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Apex Exchange | Simulation",
  description: "A simulated digital asset exchange engineering project. No real funds or trading."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
