export interface FileItem {
  id: string;
  name: string;
  size: number;
  created_at: string;
}

export interface ShareLink {
  id: string;
  file_id: string;
  token: string;
  expires_at: string;
}
