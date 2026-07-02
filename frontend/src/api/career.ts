import request from './request'

// ===== 简历生成 =====
export interface ResumeGenerateRequest {
  target_job?: string
  extra_profile?: Record<string, any>
}

export interface ResumeSavePayload {
  title: string
  content: Record<string, any>
  is_default?: boolean
}

export interface ResumeItem {
  id: number
  user_id: number
  title: string
  content: Record<string, any>
  pdf_path: string | null
  is_default: number
  created_at: string
  updated_at: string
}

export interface ResumeListResult {
  total: number
  page: number
  size: number
  items: ResumeItem[]
}

export interface ResumeGenerateResult {
  resume: Record<string, any>
  raw?: string | null
  usage?: Record<string, any>
  target_job: string
}

export function generateResume(data: ResumeGenerateRequest): Promise<ResumeGenerateResult> {
  return request.post('/career/resume', data)
}

export function saveResume(data: ResumeSavePayload): Promise<{ data: ResumeItem; message: string }> {
  return request.post('/career/resume/save', data)
}

export function listResumes(params: { page?: number; size?: number }): Promise<ResumeListResult> {
  return request.get('/career/resume/list', { params })
}

export function deleteResume(id: number): Promise<{ message: string }> {
  return request.delete(`/career/resume/${id}`)
}

export function setDefaultResume(id: number): Promise<{ data: ResumeItem; message: string }> {
  return request.post(`/career/resume/${id}/default`)
}

export function downloadResumePdf(id: number): Promise<Blob> {
  return request.get(`/career/resume/${id}/pdf`, { responseType: 'blob' })
}

// ===== 职位推荐 =====
export interface JobQuery {
  query: string
  top_k?: number
  location?: string
}

export function recommendJobs(data: JobQuery): Promise<{ items: any[]; count: number; query: string }> {
  return request.post('/career/jobs', data)
}

// ===== 日历 ICS =====
export interface CalendarIcsRequest {
  title: string
  start_time: string
  end_time?: string
  location?: string
  description?: string
}

export interface CalendarIcsResult {
  ics_content: string
  title: string
  start_time: string
  end_time: string
}

export function buildCalendarIcs(
  data: CalendarIcsRequest,
): Promise<CalendarIcsResult> {
  return request.post('/career/calendar/ics', data)
}
