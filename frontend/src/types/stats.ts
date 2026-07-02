export interface StatsOverview {
  total_questions: number
  no_answer_rate: number
  like_rate: number
  total_documents: number
  indexed_documents: number
}

export interface HotQuestion {
  question: string
  ask_count: number
}
