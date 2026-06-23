export interface User {
  id: number
  username: string
  real_name: string | null
  user_type: number
  college: string | null
  email: string | null
  phone: string | null
  status: number
  roles?: string[]
}

export interface LoginResp {
  access_token: string
  token_type: string
  user: User
}

export interface Role {
  id: number
  role_code: string
  role_name: string
  description: string | null
  created_at: string
}
