import api from './index'

export interface InviteLookup {
  valid: boolean
  message: string
}

export interface AuthUser {
  id: string
  username: string
  email: string
  role: 'admin' | 'member'
  avatar_url?: string | null
  bio?: string | null
  birthday?: string | null
  role_in_family?: string | null
  preferred_theme?: string
  created_at: string
  updated_at?: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: AuthUser
}

export function login(username: string, password: string) {
  return api.post('/login', { username, password }) as Promise<TokenResponse>
}

export function lookupInvite(inviteCode: string): Promise<InviteLookup> {
  return api.get(`/invites/${encodeURIComponent(inviteCode)}`)
}

export function register(username: string, email: string, password: string, inviteCode: string) {
  return api.post('/register', { username, email, password, invite_code: inviteCode }) as Promise<TokenResponse>
}

export function logout() {
  return api.post('/logout')
}

export function getMe(): Promise<AuthUser> {
  return api.get('/me')
}
