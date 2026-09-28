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
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className="bg-[#09090b] text-[#fafafa] antialiased min-h-screen selection:bg-zinc-700 selection:text-white" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
