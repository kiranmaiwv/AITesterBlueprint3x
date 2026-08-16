import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ETL QA Buddy",
  description: "AI-powered ETL data quality testing dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
