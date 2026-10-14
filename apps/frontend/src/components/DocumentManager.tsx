import { useCallback, useEffect, useState } from 'react'
import { apiFetch } from '@/lib/api'

interface DocumentItem { source_path: string; size: number; indexed: boolean }
interface Props { knowledgeBase: string; onChanged: () => void }

export function DocumentManager({ knowledgeBase, onChanged }: Props) {
  const [name, setName] = useState(knowledgeBase === 'all' ? '' : knowledgeBase)
  const [file, setFile] = useState<File | null>(null)
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [jobId, setJobId] = useState<string | null>(null)
  const [status, setStatus] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const load = useCallback((signal?: AbortSignal) => {
    if (!name.trim()) return Promise.resolve()
    return apiFetch(`/knowledge-bases/${encodeURIComponent(name)}/documents`, { signal })
      .then(response => response.json())
      .then(items => { if (!signal?.aborted) setDocuments(items) })
      .catch(error => { if (!signal?.aborted) setError(error instanceof Error ? error.message : 'Unable to list documents') })
  }, [name])
  useEffect(() => { const controller = new AbortController(); void load(controller.signal); return () => controller.abort() }, [load])
  useEffect(() => {
    if (!jobId) return
    let stopped = false
    let timeout: ReturnType<typeof setTimeout>
    const poll = async () => {
      try {
        const job = await (await apiFetch(`/jobs/${encodeURIComponent(jobId)}`)).json()
        if (stopped) return
        setStatus(job.progress ? `${job.status} (${job.progress.completed_files}/${job.progress.total_files} files)` : job.status)
        if (job.status === 'complete' || job.status === 'failed') {
          setJobId(null)
          setBusy(false)
          if (job.status === 'failed') setError(job.result?.error || 'Indexing failed')
          await load()
          onChanged()
          return
        }
        timeout = setTimeout(poll, 1500)
      } catch (error) {
        if (stopped) return
        setError(error instanceof Error ? error.message : 'Unable to check job')
        setBusy(false)
        setJobId(null)
      }
    }
    void poll()
    return () => { stopped = true; clearTimeout(timeout) }
  }, [jobId, load, onChanged])
  const mutate = async (path: string, options: RequestInit) => {
    setBusy(true); setError(null)
    try {
      const job = await (await apiFetch(path, options)).json()
      setStatus('queued'); setJobId(job.job_id)
      await load()
      onChanged()
    } catch (error) { setBusy(false); setError(error instanceof Error ? error.message : 'Request failed') }
  }
  const prefix = `/knowledge-bases/${encodeURIComponent(name.trim())}`
  return <section className="p-6 overflow-auto" aria-label="Document management">
    <h2 className="font-semibold text-lg mb-3">Manage documents</h2>
    <form onSubmit={event => { event.preventDefault(); if (file && name.trim()) void mutate(`${prefix}/documents/${encodeURIComponent(file.name)}`, { method: 'PUT', body: file }) }} className="flex flex-wrap gap-3 items-end mb-5">
      <label className="text-sm">Knowledge base<input className="block border rounded p-2" value={name} onChange={event => setName(event.target.value)} placeholder="product_docs" required disabled={busy} pattern="[a-z0-9][a-z0-9_-]*" /></label>
      <label className="text-sm">Document<input className="block" type="file" accept=".md,.txt,.rst,.html,.htm,.json,.csv,.pdf" onChange={event => setFile(event.target.files?.[0] || null)} disabled={busy} /></label>
      <button className="rounded bg-blue-700 text-white px-3 py-2 disabled:opacity-50" disabled={busy || !file || !name.trim()}>Upload and index</button>
      <button type="button" className="border rounded px-3 py-2" disabled={busy || !name.trim()} onClick={() => void mutate(`${prefix}/rebuild`, { method: 'POST' })}>Rebuild index</button>
    </form>
    {status && <p role="status" className="text-sm mb-3">Indexing: {status}</p>}
    {error && <p role="alert" className="text-red-700 mb-3">{error}</p>}
    <table className="w-full text-sm text-left"><thead><tr><th>Document</th><th>Size</th><th>Index</th><th>Action</th></tr></thead><tbody>{documents.map(document => <tr key={document.source_path} className="border-t"><td className="py-3">{document.source_path}</td><td>{Math.ceil(document.size / 1024)} KB</td><td>{document.indexed ? 'Indexed' : 'Pending rebuild'}</td><td><button disabled={busy} className="text-red-700 underline" onClick={() => void mutate(`${prefix}/documents/${document.source_path.split('/').map(encodeURIComponent).join('/')}`, { method: 'DELETE' })}>Delete and re-index</button></td></tr>)}</tbody></table>
    {!documents.length && <p className="text-sm text-gray-500 mt-4">Upload a document to this knowledge base.</p>}
  </section>
}
