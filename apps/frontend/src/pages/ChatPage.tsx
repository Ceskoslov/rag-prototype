import React, { useEffect, useState } from 'react';
import { ChatMessageList } from '@/components/ChatMessageList';
import { ChatInput } from '@/components/ChatInput';
import { KnowledgeBaseSelector } from '@/components/KnowledgeBaseSelector';
import { AgentTracePanel } from '@/components/AgentTracePanel';
import { useChatStore } from '@/stores/chatStore';
import { useChat } from '@/hooks/useChat';

export const ChatPage: React.FC = () => {
  const { messages, isLoading, knowledgeBase, agentTrace, error } = useChatStore();
  const { sendMessage, setKnowledgeBase } = useChat();
  const [knowledgeBases, setKnowledgeBases] = useState<string[]>([]);

  useEffect(() => {
    const apiBase = import.meta.env.VITE_API_BASE_URL || '/api/v1';
    const apiKey = import.meta.env.VITE_API_KEY || 'test-key';
    fetch(`${apiBase}/knowledge-bases`, {
      headers: { 'X-API-Key': apiKey },
    })
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((items: Array<{ name: string }>) =>
        setKnowledgeBases(items.map((item) => item.name)),
      )
      .catch(() => setKnowledgeBases([]));
  }, []);

  return (
    <div className="flex h-screen">
      <aside className="w-64 border-r border-gray-200 p-4 bg-gray-50">
        <div className="mb-6">
          <h1 className="text-xl font-bold text-gray-900">Universal RAG</h1>
          <p className="text-sm text-gray-600 mt-1">Ask questions across your data</p>
        </div>
        <KnowledgeBaseSelector
          value={knowledgeBase}
          options={knowledgeBases}
          onChange={setKnowledgeBase}
        />
      </aside>

      <main className="flex-1 flex flex-col" role="main">
        <header className="border-b border-gray-200 px-6 py-4 bg-white">
          <h2 className="text-lg font-semibold text-gray-900">Chat</h2>
        </header>

        <div className="flex-1 overflow-y-auto">
          <ChatMessageList messages={messages} />
        </div>

        {error && (
          <div className="px-6 py-3 bg-red-50 border-t border-red-200">
            <p className="text-sm text-red-800" role="alert">{error}</p>
          </div>
        )}

        <footer className="border-t border-gray-200 p-4 bg-white">
          <ChatInput onSend={sendMessage} disabled={isLoading} />
        </footer>
      </main>

      {agentTrace && <AgentTracePanel trace={agentTrace} />}
    </div>
  );
};
