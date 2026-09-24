"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { clearToken, isLoggedIn } from "@/lib/auth";

export default function Navbar() {
  const router = useRouter();

  function handleLogout() {
    clearToken();
    router.push("/login");
  }

  return (
    <nav className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
      <Link href="/" className="text-xl font-bold">
        CloudVault
      </Link>
      <div className="flex gap-4 items-center">
        {isLoggedIn() ? (
          <>
            <Link href="/dashboard">Dashboard</Link>
            <button onClick={handleLogout} className="text-red-400">
              Logout
            </button>
          </>
        ) : (
          <>
            <Link href="/login">Login</Link>
            <Link href="/signup">Sign up</Link>
          </>
        )}
      </div>
    </nav>
  );
}
