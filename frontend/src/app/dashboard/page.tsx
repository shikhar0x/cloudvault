"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";
import { FileItem } from "@/types/file";

export default function DashboardPage() {
  const router = useRouter();
  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isLoggedIn()) {
      router.push("/login");
      return;
    }
    // NOTE: confirm the real endpoint path with your backend teammate
    apiFetch<FileItem[]>("/files")
      .then(setFiles)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [router]);

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">My Files</h1>
      {loading && <p className="text-gray-400">Loading...</p>}
      {error && <p className="text-red-400">{error}</p>}
      {!loading && !error && files.length === 0 && (
        <p className="text-gray-400">
          No files yet. Upload one to get started.
        </p>
      )}
      <ul className="flex flex-col gap-2">
        {files.map((file) => (
          <li
            key={file.id}
            className="flex justify-between items-center bg-gray-900 border border-gray-800 rounded-lg px-4 py-3"
          >
            <span>{file.name}</span>
            <span className="text-gray-500 text-sm">
              {(file.size / 1024).toFixed(1)} KB
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
