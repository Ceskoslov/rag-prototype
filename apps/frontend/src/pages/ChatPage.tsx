import React, { useCallback, useEffect, useState } from 'react';
import { ChatMessageList } from '@/components/ChatMessageList';
import { ChatInput } from '@/components/ChatInput';
import { KnowledgeBaseSelector } from '@/components/KnowledgeBaseSelector';
import { AgentTracePanel } from '@/components/AgentTracePanel';
import { useChatStore } from '@/stores/chatStore';
import { useChat } from '@/hooks/useChat';
import { DocumentManager } from '@/components/DocumentManager';
import { apiFetch } from '@/lib/api';

export const ChatPage: React.FC = () => {
  const { messages, isLoading, knowledgeBase, agentTrace, error, stage, verified, clearMessages, restoreSession } = useChatStore();
  const { sendMessage, setKnowledgeBase, cancel } = useChat();
  const [knowledgeBases, setKnowledgeBases] = useState<string[]>([]);

  const [view, setView] = useState<'chat' | 'documents'>('chat');
  const [sessions, setSessions] = useState<Array<{ session_id: string; knowledge_base: string }>>([]);
  const refresh = useCallback(() => {
    apiFetch('/knowledge-bases').then(response => response.json()).then((items: Array<{ name: string }>) => setKnowledgeBases(items.map(item => item.name))).catch(() => setKnowledgeBases([]));
    apiFetch('/sessions').then(response => response.json()).then(setSessions).catch(() => setSessions([]));
  }, []);
  useEffect(() => { refresh() }, [refresh]);
  const openSession = async (sessionId: string) => {
    try {
      const data = await (await apiFetch(`/sessions/${encodeURIComponent(sessionId)}/messages`)).json();
      restoreSession(data.session_id, data.knowledge_base, data.messages);
      setView('chat');
    } catch (error) { useChatStore.getState().setError(error instanceof Error ? error.message : 'Unable to restore conversation') }
  };

  return (
    <div className="flex h-screen">
      <aside className="w-64 border-r border-gray-200 p-4 bg-gray-50">
        <div className="mb-6">
          <h1 className="text-xl font-bold text-gray-900">Universal RAG</h1>
          <p className="text-sm text-gray-600 mt-1">Ask questions across your data</p>
        </div>
        <KnowledgeBaseSelector
          value={knowledgeBase}
          disabled={isLoading}
          options={knowledgeBases}
          onChange={setKnowledgeBase}
        />
        <button className="mt-4 border rounded px-3 py-2 w-full" disabled={isLoading} onClick={() => { clearMessages(); setView('chat'); refresh() }}>New chat</button>
        <button className="mt-2 border rounded px-3 py-2 w-full" disabled={isLoading} onClick={() => setView('documents')}>Documents</button>
        <label className="block text-sm mt-4">Previous chats<select className="block w-full border rounded p-2 mt-1" value="" disabled={isLoading} onChange={event => { if (event.target.value) void openSession(event.target.value) }}><option value="">Select a chat</option>{sessions.map(session => <option key={session.session_id} value={session.session_id}>{session.knowledge_base} · {session.session_id.slice(0, 8)}</option>)}</select></label>
      </aside>

      <main className="flex-1 flex flex-col" role="main">
        <header className="border-b border-gray-200 px-6 py-4 bg-white">
          <button className="text-lg font-semibold text-gray-900" onClick={() => setView('chat')}>Chat</button>
        </header>

        {view === 'documents' ? <DocumentManager key={knowledgeBase} knowledgeBase={knowledgeBase} onChanged={refresh} /> : <>
        <div className="flex-1 overflow-y-auto">
          <ChatMessageList messages={messages} />
        </div>

        {error && (
          <div className="px-6 py-3 bg-red-50 border-t border-red-200">
            <p className="text-sm text-red-800" role="alert">{error}</p>
          </div>
        )}

        {(isLoading || stage) && <div className="px-6 py-2 text-sm" role="status">{stage}{isLoading ? ' · Draft awaiting verification' : ''}</div>}
        {!isLoading && messages.length > 0 && <p className="px-6 text-xs text-gray-500">{verified ? 'Answer passed the evidence check' : 'Review sources; this answer is not marked verified'}</p>}
        <footer className="border-t border-gray-200 p-4 bg-white">
          <ChatInput onSend={sendMessage} disabled={isLoading} />
          {isLoading && <button className="mt-2 text-sm underline" onClick={cancel}>Stop generating</button>}
        </footer>
        </>}
      </main>

      {agentTrace && <AgentTracePanel trace={agentTrace} />}
    </div>
  );
};
