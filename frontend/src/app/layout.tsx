import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CloudVault — Secure Cloud Storage & Sharing",
  description: "Modern, secure cloud file storage and sharing platform with instant links and granular expiry controls.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 antialiased min-h-screen selection:bg-indigo-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
