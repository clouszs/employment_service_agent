import request from './request'

// ===== 简历生成 =====
export interface ResumeGenerateRequest {
  target_job?: string
  extra_profile?: Record<string, any>
}

export function generateResume(data: ResumeGenerateRequest): Promise<any> {
  return request.post('/career/resume', data)
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
