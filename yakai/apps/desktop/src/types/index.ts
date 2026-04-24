export type FileType =
  | 'pdf' | 'video' | 'audio' | 'image' | 'slides'
  | 'youtube' | 'homework' | 'syllabus' | 'past-exam' | 'notes'

export type EventType = 'exam' | 'quiz' | 'assignment' | 'lab' | 'lecture' | 'other'

export interface Semester {
  id: string
  name: string
  user_id: string
  classes: Class[]
}

export interface Class {
  id: string
  semester_id: string
  course_code: string
  course_name: string
  slug: string
  professor: string | null
  major: string | null
  brain_file_path: string | null
  inherited_from_class_id: string | null
  is_archived: number
  created_at: string
}

export interface ClassDetail extends Class {
  professor_info: ProfessorInfo | null
  ta_info: TAInfo[]
  grading_weights: GradingWeight[]
  lectures: Lecture[]
  required_materials: RequiredMaterial[]
}

export interface ProfessorInfo {
  id: string
  class_id: string
  name: string
  email: string | null
  phone: string | null
  office_location: string | null
  office_hours: string | null
  department: string | null
}

export interface TAInfo {
  id: string
  class_id: string
  name: string
  email: string | null
  office_hours: string | null
}

export interface GradingWeight {
  id: string
  class_id: string
  component: string
  weight_pct: number
}

export interface Lecture {
  id: string
  class_id: string
  number: number | null
  date: string | null
  title: string | null
  reference_file_path: string | null
  created_at: string
}

export interface RequiredMaterial {
  id: string
  class_id: string
  material_type: string
  title: string
  author: string | null
  edition: string | null
  isbn: string | null
  added_to_class: number
}

export interface SyllabusData {
  course?: { title?: string; code?: string; description?: string }
  professor?: { name?: string; email?: string; office?: string; office_hours?: string }
  tas?: Array<{ name?: string; email?: string; office_hours?: string }>
  materials?: Array<{ type?: string; title?: string; author?: string; isbn?: string }>
  grading?: Array<{ component?: string; weight?: number }>
  schedule?: Array<{ week?: number; date?: string; topic?: string; chapters?: string }>
  events?: Array<{ title?: string; date?: string; type?: string }>
  policies?: string[]
}

export interface IngestResult {
  file_id: string
  type: FileType
  duplicate: boolean
  existing?: {
    id: string
    original_filename: string
    created_at: string
  }
  reference_path: string | null
  status?: 'pending_confirmation'
  syllabus_data?: SyllabusData
}

export interface CreateClassInput {
  semester_id: string
  course_code: string
  course_name: string
  professor?: string
  major?: string
}

export interface ChatMessage {
  id: string
  class_id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface QuizQuestion {
  id: string
  session_id: string
  question_text: string
  correct_answer: string
  question_type: 'mcq' | 'short-answer' | 'step-by-step' | 'diagram-label' | 'formula'
  hint_level_1: string | null
  hint_level_2: string | null
  hint_level_3: string | null
  source_lecture_id: string | null
  source_file_id: string | null
  topic_tag: string | null
  options?: string[]
}

export interface QuizAttemptResult {
  is_correct: boolean
  correct_answer: string
  explanation: string
}

export interface TopicPerformance {
  id: string
  class_id: string
  topic_tag: string
  total_attempts: number
  correct_count: number
  accuracy_rate: number
  last_updated: string
}

export interface SearchResult {
  source_name: string
  excerpt: string
  file_type: string
  relevance_score: number
}

export interface CostSummary {
  total_cost: number
  by_feature: Record<string, number>
  by_model: Record<string, number>
}
