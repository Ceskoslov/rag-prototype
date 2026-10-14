import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import type { SourceDocument } from '@/stores/chatStore';
import { API_BASE, apiFetch } from '@/lib/api';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceDocument[];
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ role, content, sources = [] }) => {
  const [selected, setSelected] = useState<SourceDocument | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const downloadSource = async (source: SourceDocument) => {
    setDownloadError(null);
    try {
      const response = await apiFetch(`/knowledge-bases/${encodeURIComponent(source.knowledge_base)}/documents/${(source.source_path || '').split('/').map(encodeURIComponent).join('/')}`);
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement('a');
      link.href = url; link.download = source.title; link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (error) { setDownloadError(error instanceof Error ? error.message : 'Download failed') }
  };
  const isUser = role === 'user';
  const markdown = content.replace(/\[(\d+)\]/g, '[$1](#source-$1)');
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[85%] rounded-lg px-4 py-2 ${isUser ? 'bg-blue-100 text-blue-900' : 'bg-gray-100 text-gray-900'}`}>
        {isUser ? <p className="text-sm whitespace-pre-wrap">{content}</p> : <div className="text-sm"><ReactMarkdown components={{
          a: ({ href, children }) => {
            if (href?.startsWith('#source-')) return <button className="text-blue-700 underline" onClick={() => setSelected(sources.find(source => source.citation_id === Number(href.slice(8))) || null)}>{children}</button>;
            return <a href={href} target="_blank" rel="noreferrer">{children}</a>;
          },
        }}>{markdown}</ReactMarkdown></div>}
        {sources.length > 0 && <div className="mt-3 flex flex-wrap gap-2" aria-label="Answer sources">{sources.map((source, index) => <button key={source.citation_id || index} className="text-xs text-blue-700 underline" onClick={() => setSelected(source)}>[{source.citation_id || index + 1}] {source.title}{source.page ? ` · p.${source.page}` : ''}</button>)}</div>}
        {selected && <section className="mt-3 border rounded p-3 bg-white" aria-label="Source evidence">
          <div className="flex justify-between gap-3"><strong>{selected.title}</strong><button onClick={() => setSelected(null)} aria-label="Close source">×</button></div>
          <p className="text-xs text-gray-600">{selected.knowledge_base}{selected.page ? ` · Page ${selected.page}` : ''}</p>
          <pre className="text-xs whitespace-pre-wrap max-h-80 overflow-y-auto mt-2">{selected.content || selected.snippet}</pre>
          {selected.source_path && <a className="text-xs underline text-blue-700" href={`${API_BASE}/knowledge-bases/${encodeURIComponent(selected.knowledge_base)}/documents/${selected.source_path.split('/').map(encodeURIComponent).join('/')}`} onClick={event => { event.preventDefault(); void downloadSource(selected) }} download>Download original</a>}
          {downloadError && <p role="alert" className="text-red-700 text-xs">{downloadError}</p>}
        </section>}
      </div>
    </div>
  );
};
