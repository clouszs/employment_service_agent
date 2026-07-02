import request from './request'
import type { PageResult } from '@/types/api'

export interface FaqItem {
  id: number
  question: string
  answer: string
  category_id: number | null
  vector_id: string | null
  hit_count: number
  ask_count: number
  status: number
  created_at: string
  updated_at: string
}

export interface FaqCreatePayload {
  question: string
  answer: string
  category_id?: number | null
}

export interface FaqUpdatePayload {
  question?: string
  answer?: string
  category_id?: number | null
}

export interface FaqStatusPayload {
  status: number
}

export interface FaqBatchPayload {
  action: 'enable' | 'disable' | 'delete'
  ids: number[]
}

export function listFaqs(params: {
  page?: number
  size?: number
  keyword?: string
  category_id?: number
  status?: number
}): Promise<PageResult<FaqItem>> {
  return request.get('/faqs', { params })
}

export function createFaq(payload: FaqCreatePayload): Promise<{ data: FaqItem; message: string }> {
  return request.post('/faqs', payload)
}

export function updateFaq(id: number, payload: FaqUpdatePayload): Promise<{ data: FaqItem; message: string }> {
  return request.put(`/faqs/${id}`, payload)
}

export function setFaqStatus(id: number, payload: FaqStatusPayload): Promise<{ data: FaqItem; message: string }> {
  return request.patch(`/faqs/${id}/status`, payload)
}

export function deleteFaq(id: number): Promise<{ message: string }> {
  return request.delete(`/faqs/${id}`)
}

export function batchFaqs(payload: FaqBatchPayload): Promise<{ data: { affected: number }; message: string }> {
  return request.post('/faqs/batch', payload)
}

export function getTopFaqs(size = 20): Promise<FaqItem[]> {
  return request.get('/faqs/top', { params: { size } })
}
