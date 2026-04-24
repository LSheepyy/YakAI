export type FileType =
  | 'pdf' | 'video' | 'audio' | 'image' | 'slides'
  | 'youtube' | 'homework' | 'syllabus' | 'past-exam' | 'notes'

export type EventType = 'exam' | 'quiz' | 'assignment' | 'lab' | 'lecture' | 'other'
export type QuizScope = 'lecture' | 'range' | 'full' | 'weak-areas' | 'past-exam'
export type QuizQuestionType = 'mcq' | 'short-answer' | 'step-by-step' | 'diagram-label' | 'formula'
export type WhisperModel = 'small' | 'medium'
export type ChatRole = 'user' | 'assistant'

export interface User {
  id: string
  name: string
  email: string | null
  major: string | null
  whisper_model: WhisperModel
  last_backup_at: string | null
  created_at: string
}

export interface Semester {
  id: string
  name: string
  user_id: string
  classes?: Class[]
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

export interface Lecture {
  id: string
  class_id: string
  number: number | null
  date: string | null
  title: string | null
  transcript_path: string | null
  reference_file_path: string | null
  created_at: string
}

export interface FileRecord {
  id: string
  class_id: string
  lecture_id: string | null
  original_filename: string
  stored_path: string
  processed_reference_path: string | null
  file_type: FileType
  sha256_hash: string
  text_fingerprint: string | null
  processed_at: string | null
  created_at: string
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
  source_file_id: string | null
  created_at: string
}

export interface TAInfo {
  id: string
  class_id: string
  name: string
  email: string | null
  office_hours: string | null
  source_file_id: string | null
  created_at: string
}

export interface GradingWeight {
  id: string
  class_id: string
  component: string
  weight_pct: number
  source_file_id: string | null
  created_at: string
}

export interface RequiredMaterial {
  id: string
  class_id: string
  material_type: 'textbook' | 'software' | 'equipment' | 'other'
  title: string
  author: string | null
  edition: string | null
  isbn: string | null
  notes: string | null
  added_to_class: number
  source_file_id: string | null
  created_at: string
}

export interface CalendarEvent {
  id: string
  class_id: string
  title: string
  event_date: string
  event_type: EventType
  location: string | null
  notes: string | null
  source_file_id: string | null
  created_at: string
}

export interface CourseScheduleEntry {
  id: string
  class_id: string
  week_number: number | null
  scheduled_date: string | null
  topic: string
  chapters: string | null
  linked_lecture_id: string | null
  source_file_id: string | null
  created_at: string
}

export interface ChatMessage {
  id: string
  class_id: string
  role: ChatRole
  content: string
  created_at: string
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

export interface APIUsageLog {
  id: string
  model: 'gpt-4o' | 'gpt-4o-mini'
  tokens_in: number
  tokens_out: number
  estimated_cost_usd: number
  feature: string
  created_at: string
}

// API contract shapes
export interface CreateSemesterRequest { name: string; user_id: string }
export interface CreateClassRequest {
  semester_id: string
  course_code: string
  course_name: string
  professor?: string
  major?: string
  slug?: string
}
export interface IngestFileResponse {
  file_id: string
  type: FileType
  duplicate: boolean
  existing?: FileRecord
  reference_path: string | null
}
export interface HealthResponse { status: 'ok'; version: string }
export interface SyllabusExtractionResult {
  course: { code: string; name: string; section?: string; credits?: number; schedule?: string }
  professor: { name: string; email?: string; phone?: string; office?: string; hours?: string }
  tas: Array<{ name: string; email?: string; hours?: string }>
  materials: Array<{ type: string; title: string; author?: string; edition?: string; isbn?: string }>
  grading: Array<{ component: string; weight_pct: number }>
  schedule: Array<{ week_or_date: string; topic: string; chapters?: string }>
  events: Array<{ title: string; date: string; type: string; location?: string }>
  policies: { late?: string; attendance?: string; integrity?: string }
}
