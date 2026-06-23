import request, { getToken } from './request'
import type { PageResult } from '@/types/api'
import type { Category, Chunk, Faq, IndexTask, KbDocument, Synonym } from '@/types/knowledge'

// ---------------- 分类 ----------------
export function listCategories(): Promise<Category[]> {
  return request.get('/categories')
}
export function createCategory(payload: { name: string; parent_id?: number; sort?: number }): Promise<Category> {
  return request.post('/categories', payload)
}
export function updateCategory(id: number, payload: Partial<Category>): Promise<Category> {
  return request.put(`/categories/${id}`, payload)
}
export function deleteCategory(id: number): Promise<unknown> {
  return request.delete(`/categories/${id}`)
}

// ---------------- 文档 ----------------
export interface DocumentQuery {
  page?: number
  size?: number
  keyword?: string
  category_id?: number
  status?: number
  index_status?: number
}

export function listDocuments(params: DocumentQuery): Promise<PageResult<KbDocument>> {
  return request.get('/documents', { params })
}

export function getDocument(id: number): Promise<KbDocument> {
  return request.get(`/documents/${id}`)
}

/** 上传文档（multipart）。用原生 fetch 以正确处理 FormData 与统一解包。 */
export async function uploadDocument(form: FormData): Promise<KbDocument> {
  const base = import.meta.env.VITE_API_BASE
  const token = getToken()
  const resp = await fetch(`${base}/documents`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  })
  const body = await resp.json()
  if (body.code !== 0) throw new Error(body.message || '上传失败')
  return body.data
}

export function updateDocument(id: number, payload: Partial<KbDocument>): Promise<KbDocument> {
  return request.put(`/documents/${id}`, payload)
}

export function deleteDocument(id: number): Promise<unknown> {
  return request.delete(`/documents/${id}`)
}

export function parseDocument(id: number): Promise<IndexTask> {
  return request.post(`/documents/${id}/parse`)
}

export function indexDocument(id: number): Promise<IndexTask> {
  return request.post(`/documents/${id}/index`)
}

export function listChunks(id: number): Promise<Chunk[]> {
  return request.get(`/documents/${id}/chunks`)
}

// ---------------- FAQ ----------------
export interface FaqQuery {
  page?: number
  size?: number
  keyword?: string
  status?: number
}
export function listFaqs(params: FaqQuery): Promise<PageResult<Faq>> {
  return request.get('/faqs', { params })
}
export function createFaq(payload: { question: string; answer: string; category_id?: number }): Promise<Faq> {
  return request.post('/faqs', payload)
}
export function updateFaq(id: number, payload: Partial<Faq>): Promise<Faq> {
  return request.put(`/faqs/${id}`, payload)
}
export function deleteFaq(id: number): Promise<unknown> {
  return request.delete(`/faqs/${id}`)
}

// ---------------- 同义词 ----------------
export interface SynonymQuery {
  page?: number
  size?: number
  keyword?: string
  status?: number
}
export function listSynonyms(params: SynonymQuery): Promise<PageResult<Synonym>> {
  return request.get('/synonyms', { params })
}
export function createSynonym(payload: { term: string; synonyms: string }): Promise<Synonym> {
  return request.post('/synonyms', payload)
}
export function updateSynonym(id: number, payload: Partial<Synonym>): Promise<Synonym> {
  return request.put(`/synonyms/${id}`, payload)
}
export function deleteSynonym(id: number): Promise<unknown> {
  return request.delete(`/synonyms/${id}`)
}
