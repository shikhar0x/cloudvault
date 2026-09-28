import { User, AuthResponse, FileItem, FolderItem, ShareResponse, PublicShareResponse, StorageStats } from '../types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export class ApiClient {
  public static getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('cloudvault_token');
  }

  public static setToken(token: string) {
    if (typeof window !== 'undefined') {
      localStorage.setItem('cloudvault_token', token);
    }
  }

  public static clearToken() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('cloudvault_token');
      localStorage.removeItem('cloudvault_user');
    }
  }

  public static getUser(): User | null {
    if (typeof window === 'undefined') return null;
    const userStr = localStorage.getItem('cloudvault_user');
    if (!userStr) return null;
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  }

  public static setUser(user: User) {
    if (typeof window !== 'undefined') {
      localStorage.setItem('cloudvault_user', JSON.stringify(user));
    }
  }

  private static async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        let errorMsg = `Request failed with status ${response.status}`;
        try {
          const errData = await response.json();
          if (errData.detail) {
            errorMsg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
          }
        } catch {
          // ignore parsing error
        }
        throw new Error(errorMsg);
      }

      if (response.status === 204) {
        return {} as T;
      }

      return await response.json();
    } catch (err: any) {
      throw err;
    }
  }

  // Authentication
  static async register(name: string, email: string, password: string): Promise<User> {
    return this.request<User>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    });
  }

  static async login(email: string, password: string): Promise<AuthResponse> {
    const res = await this.request<AuthResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    if (res.access_token) {
      this.setToken(res.access_token);
      if (res.user) {
        this.setUser(res.user);
      }
    }
    return res;
  }

  static async getMe(): Promise<User> {
    const user = await this.request<User>('/api/auth/me');
    this.setUser(user);
    return user;
  }

  // Folders
  static async getFolders(parentId: string | null = null): Promise<FolderItem[]> {
    const query = parentId ? `?parent_id=${encodeURIComponent(parentId)}` : '';
    return this.request<FolderItem[]>(`/api/folders${query}`);
  }

  static async createFolder(name: string, parentId: string | null = null): Promise<FolderItem> {
    return this.request<FolderItem>('/api/folders', {
      method: 'POST',
      body: JSON.stringify({ name, parent_id: parentId }),
    });
  }

  static async deleteFolder(folderId: string): Promise<void> {
    await this.request(`/api/folders/${folderId}`, {
      method: 'DELETE',
    });
  }

  // Files
  static async getFiles(folderId: string | null = null): Promise<FileItem[]> {
    const query = folderId ? `?folder_id=${encodeURIComponent(folderId)}` : '';
    return this.request<FileItem[]>(`/api/files${query}`);
  }

  static async uploadFile(file: File, folderId: string | null = null): Promise<FileItem> {
    const formData = new FormData();
    formData.append('file', file);
    if (folderId) {
      formData.append('folder_id', folderId);
    }

    return this.request<FileItem>('/api/files/upload', {
      method: 'POST',
      body: formData,
    });
  }

  static async deleteFile(fileId: string): Promise<void> {
    await this.request(`/api/files/${fileId}`, {
      method: 'DELETE',
    });
  }

  static getDownloadUrl(fileId: string): string {
    const token = this.getToken();
    return `${API_BASE}/api/files/${fileId}/download${token ? `?token=${token}` : ''}`;
  }

  // Sharing
  static async createShareLink(fileId: string, expiresIn: string = '1d'): Promise<ShareResponse> {
    return this.request<ShareResponse>('/api/shares', {
      method: 'POST',
      body: JSON.stringify({ file_id: fileId, expires_in: expiresIn }),
    });
  }

  static async getPublicShare(token: string): Promise<PublicShareResponse> {
    return this.request<PublicShareResponse>(`/api/shares/${token}`);
  }

  static getPublicDownloadUrl(token: string): string {
    return `${API_BASE}/api/shares/${token}/download`;
  }

  // Storage Stats
  static async getStorageStats(): Promise<StorageStats> {
    try {
      return await this.request<StorageStats>('/api/storage/stats');
    } catch {
      return {
        used_bytes: 0,
        total_bytes: 10 * 1024 * 1024 * 1024, // 10 GB default quota
        file_count: 0,
        folder_count: 0,
      };
    }
  }
}
