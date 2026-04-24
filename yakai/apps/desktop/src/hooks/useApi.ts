import type {
  ChatMessage,
  Class,
  ClassDetail,
  CostSummary,
  CreateClassInput,
  IngestResult,
  QuizAttemptResult,
  QuizQuestion,
  SearchResult,
  Semester,
  TopicPerformance,
} from '../types'

export const SIDECAR_BASE = 'http://localhost:8765'

export function useApi() {
  async function checkHealth(): Promise<boolean> {
    try {
      const res = await fetch(`${SIDECAR_BASE}/health`)
      return res.ok
    } catch {
      return false
    }
  }

  async function fetchSemesters(): Promise<Semester[]> {
    const res = await fetch(`${SIDECAR_BASE}/semesters`)
    if (!res.ok) throw new Error('Failed to fetch semesters')
    return res.json()
  }

  async function createSemester(name: string, userId: string): Promise<Semester> {
    const res = await fetch(`${SIDECAR_BASE}/semesters`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, user_id: userId }),
    })
    if (!res.ok) throw new Error('Failed to create semester')
    const sem = await res.json()
    return { ...sem, classes: sem.classes ?? [] }
  }

  async function createClass(data: CreateClassInput): Promise<Class> {
    const res = await fetch(`${SIDECAR_BASE}/classes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error('Failed to create class')
    return res.json()
  }

  async function renameClass(id: string, courseName: string): Promise<Class> {
    const res = await fetch(`${SIDECAR_BASE}/classes/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ course_name: courseName }),
    })
    if (!res.ok) throw new Error('Failed to rename class')
    return res.json()
  }

  async function deleteClass(id: string): Promise<void> {
    const res = await fetch(`${SIDECAR_BASE}/classes/${id}`, { method: 'DELETE' })
    if (!res.ok) throw new Error('Failed to delete class')
  }

  async function getClass(id: string): Promise<ClassDetail> {
    const res = await fetch(`${SIDECAR_BASE}/classes/${id}`)
    if (!res.ok) throw new Error('Failed to fetch class')
    return res.json()
  }

  async function archiveClass(id: string): Promise<Class> {
    const res = await fetch(`${SIDECAR_BASE}/classes/${id}/archive`, { method: 'PATCH' })
    if (!res.ok) throw new Error('Failed to archive class')
    return res.json()
  }

  async function ingestFile(classId: string, file: File): Promise<IngestResult> {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${SIDECAR_BASE}/classes/${classId}/ingest`, {
      method: 'POST',
      body: form,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }))
      throw new Error(err.detail ?? 'Upload failed')
    }
    return res.json()
  }

  async function confirmSyllabus(
    classId: string,
    fileId: string,
    syllabusData: Record<string, unknown>
  ): Promise<void> {
    const res = await fetch(`${SIDECAR_BASE}/classes/${classId}/syllabus/confirm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_id: fileId, syllabus_data: syllabusData }),
    })
    if (!res.ok) throw new Error('Failed to confirm syllabus')
  }

  async function validateApiKey(apiKey: string): Promise<boolean> {
    try {
      const res = await fetch(`${SIDECAR_BASE}/validate-api-key`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKey }),
      })
      if (!res.ok) return false
      const data = await res.json()
      return data.valid === true
    } catch {
      return false
    }
  }

  async function getChatHistory(classId: string): Promise<ChatMessage[]> {
    const res = await fetch(`${SIDECAR_BASE}/classes/${classId}/chat/messages`)
    if (!res.ok) throw new Error('Failed to fetch chat history')
    return res.json()
  }

  async function sendChatMessage(classId: string, content: string): Promise<ChatMessage> {
    const res = await fetch(`${SIDECAR_BASE}/classes/${classId}/chat/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    })
    if (!res.ok) throw new Error('Failed to send message')
    return res.json()
  }

  async function clearChatHistory(classId: string): Promise<void> {
    const res = await fetch(`${SIDECAR_BASE}/classes/${classId}/chat/messages`, {
      method: 'DELETE',
    })
    if (!res.ok) throw new Error('Failed to clear chat history')
  }

  async function searchClass(
    classId: string,
    query: string,
    filterType?: string
  ): Promise<{ results: SearchResult[] }> {
    const res = await fetch(`${SIDECAR_BASE}/classes/${classId}/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, filter_type: filterType ?? null }),
    })
    if (!res.ok) throw new Error('Search failed')
    return res.json()
  }

  async function generateQuiz(
    classId: string,
    scope: string,
    numQuestions = 10,
    lectureId?: string
  ): Promise<{ session_id: string; questions: QuizQuestion[] }> {
    const res = await fetch(`${SIDECAR_BASE}/classes/${classId}/quiz/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scope,
        num_questions: numQuestions,
        lecture_id: lectureId ?? null,
      }),
    })
    if (!res.ok) throw new Error('Failed to generate quiz')
    return res.json()
  }

  async function submitQuizAttempt(
    sessionId: string,
    questionId: string,
    userAnswer: string,
    hintsUsed: number,
    timeTaken: number
  ): Promise<QuizAttemptResult> {
    const res = await fetch(`${SIDECAR_BASE}/quiz/sessions/${sessionId}/attempt`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question_id: questionId,
        user_answer: userAnswer,
        hints_used: hintsUsed,
        time_taken_seconds: timeTaken,
      }),
    })
    if (!res.ok) throw new Error('Failed to submit answer')
    return res.json()
  }

  async function getPerformance(classId: string): Promise<TopicPerformance[]> {
    const res = await fetch(`${SIDECAR_BASE}/classes/${classId}/performance`)
    if (!res.ok) throw new Error('Failed to fetch performance')
    return res.json()
  }

  async function askHomework(
    classId: string,
    question: string
  ): Promise<{ answer: string; sources: string[]; sufficient_knowledge: boolean }> {
    const res = await fetch(`${SIDECAR_BASE}/classes/${classId}/homework`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    })
    if (!res.ok) throw new Error('Failed to get homework help')
    return res.json()
  }

  async function getCostSummary(): Promise<CostSummary> {
    const res = await fetch(`${SIDECAR_BASE}/settings/cost-summary`)
    if (!res.ok) throw new Error('Failed to fetch cost summary')
    return res.json()
  }

  async function setApiKey(apiKey: string): Promise<{ valid: boolean }> {
    const res = await fetch(`${SIDECAR_BASE}/settings/api-key`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: apiKey }),
    })
    if (!res.ok) throw new Error('Failed to set API key')
    return res.json()
  }

  return {
    checkHealth,
    fetchSemesters,
    createSemester,
    createClass,
    renameClass,
    deleteClass,
    getClass,
    archiveClass,
    ingestFile,
    confirmSyllabus,
    validateApiKey,
    getChatHistory,
    sendChatMessage,
    clearChatHistory,
    searchClass,
    generateQuiz,
    submitQuizAttempt,
    getPerformance,
    askHomework,
    getCostSummary,
    setApiKey,
  }
}
