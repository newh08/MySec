import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "MySecretary",
  description: "Personal AI Secretary Dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
