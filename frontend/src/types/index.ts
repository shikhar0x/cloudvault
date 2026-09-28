export interface User {
  id: string;
  name: string;
  email: string;
  created_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type?: string;
  user: User;
}

export interface FolderItem {
  id: string;
  name: string;
  parent_id: string | null;
  created_at: string;
  updated_at?: string;
  item_count?: number;
}

export interface FileItem {
  id: string;
  file_name: string;
  folder_id: string | null;
  file_size: number;
  mime_type: string;
  created_at: string;
  updated_at?: string;
  object_key?: string;
}

export interface SharedFileInfo {
  id: string;
  file_name: string;
  mime_type: string;
  file_size: number;
}

export interface ShareResponse {
  id: string;
  token: string;
  share_url: string;
  expires_at: string;
  created_at: string;
  file: SharedFileInfo;
}

export interface PublicShareResponse {
  file: SharedFileInfo;
  expires_at: string;
  download_url: string;
}

export interface StorageStats {
  used_bytes: number;
  total_bytes: number;
  file_count: number;
  folder_count: number;
}
