import { useEffect, useRef, useState } from 'react'
import { useApi } from '../../hooks/useApi'
import type { ChatMessage } from '../../types'

interface Props {
  classId: string
}

function renderContent(text: string) {
  const lines = text.split('\n')
  const elements: React.ReactNode[] = []
  let inCode = false
  let codeBuffer: string[] = []
  let key = 0

  for (const line of lines) {
    if (line.startsWith('```')) {
      if (inCode) {
        elements.push(
          <pre key={key++} className="bg-gray-800 rounded p-2 my-1 text-xs overflow-x-auto text-gray-200">
            {codeBuffer.join('\n')}
          </pre>
        )
        codeBuffer = []
        inCode = false
      } else {
        inCode = true
      }
      continue
    }
    if (inCode) {
      codeBuffer.push(line)
      continue
    }
    const parts = line.split(/(\*\*[^*]+\*\*)/)
    elements.push(
      <span key={key++}>
        {parts.map((p, i) =>
          p.startsWith('**') && p.endsWith('**')
            ? <strong key={i} className="font-semibold text-gray-100">{p.slice(2, -2)}</strong>
            : p
        )}
        <br />
      </span>
    )
  }
  return elements
}

export function ChatScreen({ classId }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [loading, setLoading] = useState(true)
  const bottomRef = useRef<HTMLDivElement>(null)
  const api = useApi()

  useEffect(() => {
    setLoading(true)
    api.getChatHistory(classId)
      .then(setMessages)
      .catch(() => setMessages([]))
      .finally(() => setLoading(false))
  }, [classId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, sending])

  async function handleSend() {
    const content = input.trim()
    if (!content || sending) return
    setInput('')
    setSending(true)

    const optimistic: ChatMessage = {
      id: `temp-${Date.now()}`,
      class_id: classId,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, optimistic])

    try {
      const reply = await api.sendChatMessage(classId, content)
      setMessages((prev) => [...prev, reply])
    } catch {
      setMessages((prev) => prev.filter((m) => m.id !== optimistic.id))
    } finally {
      setSending(false)
    }
  }

  async function handleClear() {
    await api.clearChatHistory(classId).catch(() => null)
    setMessages([])
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Chat header */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-gray-800">
        <span className="text-gray-400 text-sm">Chat — context from all uploaded files</span>
        <button
          onClick={handleClear}
          className="text-gray-600 hover:text-gray-400 text-xs transition-colors"
        >
          Clear history
        </button>
      </div>

      {/* Message list */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {loading && (
          <div className="flex justify-center py-8">
            <div className="w-4 h-4 rounded-full bg-indigo-500 animate-pulse" />
          </div>
        )}
        {!loading && messages.length === 0 && (
          <p className="text-center text-gray-600 text-sm mt-16">
            Ask anything about your class materials.
          </p>
        )}
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-indigo-600 text-white rounded-br-sm'
                  : 'bg-gray-800 text-gray-200 rounded-bl-sm'
              }`}
            >
              {renderContent(msg.content)}
            </div>
          </div>
        ))}
        {sending && (
          <div className="flex justify-start">
            <div className="bg-gray-800 text-gray-400 rounded-2xl rounded-bl-sm px-4 py-2.5 text-sm">
              YakAI is thinking...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="px-6 py-4 border-t border-gray-800">
        <div className="flex gap-3 items-end">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your class materials… (Enter to send)"
            rows={2}
            className="flex-1 bg-gray-900 border border-gray-700 rounded-xl px-4 py-2.5 text-gray-100 text-sm placeholder-gray-600 resize-none focus:outline-none focus:border-indigo-500 transition-colors"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || sending}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm px-4 py-2.5 rounded-xl transition-colors whitespace-nowrap"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
