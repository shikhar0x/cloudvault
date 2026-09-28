'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Cloud, Lock, Mail, User as UserIcon } from 'lucide-react';
import { ApiClient } from '@/lib/api';

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await ApiClient.register(name, email, password);
      await ApiClient.login(email, password);
      router.push('/');
    } catch (err: any) {
      setError(err.message || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] text-[#fafafa] flex items-center justify-center p-4">
      <div className="w-full max-w-sm surface-panel p-6 rounded-xl border border-[#27272a] space-y-6 shadow-2xl">
        <div className="space-y-1 text-center">
          <div className="inline-flex items-center justify-center w-9 h-9 rounded-lg bg-zinc-800 border border-zinc-700 mb-2">
            <Cloud className="w-5 h-5 text-zinc-100" />
          </div>
          <h2 className="text-lg font-semibold text-white tracking-tight">Create an account</h2>
          <p className="text-xs text-zinc-400">Get started with CloudVault storage</p>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-900/60 text-rose-300 text-xs">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3.5">
          <div>
            <label className="block text-[10px] font-semibold uppercase tracking-wider text-zinc-400 mb-1.5">
              Full Name
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Alex Vance"
              className="w-full px-3 py-2 bg-[#18181b] border border-[#27272a] rounded-lg text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-500 transition"
            />
          </div>

          <div>
            <label className="block text-[10px] font-semibold uppercase tracking-wider text-zinc-400 mb-1.5">
              Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="alex@example.com"
              className="w-full px-3 py-2 bg-[#18181b] border border-[#27272a] rounded-lg text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-500 transition"
            />
          </div>

          <div>
            <label className="block text-[10px] font-semibold uppercase tracking-wider text-zinc-400 mb-1.5">
              Password
            </label>
            <input
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-3 py-2 bg-[#18181b] border border-[#27272a] rounded-lg text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-500 transition"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 px-3 bg-white hover:bg-zinc-200 text-zinc-950 font-medium rounded-lg text-xs transition flex items-center justify-center space-x-1.5"
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-zinc-600 border-t-zinc-950 rounded-full animate-spin" />
            ) : (
              <span>Create Account</span>
            )}
          </button>
        </form>

        <p className="text-center text-xs text-zinc-500">
          Already have an account?{' '}
          <Link href="/login" className="text-zinc-300 hover:text-white underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
