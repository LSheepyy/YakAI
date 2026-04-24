import { useRef, useState } from 'react'
import { useApi } from '../../hooks/useApi'
import type { IngestResult, SyllabusData } from '../../types'
import { SyllabusConfirmModal } from './SyllabusConfirmModal'

interface Props {
  classId: string
  onIngested?: (result: IngestResult) => void
}

type State = 'idle' | 'uploading' | 'done' | 'error' | 'duplicate' | 'syllabus_confirm'

export function FileDropZone({ classId, onIngested }: Props) {
  const [state, setState] = useState<State>('idle')
  const [message, setMessage] = useState('')
  const [duplicateResult, setDuplicateResult] = useState<IngestResult | null>(null)
  const [syllabusResult, setSyllabusResult] = useState<IngestResult | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const api = useApi()

  async function handleFile(file: File) {
    setState('uploading')
    setMessage(`Uploading ${file.name}...`)
    try {
      const result = await api.ingestFile(classId, file)
      if (result.duplicate) {
        setState('duplicate')
        setDuplicateResult(result)
        setMessage(`This looks like a file you already added (${result.existing?.original_filename ?? 'unknown'}).`)
      } else if (result.status === 'pending_confirmation') {
        setSyllabusResult(result)
        setState('syllabus_confirm')
      } else {
        setState('done')
        setMessage(`${file.name} processed successfully.`)
        onIngested?.(result)
        setTimeout(() => setState('idle'), 3000)
      }
    } catch (err) {
      setState('error')
      setMessage(err instanceof Error ? err.message : 'Upload failed')
    }
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  function onInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
    e.target.value = ''
  }

  const borderColor: Record<State, string> = {
    idle: 'border-gray-700 hover:border-indigo-600',
    uploading: 'border-indigo-500',
    done: 'border-green-600',
    error: 'border-red-700',
    duplicate: 'border-yellow-600',
    syllabus_confirm: 'border-indigo-500',
  }

  return (
    <>
    <div
      onDrop={onDrop}
      onDragOver={(e) => e.preventDefault()}
      className={`border-2 border-dashed ${borderColor[state]} rounded-xl p-6 text-center transition-colors cursor-pointer`}
      onClick={() => state === 'idle' && inputRef.current?.click()}
      role="button"
      aria-label="Drop files here or click to upload"
    >
      <input ref={inputRef} type="file" className="hidden" onChange={onInputChange} />

      {state === 'idle' && (
        <>
          <p className="text-gray-400 font-medium">Drop any file here</p>
          <p className="text-gray-600 text-sm mt-1">PDF, MP4, MP3, PPTX, JPG, PNG — or click to browse</p>
        </>
      )}

      {state === 'uploading' && (
        <div className="flex items-center justify-center gap-2">
          <div className="w-4 h-4 rounded-full bg-indigo-500 animate-pulse" />
          <span className="text-gray-300 text-sm">{message}</span>
        </div>
      )}

      {state === 'done' && (
        <p className="text-green-400 text-sm font-medium">{message}</p>
      )}

      {state === 'error' && (
        <div>
          <p className="text-red-400 text-sm font-medium">{message}</p>
          <button
            onClick={(e) => { e.stopPropagation(); setState('idle') }}
            className="text-xs text-gray-500 hover:text-gray-300 mt-2 transition-colors"
          >
            Dismiss
          </button>
        </div>
      )}

      {state === 'duplicate' && (
        <div onClick={(e) => e.stopPropagation()}>
          <p className="text-yellow-400 text-sm font-medium mb-3">{message}</p>
          <div className="flex gap-2 justify-center">
            <button
              onClick={() => setState('idle')}
              className="text-sm bg-gray-800 hover:bg-gray-700 text-gray-300 px-4 py-1.5 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={() => {
                setDuplicateResult(null)
                setState('idle')
              }}
              className="text-sm bg-yellow-700 hover:bg-yellow-600 text-white px-4 py-1.5 rounded-lg transition-colors"
            >
              Replace
            </button>
          </div>
        </div>
      )}

      {state === 'syllabus_confirm' && (
        <p className="text-indigo-400 text-sm font-medium">
          Syllabus detected — review the extracted data in the panel above.
        </p>
      )}
    </div>

    {state === 'syllabus_confirm' && syllabusResult?.syllabus_data && (
      <SyllabusConfirmModal
        classId={classId}
        fileId={syllabusResult.file_id}
        data={syllabusResult.syllabus_data as SyllabusData}
        onSaved={() => {
          setState('done')
          setMessage('Syllabus saved successfully.')
          onIngested?.(syllabusResult)
          setTimeout(() => setState('idle'), 3000)
        }}
        onSkip={() => {
          setState('idle')
          setSyllabusResult(null)
        }}
      />
    )}
    </>
  )
}
