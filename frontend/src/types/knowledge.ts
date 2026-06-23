// 知识库相关类型（对齐后端 schemas/knowledge.py）

export interface Category {
  id: number
  parent_id: number
  name: string
  sort: number
  created_at: string
}

export interface KbDocument {
  id: number
  title: string
  category_id: number | null
  source: string | null
  source_level: number | null
  file_name: string | null
  file_type: string | null
  file_size: number | null
  effective_date: string | null
  expire_date: string | null
  confidential_level: number
  parse_status: number // 0待解析 1解析中 2成功 3失败
  index_status: number // 0未索引 1索引中 2已索引 3失败
  status: number // 1上架 0下架
  uploader_id: number | null
  remark: string | null
  created_at: string
  updated_at: string
}

export interface Chunk {
  id: number
  document_id: number
  chunk_index: number
  content: string
  content_tokens: number | null
  heading_path: string | null
  page_no: number | null
  vector_id: string | null
  embedding_model: string | null
  created_at: string
}

export interface IndexTask {
  id: number
  document_id: number
  task_type: number
  status: number
  progress: number
  error_msg: string | null
  started_at: string | null
  finished_at: string | null
  created_at: string
}

export interface Faq {
  id: number
  question: string
  answer: string
  category_id: number | null
  vector_id: string | null
  hit_count: number
  status: number
  created_at: string
  updated_at: string
}

export interface Synonym {
  id: number
  term: string
  synonyms: string
  status: number
  created_at: string
}
