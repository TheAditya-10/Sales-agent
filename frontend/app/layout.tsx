import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AutoElite AI Sales Assistant",
  description: "AI sales assistant demo for a Mahindra XUV700 dealership catalog.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
