export interface User {
  id: string; first_name: string; last_name: string;
  middle_name: string | null; email: string;
  recovery_email: string | null; is_active: boolean;
  last_login_at: string | null; avatar_url: string | null; created_at: string; updated_at: string;
}
export interface Role { id: string; name: string; description: string | null; is_system: boolean; }
export interface Permission { id: string; code: string; resource: string; action: string; description: string | null; }
export interface TokenResponse { access_token: string; token_type: string; expires_at: string; }
export interface SessionInfo { id: string; created_at: string; expires_at: string; ip_address: string | null; user_agent: string | null; }
export interface Notification { id: string; event: string; title: string; body: string | null; link: string | null; is_read: boolean; user_id: string | null; created_at: string; }
export interface AuditEntry { id: string; user_id: string | null; user_email: string | null; action: string; entity_type: string | null; entity_id: string | null; detail: string | null; ip_address: string | null; created_at: string; }
export interface Settings { site_name: string; maintenance_mode: boolean; max_upload_size_mb: number; }
export interface Report { id: string; title: string; content: string; created_by: string; }
export interface Document { id: string; name: string; body: string; created_by: string; }
