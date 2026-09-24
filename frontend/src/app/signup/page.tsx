"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { saveToken } from "@/lib/auth";
import Button from "@/components/Button";

export default function SignupPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      // NOTE: confirm the real endpoint path + response shape with your backend teammate
      const data = await apiFetch<{ access_token: string }>("/auth/register", {
        method: "POST",
        body: JSON.stringify({ name, email, password }),
      });
      saveToken(data.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Signup failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-sm mx-auto mt-16">
      <h1 className="text-2xl font-bold mb-6">Sign up</h1>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <input
          type="text"
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="bg-gray-900 border border-gray-700 rounded-lg px-4 py-2"
          required
        />
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="bg-gray-900 border border-gray-700 rounded-lg px-4 py-2"
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="bg-gray-900 border border-gray-700 rounded-lg px-4 py-2"
          required
        />
        {error && <p className="text-red-400 text-sm">{error}</p>}
        <Button type="submit" disabled={loading}>
          {loading ? "Creating account..." : "Sign up"}
        </Button>
      </form>
    </div>
  );
}
