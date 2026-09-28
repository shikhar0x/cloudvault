'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Cloud, Lock, Mail, ArrowRight, ShieldCheck, HardDrive, Share2 } from 'lucide-react';
import { ApiClient } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await ApiClient.login(email, password);
      router.push('/');
    } catch (err: any) {
      setError(err.message || 'Invalid email or password.');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setEmail('demo@cloudvault.dev');
    setPassword('demopassword123');
    setLoading(true);
    setError(null);
    try {
      await ApiClient.login('demo@cloudvault.dev', 'demopassword123');
      router.push('/');
    } catch {
      ApiClient.setUser({
        id: 'usr_demo_01',
        name: 'Demo Student',
        email: 'demo@cloudvault.dev',
      });
      ApiClient.setToken('mock_jwt_token_demo_mode');
      router.push('/');
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
          <h2 className="text-lg font-semibold text-white tracking-tight">Sign in to CloudVault</h2>
          <p className="text-xs text-zinc-400">Enter your credentials to access your drive</p>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-900/60 text-rose-300 text-xs">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3.5">
          <div>
            <label className="block text-[10px] font-semibold uppercase tracking-wider text-zinc-400 mb-1.5">
              Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@example.com"
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
              <span>Sign In</span>
            )}
          </button>
        </form>

        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-[#27272a]" />
          </div>
          <div className="relative flex justify-center text-[10px] uppercase">
            <span className="bg-[#121215] px-2 text-zinc-500">Or</span>
          </div>
        </div>

        <button
          type="button"
          onClick={handleDemoLogin}
          className="w-full py-2 px-3 bg-[#18181b] hover:bg-zinc-800 text-zinc-200 border border-[#27272a] font-medium rounded-lg text-xs transition"
        >
          Quick Demo Login
        </button>

        <p className="text-center text-xs text-zinc-500">
          Don&apos;t have an account?{' '}
          <Link href="/register" className="text-zinc-300 hover:text-white underline">
            Register
          </Link>
        </p>
      </div>
    </div>
  );
}
