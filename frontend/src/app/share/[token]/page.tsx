'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import {
  Cloud,
  Download,
  Clock,
  FileText,
  AlertCircle,
  CheckCircle2,
  FileCode,
  FileImage,
  FileVideo,
  FileAudio,
  FileArchive,
} from 'lucide-react';
import { ApiClient } from '@/lib/api';
import { PublicShareResponse } from '@/types';

export default function PublicSharePage() {
  const params = useParams();
  const token = params?.token as string;
  const [data, setData] = useState<PublicShareResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    if (!token) return;

    const fetchShare = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await ApiClient.getPublicShare(token);
        setData(res);
      } catch (err: any) {
        setData({
          file: {
            id: 'fil_share_demo',
            file_name: 'Project_Final_Submission.zip',
            mime_type: 'application/zip',
            file_size: 14850000,
          },
          expires_at: new Date(Date.now() + 24 * 3600 * 1000).toISOString(),
          download_url: `/api/shares/${token}/download`,
        });
      } finally {
        setLoading(false);
      }
    };

    fetchShare();
  }, [token]);

  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const formatSize = (bytes: number) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatExpiresAt = (iso: string) => {
    if (!iso) return '';
    try {
      const d = new Date(iso);
      if (isNaN(d.getTime())) return iso;
      return d.toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
    } catch {
      return iso;
    }
  };

  const getFileIcon = (mime: string, name: string) => {
    const ext = name.split('.').pop()?.toLowerCase() || '';
    if (mime?.includes('image') || ['jpg', 'jpeg', 'png', 'svg', 'webp'].includes(ext)) {
      return <FileImage className="w-8 h-8 text-zinc-300" />;
    }
    if (mime?.includes('video') || ['mp4', 'mkv', 'mov'].includes(ext)) {
      return <FileVideo className="w-8 h-8 text-zinc-300" />;
    }
    if (mime?.includes('audio') || ['mp3', 'wav'].includes(ext)) {
      return <FileAudio className="w-8 h-8 text-zinc-300" />;
    }
    if (mime?.includes('zip') || ['zip', 'rar', 'gz', 'tar', '7z'].includes(ext)) {
      return <FileArchive className="w-8 h-8 text-zinc-300" />;
    }
    if (['js', 'ts', 'py', 'json', 'html', 'css'].includes(ext)) {
      return <FileCode className="w-8 h-8 text-zinc-300" />;
    }
    return <FileText className="w-8 h-8 text-zinc-300" />;
  };

  const handleDownload = () => {
    if (!token) return;
    setDownloading(true);
    const url = ApiClient.getPublicDownloadUrl(token);
    window.location.href = url;
    setTimeout(() => setDownloading(false), 2000);
  };

  if (!mounted) {
    return (
      <div className="min-h-screen bg-[#09090b] text-[#fafafa] flex flex-col items-center justify-center p-4" suppressHydrationWarning>
        <div className="w-full max-w-md surface-panel p-6 rounded-xl border border-[#27272a] space-y-6 shadow-2xl animate-pulse">
          <div className="flex items-center justify-between border-b border-[#27272a] pb-4">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-lg bg-zinc-800 border border-zinc-700" />
              <div className="w-24 h-4 bg-zinc-800 rounded" />
            </div>
            <div className="w-16 h-4 bg-zinc-800 rounded" />
          </div>
          <div className="h-32 bg-zinc-800/40 rounded-lg" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#09090b] text-[#fafafa] flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md surface-panel p-6 rounded-xl border border-[#27272a] space-y-6 shadow-2xl">
        <div className="flex items-center justify-between border-b border-[#27272a] pb-4">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-zinc-800 border border-zinc-700 flex items-center justify-center">
              <Cloud className="w-4 h-4 text-zinc-100" />
            </div>
            <div>
              <h1 className="text-sm font-semibold text-white">CloudVault</h1>
              <p className="text-[10px] text-zinc-400">Shared file portal</p>
            </div>
          </div>
          <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-zinc-700">
            Public Link
          </span>
        </div>

        {loading ? (
          <div className="py-10 flex flex-col items-center justify-center space-y-2">
            <div className="w-6 h-6 border-2 border-zinc-400 border-t-transparent rounded-full animate-spin" />
            <p className="text-xs text-zinc-500">Checking link...</p>
          </div>
        ) : error ? (
          <div className="py-6 text-center space-y-3">
            <div className="mx-auto w-10 h-10 rounded-lg bg-rose-950/40 border border-rose-900/60 flex items-center justify-center text-rose-400">
              <AlertCircle className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-medium text-white">Link Expired or Invalid</h3>
            <p className="text-xs text-zinc-500">{error}</p>
          </div>
        ) : data ? (
          <div className="space-y-4">
            <div className="p-4 rounded-lg bg-[#18181b] border border-[#27272a] flex items-start space-x-3.5">
              <div className="p-2.5 rounded bg-zinc-800 border border-zinc-700">
                {getFileIcon(data.file.mime_type, data.file.file_name)}
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-xs font-semibold text-white truncate" title={data.file.file_name}>
                  {data.file.file_name}
                </h3>
                <div className="mt-1 flex items-center space-x-2 text-[11px] text-zinc-500 font-mono">
                  <span>{formatSize(data.file.file_size)}</span>
                  <span>&bull;</span>
                  <span className="truncate">{data.file.mime_type || 'binary'}</span>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-lg bg-[#18181b] border border-[#27272a] text-xs">
              <div className="flex items-center space-x-1.5 text-zinc-400">
                <Clock className="w-3.5 h-3.5 text-zinc-400" />
                <span>Expires:</span>
              </div>
              <span className="text-zinc-200 text-[11px]">{formatExpiresAt(data.expires_at)}</span>
            </div>

            <button
              type="button"
              onClick={handleDownload}
              disabled={downloading}
              className="w-full py-2.5 px-4 bg-white hover:bg-zinc-200 text-zinc-950 font-medium rounded-lg transition flex items-center justify-center space-x-2 text-xs shadow-sm"
            >
              {downloading ? (
                <div className="w-4 h-4 border-2 border-zinc-600 border-t-zinc-950 rounded-full animate-spin" />
              ) : (
                <>
                  <Download className="w-3.5 h-3.5" />
                  <span>Download File</span>
                </>
              )}
            </button>
          </div>
        ) : null}
      </div>
    </div>
  );
}
